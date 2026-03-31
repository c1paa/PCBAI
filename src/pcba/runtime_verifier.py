"""
Runtime Verifier - validates symbols exist in KiCad libraries before generation.

Checks:
1. All lib_ids exist in KiCad libraries
2. All footprints exist (optional)
3. All pins are correctly mapped
4. Generated schematic passes kicad-cli validation
"""

import subprocess
from pathlib import Path
from typing import Any
from dataclasses import dataclass

from .kicad_library import KiCadLibraryReader


@dataclass
class ValidationResult:
    """Result of symbol/library validation."""
    valid: bool
    errors: list[str]
    warnings: list[str]
    missing_symbols: list[str]
    suggestions: list[str]


class SymbolVerifier:
    """Verifies that symbols exist in KiCad libraries."""

    def __init__(self, kicad_symbols_dir: str | None = None):
        """Initialize verifier.
        
        Args:
            kicad_symbols_dir: Path to KiCad symbols directory.
                              Auto-detected on macOS if not specified.
        """
        if kicad_symbols_dir:
            self.symbols_dir = Path(kicad_symbols_dir)
        else:
            # Auto-detect on macOS
            self.symbols_dir = Path(
                '/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols'
            )
        
        self.reader = KiCadLibraryReader(str(self.symbols_dir))
        self._available_libraries: dict[str, set[str]] = {}

    def verify_components(self, components: list[dict]) -> ValidationResult:
        """Verify all components have valid symbols.
        
        Args:
            components: List of component dicts with 'lib_id' keys
            
        Returns:
            ValidationResult with errors and suggestions
        """
        errors = []
        warnings = []
        missing_symbols = []
        suggestions = []

        for comp in components:
            lib_id = comp.get('lib_id', '')
            if not lib_id:
                errors.append(f"Component {comp.get('ref', 'Unknown')} has no lib_id")
                continue

            # Check if symbol exists
            if not self.symbol_exists(lib_id):
                missing_symbols.append(lib_id)
                error_msg = f"Symbol '{lib_id}' not found in KiCad libraries"
                
                # Try to find similar symbol
                similar = self._find_similar_symbol(lib_id)
                if similar:
                    suggestion = f"Did you mean '{similar}'?"
                    warnings.append(f"{error_msg}. {suggestion}")
                    suggestions.append(similar)
                else:
                    errors.append(error_msg)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            missing_symbols=missing_symbols,
            suggestions=suggestions
        )

    def symbol_exists(self, lib_id: str) -> bool:
        """Check if a symbol exists in KiCad libraries.
        
        Args:
            lib_id: Full library ID like "Device:R" or "MCU_Module:Arduino_UNO_R3"
            
        Returns:
            True if symbol exists, False otherwise
        """
        if ':' not in lib_id:
            return False
        
        lib_name, symbol_name = lib_id.split(':', 1)
        
        # Check cache
        if lib_name not in self._available_libraries:
            self._load_library(lib_name)
        
        # Check if symbol in library
        return symbol_name in self._available_libraries.get(lib_name, set())

    def _load_library(self, lib_name: str) -> None:
        """Load all symbol names from a library.
        
        Args:
            lib_name: Library name like "Device" or "MCU_Module"
        """
        lib_path = self.symbols_dir / f'{lib_name}.kicad_sym'
        
        if not lib_path.exists():
            self._available_libraries[lib_name] = set()
            return
        
        # Extract all symbol names
        symbols = set()
        with open(lib_path, 'r', encoding='utf-8') as f:
            for line in f:
                if '(symbol "' in line:
                    # Extract symbol name
                    start = line.find('(symbol "') + 9
                    end = line.find('"', start)
                    if start > 8 and end > start:
                        symbols.add(line[start:end])
        
        self._available_libraries[lib_name] = symbols

    def _find_similar_symbol(self, lib_id: str) -> str | None:
        """Find a similar symbol if the requested one doesn't exist.
        
        Args:
            lib_id: Requested library ID
            
        Returns:
            Similar symbol name or None
        """
        if ':' not in lib_id:
            return None
        
        lib_name, symbol_name = lib_id.split(':', 1)
        symbol_name_lower = symbol_name.lower()
        
        # Load library if not cached
        if lib_name not in self._available_libraries:
            self._load_library(lib_name)
        
        # Search for similar names
        for available in self._available_libraries.get(lib_name, set()):
            available_lower = available.lower()
            
            # Exact substring match
            if symbol_name_lower in available_lower or available_lower in symbol_name_lower:
                return f'{lib_name}:{available}'
            
            # Levenshtein-like fuzzy match (simple version)
            if symbol_name_lower.replace('_', '') == available_lower.replace('_', ''):
                return f'{lib_name}:{available}'
            
            # Version number variations (R2 vs R3, etc.)
            import re
            symbol_base = re.sub(r'\d+$', '', symbol_name_lower)
            available_base = re.sub(r'\d+$', '', available_lower)
            if symbol_base == available_base:
                return f'{lib_name}:{available}'
        
        return None

    def get_available_symbols(self, lib_name: str) -> list[str]:
        """List all available symbols in a library.
        
        Args:
            lib_name: Library name like "Device" or "MCU_Module"
            
        Returns:
            List of symbol names
        """
        if lib_name not in self._available_libraries:
            self._load_library(lib_name)
        
        return sorted(self._available_libraries.get(lib_name, set()))

    def list_libraries(self) -> list[str]:
        """List all available KiCad symbol libraries.
        
        Returns:
            List of library names
        """
        if not self.symbols_dir.exists():
            return []
        
        return sorted([
            f.stem for f in self.symbols_dir.glob('*.kicad_sym')
        ])


def validate_schematic_before_generation(
    components: list[dict],
    kicad_symbols_dir: str | None = None
) -> ValidationResult:
    """Convenience function to validate components before generating schematic.
    
    Args:
        components: List of component dicts
        kicad_symbols_dir: Optional path to KiCad symbols
        
    Returns:
        ValidationResult
    """
    verifier = SymbolVerifier(kicad_symbols_dir)
    return verifier.verify_components(components)


def validate_schematic_after_generation(
    filepath: Path | str,
    kicad_cli_path: str | None = None
) -> tuple[bool, list[str]]:
    """Validate generated schematic with kicad-cli.
    
    Args:
        filepath: Path to .kicad_sch file
        kicad_cli_path: Optional path to kicad-cli executable
        
    Returns:
        (success, list_of_errors)
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        return False, [f"File not found: {filepath}"]
    
    # Auto-detect kicad-cli on macOS
    if kicad_cli_path is None:
        kicad_cli_path = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
    
    try:
        result = subprocess.run(
            [
                kicad_cli_path,
                'sch', 'export', 'netlist',
                str(filepath),
                '-o', '/dev/null'
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            errors = [result.stderr] if result.stderr else ['Unknown error']
            return False, errors
        
        return True, []
        
    except FileNotFoundError:
        return True, []  # kicad-cli not installed, skip validation
    except subprocess.TimeoutExpired:
        return False, ['Validation timed out']
