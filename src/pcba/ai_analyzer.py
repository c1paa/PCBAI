"""
AI Circuit Analyzer — enhanced circuit description analysis.

Extracts component quantities, connection types, pin assignments,
and generates clarifying questions when information is ambiguous.
"""

import json
import re
from typing import Any


# Word-to-number mapping for quantity extraction
WORD_NUMBERS = {
    'one': 1, 'a': 1, 'an': 1, 'single': 1,
    'two': 2, 'double': 2, 'pair': 2, 'dual': 2,
    'three': 3, 'triple': 3,
    'four': 4, 'quad': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9,
    'ten': 10,
}

# Footprint database for component types
FOOTPRINT_DB = {
    'resistor': 'Resistor_SMD:R_0805_2012Metric',
    'capacitor': 'Capacitor_SMD:C_0805_2012Metric',
    'led': 'LED_SMD:LED_0805_2012Metric',
    'diode': 'Diode_SMD:D_SOD-123',
    'npn': 'Package_TO_SOT_SMD:SOT-23',
    'pnp': 'Package_TO_SOT_SMD:SOT-23',
    'inductor': 'Inductor_SMD:L_0805_2012Metric',
}

# Reference prefix mapping
REF_PREFIX = {
    'resistor': 'R',
    'capacitor': 'C',
    'led': 'D',
    'diode': 'D',
    'npn': 'Q',
    'pnp': 'Q',
    'inductor': 'L',
    'connector': 'J',
    'mcu': 'U',
    'sensor': 'U',
    'ic': 'U',
    'crystal': 'Y',
    'switch': 'SW',
}


ENHANCED_ANALYSIS_PROMPT = r"""You are an expert electronics engineer. Analyze the circuit description and return ONLY valid JSON.

RULES FOR QUANTITY:
- "two LED" = quantity: 2
- "3 resistors" = quantity: 3
- "LED" (no number) = quantity: 1
- "a LED" or "an LED" = quantity: 1
- Always extract the exact number mentioned

RULES FOR CONNECTIONS:
- If multiple LEDs without specified connection type → default to "parallel"
- "in series" → configuration: "series"
- "in parallel" → configuration: "parallel"
- Always include a current-limiting resistor before LEDs unless explicitly stated otherwise

RULES FOR MCU PINS:
- "Arduino pin 5" → mcu_pin: "5"
- "GPIO 13" → mcu_pin: "13"
- "pin D2" → mcu_pin: "D2"

JSON FORMAT (strict, no markdown, no explanations):
{
  "circuit_type": "led_array|sensor_circuit|mcu_project|power_supply|custom",
  "components": [
    {
      "type": "resistor|capacitor|led|diode|npn|pnp|inductor|mcu|arduino|sensor",
      "value": "330",
      "quantity": 2,
      "purpose": "current limiting"
    }
  ],
  "configuration": "series|parallel|custom",
  "mcu_pin": null,
  "power": {"positive": "+5V", "ground": "GND"},
  "questions": []
}

EXAMPLE INPUT: "two LED with 330 ohm resistor to Arduino pin 5"
EXAMPLE OUTPUT:
{
  "circuit_type": "led_array",
  "components": [
    {"type": "resistor", "value": "330", "quantity": 1, "purpose": "current limiting"},
    {"type": "led", "value": "RED", "quantity": 2},
    {"type": "arduino", "value": "Arduino UNO R3", "quantity": 1}
  ],
  "configuration": "parallel",
  "mcu_pin": "5",
  "power": {"positive": "+5V", "ground": "GND"},
  "questions": ["What color should the LEDs be?", "Should the LEDs be in series or parallel?"]
}

NOW ANALYZE:
"""


class EnhancedCircuitAnalyzer:
    """Enhanced AI circuit analyzer with quantity extraction and connection inference."""

    def __init__(self, llm_client: Any):
        self.client = llm_client

    def analyze(self, description: str) -> dict[str, Any]:
        """Analyze circuit description using LLM + local post-processing.

        Returns structured circuit data with expanded components and connections.
        """
        # Try LLM analysis first
        try:
            analysis = self._llm_analyze(description)
        except Exception as e:
            print(f"LLM analysis failed ({e}), using fallback")
            analysis = self._fallback_analyze(description)

        # Post-process: auto-add current-limiting resistor for LEDs
        components = analysis.get('components', [])
        has_led = any(c.get('type') == 'led' for c in components)
        has_resistor = any(c.get('type') == 'resistor' for c in components)
        if has_led and not has_resistor:
            components.insert(0, {
                'type': 'resistor', 'value': '330', 'quantity': 1,
                'purpose': 'current limiting',
            })

        # Expand quantities
        analysis['components'] = self._expand_quantities(components)

        # Assign references
        self._assign_references(analysis['components'])

        # Assign footprints AND lib_ids
        self._assign_footprints(analysis['components'])
        self._assign_lib_ids(analysis['components'])

        # Validate symbols BEFORE returning
        from .runtime_verifier import SymbolVerifier
        verifier = SymbolVerifier()
        validation = verifier.verify_components(analysis['components'])
        
        if not validation.valid and validation.suggestions:
            # Auto-fix with suggestions
            print(f"\n  Auto-fixing symbols...")
            for comp in analysis['components']:
                lib_id = comp.get('lib_id', '')
                if lib_id in validation.missing_symbols:
                    similar = verifier._find_similar_symbol(lib_id)
                    if similar:
                        print(f"    {lib_id} → {similar}")
                        comp['lib_id'] = similar

        return analysis

    def _assign_lib_ids(self, components: list[dict]) -> None:
        """Assign lib_id to components that don't have one."""
        lib_id_map = {
            'resistor': 'Device:R',
            'capacitor': 'Device:C',
            'led': 'Device:LED',
            'diode': 'Device:D',
            'arduino': 'MCU_Module:Arduino_UNO_R3',
            'mcu': 'MCU_Module:Arduino_UNO_R3',  # Use Arduino for all MCU types
        }
        
        for comp in components:
            if 'lib_id' not in comp:
                comp_type = comp.get('type', 'unknown')
                comp['lib_id'] = lib_id_map.get(comp_type, 'Device:GenericSensor')
            elif comp.get('lib_id') == 'MCU_Microchip_ATmega:ATmega328P-AU':
                # Auto-fix: ATmega328P-AU doesn't exist, use Arduino_UNO_R3
                comp['lib_id'] = 'MCU_Module:Arduino_UNO_R3'

    def _llm_analyze(self, description: str) -> dict[str, Any]:
        """Use LLM to analyze circuit description."""
        prompt = ENHANCED_ANALYSIS_PROMPT + description
        response = self.client.generate(prompt)

        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(response)

    def _fallback_analyze(self, description: str) -> dict[str, Any]:
        """Local fallback analysis using regex patterns."""
        desc = description.lower()
        components: list[dict] = []
        configuration = 'parallel'
        mcu_pin = None

        # Extract connection type
        if 'in series' in desc or 'series' in desc:
            configuration = 'series'
        elif 'in parallel' in desc or 'parallel' in desc:
            configuration = 'parallel'

        # Extract MCU pin
        pin_match = re.search(r'(?:arduino|mcu|gpio|pin)\s*(?:pin\s*)?(\w+)', desc)
        if pin_match:
            mcu_pin = pin_match.group(1)

        # Extract components with quantities
        # Patterns allow optional value between quantity and component name
        # e.g., "three 10k resistors", "two red LEDs", "5 100nF capacitors"
        component_patterns = [
            (r'(\w+)\s+(?:[\d.]+[kKmM]?\s*(?:ohm|Ω)?\s+)?resistors?', 'resistor'),
            (r'(\w+)\s+(?:\w+\s+)?leds?', 'led'),
            (r'(\w+)\s+(?:[\d.]+\s*(?:n|u|p|µ)?[fF]\s+)?capacitors?', 'capacitor'),
            (r'(\w+)\s+diodes?', 'diode'),
            (r'(\w+)\s+inductors?', 'inductor'),
        ]

        for pattern, comp_type in component_patterns:
            match = re.search(pattern, desc)
            if match:
                qty_str = match.group(1)
                qty = self._parse_quantity(qty_str)
                value = self._extract_value(desc, comp_type)
                components.append({
                    'type': comp_type,
                    'value': value,
                    'quantity': qty,
                })

        # Check for components without quantity prefix
        if not any(c['type'] == 'led' for c in components) and 'led' in desc:
            components.append({'type': 'led', 'value': 'RED', 'quantity': 1})

        if not any(c['type'] == 'resistor' for c in components) and 'resistor' in desc:
            value = self._extract_value(desc, 'resistor')
            components.append({'type': 'resistor', 'value': value, 'quantity': 1})

        # Auto-add resistor if LEDs exist but no resistor
        has_led = any(c['type'] == 'led' for c in components)
        has_resistor = any(c['type'] == 'resistor' for c in components)
        if has_led and not has_resistor:
            components.insert(0, {
                'type': 'resistor', 'value': '330', 'quantity': 1,
                'purpose': 'current limiting',
            })

        # Add MCU if Arduino mentioned
        if 'arduino' in desc:
            # Use Arduino UNO R3 from MCU_Module library
            components.append({
                'type': 'arduino',
                'name': 'Arduino Uno',
                'value': 'Arduino UNO R3',
                'lib_id': 'MCU_Module:Arduino_UNO_R3',
                'footprint': 'Module:Arduino_UNO_R3',
                'quantity': 1,
            })

        # Extract standalone value patterns like "330 ohm"
        for comp in components:
            if comp['type'] == 'resistor' and comp['value'] == '10k':
                val_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:ohm|Ω|k|M)', desc)
                if val_match:
                    raw = val_match.group(0)
                    comp['value'] = raw.replace(' ', '').replace('ohm', '').replace('Ω', '')
            
            # Add lib_id if missing
            if 'lib_id' not in comp:
                comp_type = comp.get('type', 'unknown')
                if comp_type == 'resistor':
                    comp['lib_id'] = 'Device:R'
                elif comp_type == 'led':
                    comp['lib_id'] = 'Device:LED'
                elif comp_type == 'capacitor':
                    comp['lib_id'] = 'Device:C'
                elif comp_type == 'arduino':
                    comp['lib_id'] = 'MCU_Module:Arduino_UNO_R3'

        questions: list[str] = []
        if any(c['type'] == 'led' and c['quantity'] > 1 for c in components):
            if 'series' not in desc and 'parallel' not in desc:
                questions.append("Should the LEDs be connected in series or parallel?")

        return {
            'circuit_type': 'led_array' if has_led else 'custom',
            'components': components,
            'configuration': configuration,
            'mcu_pin': mcu_pin,
            'power': {'positive': '+5V', 'ground': 'GND'},
            'questions': questions,
        }

    def _parse_quantity(self, text: str) -> int:
        """Parse quantity from text (number word or digit)."""
        text = text.strip().lower()
        if text in WORD_NUMBERS:
            return WORD_NUMBERS[text]
        try:
            return int(text)
        except ValueError:
            return 1

    def _extract_value(self, desc: str, comp_type: str) -> str:
        """Extract component value from description."""
        defaults = {
            'resistor': '10k',
            'capacitor': '100nF',
            'led': 'RED',
            'diode': '1N4148',
            'inductor': '10uH',
        }

        if comp_type == 'resistor':
            # Match patterns like "330 ohm", "10k", "4.7k"
            match = re.search(r'(\d+(?:\.\d+)?)\s*(?:ohm|Ω)', desc.lower())
            if match:
                return match.group(1)
            match = re.search(r'(\d+(?:\.\d+)?[kKmM])\s*(?:ohm|Ω|resistor|\s)', desc.lower())
            if match:
                return match.group(1)

        if comp_type == 'capacitor':
            match = re.search(r'(\d+(?:\.\d+)?\s*(?:nF|uF|pF|µF))', desc, re.IGNORECASE)
            if match:
                return match.group(1).replace(' ', '')

        if comp_type == 'led':
            for color in ['red', 'green', 'blue', 'white', 'yellow', 'orange']:
                if color in desc.lower():
                    return color.upper()

        return defaults.get(comp_type, '')

    def _expand_quantities(self, components: list[dict]) -> list[dict]:
        """Expand components with quantity > 1 into individual instances."""
        expanded: list[dict] = []
        for comp in components:
            quantity = comp.get('quantity', 1)
            for _ in range(max(1, quantity)):
                instance = comp.copy()
                instance['quantity'] = 1
                expanded.append(instance)
        return expanded

    def _assign_references(self, components: list[dict]) -> None:
        """Assign unique reference designators (R1, R2, LED1, LED2, etc.)."""
        counters: dict[str, int] = {}
        for comp in components:
            comp_type = comp.get('type', 'unknown')
            prefix = REF_PREFIX.get(comp_type, 'U')
            counters[prefix] = counters.get(prefix, 0) + 1
            comp['ref'] = f"{prefix}{counters[prefix]}"
            
            # Assign default lib_id for MCU types
            if comp_type == 'mcu' and 'lib_id' not in comp:
                comp['lib_id'] = 'MCU_Module:Arduino_UNO_R3'

    def _assign_footprints(self, components: list[dict]) -> None:
        """Assign default footprints if not already set."""
        for comp in components:
            if 'footprint' not in comp:
                comp_type = comp.get('type', '')
                if comp_type in FOOTPRINT_DB:
                    comp['footprint'] = FOOTPRINT_DB[comp_type]
