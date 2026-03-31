"""
Enhanced dialog manager for circuit design.

Handles clarifying questions, user input, and analysis updates
during interactive schematic generation.
"""

from typing import Any


# Predefined choices for common questions
CHOICE_TEMPLATES: dict[str, dict[str, Any]] = {
    'led_color': {
        'question': 'What color should the LEDs be?',
        'choices': ['Red', 'Green', 'Blue', 'White', 'Yellow', 'Orange'],
        'default': 'Red',
        'key': 'led_color',
    },
    'led_connection': {
        'question': 'How should the LEDs be connected?',
        'choices': ['In parallel (side by side)', 'In series (one after another)'],
        'default': 'In parallel (side by side)',
        'key': 'configuration',
        'values': ['parallel', 'series'],
    },
    'resistor_value': {
        'question': 'What resistance value should be used?',
        'choices': ['220 Ω', '330 Ω', '470 Ω', '1 kΩ', '4.7 kΩ', '10 kΩ'],
        'default': '330 Ω',
        'key': 'resistor_value',
        'values': ['220', '330', '470', '1k', '4.7k', '10k'],
    },
    'power_voltage': {
        'question': 'What supply voltage?',
        'choices': ['3.3V', '5V', '9V', '12V'],
        'default': '5V',
        'key': 'supply_voltage',
        'values': ['3.3V', '5V', '9V', '12V'],
    },
}


class DialogManager:
    """Manages interactive dialog for circuit clarification.

    In non-interactive mode (default), uses defaults for all questions.
    In interactive mode, prompts the user via stdin.
    """

    def __init__(self, interactive: bool = False):
        self.interactive = interactive
        self.answers: dict[str, Any] = {}

    def ask_questions(self, questions: list[str]) -> dict[str, Any]:
        """Process a list of questions and return answers.

        Args:
            questions: List of question strings from the AI analyzer

        Returns:
            Dict mapping question keys to answer values
        """
        for question in questions:
            template = self._match_template(question)
            if template:
                answer = self._ask_with_choices(template)
            else:
                answer = self._ask_freeform(question)
            self.answers[self._question_key(question)] = answer

        return self.answers

    def update_analysis(
        self, analysis: dict[str, Any], answers: dict[str, Any]
    ) -> dict[str, Any]:
        """Update circuit analysis based on user answers.

        Args:
            analysis: Original circuit analysis dict
            answers: User answers from ask_questions()

        Returns:
            Updated analysis dict
        """
        updated = analysis.copy()

        for key, value in answers.items():
            # Update configuration
            if key == 'configuration':
                updated['configuration'] = value

            # Update LED colors
            elif key == 'led_color':
                for comp in updated.get('components', []):
                    if comp.get('type') == 'led':
                        comp['value'] = value.upper()

            # Update resistor values
            elif key == 'resistor_value':
                for comp in updated.get('components', []):
                    if comp.get('type') == 'resistor':
                        comp['value'] = value

            # Update supply voltage
            elif key == 'supply_voltage':
                power = updated.get('power', {})
                power['positive'] = f"+{value}"
                updated['power'] = power

        return updated

    def _match_template(self, question: str) -> dict[str, Any] | None:
        """Match a question to a predefined template."""
        q_lower = question.lower()

        if 'color' in q_lower and 'led' in q_lower:
            return CHOICE_TEMPLATES['led_color']
        if 'series' in q_lower or 'parallel' in q_lower or 'connect' in q_lower:
            return CHOICE_TEMPLATES['led_connection']
        if 'resistance' in q_lower or 'resistor' in q_lower and 'value' in q_lower:
            return CHOICE_TEMPLATES['resistor_value']
        if 'voltage' in q_lower or 'supply' in q_lower:
            return CHOICE_TEMPLATES['power_voltage']

        return None

    def _ask_with_choices(self, template: dict[str, Any]) -> Any:
        """Ask a multiple-choice question."""
        question = template['question']
        choices = template['choices']
        default = template['default']
        values = template.get('values', choices)

        if not self.interactive:
            # Non-interactive: use default
            default_idx = choices.index(default) if default in choices else 0
            print(f"  ? {question} → {default} (default)")
            return values[default_idx]

        # Interactive mode
        print(f"\n  {question}")
        for i, choice in enumerate(choices, 1):
            marker = '*' if choice == default else ' '
            print(f"    {marker} {i}) {choice}")

        while True:
            try:
                raw = input(f"  Your choice [1-{len(choices)}, default={choices.index(default)+1}]: ").strip()
                if not raw:
                    idx = choices.index(default)
                    return values[idx]
                num = int(raw) - 1
                if 0 <= num < len(choices):
                    return values[num]
                print(f"  Please enter 1-{len(choices)}")
            except (ValueError, EOFError):
                idx = choices.index(default)
                return values[idx]

    def _ask_freeform(self, question: str) -> str:
        """Ask a free-form question."""
        if not self.interactive:
            print(f"  ? {question} → (skipped, using defaults)")
            return ''

        try:
            return input(f"  {question}: ").strip()
        except EOFError:
            return ''

    def _question_key(self, question: str) -> str:
        """Generate a key from a question string."""
        q_lower = question.lower()
        if 'color' in q_lower:
            return 'led_color'
        if 'series' in q_lower or 'parallel' in q_lower:
            return 'configuration'
        if 'resistance' in q_lower or 'resistor' in q_lower:
            return 'resistor_value'
        if 'voltage' in q_lower:
            return 'supply_voltage'
        # Fallback: sanitize question text
        return q_lower[:30].replace(' ', '_').replace('?', '')
