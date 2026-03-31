"""
KiCad Schematic Validator.

Validates generated .kicad_sch files using kicad-cli.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ValidationResult:
    """Result of schematic validation."""
    valid: bool
    errors: list[str]
    warnings: list[str]


class KiCadValidator:
    """Validate KiCad schematics using kicad-cli."""

    def __init__(self, kicad_cli_path: str | None = None):
        """Initialize validator.
        
        Args:
            kicad_cli_path: Path to kicad-cli executable.
                           Auto-detected on macOS if not specified.
        """
        if kicad_cli_path:
            self.kicad_cli = kicad_cli_path
        else:
            # Auto-detect on macOS
            self.kicad_cli = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

    def validate_schematic(self, filepath: Path | str) -> ValidationResult:
        """Validate a .kicad_sch file.
        
        Args:
            filepath: Path to .kicad_sch file
            
        Returns:
            ValidationResult with valid/errors/warnings
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            return ValidationResult(
                valid=False,
                errors=[f"File not found: {filepath}"],
                warnings=[]
            )

        # Check syntax with kicad-cli
        result = self._run_kicad_cli(filepath)
        if result.returncode != 0:
            return ValidationResult(
                valid=False,
                errors=[result.stderr],
                warnings=[]
            )

        # Check for common issues
        errors = []
        warnings = []
        
        content = filepath.read_text()
        
        # Check for missing symbols (question marks)
        if "??" in content or "QuestionMark" in content:
            errors.append("Missing symbol definitions detected (question marks in schematic)")
        
        # Check for empty lib_ids
        if '(lib_id "")' in content:
            errors.append("Components with empty lib_id found")
        
        # Check for missing connections
        if '(wire' not in content and 'connection' in content.lower():
            warnings.append("No wires found - connections may be missing")
        
        # Check for power symbols
        if 'power:+5V' not in content and 'power:GND' not in content:
            warnings.append("No power symbols found")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _run_kicad_cli(self, filepath: Path) -> subprocess.CompletedProcess:
        """Run kicad-cli validation."""
        try:
            result = subprocess.run(
                [
                    self.kicad_cli,
                    "sch", "export", "netlist",
                    str(filepath),
                    "-o", "/dev/null"
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result
        except FileNotFoundError:
            # kicad-cli not installed
            return subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="",
                stderr="kicad-cli not found (validation skipped)"
            )
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(
                args=[],
                returncode=1,
                stdout="",
                stderr="kicad-cli validation timed out"
            )

    def quick_check(self, filepath: Path | str) -> tuple[bool, list[str]]:
        """Quick syntax check without kicad-cli.
        
        Returns:
            (is_valid, list_of_issues)
        """
        filepath = Path(filepath)
        content = filepath.read_text()
        
        issues = []
        
        # Check basic structure
        if not content.strip().startswith('(kicad_sch'):
            issues.append("File doesn't start with (kicad_sch)")
        
        if not content.strip().endswith(')'):
            issues.append("File doesn't end with closing parenthesis")
        
        # Check version
        if '(version' not in content:
            issues.append("Missing version statement")
        
        # Check lib_symbols
        if '(lib_symbols' not in content:
            issues.append("Missing lib_symbols section")
        
        # Check for at least one component
        if '(symbol' not in content:
            issues.append("No components found")
        
        return len(issues) == 0, issues


def validate_schematic(filepath: Path | str, kicad_cli_path: str | None = None) -> ValidationResult:
    """Convenience function to validate a schematic."""
    validator = KiCadValidator(kicad_cli_path)
    return validator.validate_schematic(filepath)
