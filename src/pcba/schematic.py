"""
AI-Powered Schematic Generator for KiCad 9.0.

Uses LLM to understand circuit description and generate schematic.
Integrates with knowledge base for component data.
"""

import json
import uuid
import re
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any


# ============================================================================
# Configuration
# ============================================================================

CONFIG_PATH = Path(__file__).parent.parent / 'knowledge_base' / 'config.json'
COMPONENTS_PATH = Path(__file__).parent.parent / 'knowledge_base' / 'components.json'


# ============================================================================
# Component Database - KiCad 9.0 Official Libraries
# ============================================================================

KICAD_COMPONENTS = {
    "resistor": {
        "lib_id": "Device:R",
        "footprint_smd": "Resistor_SMD:R_0805_2012Metric",
        "footprint_tht": "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
    },
    "capacitor": {
        "lib_id": "Device:C",
        "footprint_smd": "Capacitor_SMD:C_0805_2012Metric",
        "footprint_tht": "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
    },
    "led": {
        "lib_id": "Device:LED",
        "footprint_smd": "LED_SMD:LED_0805_2012Metric",
        "footprint_tht": "LED_THT:LED_D5.0mm"
    },
    "atmega328p": {
        "lib_id": "MCU_Microchip_ATmega:ATMEGA328P-A",
        "footprint": "Package_QFP:TQFP-32_7x7mm_P0.8mm",
        "pins": {
            "VCC": ["19", "30"],
            "GND": ["20", "31"],
            "XTAL1": "16",
            "XTAL2": "15",
            "RESET": "1",
            "GPIO": ["2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "17", "18", "21", "22", "23", "24", "25", "26", "27", "28", "29", "32"]
        }
    },
    "dht22": {
        "lib_id": "Sensor:DHT11",
        "footprint": "Sensor:AOSONG_DHT11_5.5x12.0_P2.54mm",
        "pins": {
            "VDD": "1",
            "DATA": "2",
            "NC": "3",
            "GND": "4"
        }
    },
    "bmp280": {
        "lib_id": "Sensor:BME280",
        "footprint": "Package_LGA:BME280_LGA-8_2.5x2.5mm_P0.65mm",
        "pins": {
            "VCC": "1",
            "GND": "2",
            "SDA": "3",
            "SDO": "4",
            "SCL": "5",
            "CSB": "6",
            "SDI": "7",
            "PS": "8"
        }
    },
    "esp32_wroom": {
        "lib_id": "PCM_Espressif:ESP32-WROOM-32E",
        "footprint": "RF_Module:ESP32-WROOM-32",
        "pins": {
            "3V3": "13",
            "GND": "12",
            "GPIO": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38"]
        }
    },
    "connector_2pin": {
        "lib_id": "Connector:CONN_01X02_MALE",
        "footprint": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
    },
    "connector_3pin": {
        "lib_id": "Connector:CONN_01X03_MALE",
        "footprint": "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
    }
}


def load_config() -> dict:
    """Load LLM provider configuration."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {
        "default_provider": "puter",
        "fallback_provider": "ollama"
    }


def load_components() -> dict:
    """Load component database."""
    # Return the built-in KiCad 9.0 component database
    return {"components": [], "design_rules": {}, "kicad_components": KICAD_COMPONENTS}


# ============================================================================
# LLM Client (Multi-Provider)
# ============================================================================

class LLMClient:
    """Multi-provider LLM client with automatic fallback."""
    
    def __init__(self, config: dict | None = None):
        self.config = config or load_config()
        self.providers = {
            'google': self._generate_google,
            'groq': self._generate_groq,
            'ollama': self._generate_ollama,
            'puter': self._generate_puter,
        }
    
    def generate(self, prompt: str, provider: str | None = None) -> str:
        """
        Generate text from LLM with automatic fallback.
        
        Tries providers in order until one succeeds.
        """
        if provider is None:
            provider = self.config.get('default_provider', 'puter')
        
        # Try primary provider
        try:
            generate_func = self.providers.get(provider)
            if generate_func:
                return generate_func(prompt)
        except Exception as e:
            print(f"Provider {provider} failed: {e}")
        
        # Try fallback
        fallback = self.config.get('fallback_provider', 'ollama')
        if fallback != provider:
            try:
                generate_func = self.providers.get(fallback)
                if generate_func:
                    return generate_func(prompt)
            except Exception as e:
                print(f"Fallback {fallback} failed: {e}")
        
        raise RuntimeError("All LLM providers failed")
    
    def _generate_google(self, prompt: str) -> str:
        """Generate using Google AI Studio (Gemini)."""
        providers = self.config.get('llm_providers', {})
        google_config = providers.get('google', {})
        api_key = google_config.get('api_key', '')
        
        if not api_key:
            raise RuntimeError("Google API key not configured")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result["candidates"][0]["content"]["parts"][0]["text"]
    
    def _generate_groq(self, prompt: str) -> str:
        """Generate using Groq Cloud (Llama)."""
        api_key = self.config.get('api_keys', {}).get('groq', '')
        if not api_key:
            raise RuntimeError("Groq API key not configured")
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        data = {
            "model": "llama-3.1-70b-versatile",
            "messages": [{"role": "user", "content": prompt}]
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
        )
        
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result["choices"][0]["message"]["content"]
    
    def _generate_ollama(self, prompt: str) -> str:
        """Generate using Ollama (local)."""
        url = "http://localhost:11434/api/generate"
        
        data = {
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result.get("response", "")
    
    def _generate_puter(self, prompt: str) -> str:
        """Generate using Puter.js (free, no key needed)."""
        # Simplified Puter API call
        url = "https://api.puter.com/v1/completion"
        
        data = {
            "model": "gemini-pro",
            "prompt": prompt,
            "max_tokens": 2000
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result.get("text", "")
        except Exception:
            # Fallback to ollama
            return self._generate_ollama(prompt)


# ============================================================================
# AI Circuit Analyzer
# ============================================================================

CIRCUIT_ANALYSIS_PROMPT = r'''You are an expert electronics engineer AI assistant.

Analyze the circuit description and extract component information.

IMPORTANT: Output ONLY valid JSON, no explanations, no markdown.

The JSON must have this exact structure:
{
  "circuit_type": "mcu_project" | "sensor_circuit" | "power_supply" | "custom",
  "description": "Brief summary of the circuit",
  "components": [
    {
      "ref": "U1",
      "name": "ATmega328P",
      "category": "mcu",
      "quantity": 1
    },
    {
      "ref": "R1",
      "type": "resistor",
      "value": "10k",
      "footprint": "Resistor_SMD:R_0805"
    }
  ],
  "connections": [
    {"from": "U1:VCC", "to": "C1:1", "net": "VCC"},
    {"from": "U1:GND", "to": "GND", "net": "GND"}
  ],
  "power": {
    "positive": "+5V",
    "ground": "GND"
  },
  "questions": [
    "Which interface should be used for sensor: I2C or SPI?"
  ]
}

Supported categories: mcu, sensor, module, resistor, capacitor, led, diode, transistor, connector, switch, inductor

Example input: "ATmega328P с DHT22 и BMP280"
Example output:
{
  "circuit_type": "mcu_project",
  "description": "Microcontroller project with temperature/humidity and pressure sensors",
  "components": [
    {"ref": "U1", "name": "ATmega328P", "category": "mcu", "quantity": 1},
    {"ref": "D1", "name": "DHT22", "category": "sensor", "quantity": 1},
    {"ref": "U2", "name": "BMP280", "category": "sensor", "quantity": 1},
    {"ref": "R1", "type": "resistor", "value": "10k", "footprint": "Resistor_SMD:R_0805", "purpose": "DHT22 pullup"},
    {"ref": "R2", "type": "resistor", "value": "4.7k", "footprint": "Resistor_SMD:R_0805", "purpose": "I2C pullup SDA"},
    {"ref": "R3", "type": "resistor", "value": "4.7k", "footprint": "Resistor_SMD:R_0805", "purpose": "I2C pullup SCL"},
    {"ref": "C1", "type": "capacitor", "value": "100nF", "footprint": "Capacitor_SMD:C_0805", "purpose": "MCU decoupling"},
    {"ref": "Y1", "type": "crystal", "value": "16MHz", "purpose": "MCU oscillator"}
  ],
  "connections": [
    {"from": "U1:VCC", "to": "C1:1", "net": "VCC"},
    {"from": "U1:GND", "to": "GND", "net": "GND"},
    {"from": "D1:VDD", "to": "VCC", "net": "VCC"},
    {"from": "D1:GND", "to": "GND", "net": "GND"},
    {"from": "U2:VCC", "to": "VCC", "net": "VCC"},
    {"from": "U2:GND", "to": "GND", "net": "GND"}
  ],
  "power": {"positive": "+5V", "ground": "GND"},
  "questions": []
}

Now analyze this circuit:
'''


class CircuitAnalyzer:
    """Analyze circuit description using LLM."""
    
    def __init__(self, llm_client: LLMClient, components_db: dict):
        self.client = llm_client
        self.db = components_db
    
    def analyze(self, description: str) -> dict[str, Any]:
        """Analyze circuit description and return structured data."""
        prompt = CIRCUIT_ANALYSIS_PROMPT + description
        
        print(f"Analyzing circuit: {description}")
        response = self.client.generate(prompt)
        
        # Parse JSON
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return json.loads(response)
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse AI response: {e}")
            return self._fallback_analysis(description)
    
    def _fallback_analysis(self, description: str) -> dict:
        """Fallback analysis if LLM fails."""
        desc_lower = description.lower()
        
        # Simple keyword-based analysis
        components = []
        
        if 'atmega' in desc_lower or 'arduino' in desc_lower:
            components.append({"ref": "U1", "name": "ATmega328P", "category": "mcu", "quantity": 1})
        
        if 'esp32' in desc_lower:
            components.append({"ref": "U1", "name": "ESP32", "category": "mcu", "quantity": 1})
        
        if 'dht' in desc_lower:
            components.append({"ref": "D1", "name": "DHT22", "category": "sensor", "quantity": 1})
            components.append({"ref": "R1", "type": "resistor", "value": "10k", "purpose": "DHT pullup"})
        
        if 'bmp' in desc_lower:
            components.append({"ref": "U2", "name": "BMP280", "category": "sensor", "quantity": 1})
        
        if 'led' in desc_lower:
            components.append({"ref": "LED1", "type": "led", "value": "RED"})
            components.append({"ref": "R2", "type": "resistor", "value": "330", "purpose": "LED current limit"})
        
        return {
            "circuit_type": "custom",
            "description": description,
            "components": components,
            "connections": [],
            "power": {"positive": "+5V", "ground": "GND"},
            "questions": []
        }


# ============================================================================
# Schematic Generator
# ============================================================================

class SchematicGenerator:
    """Generate KiCad 9.0 schematic from analyzed circuit data."""
    
    def __init__(self, components_db: dict):
        self.db = components_db
        self.project_uuid = str(uuid.uuid4())
    
    def generate(self, circuit_data: dict[str, Any]) -> str:
        """Generate complete .kicad_sch content."""
        components = circuit_data.get('components', [])
        power = circuit_data.get('power', {'positive': '+5V', 'ground': 'GND'})
        
        # Get component details from database
        enriched_components = self._enrich_components(components)
        
        # Generate content
        lines = []
        lines.append('(kicad_sch')
        lines.append('\t(version 20250114)')
        lines.append('\t(generator "eeschema")')
        lines.append('\t(generator_version "9.0")')
        lines.append(f'\t(uuid "{self.project_uuid}")')
        lines.append('\t(paper "A4")')
        
        # Library symbols
        lines.append('\t(lib_symbols')
        lines.extend(self._generate_lib_symbols(enriched_components))
        lines.append('\t)')
        
        # Component instances
        for comp in enriched_components:
            lines.append(self._generate_component_instance(comp))
        
        # Power flags
        lines.extend(self._generate_power_flags(power))
        
        # Sheet instances
        lines.append('\t(sheet_instances')
        lines.append('\t\t(path "/"')
        lines.append('\t\t\t(page "1")')
        lines.append('\t\t)')
        lines.append('\t)')
        lines.append('\t(embedded_fonts no)')
        lines.append(')')
        
        return '\n'.join(lines)
    
    def _enrich_components(self, components: list[dict]) -> list[dict]:
        """Add detailed info from database to components."""
        enriched = []
        
        for comp in components:
            name = comp.get('name', '')
            
            # Search in database
            db_comp = self._find_in_database(name)
            
            if db_comp:
                # Merge with AI data
                enriched_comp = {**db_comp, **comp}
            else:
                # Use AI data only
                enriched_comp = comp
            
            enriched.append(enriched_comp)
        
        return enriched
    
    def _find_in_database(self, name: str) -> dict | None:
        """Find component in database by name."""
        name_lower = name.lower()
        
        for comp in self.db.get('components', []):
            if name_lower in comp.get('name', '').lower():
                return comp
        
        return None
    
    def _generate_lib_symbols(self, components: list[dict]) -> list[str]:
        """Generate library symbols section."""
        symbols = []
        used_symbols = set()

        # Symbol templates
        symbol_templates = {
            'resistor': self._symbol_resistor(),
            'led': self._symbol_led(),
            'capacitor': self._symbol_capacitor(),
            'mcu': self._symbol_generic_ic(),
            'sensor': self._symbol_generic_sensor(),
        }

        for comp in components:
            category = comp.get('category', 'sensor')
            comp_type = comp.get('type', '')
            name = comp.get('name', '').lower()
            lib_id = comp.get('lib_id', '')

            # Determine which symbol to use based on multiple factors
            symbol_to_add = None
            
            # Check by lib_id first (most reliable)
            if 'R' in lib_id or 'resistor' in comp_type or 'resistor' in name:
                symbol_to_add = 'resistor'
            elif 'LED' in lib_id or 'led' in comp_type or 'led' in name:
                symbol_to_add = 'led'
            elif 'C' in lib_id or 'capacitor' in comp_type or 'capacitor' in name:
                symbol_to_add = 'capacitor'
            elif 'ATmega' in name or 'ESP32' in name or 'arduino' in name:
                symbol_to_add = 'mcu'
            elif category == 'resistor':
                symbol_to_add = 'resistor'
            elif category == 'led':
                symbol_to_add = 'led'
            elif category == 'capacitor':
                symbol_to_add = 'capacitor'
            elif category == 'mcu':
                symbol_to_add = 'mcu'
            else:
                symbol_to_add = 'sensor'  # Default
            
            # Add symbol if not already added
            if symbol_to_add and symbol_to_add not in used_symbols:
                template = symbol_templates.get(symbol_to_add)
                if template:
                    symbols.append(template)
                    used_symbols.add(symbol_to_add)

        # Always add power symbols
        symbols.append(self._symbol_power_5v())
        symbols.append(self._symbol_gnd())

        return symbols
    
    def _symbol_resistor(self) -> str:
        """Resistor symbol - KiCad 9.0 format."""
        return r'''		(symbol "Device:R"
			(in_bom yes)
			(on_board yes)
			(property "Reference" "R"
				(at 2.032 0 90)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Value" "R"
				(at 0 0 90)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Footprint" ""
				(at -1.778 0 90)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Datasheet" "~"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Description" "Resistor"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "ki_keywords" "R res resistor"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "ki_fp_filters" "R_*"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "R_0_1"
				(rectangle
					(start -1.016 -2.54)
					(end 1.016 2.54)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
			)
			(symbol "R_1_1"
				(pin passive line
					(at 0 3.81 270)
					(length 1.27)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "1"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin passive line
					(at 0 -3.81 90)
					(length 1.27)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "2"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
			)
			(embedded_fonts no)
		)'''
    
    def _symbol_led(self) -> str:
        """LED symbol - KiCad 9.0 format."""
        return r'''		(symbol "Device:LED"
			(in_bom yes)
			(on_board yes)
			(property "Reference" "D"
				(at 0 2.54 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Value" "LED"
				(at 0 -2.54 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Footprint" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Datasheet" "~"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Description" "Light emitting diode"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Sim.Pins" "1=K 2=A"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "ki_keywords" "LED diode"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "ki_fp_filters" "LED* LED_SMD:* LED_THT:*"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "LED_0_1"
				(polyline
					(pts
						(xy -3.048 -0.762)
						(xy -4.572 -2.286)
						(xy -3.81 -2.286)
						(xy -4.572 -2.286)
						(xy -4.572 -1.524)
					)
					(stroke
						(width 0)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy -1.778 -0.762)
						(xy -3.302 -2.286)
						(xy -2.54 -2.286)
						(xy -3.302 -2.286)
						(xy -3.302 -1.524)
					)
					(stroke
						(width 0)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy -1.27 0)
						(xy 1.27 0)
					)
					(stroke
						(width 0)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy -1.27 -1.27)
						(xy -1.27 1.27)
					)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy 1.27 -1.27)
						(xy 1.27 1.27)
						(xy -1.27 0)
						(xy 1.27 -1.27)
					)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
			)
			(symbol "LED_1_1"
				(pin passive line
					(at -3.81 0 0)
					(length 2.54)
					(name "K"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "1"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin passive line
					(at 3.81 0 180)
					(length 2.54)
					(name "A"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "2"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
			)
			(embedded_fonts no)
		)'''
    
    def _symbol_capacitor(self) -> str:
        """Capacitor symbol - KiCad 9.0 format."""
        return r'''		(symbol "Device:C"
			(in_bom yes)
			(on_board yes)
			(property "Reference" "C"
				(at 0 2.54 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Value" "C"
				(at 0 -2.54 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Footprint" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Datasheet" "~"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Description" "Capacitor"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "ki_keywords" "cap capacitor"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "ki_fp_filters" "C_*"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "C_0_1"
				(polyline
					(pts
						(xy -1.016 -1.016)
						(xy 1.016 -1.016)
					)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy -1.016 1.016)
						(xy 1.016 1.016)
					)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
			)
			(symbol "C_1_1"
				(pin passive line
					(at 0 3.81 270)
					(length 2.54)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "1"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin passive line
					(at 0 -3.81 90)
					(length 2.54)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "2"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
			)
			(embedded_fonts no)
		)'''
    
    def _symbol_generic_ic(self) -> str:
        """Generic IC symbol - KiCad 9.0 format."""
        return r'''		(symbol "Device:GenericIC"
			(in_bom yes)
			(on_board yes)
			(property "Reference" "U"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Value" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Footprint" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Datasheet" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "GenericIC_0_1"
				(rectangle
					(start -7.62 -7.62)
					(end 7.62 7.62)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type background)
					)
				)
			)
			(embedded_fonts no)
		)'''
    
    def _symbol_generic_sensor(self) -> str:
        """Generic sensor symbol - KiCad 9.0 format."""
        return r'''		(symbol "Device:GenericSensor"
			(in_bom yes)
			(on_board yes)
			(property "Reference" "S"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Value" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Footprint" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Datasheet" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "GenericSensor_0_1"
				(circle
					(center 0 0)
					(radius 5.08)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type background)
					)
				)
			)
			(embedded_fonts no)
		)'''
    
    def _symbol_power_5v(self) -> str:
        """+5V power symbol - KiCad 9.0 format."""
        return r'''		(symbol "power:+5V"
			(power)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "#PWR"
				(at 0 -3.81 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Value" "+5V"
				(at 0 3.556 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Footprint" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Datasheet" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Description" "Power symbol creates a global label with name \"+5V\""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "ki_keywords" "global power"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "+5V_0_1"
				(polyline
					(pts
						(xy -0.762 1.27)
						(xy 0 2.54)
					)
					(stroke
						(width 0)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy 0 2.54)
						(xy 0.762 1.27)
					)
					(stroke
						(width 0)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy 0 0)
						(xy 0 2.54)
					)
					(stroke
						(width 0)
						(type default)
					)
					(fill
						(type none)
					)
				)
			)
			(symbol "+5V_1_1"
				(pin power_in line
					(at 0 0 90)
					(length 0)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "1"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
			)
			(embedded_fonts no)
		)'''
    
    def _symbol_gnd(self) -> str:
        """GND power symbol - KiCad 9.0 format."""
        return r'''		(symbol "power:GND"
			(power)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "#PWR"
				(at 0 -6.35 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Value" "GND"
				(at 0 -3.81 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Footprint" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Datasheet" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Description" "Power symbol creates a global label with name \"GND\" , ground"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "ki_keywords" "global power"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "GND_0_1"
				(polyline
					(pts
						(xy 0 0)
						(xy 0 -1.27)
						(xy 1.27 -1.27)
						(xy 0 -2.54)
						(xy -1.27 -1.27)
						(xy 0 -1.27)
					)
					(stroke
						(width 0)
						(type default)
					)
					(fill
						(type none)
					)
				)
			)
			(symbol "GND_1_1"
				(pin power_in line
					(at 0 0 270)
					(length 0)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "1"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
			)
			(embedded_fonts no)
		)'''
    
    def _generate_component_instance(self, comp: dict) -> str:
        """Generate symbol instance for a component."""
        ref = comp.get('ref', 'U1')
        comp_type = comp.get('type', comp.get('category', 'sensor'))
        name = comp.get('name', ref)
        value = comp.get('value', comp.get('name', '?'))
        
        # Get correct lib_id from KiCad database
        lib_id = self._get_lib_id_for_component(comp_type, name, value)
        footprint = comp.get('footprint', '')
        
        # Generate UUIDs
        comp_uuid = str(uuid.uuid4())
        
        # Position (simple grid)
        idx = hash(ref) % 10
        x = 100 + (idx * 25)
        y = 80 + (hash(name) % 5 * 25)
        
        return f'''	(symbol
		(lib_id "{lib_id}")
		(at {x} {y} 0)
		(unit 1)
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(dnp no)
		(fields_autoplaced yes)
		(uuid "{comp_uuid}")
		(property "Reference" "{ref}"
			(at {x} {y-5} 0)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Value" "{value}"
			(at {x} {y+5} 0)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Footprint" "{footprint}"
			(at {x} {y} 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(hide yes)
			)
		)
		(property "Datasheet" "~"
			(at {x} {y} 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(hide yes)
			)
		)
		(instances
			(project ""
				(path "/{self.project_uuid}"
					(reference "{ref}")
					(unit 1)
				)
			)
		)
	)'''
    
    def _get_lib_id_for_component(self, comp_type: str, name: str, value: str) -> str:
        """Get correct KiCad lib_id for component type."""
        # Check component database
        kicad_db = self.db.get('kicad_components', {})

        # Direct match by type
        if comp_type in kicad_db:
            return kicad_db[comp_type].get('lib_id', f"Device:{comp_type.upper()}")

        # Match by name
        name_lower = name.lower()
        if 'atmega' in name_lower or 'arduino' in name_lower:
            return kicad_db.get('atmega328p', {}).get('lib_id', 'MCU_Microchip_ATmega:ATMEGA328P-A')
        elif 'esp32' in name_lower:
            return kicad_db.get('esp32_wroom', {}).get('lib_id', 'PCM_Espressif:ESP32-WROOM-32E')
        elif 'dht' in name_lower:
            return kicad_db.get('dht22', {}).get('lib_id', 'Sensor:DHT11')
        elif 'bmp' in name_lower:
            return kicad_db.get('bmp280', {}).get('lib_id', 'Sensor:BME280')
        elif 'resistor' in comp_type or comp_type == 'r':
            return kicad_db.get('resistor', {}).get('lib_id', 'Device:R')
        elif 'capacitor' in comp_type or comp_type == 'c':
            return kicad_db.get('capacitor', {}).get('lib_id', 'Device:C')
        elif 'led' in comp_type or comp_type == 'd':
            return kicad_db.get('led', {}).get('lib_id', 'Device:LED')
        elif 'connector' in comp_type:
            return kicad_db.get('connector_2pin', {}).get('lib_id', 'Connector:CONN_01X02_MALE')
        else:
            # Default to generic sensor
            return kicad_db.get('connector_2pin', {}).get('lib_id', 'Device:GenericSensor')

    def _generate_custom_ic_symbol(self, name: str, pins: list[dict], size: float = 7.62) -> str:
        """
        Generate custom IC symbol with rectangular body and pins.
        
        Args:
            name: Component name (e.g., "MySensor")
            pins: List of pin dicts with {'num': '1', 'name': 'VCC', 'side': 'top'}
            size: Half-size of rectangle (default 7.62mm = 15.24mm total)
        
        Returns:
            KiCad 9.0 S-expression symbol definition
        """
        # Pin positions
        pin_positions = {
            'top': {'x': -5.08, 'y': size, 'rot': 270},
            'bottom': {'x': -5.08, 'y': -size, 'rot': 90},
            'left': {'x': -size, 'y': 5.08, 'rot': 0},
            'right': {'x': size, 'y': 5.08, 'rot': 180},
        }
        
        # Group pins by side
        pins_by_side = {'top': [], 'bottom': [], 'left': [], 'right': []}
        for pin in pins:
            side = pin.get('side', 'left')
            if side not in pins_by_side:
                side = 'left'
            pins_by_side[side].append(pin)
        
        # Generate pin definitions
        pin_defs = []
        y_offset = {'top': 0, 'bottom': 0, 'left': 5.08, 'right': 5.08}
        
        for side in ['left', 'right', 'top', 'bottom']:
            side_pins = pins_by_side[side]
            pos = pin_positions[side]
            
            for i, pin in enumerate(side_pins):
                pin_num = pin.get('num', str(i+1))
                pin_name = pin.get('name', f'Pin{pin_num}')
                
                if side in ['left', 'right']:
                    y = pos['y'] - (i * 2.54)
                    x = pos['x']
                else:  # top/bottom
                    x = pos['x'] + (i * 2.54)
                    y = pos['y']
                
                pin_defs.append(f'''			(pin passive line
				(at {x} {y} {pos['rot']})
				(length 2.54)
				(name "{pin_name}"
					(effects
						(font
							(size 1.27 1.27)
						)
					)
				)
				(number "{pin_num}"
					(effects
						(font
							(size 1.27 1.27)
						)
					)
				)
			)''')
        
        pins_str = '\n'.join(pin_defs)
        
        return f'''		(symbol "Custom:{name}"
			(in_bom yes)
			(on_board yes)
			(property "Reference" "U"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Value" "{name}"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Footprint" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Datasheet" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "{name}_0_1"
				(rectangle
					(start {-size} {-size})
					(end {size} {size})
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type background)
					)
				)
			)
			(symbol "{name}_1_1"
{pins_str}
			)
			(embedded_fonts no)
		)'''
    
    def _generate_power_flags(self, power: dict) -> list[str]:
        """Generate power flag symbols."""
        return []  # Simplified for now


# ============================================================================
# Main Generation Function
# ============================================================================

def generate_schematic(
    description: str,
    output: str,
    model: str = "llama3.2",
    ollama_url: str = "http://localhost:11434",
    learning_context: dict | None = None,
) -> Path:
    """
    Generate a KiCad 9.0 schematic using AI.
    
    Args:
        description: Circuit description
        output: Output file path
        model: Model name (not used yet)
        ollama_url: Ollama URL (not used yet)
        learning_context: Learning context (not used yet)
    
    Returns:
        Path to generated schematic
    """
    output_path = Path(output)
    
    # Load configuration and database
    config = load_config()
    components_db = load_components()
    
    # Initialize LLM client
    llm = LLMClient(config)
    
    # Analyze circuit
    analyzer = CircuitAnalyzer(llm, components_db)
    circuit_data = analyzer.analyze(description)
    
    # Check if there are questions for the user
    questions = circuit_data.get('questions', [])
    if questions:
        print("\n⚠️  AI has questions about the circuit:")
        for i, q in enumerate(questions, 1):
            print(f"  {i}. {q}")
        print("\nContinuing with default assumptions...\n")
    
    # Generate schematic
    generator = SchematicGenerator(components_db)
    content = generator.generate(circuit_data)
    
    # Write file
    output_path.write_text(content)
    
    print(f"✓ Schematic generated: {output_path}")
    print(f"  Components: {len(circuit_data.get('components', []))}")
    
    return output_path
