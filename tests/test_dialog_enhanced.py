"""
Tests for enhanced dialog manager.
"""

import pytest
from pcba.dialog_enhanced import DialogManager, CHOICE_TEMPLATES


class TestDialogManagerNonInteractive:
    """Test dialog manager in non-interactive mode (uses defaults)."""

    def setup_method(self):
        self.dialog = DialogManager(interactive=False)

    def test_led_color_default(self):
        answers = self.dialog.ask_questions(["What color should the LEDs be?"])
        assert 'led_color' in answers
        assert answers['led_color'] == 'Red'

    def test_connection_type_default(self):
        answers = self.dialog.ask_questions(["Should the LEDs be in series or parallel?"])
        assert 'configuration' in answers
        assert answers['configuration'] == 'parallel'

    def test_multiple_questions(self):
        answers = self.dialog.ask_questions([
            "What color should the LEDs be?",
            "Should the LEDs be in series or parallel?",
        ])
        assert len(answers) == 2

    def test_unknown_question_skipped(self):
        answers = self.dialog.ask_questions(["What is the meaning of life?"])
        assert len(answers) == 1  # Still adds with empty value


class TestDialogUpdateAnalysis:
    """Test analysis update based on answers."""

    def setup_method(self):
        self.dialog = DialogManager(interactive=False)

    def test_update_configuration(self):
        analysis = {
            'configuration': 'parallel',
            'components': [
                {'type': 'led', 'value': 'RED'},
            ],
        }
        updated = self.dialog.update_analysis(analysis, {'configuration': 'series'})
        assert updated['configuration'] == 'series'

    def test_update_led_color(self):
        analysis = {
            'components': [
                {'type': 'led', 'value': 'RED'},
                {'type': 'led', 'value': 'RED'},
                {'type': 'resistor', 'value': '330'},
            ],
        }
        updated = self.dialog.update_analysis(analysis, {'led_color': 'Blue'})
        leds = [c for c in updated['components'] if c['type'] == 'led']
        assert all(led['value'] == 'BLUE' for led in leds)
        # Resistor should be unchanged
        resistors = [c for c in updated['components'] if c['type'] == 'resistor']
        assert resistors[0]['value'] == '330'

    def test_update_supply_voltage(self):
        analysis = {'power': {'positive': '+5V', 'ground': 'GND'}}
        updated = self.dialog.update_analysis(analysis, {'supply_voltage': '3.3V'})
        assert updated['power']['positive'] == '+3.3V'


class TestChoiceTemplates:
    """Test predefined choice templates."""

    def test_led_color_template_exists(self):
        assert 'led_color' in CHOICE_TEMPLATES
        assert 'choices' in CHOICE_TEMPLATES['led_color']

    def test_led_connection_template(self):
        template = CHOICE_TEMPLATES['led_connection']
        assert 'parallel' in template['values']
        assert 'series' in template['values']

    def test_all_templates_have_defaults(self):
        for name, template in CHOICE_TEMPLATES.items():
            assert 'default' in template, f"Template {name} missing default"
            assert 'choices' in template, f"Template {name} missing choices"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
