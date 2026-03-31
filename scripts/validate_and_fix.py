#!/usr/bin/env python3
"""
KiCad 9.0 Schematic Generator with Validation.

Generates .kicad_sch files with built-in validation to ensure
files will open correctly in KiCad 9.0.

Usage:
    python scripts/validate_and_fix.py schematic.kicad_sch
"""

import argparse
import json
import sys
from pathlib import Path

from pcba.kicad9_validator import KiCad9Validator, validate_schematic


def validate_and_report(filepath: Path) -> bool:
    """
    Validate a schematic and print results.
    
    Args:
        filepath: Path to .kicad_sch file
        
    Returns:
        True if valid, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Validating: {filepath}")
    print(f"{'='*60}\n")
    
    result = validate_schematic(filepath)
    
    # Print errors
    if result.errors:
        print("❌ ERRORS (must fix):")
        for i, error in enumerate(result.errors, 1):
            print(f"  {i}. {error}")
        print()
    
    # Print warnings
    if result.warnings:
        print("⚠️  WARNINGS (should fix):")
        for i, warning in enumerate(result.warnings, 1):
            print(f"  {i}. {warning}")
        print()
    
    # Print suggestions
    if result.suggestions:
        print("💡 SUGGESTIONS (optional improvements):")
        for i, suggestion in enumerate(result.suggestions, 1):
            print(f"  {i}. {suggestion}")
        print()
    
    # Summary
    print(f"{'='*60}")
    if result.valid:
        print("✅ VALIDATION PASSED")
        print(f"   Errors: 0, Warnings: {len(result.warnings)}")
    else:
        print("❌ VALIDATION FAILED")
        print(f"   Errors: {len(result.errors)}, Warnings: {len(result.warnings)}")
    print(f"{'='*60}\n")
    
    return result.valid


def fix_common_issues(filepath: Path, backup: bool = True) -> bool:
    """
    Attempt to fix common validation issues.
    
    Args:
        filepath: Path to .kicad_sch file
        backup: Create backup before fixing
        
    Returns:
        True if fixes applied, False otherwise
    """
    content = filepath.read_text(encoding='utf-8')
    original_content = content
    fixes_applied = []
    
    # Fix 1: Add missing embedded_fonts
    if '(embedded_fonts' not in content:
        # Add before closing parenthesis
        if content.strip().endswith(')'):
            content = content.rstrip()[:-1] + '\n\t(embedded_fonts no)\n)'
            fixes_applied.append("Added 'embedded_fonts no'")
    
    # Fix 2: Add missing generator_version
    if '(generator_version' not in content and '(generator "eeschema")' in content:
        content = content.replace(
            '(generator "eeschema")',
            '(generator "eeschema")\n\t(generator_version "9.0")'
        )
        fixes_applied.append("Added 'generator_version 9.0'")
    
    # Fix 3: Fix unquoted property values
    import re
    unquoted_pattern = r'(\(property\s+"[^"]+"\s+)([A-Z][a-zA-Z0-9_]+)(\s+\(at)'
    matches = re.findall(unquoted_pattern, content)
    if matches:
        for match in matches:
            old = f'{match[0]}{match[1]}{match[2]}'
            new = f'{match[0]}"{match[1]}"{match[2]}'
            content = content.replace(old, new, 1)
        fixes_applied.append("Quoted unquoted property values")
    
    # Fix 4: Fix parenthesis balance
    open_count = content.count('(')
    close_count = content.count(')')
    
    if open_count > close_count:
        # Add missing closing parentheses
        content = content.rstrip() + ')' * (open_count - close_count)
        fixes_applied.append(f"Added {open_count - close_count} missing closing parentheses")
    elif close_count > open_count:
        # Remove extra closing parentheses
        diff = close_count - open_count
        # Remove from end
        content = content.rstrip(')') + ')' * diff
        fixes_applied.append(f"Removed {diff} extra closing parentheses")
    
    # Save if fixes applied
    if fixes_applied:
        if backup:
            backup_path = filepath.with_suffix('.kicad_sch.bak')
            backup_path.write_text(original_content, encoding='utf-8')
            print(f"Backup created: {backup_path}")
        
        filepath.write_text(content, encoding='utf-8')
        
        print("\n✅ Fixes applied:")
        for fix in fixes_applied:
            print(f"  ✓ {fix}")
        print()
        
        return True
    else:
        print("\nℹ️  No automatic fixes available")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Validate and fix KiCad 9.0 schematic files'
    )
    parser.add_argument(
        'filepath',
        type=Path,
        help='Path to .kicad_sch file'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Attempt to fix common issues'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Do not create backup when fixing'
    )

    args = parser.parse_args()

    if not args.filepath.exists():
        print(f"❌ File not found: {args.filepath}")
        return 1

    # Validate
    is_valid = validate_and_report(args.filepath)

    # Fix if requested and not valid
    if not is_valid and args.fix:
        print("Attempting to fix issues...\n")
        fix_applied = fix_common_issues(args.filepath, backup=not args.no_backup)
        
        if fix_applied:
            # Re-validate
            print("Re-validating after fixes...\n")
            is_valid = validate_and_report(args.filepath)

    return 0 if is_valid else 1


if __name__ == '__main__':
    sys.exit(main())
