"""
Tests for enhanced AI circuit analyzer.
"""

import pytest
from pcba.ai_analyzer import EnhancedCircuitAnalyzer, WORD_NUMBERS


class FakeLLMClient:
    """Fake LLM client that always raises to trigger fallback."""
    def generate(self, prompt: str) -> str:
        raise RuntimeError("LLM unavailable (test)")


class TestQuantityExtraction:
    """Test that component quantities are correctly extracted."""

    def setup_method(self):
        self.analyzer = EnhancedCircuitAnalyzer(FakeLLMClient())

    def test_two_leds(self):
        result = self.analyzer.analyze("two LED with 330 ohm resistor")
        leds = [c for c in result['components'] if c['type'] == 'led']
        assert len(leds) == 2
        assert leds[0]['ref'] != leds[1]['ref']

    def test_three_resistors(self):
        result = self.analyzer.analyze("three 10k resistors as pull-ups")
        resistors = [c for c in result['components'] if c['type'] == 'resistor']
        assert len(resistors) == 3
        assert resistors[0]['ref'] == 'R1'
        assert resistors[1]['ref'] == 'R2'
        assert resistors[2]['ref'] == 'R3'

    def test_numeric_quantity(self):
        result = self.analyzer.analyze("5 LEDs in parallel")
        leds = [c for c in result['components'] if c['type'] == 'led']
        assert len(leds) == 5

    def test_single_led_no_quantity(self):
        result = self.analyzer.analyze("LED with resistor")
        leds = [c for c in result['components'] if c['type'] == 'led']
        assert len(leds) == 1

    def test_auto_adds_resistor_for_led(self):
        result = self.analyzer.analyze("two LED")
        resistors = [c for c in result['components'] if c['type'] == 'resistor']
        assert len(resistors) >= 1, "Should auto-add current-limiting resistor"


class TestConnectionTypeInference:
    """Test series/parallel detection."""

    def setup_method(self):
        self.analyzer = EnhancedCircuitAnalyzer(FakeLLMClient())

    def test_series_keyword(self):
        result = self.analyzer.analyze("two LED in series with 330 ohm resistor")
        assert result['configuration'] == 'series'

    def test_parallel_keyword(self):
        result = self.analyzer.analyze("two LED in parallel with 330 ohm resistor")
        assert result['configuration'] == 'parallel'

    def test_default_parallel(self):
        result = self.analyzer.analyze("two LED with resistor")
        assert result['configuration'] == 'parallel'


class TestMCUPinExtraction:
    """Test MCU pin extraction from description."""

    def setup_method(self):
        self.analyzer = EnhancedCircuitAnalyzer(FakeLLMClient())

    def test_arduino_pin(self):
        result = self.analyzer.analyze("LED with resistor to Arduino pin 5")
        assert result.get('mcu_pin') is not None

    def test_gpio_pin(self):
        result = self.analyzer.analyze("LED connected to GPIO 13")
        assert result.get('mcu_pin') is not None


class TestValueExtraction:
    """Test component value extraction."""

    def setup_method(self):
        self.analyzer = EnhancedCircuitAnalyzer(FakeLLMClient())

    def test_ohm_value(self):
        result = self.analyzer.analyze("LED with 330 ohm resistor")
        resistors = [c for c in result['components'] if c['type'] == 'resistor']
        assert any(r['value'] == '330' for r in resistors)

    def test_k_ohm_value(self):
        result = self.analyzer.analyze("10k resistor pull-up")
        resistors = [c for c in result['components'] if c['type'] == 'resistor']
        assert len(resistors) >= 1


class TestReferenceAssignment:
    """Test unique reference designator generation."""

    def setup_method(self):
        self.analyzer = EnhancedCircuitAnalyzer(FakeLLMClient())

    def test_unique_refs(self):
        result = self.analyzer.analyze("three LED with two resistors")
        refs = [c['ref'] for c in result['components']]
        assert len(refs) == len(set(refs)), f"Duplicate refs found: {refs}"

    def test_correct_prefixes(self):
        result = self.analyzer.analyze("two LED with 330 ohm resistor")
        for comp in result['components']:
            if comp['type'] == 'led':
                assert comp['ref'].startswith('D'), f"LED should have D prefix, got {comp['ref']}"
            elif comp['type'] == 'resistor':
                assert comp['ref'].startswith('R'), f"Resistor should have R prefix, got {comp['ref']}"


class TestFootprintAssignment:
    """Test automatic footprint assignment."""

    def setup_method(self):
        self.analyzer = EnhancedCircuitAnalyzer(FakeLLMClient())

    def test_footprints_assigned(self):
        result = self.analyzer.analyze("LED with resistor")
        for comp in result['components']:
            assert 'footprint' in comp, f"Component {comp['ref']} missing footprint"


class TestWordNumbers:
    """Test word-to-number mapping."""

    def test_common_words(self):
        assert WORD_NUMBERS['one'] == 1
        assert WORD_NUMBERS['two'] == 2
        assert WORD_NUMBERS['three'] == 3
        assert WORD_NUMBERS['ten'] == 10

    def test_aliases(self):
        assert WORD_NUMBERS['a'] == 1
        assert WORD_NUMBERS['pair'] == 2
        assert WORD_NUMBERS['dual'] == 2
        assert WORD_NUMBERS['triple'] == 3


class TestClarifyingQuestions:
    """Test that questions are generated for ambiguous descriptions."""

    def setup_method(self):
        self.analyzer = EnhancedCircuitAnalyzer(FakeLLMClient())

    def test_multiple_leds_no_config(self):
        result = self.analyzer.analyze("two LED with resistor")
        # Should ask about series/parallel
        questions = result.get('questions', [])
        assert any('series' in q.lower() or 'parallel' in q.lower() for q in questions)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
