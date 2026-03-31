"""
KiCad Symbol Library Reader — loads official symbols from .kicad_sym files.

Extracts symbol definitions and pin information from KiCad's installed
symbol libraries for embedding in schematic files.
"""

import os
import re
from pathlib import Path
from typing import Any


# Default KiCad symbol library path on macOS
DEFAULT_SYMBOL_DIR = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols'

# Library file mapping: library name → filename
LIB_FILE_MAP = {
    'Device': 'Device.kicad_sym',
    'MCU_Module': 'MCU_Module.kicad_sym',
    'MCU_Microchip_ATmega': 'MCU_Microchip_ATmega.kicad_sym',
    'power': 'power.kicad_sym',
    'Connector': 'Connector.kicad_sym',
    'Connector_Generic': 'Connector_Generic.kicad_sym',
    'Transistor_BJT': 'Transistor_BJT.kicad_sym',
    'Diode': 'Diode.kicad_sym',
    'Sensor': 'Sensor.kicad_sym',
}


class KiCadLibraryReader:
    """Reads official KiCad symbol libraries from disk."""

    def __init__(self, symbol_dir: str | None = None):
        self.symbol_dir = Path(
            symbol_dir
            or os.environ.get('KICAD_SYMBOL_LIB_DIR', '')
            or DEFAULT_SYMBOL_DIR
        )

    def load_symbol(self, lib_id: str) -> str | None:
        """Extract a symbol definition from a .kicad_sym file.

        Args:
            lib_id: Full library ID like "Device:R" or "MCU_Module:Arduino_UNO_R3"

        Returns:
            The symbol S-expression block (including outer parentheses),
            with the symbol name prefixed by library name for schematic use.
            Returns None if not found.
        """
        lib_name, symbol_name = self._parse_lib_id(lib_id)
        if not lib_name or not symbol_name:
            return None

        lib_path = self._get_lib_path(lib_name)
        if not lib_path or not lib_path.exists():
            return None

        raw = self._extract_symbol_block(lib_path, symbol_name)
        if raw is None:
            return None

        # In .kicad_sym files, symbols are named without prefix (e.g., "R").
        # In schematic lib_symbols, they need the prefix (e.g., "Device:R").
        # Replace the first occurrence of the bare name with the prefixed name.
        prefixed_name = f'{lib_name}:{symbol_name}'
        raw = raw.replace(f'(symbol "{symbol_name}"', f'(symbol "{prefixed_name}"', 1)

        return raw

    def extract_pin_info(self, lib_id: str) -> list[dict[str, Any]]:
        """Extract pin positions from a symbol definition.

        Args:
            lib_id: Full library ID like "Device:R"

        Returns:
            List of pin dicts: {"number": str, "name": str, "x": float, "y": float, "rotation": float}
        """
        lib_name, symbol_name = self._parse_lib_id(lib_id)
        if not lib_name or not symbol_name:
            return []

        lib_path = self._get_lib_path(lib_name)
        if not lib_path or not lib_path.exists():
            return []

        raw = self._extract_symbol_block(lib_path, symbol_name)
        if raw is None:
            return []

        return self._parse_pins(raw)

    def _parse_lib_id(self, lib_id: str) -> tuple[str | None, str | None]:
        """Parse "Library:SymbolName" into (library, name)."""
        if ':' not in lib_id:
            return None, None
        parts = lib_id.split(':', 1)
        return parts[0], parts[1]

    def _get_lib_path(self, lib_name: str) -> Path | None:
        """Get the filesystem path for a library name."""
        filename = LIB_FILE_MAP.get(lib_name)
        if filename:
            return self.symbol_dir / filename
        # Try direct mapping: lib_name.kicad_sym
        candidate = self.symbol_dir / f'{lib_name}.kicad_sym'
        if candidate.exists():
            return candidate
        return None

    def _extract_symbol_block(self, lib_path: Path, symbol_name: str) -> str | None:
        """Extract a top-level symbol block from a .kicad_sym file.

        Uses parenthesis-depth counting to find the complete S-expression
        for the named symbol.
        """
        target = f'(symbol "{symbol_name}"'

        with open(lib_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith(target):
                    # Found the symbol start — now collect the full block
                    block_lines = [line.rstrip('\n')]
                    depth = line.count('(') - line.count(')')

                    if depth <= 0:
                        # Single-line symbol (unlikely but handle it)
                        return stripped

                    for next_line in f:
                        block_lines.append(next_line.rstrip('\n'))
                        depth += next_line.count('(') - next_line.count(')')
                        if depth <= 0:
                            break

                    return '\n'.join(block_lines)

        return None

    def _parse_pins(self, symbol_text: str) -> list[dict[str, Any]]:
        """Parse pin definitions from a symbol S-expression block.

        Extracts pin number, name, position (x, y), and rotation.
        Pin format: (pin TYPE STYLE (at X Y ROT) (length L) (name "N" ...) (number "N" ...))
        """
        pins: list[dict[str, Any]] = []

        # Match pin blocks
        pin_pattern = re.compile(
            r'\(pin\s+\w+\s+\w+'          # (pin TYPE STYLE
            r'\s+\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)'  # (at X Y [ROT])
            r'.*?'                          # length etc.
            r'\(name\s+"([^"]*)"'          # (name "NAME"
            r'.*?'                          # ...
            r'\(number\s+"([^"]*)"',       # (number "NUM"
            re.DOTALL
        )

        for match in pin_pattern.finditer(symbol_text):
            x = float(match.group(1))
            y = float(match.group(2))
            rot = float(match.group(3)) if match.group(3) else 0.0
            name = match.group(4)
            number = match.group(5)

            pins.append({
                'number': number,
                'name': name,
                'x': x,
                'y': y,
                'rotation': rot,
            })

        return pins

    def get_available_libraries(self) -> list[str]:
        """List all available .kicad_sym files in the symbol directory."""
        if not self.symbol_dir.exists():
            return []
        return [
            f.stem for f in self.symbol_dir.glob('*.kicad_sym')
        ]
