"""
Tests for circuit connection generator.
"""

import pytest
from pcba.circuit_generator import ConnectionGenerator


class TestSeriesConnections:
    """Test series connection generation."""

    def setup_method(self):
        self.gen = ConnectionGenerator()

    def test_series_two_leds_with_resistor(self):
        components = [
            {'ref': 'R1', 'type': 'resistor', 'value': '330'},
            {'ref': 'D1', 'type': 'led', 'value': 'RED'},
            {'ref': 'D2', 'type': 'led', 'value': 'RED'},
        ]
        conns = self.gen.generate_connections(components, 'series')

        # Should have: source→R1, R1→LED1, LED1→LED2, LED2→GND
        assert len(conns) >= 4

        # Verify chain: R1→D1→D2→GND
        targets = [c['to'] for c in conns]
        assert any('R1:1' in t for t in targets)
        assert any('D1:2' in t for t in targets)
        assert any('D2:2' in t for t in targets)
        assert any('GND' in t for t in targets)

    def test_series_with_mcu_pin(self):
        components = [
            {'ref': 'R1', 'type': 'resistor', 'value': '330'},
            {'ref': 'D1', 'type': 'led', 'value': 'RED'},
        ]
        conns = self.gen.generate_connections(components, 'series', mcu_pin='5')

        sources = [c['from'] for c in conns]
        assert any('Arduino:Pin5' in s for s in sources)

    def test_series_single_led(self):
        components = [
            {'ref': 'R1', 'type': 'resistor', 'value': '330'},
            {'ref': 'D1', 'type': 'led', 'value': 'RED'},
        ]
        conns = self.gen.generate_connections(components, 'series')

        # source→R1→LED→GND = 3 connections
        assert len(conns) >= 3


class TestParallelConnections:
    """Test parallel connection generation."""

    def setup_method(self):
        self.gen = ConnectionGenerator()

    def test_parallel_two_leds_shared_resistor(self):
        components = [
            {'ref': 'R1', 'type': 'resistor', 'value': '330'},
            {'ref': 'D1', 'type': 'led', 'value': 'RED'},
            {'ref': 'D2', 'type': 'led', 'value': 'RED'},
        ]
        conns = self.gen.generate_connections(components, 'parallel')

        # Should have: source→R1, R1→D1, D1→GND, R1→D2, D2→GND
        assert len(conns) >= 5

        # Both LEDs should connect to GND
        gnd_conns = [c for c in conns if c['to'] == 'GND']
        assert len(gnd_conns) >= 2

    def test_parallel_individual_resistors(self):
        components = [
            {'ref': 'R1', 'type': 'resistor', 'value': '330'},
            {'ref': 'R2', 'type': 'resistor', 'value': '330'},
            {'ref': 'D1', 'type': 'led', 'value': 'RED'},
            {'ref': 'D2', 'type': 'led', 'value': 'RED'},
        ]
        conns = self.gen.generate_connections(components, 'parallel')

        # Each LED should have its own resistor connection
        assert len(conns) >= 6

    def test_parallel_with_mcu_pin(self):
        components = [
            {'ref': 'R1', 'type': 'resistor', 'value': '330'},
            {'ref': 'D1', 'type': 'led', 'value': 'RED'},
            {'ref': 'D2', 'type': 'led', 'value': 'RED'},
        ]
        conns = self.gen.generate_connections(components, 'parallel', mcu_pin='13')

        sources = [c['from'] for c in conns]
        assert any('Arduino:Pin13' in s for s in sources)


class TestCustomConnections:
    """Test custom/fallback connection generation."""

    def setup_method(self):
        self.gen = ConnectionGenerator()

    def test_custom_mcu_component(self):
        components = [
            {'ref': 'U1', 'type': 'mcu', 'name': 'ATmega328P'},
        ]
        conns = self.gen.generate_connections(components, 'custom')

        # Should get VCC and GND connections
        nets = [c['net'] for c in conns]
        assert 'VCC' in nets
        assert 'GND' in nets

    def test_no_components(self):
        conns = self.gen.generate_connections([], 'parallel')
        assert conns == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
