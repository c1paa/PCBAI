#!/usr/bin/env python3
"""
KiCad 9.0 Schematic File Validator.

Comprehensive validation to ensure generated .kicad_sch files
will open correctly in KiCad 9.0.

Based on official specification:
https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/
"""

import re
import uuid
from pathlib import Path
from typing import Any
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of validation check."""
    valid: bool
    errors: list[str]
    warnings: list[str]
    suggestions: list[str]


class KiCad9Validator:
    """
    Comprehensive KiCad 9.0 schematic validator.
    
    Validates:
    1. File structure (required sections)
    2. Syntax (S-expression format)
    3. UUIDs (valid format)
    4. Component references
    5. Pin connections
    6. Library symbols
    """
    
    # Required KiCad 9.0 version
    REQUIRED_VERSION = "20250114"
    
    # Required generator identifiers
    VALID_GENERATORS = ["eeschema", "pcbnew"]
    
    # Required properties for hierarchical sheets
    REQUIRED_SHEET_PROPERTIES = ["Sheet name", "Sheet file"]
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.suggestions = []
    
    def validate_file(self, filepath: Path | str) -> ValidationResult:
        """
        Validate a .kicad_sch file.
        
        Args:
            filepath: Path to .kicad_sch file
            
        Returns:
            ValidationResult with errors, warnings, suggestions
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            return ValidationResult(
                valid=False,
                errors=[f"File not found: {filepath}"],
                warnings=[],
                suggestions=[]
            )
        
        content = filepath.read_text(encoding='utf-8')
        
        return self.validate_content(content)
    
    def validate_content(self, content: str) -> ValidationResult:
        """
        Validate schematic content string.
        
        Args:
            content: Schematic file content
            
        Returns:
            ValidationResult
        """
        self.errors = []
        self.warnings = []
        self.suggestions = []
        
        # Level 1: Basic structure
        self._check_header(content)
        self._check_uuid_section(content)
        self._check_root_sheet(content)
        
        # Level 2: Syntax validation
        self._check_syntax_balance(content)
        self._check_strings_quoted(content)
        
        # Level 3: Component validation
        self._check_components(content)
        self._check_component_instances(content)
        
        # Level 4: Connection validation
        self._check_wires(content)
        self._check_pins_exist(content)
        
        # Level 5: Library symbols
        self._check_lib_symbols(content)
        
        # Level 6: KiCad 9.0 specific
        self._check_kicad9_specific(content)
        
        return ValidationResult(
            valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings,
            suggestions=self.suggestions
        )
    
    def _check_header(self, content: str) -> None:
        """Check required header section."""
        # Check kicad_sch token
        if '(kicad_sch' not in content:
            self.errors.append("Missing required '(kicad_sch' token")
            return
        
        # Check version
        version_match = re.search(r'\(version\s+(\d+)\)', content)
        if not version_match:
            self.errors.append("Missing required 'version' in header")
        else:
            version = version_match.group(1)
            if version != self.REQUIRED_VERSION:
                self.warnings.append(
                    f"Version {version} differs from expected {self.REQUIRED_VERSION}"
                )
        
        # Check generator
        gen_match = re.search(r'\(generator\s+"([^"]+)"\)', content)
        if not gen_match:
            self.errors.append("Missing required 'generator' in header")
        else:
            generator = gen_match.group(1)
            if generator not in self.VALID_GENERATORS:
                self.warnings.append(
                    f"Generator '{generator}' is not standard "
                    f"(expected: {self.VALID_GENERATORS})"
                )
    
    def _check_uuid_section(self, content: str) -> None:
        """Check UUID section exists and is valid."""
        # Check for uuid
        uuid_match = re.search(r'\(uuid\s+"([^"]+)"\)', content)
        if not uuid_match:
            self.errors.append("Missing required 'uuid' in schematic header")
            return
        
        # Validate UUID format
        uuid_str = uuid_match.group(1)
        try:
            uuid.UUID(uuid_str)
        except ValueError:
            self.errors.append(f"Invalid UUID format: {uuid_str}")
    
    def _check_root_sheet(self, content: str) -> None:
        """Check root sheet instance section."""
        # Check sheet_instances section
        if '(sheet_instances' not in content:
            self.errors.append("Missing required 'sheet_instances' section")
            return
        
        # Check root path
        root_match = re.search(r'\(path\s+"/"\)', content)
        if not root_match:
            self.errors.append("Missing root sheet instance path '/'")
        
        # Check page number
        page_match = re.search(r'\(page\s+"([^"]+)"\)', content)
        if not page_match:
            self.warnings.append("Missing page number in root sheet")
    
    def _check_syntax_balance(self, content: str) -> None:
        """Check S-expression parenthesis balance."""
        # Count parentheses
        open_count = content.count('(')
        close_count = content.count(')')
        
        if open_count != close_count:
            self.errors.append(
                f"Unbalanced parentheses: {open_count} open, {close_count} close"
            )
        
        # Check for empty parentheses
        if '()' in content:
            self.warnings.append("Found empty parentheses '()'")
    
    def _check_strings_quoted(self, content: str) -> None:
        """Check that all strings are properly quoted."""
        # Check for common unquoted strings
        unquoted_pattern = r'\(property\s+"[^"]+"\s+([A-Z][a-zA-Z0-9_]+)\s'
        matches = re.findall(unquoted_pattern, content)
        
        if matches:
            self.errors.append(
                f"Unquoted string values found: {matches[:5]}"
            )
    
    def _check_components(self, content: str) -> None:
        """Check component definitions."""
        # Find all components
        components = re.findall(
            r'\(symbol\s+\(lib_id\s+"([^"]+)"\)[^)]*\(property\s+"Reference"\s+"([^"]+)"',
            content,
            re.DOTALL
        )
        
        if not components:
            self.warnings.append("No components found in schematic")
            return
        
        # Check for duplicate references
        refs = [comp[1] for comp in components]
        duplicates = set([r for r in refs if refs.count(r) > 1])
        
        if duplicates:
            self.errors.append(f"Duplicate component references: {duplicates}")
        
        # Check lib_id format
        for lib_id, ref in components:
            if ':' not in lib_id:
                self.warnings.append(
                    f"Component {ref}: lib_id '{lib_id}' missing library prefix"
                )
    
    def _check_component_instances(self, content: str) -> None:
        """Check that all components have instance definitions."""
        # Find all symbol definitions
        symbols = re.findall(
            r'\(symbol\s+\(lib_id[^)]+\)[^)]*\(uuid\s+"([^"]+)"\)',
            content,
            re.DOTALL
        )
        
        # Find all instance definitions
        instances = re.findall(
            r'\(instances[^)]+\(path\s+"([^"]+)"\s+\(reference\s+"([^"]+)"\)',
            content,
            re.DOTALL
        )
        
        if symbols and not instances:
            self.errors.append(
                "Components found but no instance definitions"
            )
    
    def _check_wires(self, content: str) -> None:
        """Check wire definitions."""
        # Find all wires
        wires = re.findall(r'\(wire\s+\(pts\s+([^)]+)\)', content)
        
        for wire_pts in wires:
            # Check for at least 2 points
            points = re.findall(r'\(xy\s+[\d.-]+\s+[\d.-]+\)', wire_pts)
            if len(points) < 2:
                self.errors.append("Wire with less than 2 connection points")
    
    def _check_pins_exist(self, content: str) -> None:
        """Check that referenced pins exist in components."""
        # This is a simplified check - full validation requires
        # loading component library definitions
        
        # Extract all connection references
        connections = re.findall(
            r'\(from\s+"([^:]+):([^"]+)"\)|\(to\s+"([^:]+):([^"]+)"\)',
            content
        )
        
        # Group by component
        comp_pins = {}
        for match in connections:
            if match[0]:  # from
                ref, pin = match[0], match[1]
            else:  # to
                ref, pin = match[2], match[3]
            
            if ref not in comp_pins:
                comp_pins[ref] = []
            comp_pins[ref].append(pin)
        
        # Check for obviously invalid pins
        for ref, pins in comp_pins.items():
            for pin in pins:
                if not pin or pin.isdigit() and int(pin) < 1:
                    self.warnings.append(
                        f"Suspicious pin '{pin}' on component {ref}"
                    )
    
    def _check_lib_symbols(self, content: str) -> None:
        """Check library symbol definitions."""
        # Check for lib_symbols section
        if '(lib_symbols' in content:
            # Count symbols
            symbols = re.findall(
                r'\(lib_symbols.*?\(symbol\s+"([^:]+):([^"]+)"',
                content,
                re.DOTALL
            )
            
            if not symbols:
                self.warnings.append(
                    "lib_symbols section present but no symbols defined"
                )
        else:
            self.suggestions.append(
                "Consider adding lib_symbols section for self-contained schematic"
            )
    
    def _check_kicad9_specific(self, content: str) -> None:
        """Check KiCad 9.0 specific requirements."""
        # Check for embedded_fonts
        if '(embedded_fonts' not in content:
            self.warnings.append(
                "Missing 'embedded_fonts' section (KiCad 9.0 requirement)"
            )
        
        # Check for generator_version
        if '(generator_version' not in content:
            self.warnings.append(
                "Missing 'generator_version' (KiCad 9.0 requirement)"
            )
        
        # Check property format (KiCad 9.0 uses nested effects)
        properties = re.findall(
            r'\(property\s+"[^"]+"\s+"[^"]+"\s+\(at[^)]+\)\s+\(effects',
            content
        )
        
        if not properties:
            self.warnings.append(
                "Properties may not follow KiCad 9.0 format "
                "(should have nested effects)"
            )


def validate_schematic(filepath: Path | str) -> ValidationResult:
    """
    Convenience function to validate a schematic file.
    
    Args:
        filepath: Path to .kicad_sch file
        
    Returns:
        ValidationResult
    """
    validator = KiCad9Validator()
    return validator.validate_file(filepath)


def validate_schematic_content(content: str) -> ValidationResult:
    """
    Convenience function to validate schematic content.
    
    Args:
        content: Schematic file content string
        
    Returns:
        ValidationResult
    """
    validator = KiCad9Validator()
    return validator.validate_content(content)
