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

from .kicad_library import KiCadLibraryReader


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
    "arduino": {
        "lib_id": "MCU_Module:Arduino_UNO_R3",
        "footprint": "Module:Arduino_UNO_R3",
        "pins": {
            "VIN": "1", "GND": "4", "5V": "5", "3V3": "6",
            "D0": "15", "D1": "16", "D2": "17", "D3": "18",
            "D4": "19", "D5": "20", "D6": "21", "D7": "22",
            "D8": "23", "D9": "24", "D10": "25", "D11": "26",
            "D12": "27", "D13": "28",
            "A0": "9", "A1": "10", "A2": "11", "A3": "12", "A4": "13", "A5": "14",
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
    """Analyze circuit description using LLM with enhanced quantity/connection support."""

    def __init__(self, llm_client: LLMClient, components_db: dict):
        self.client = llm_client
        self.db = components_db
        # Use enhanced analyzer for quantity extraction and connection inference
        from .ai_analyzer import EnhancedCircuitAnalyzer
        self._enhanced = EnhancedCircuitAnalyzer(llm_client)

    def analyze(self, description: str) -> dict[str, Any]:
        """Analyze circuit description and return structured data.

        Uses EnhancedCircuitAnalyzer for:
        - Quantity extraction ("two LED" → 2 instances)
        - Connection type inference (series/parallel)
        - MCU pin extraction
        - Automatic reference and footprint assignment
        """
        print(f"Analyzing circuit: {description}")

        # Enhanced analysis with quantity expansion
        analysis = self._enhanced.analyze(description)

        # DO NOT merge with legacy - causes duplicate MCU
        # Enhanced analyzer handles all cases correctly

        return analysis


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
        connections = circuit_data.get('connections', [])

        # Get component details from database
        enriched_components = self._enrich_components(components)

        # Calculate positions for all components
        positions = self._calculate_positions(enriched_components)

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

        # Component instances with positions
        for comp in enriched_components:
            lines.append(self._generate_component_instance(comp, positions))

        # Wires (connections)
        if connections:
            lines.extend(self._generate_wires(connections, positions, enriched_components))

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

    def _calculate_positions(self, components: list[dict]) -> dict[str, tuple[float, float, int]]:
        """Calculate positions for all components.
        
        Layout: left-to-right with MCU in center.
        Returns: dict[ref, (x, y, rotation)]
        """
        positions = {}
        
        # Find MCU (if any) — check both type and name
        mcus = [c for c in components if c.get('type', '') in ('mcu', 'arduino') or
                'arduino' in c.get('name', '').lower() or
                'atmega' in c.get('name', '').lower()]
        
        # Find other components
        others = [c for c in components if c not in mcus]
        
        # Place MCU in center
        mcu_x, mcu_y = 150, 100
        for mcu in mcus:
            positions[mcu['ref']] = (mcu_x, mcu_y, 0)
        
        # Place other components left-to-right
        start_x = 80
        y_level = 90
        spacing_x = 40
        
        for i, comp in enumerate(others):
            x = start_x + (i * spacing_x)
            rotation = 90 if 'resistor' in comp.get('type', '') else 0
            positions[comp['ref']] = (x, y_level, rotation)
        
        return positions

    def _generate_wires(
        self,
        connections: list[dict],
        positions: dict[str, tuple[float, float, int]],
        components: list[dict] | None = None,
    ) -> list[str]:
        """Generate wire statements connecting actual pin positions."""
        reader = KiCadLibraryReader()
        wires = []

        # Build ref → lib_id mapping from components
        ref_to_lib_id: dict[str, str] = {}
        if components:
            for comp in components:
                ref = comp.get('ref', '')
                lib_id = comp.get('lib_id', '')
                if ref and lib_id:
                    ref_to_lib_id[ref] = lib_id

        # Build pin-position cache: {comp_ref: {pin_number_or_name: (local_x, local_y)}}
        pin_cache: dict[str, dict[str, tuple[float, float]]] = {}

        for conn in connections:
            from_ref = conn.get('from', '')
            to_ref = conn.get('to', '')
            if not from_ref or not to_ref:
                continue

            x1, y1 = self._resolve_pin_position(
                from_ref, positions, pin_cache, reader, ref_to_lib_id,
            )
            x2, y2 = self._resolve_pin_position(
                to_ref, positions, pin_cache, reader, ref_to_lib_id,
            )

            # L-shaped routing: horizontal then vertical
            wire_uuid1 = str(uuid.uuid4())
            if abs(x1 - x2) > 0.01 and abs(y1 - y2) > 0.01:
                # Two-segment L-shaped wire
                wire_uuid2 = str(uuid.uuid4())
                wires.append(f'''\t(wire
\t\t(pts (xy {x1} {y1}) (xy {x2} {y1}))
\t\t(stroke
\t\t\t(width 0)
\t\t\t(type default)
\t\t)
\t\t(uuid "{wire_uuid1}")
\t)''')
                wires.append(f'''\t(wire
\t\t(pts (xy {x2} {y1}) (xy {x2} {y2}))
\t\t(stroke
\t\t\t(width 0)
\t\t\t(type default)
\t\t)
\t\t(uuid "{wire_uuid2}")
\t)''')
            else:
                # Straight wire
                wires.append(f'''\t(wire
\t\t(pts (xy {x1} {y1}) (xy {x2} {y2}))
\t\t(stroke
\t\t\t(width 0)
\t\t\t(type default)
\t\t)
\t\t(uuid "{wire_uuid1}")
\t)''')

        return wires

    def _resolve_pin_position(
        self,
        pin_ref: str,
        positions: dict[str, tuple[float, float, int]],
        pin_cache: dict[str, dict[str, tuple[float, float]]],
        reader: KiCadLibraryReader,
        ref_to_lib_id: dict[str, str] | None = None,
    ) -> tuple[float, float]:
        """Resolve a pin reference like 'R1:1' or 'Arduino:Pin5' to absolute (x, y).

        For power symbols (+5V, GND), returns a position near the connected component.
        """
        # Power symbols — not actual components, place at fixed positions
        if pin_ref in ('+5V', 'VCC'):
            return (80.0, 60.0)
        if pin_ref == 'GND':
            return (80.0, 120.0)

        # Parse "CompRef:PinId"
        if ':' in pin_ref:
            comp_ref, pin_id = pin_ref.split(':', 1)
        else:
            comp_ref, pin_id = pin_ref, ''

        # Handle "Arduino:Pin5" → resolve to pin D5 on the Arduino component
        comp_pos = positions.get(comp_ref)
        if not comp_pos:
            # Try to find by component type/name (e.g., "Arduino" → U1)
            ref_to_lib = ref_to_lib_id or {}
            for ref, pos in positions.items():
                lib_id_val = ref_to_lib.get(ref, '')
                if (comp_ref.lower() in ref.lower()
                    or comp_ref.lower() in lib_id_val.lower()):
                    comp_pos = pos
                    comp_ref = ref
                    break
            if not comp_pos:
                return (0.0, 0.0)

        cx, cy, rotation = comp_pos

        # Build pin cache for this component
        if comp_ref not in pin_cache:
            pin_cache[comp_ref] = self._build_pin_cache(
                comp_ref, reader, ref_to_lib_id,
            )

        pins = pin_cache[comp_ref]

        # Resolve pin_id to a cache key
        # "Pin5" → try "D5", "5", "Pin5"
        pin_pos = None
        if pin_id:
            # Normalize "PinN" → "DN" for Arduino-style
            normalized = pin_id
            if pin_id.startswith('Pin'):
                normalized = 'D' + pin_id[3:]

            for candidate in [pin_id, normalized, f'D{pin_id}', f'A{pin_id}']:
                if candidate in pins:
                    pin_pos = pins[candidate]
                    break

            # Try by pin number directly
            if not pin_pos:
                for key, pos in pins.items():
                    if key == pin_id:
                        pin_pos = pos
                        break

        if not pin_pos:
            # Fallback: use first pin or center
            if pins:
                pin_pos = next(iter(pins.values()))
            else:
                return (cx, cy)

        local_x, local_y = pin_pos

        # Transform local pin coordinates to global using component rotation
        import math
        rad = math.radians(rotation)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)
        global_x = cx + local_x * cos_r - local_y * sin_r
        global_y = cy + local_x * sin_r + local_y * cos_r

        return (round(global_x, 2), round(global_y, 2))

    def _build_pin_cache(
        self,
        comp_ref: str,
        reader: KiCadLibraryReader,
        ref_to_lib_id: dict[str, str] | None = None,
    ) -> dict[str, tuple[float, float]]:
        """Build {pin_name_or_number: (local_x, local_y)} cache for a component."""
        # Look up lib_id from component data first
        lib_id = (ref_to_lib_id or {}).get(comp_ref)

        # Fallback: guess from reference prefix
        if not lib_id:
            ref_prefix = ''.join(c for c in comp_ref if c.isalpha())
            fallback_map = {
                'R': 'Device:R', 'C': 'Device:C', 'D': 'Device:LED',
                'U': 'MCU_Module:Arduino_UNO_R3', 'Q': 'Transistor_BJT:BC547',
            }
            lib_id = fallback_map.get(ref_prefix)

        if not lib_id:
            return {}

        pins_info = reader.extract_pin_info(lib_id)
        cache: dict[str, tuple[float, float]] = {}
        for pin in pins_info:
            # Index by both pin number and name
            cache[pin['number']] = (pin['x'], pin['y'])
            if pin['name'] and pin['name'] != '~':
                cache[pin['name']] = (pin['x'], pin['y'])
                # Also index short names: "D5" from "D5", "D0/RX" → "D0"
                if '/' in pin['name']:
                    short = pin['name'].split('/')[0]
                    cache[short] = (pin['x'], pin['y'])
        return cache
    
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
        """Generate library symbols section using official KiCad libraries.

        Loads all symbols from .kicad_sym files via KiCadLibraryReader.
        No hand-written templates — only official library data.
        """
        reader = KiCadLibraryReader()
        symbols = []
        used_lib_ids = set()

        for comp in components:
            # Use lib_id from component (set by ai_analyzer) first,
            # then fall back to database lookup
            lib_id = comp.get('lib_id')
            if not lib_id:
                comp_type = comp.get('type', comp.get('category', 'sensor'))
                name = comp.get('name', '')
                value = comp.get('value', '')
                lib_id = self._get_lib_id_for_component(comp_type, name, value)
                comp['lib_id'] = lib_id

            if lib_id in used_lib_ids:
                continue
            used_lib_ids.add(lib_id)

            # Load from official KiCad library
            symbol_text = reader.load_symbol(lib_id)
            if symbol_text:
                # Re-indent: library files use 1 tab, schematics need 2 tabs
                symbol_text = self._reindent_symbol(symbol_text)
                symbols.append(symbol_text)
            else:
                print(f"⚠️  Symbol '{lib_id}' not found in KiCad libraries")

        # Always add power symbols
        for power_id in ['power:+5V', 'power:GND']:
            if power_id not in used_lib_ids:
                sym = reader.load_symbol(power_id)
                if sym:
                    sym = self._reindent_symbol(sym)
                    symbols.append(sym)
                else:
                    print(f"⚠️  Power symbol '{power_id}' not found in KiCad libraries")
                used_lib_ids.add(power_id)

        return symbols

    @staticmethod
    def _reindent_symbol(symbol_text: str) -> str:
        """Re-indent symbol from library format (1 tab) to schematic format (2 tabs)."""
        lines = symbol_text.split('\n')
        reindented = []
        for line in lines:
            if line.strip():
                reindented.append('\t' + line)
            else:
                reindented.append(line)
        return '\n'.join(reindented)
    
    def _generate_component_instance(self, comp: dict, positions: dict[str, tuple[float, float, int]] | None = None) -> str:
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

        # Use provided positions or calculate default
        if positions and ref in positions:
            x, y, rotation = positions[ref]
        else:
            # Fallback to old logic
            if 'resistor' in comp_type or comp_type == 'r' or 'R' in lib_id:
                x, y, rotation = 120, 90, 90
            elif 'led' in comp_type or comp_type == 'd' or 'LED' in lib_id:
                x, y, rotation = 180, 90, 0
            elif 'atmega' in name.lower() or 'arduino' in name.lower():
                x, y, rotation = 150, 100, 0
            elif 'capacitor' in comp_type or comp_type == 'c':
                x, y, rotation = 140, 80, 0
            else:
                x, y, rotation = 150, 100, 0

        return f'''	(symbol
		(lib_id "{lib_id}")
		(at {x} {y} {rotation})
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
			(at {x} {y} {rotation})
			(effects
				(font
					(size 1.27 1.27)
				)
				(hide yes)
			)
		)
		(property "Datasheet" "~"
			(at {x} {y} {rotation})
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

        # Match by name - check arduino FIRST
        name_lower = name.lower()
        if 'arduino' in name_lower:
            return kicad_db.get('arduino', {}).get('lib_id', 'MCU_Module:Arduino_UNO_R3')
        elif 'atmega' in name_lower:
            # Fallback to Arduino UNO R3 since ATmega328P-AU doesn't exist
            return 'MCU_Module:Arduino_UNO_R3'
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
        """Generate power symbol instances (+5V, GND) at wire endpoints."""
        flags = []
        pwr_counter = 1

        # GND at (80, 120) — matching _resolve_pin_position's GND position
        gnd_uuid = str(uuid.uuid4())
        gnd_ref = f"#PWR0{pwr_counter}"
        pwr_counter += 1
        flags.append(f'''\t(symbol
\t\t(lib_id "power:GND")
\t\t(at 80 120 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(fields_autoplaced yes)
\t\t(uuid "{gnd_uuid}")
\t\t(property "Reference" "{gnd_ref}"
\t\t\t(at 80 123 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(hide yes)
\t\t\t)
\t\t)
\t\t(property "Value" "GND"
\t\t\t(at 80 125.54 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Footprint" ""
\t\t\t(at 80 120 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(hide yes)
\t\t\t)
\t\t)
\t\t(property "Datasheet" "~"
\t\t\t(at 80 120 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(hide yes)
\t\t\t)
\t\t)
\t\t(instances
\t\t\t(project ""
\t\t\t\t(path "/{self.project_uuid}"
\t\t\t\t\t(reference "{gnd_ref}")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)''')

        # +5V at (80, 60) — matching _resolve_pin_position's +5V position
        v5_uuid = str(uuid.uuid4())
        v5_ref = f"#PWR0{pwr_counter}"
        flags.append(f'''\t(symbol
\t\t(lib_id "power:+5V")
\t\t(at 80 60 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(fields_autoplaced yes)
\t\t(uuid "{v5_uuid}")
\t\t(property "Reference" "{v5_ref}"
\t\t\t(at 80 56 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(hide yes)
\t\t\t)
\t\t)
\t\t(property "Value" "+5V"
\t\t\t(at 80 53.46 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Footprint" ""
\t\t\t(at 80 60 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(hide yes)
\t\t\t)
\t\t)
\t\t(property "Datasheet" "~"
\t\t\t(at 80 60 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(hide yes)
\t\t\t)
\t\t)
\t\t(instances
\t\t\t(project ""
\t\t\t\t(path "/{self.project_uuid}"
\t\t\t\t\t(reference "{v5_ref}")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)''')

        return flags


# ============================================================================
# Main Generation Function
# ============================================================================

def generate_schematic(
    description: str,
    output: str,
    model: str = "llama3.2",
    ollama_url: str = "http://localhost:11434",
    learning_context: dict | None = None,
    interactive: bool = False,
) -> Path:
    """
    Generate a KiCad 9.0 schematic using AI.

    Enhanced pipeline:
    1. AI analysis with quantity extraction ("two LED" → 2 LEDs)
    2. Dialog for clarifying questions (series/parallel, color, etc.)
    3. Connection generation based on circuit topology
    4. KiCad schematic file generation

    Args:
        description: Circuit description in natural language
        output: Output file path (.kicad_sch)
        model: Model name (not used yet)
        ollama_url: Ollama URL (not used yet)
        learning_context: Learning context (not used yet)
        interactive: If True, prompt user for clarifying questions

    Returns:
        Path to generated schematic
    """
    from .circuit_generator import ConnectionGenerator
    from .dialog_enhanced import DialogManager

    output_path = Path(output)

    # Load configuration and database
    config = load_config()
    components_db = load_components()

    # Initialize LLM client
    llm = LLMClient(config)

    # Step 1: Analyze circuit with enhanced AI analyzer
    # (includes automatic symbol validation and auto-fix)
    analyzer = CircuitAnalyzer(llm, components_db)
    circuit_data = analyzer.analyze(description)
    
    # Step 2: Handle clarifying questions via dialog manager
    questions = circuit_data.get('questions', [])
    if questions:
        dialog = DialogManager(interactive=interactive)
        print("\n  AI needs clarification:")
        answers = dialog.ask_questions(questions)
        circuit_data = dialog.update_analysis(circuit_data, answers)

    # Step 3: Generate connections if not already provided by LLM
    if not circuit_data.get('connections'):
        conn_gen = ConnectionGenerator()
        circuit_data['connections'] = conn_gen.generate_connections(
            components=circuit_data.get('components', []),
            configuration=circuit_data.get('configuration', 'parallel'),
            mcu_pin=circuit_data.get('mcu_pin'),
        )

    # Step 4: Generate KiCad schematic
    generator = SchematicGenerator(components_db)
    content = generator.generate(circuit_data)

    # Write file
    output_path.write_text(content)

    # Step 5: Validate schematic (connectivity, ERC, readability)
    from .circuit_validator import validate_schematic
    
    print("\n  Validating schematic...")
    validation = validate_schematic(output_path)
    
    if validation['connectivity'].valid:
        print(f"  ✓ Connectivity: PASS")
    else:
        for error in validation['connectivity'].errors:
            print(f"  ✗ {error}")
    
    if validation['erc'].valid:
        print(f"  ✓ ERC: PASS")
    else:
        for error in validation['erc'].errors:
            print(f"  ✗ {error}")
    
    readability = validation['readability']
    print(f"  ✓ Readability: {readability['score']:.1f}% ({readability['rating']})")
    
    # Step 6: Validate with kicad-cli
    from .validator import KiCadValidator
    validator = KiCadValidator()
    result = validator.validate_schematic(output_path)

    n_comps = len(circuit_data.get('components', []))
    n_conns = len(circuit_data.get('connections', []))
    config_type = circuit_data.get('configuration', 'custom')

    if result.valid:
        print(f"\n✓ Schematic generated: {output_path}")
        print(f"  Components: {n_comps}, Connections: {n_conns}, Configuration: {config_type}")
    else:
        print(f"\n⚠️ Schematic generated but kicad-cli validation failed:")
        for error in result.errors:
            print(f"  ✗ {error}")

    return output_path
