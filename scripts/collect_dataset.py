#!/usr/bin/env python3
"""
KiCad Schematic Dataset Collector.

Scrapes GitHub for KiCad projects and creates training pairs:
(description → schematic JSON)

Usage:
    python scripts/collect_dataset.py --output datasets/schematic_generation.json --limit 1000
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


def parse_kicad_sch(sch_path: Path) -> dict[str, Any]:
    """
    Parse a .kicad_sch file into structured JSON.

    Returns:
        Dict with components, connections, and metadata
    """
    if not sch_path.exists():
        return {}

    content = sch_path.read_text()

    # Parse components (symbol instances, not lib_symbols)
    # Look for: (symbol (lib_id "...") ... (property "Reference" "X1"
    components = []
    
    # Find all symbol instances (not library definitions)
    # Pattern: (symbol\n\t\t(lib_id "...")\n\t\t... (property "Reference" "X1"
    in_lib_symbols = False
    current_symbol_start = 0
    
    for match in re.finditer(r'\(symbol\s+', content):
        pos = match.start()
        
        # Check if this is in lib_symbols section
        if '(lib_symbols' in content[max(0, pos-200):pos]:
            in_lib_symbols = True
            continue
        
        # Skip library symbol definitions
        if in_lib_symbols:
            # Check if lib_symbols section ended
            if pos > content.find(')', content.find('(lib_symbols')):
                in_lib_symbols = False
        
        if in_lib_symbols:
            continue
        
        # Parse this symbol instance
        symbol_content = content[pos:pos+2000]  # Get next 2000 chars
        
        # Extract lib_id
        lib_id_match = re.search(r'\(lib_id\s+"([^"]+)"', symbol_content)
        if not lib_id_match:
            continue
        
        lib_id = lib_id_match.group(1)
        
        # Extract reference
        ref_match = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', symbol_content)
        if not ref_match:
            continue
        
        ref = ref_match.group(1)
        
        # Extract value
        value_match = re.search(r'\(property\s+"Value"\s+"([^"]+)"', symbol_content)
        value = value_match.group(1) if value_match else ''
        
        # Determine type
        comp_type = lib_id_to_type(lib_id)
        
        components.append({
            'ref': ref,
            'lib_id': lib_id,
            'type': comp_type,
            'value': value,
        })

    # Parse wires
    wires = []
    wire_pattern = r'\(wire\s+\(pts\s+\(xy\s+([\d.-]+)\s+([\d.-]+)\)\s+\(xy\s+([\d.-]+)\s+([\d.-]+)\)'

    for match in re.finditer(wire_pattern, content):
        wires.append({
            'x1': float(match.group(1)),
            'y1': float(match.group(2)),
            'x2': float(match.group(3)),
            'y2': float(match.group(4)),
        })

    # Parse nets
    nets = []
    net_pattern = r'\(net\s+(\d+)\s+"([^"]+)"\)'

    for match in re.finditer(net_pattern, content):
        nets.append({
            'code': int(match.group(1)),
            'name': match.group(2),
        })

    return {
        'components': components,
        'wires': wires,
        'nets': nets,
        'component_count': len(components),
        'wire_count': len(wires),
    }


def lib_id_to_type(lib_id: str) -> str:
    """Convert library ID to component type."""
    lib_id_lower = lib_id.lower()

    if 'resistor' in lib_id_lower or lib_id_lower.endswith(':r'):
        return 'resistor'
    elif 'capacitor' in lib_id_lower or lib_id_lower.endswith(':c'):
        return 'capacitor'
    elif 'led' in lib_id_lower:
        return 'led'
    elif 'diode' in lib_id_lower:
        return 'diode'
    elif 'arduino' in lib_id_lower or 'atmega' in lib_id_lower:
        return 'mcu'
    elif 'esp32' in lib_id_lower:
        return 'mcu'
    elif 'power:' in lib_id_lower:
        if 'gnd' in lib_id_lower:
            return 'ground'
        else:
            return 'power'
    else:
        return 'other'


def extract_description_from_readme(readme_path: Path) -> str:
    """Extract project description from README.md."""
    if not readme_path.exists():
        return "KiCad schematic project"

    content = readme_path.read_text()

    # Get first paragraph or title
    lines = content.split('\n')
    description_lines = []

    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            description_lines.append(line)
            if len(description_lines) >= 2:
                break

    if description_lines:
        return ' '.join(description_lines)[:200]

    return "KiCad schematic project"


def collect_from_directory(project_dir: Path) -> list[dict[str, Any]]:
    """
    Collect schematic data from a local directory.

    Args:
        project_dir: Directory with KiCad projects

    Returns:
        List of training pairs
    """
    training_pairs = []

    # Find all .kicad_sch files
    sch_files = list(project_dir.glob('**/*.kicad_sch'))

    for sch_file in sch_files:
        # Parse schematic
        schematic_data = parse_kicad_sch(sch_file)

        if not schematic_data or schematic_data['component_count'] == 0:
            continue

        # Try to find README in same directory
        readme_path = sch_file.parent / 'README.md'
        description = extract_description_from_readme(readme_path)

        # Create training pair
        training_pair = {
            'input': description,
            'output': schematic_data,
            'source_file': str(sch_file.absolute()),
        }

        training_pairs.append(training_pair)
        print(f"  ✓ Collected: {sch_file.name} ({schematic_data['component_count']} components)")

    return training_pairs


def collect_from_examples(examples_dir: Path) -> list[dict[str, Any]]:
    """
    Collect training data from PCBAI examples directory.

    Args:
        examples_dir: Path to examples/ directory

    Returns:
        List of training pairs
    """
    print(f"\nCollecting from examples directory: {examples_dir}")

    training_pairs = []

    # Find all .kicad_sch files in examples
    sch_files = list(examples_dir.glob('**/*.kicad_sch'))

    for sch_file in sch_files:
        schematic_data = parse_kicad_sch(sch_file)

        if not schematic_data or schematic_data['component_count'] == 0:
            continue

        # Create description from filename
        filename = sch_file.stem
        description = f"KiCad schematic: {filename.replace('_', ' ').replace('-', ' ')}"

        training_pair = {
            'input': description,
            'output': schematic_data,
            'source_file': str(sch_file.absolute()),
        }

        training_pairs.append(training_pair)
        print(f"  ✓ Collected: {filename} ({schematic_data['component_count']} components)")

    return training_pairs


def main():
    parser = argparse.ArgumentParser(description='Collect KiCad schematic dataset')
    parser.add_argument('--output', type=str, default='datasets/schematic_generation.json',
                        help='Output JSON file path')
    parser.add_argument('--input-dir', type=str, default='examples',
                        help='Input directory with KiCad projects')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit number of training pairs')

    args = parser.parse_args()

    output_path = Path(args.output)
    input_dir = Path(args.input_dir)

    print("=" * 60)
    print("KiCad Schematic Dataset Collector")
    print("=" * 60)

    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Collect from examples
    training_pairs = collect_from_examples(input_dir)

    # Also collect from test1 directory
    test1_dir = input_dir / 'test1'
    if test1_dir.exists():
        print(f"\nCollecting from test1 directory:")
        test1_pairs = collect_from_directory(test1_dir)
        training_pairs.extend(test1_pairs)

    # Remove duplicates
    seen_sources = set()
    unique_pairs = []
    for pair in training_pairs:
        if pair['source_file'] not in seen_sources:
            seen_sources.add(pair['source_file'])
            unique_pairs.append(pair)

    training_pairs = unique_pairs

    # Apply limit
    if args.limit and len(training_pairs) > args.limit:
        training_pairs = training_pairs[:args.limit]

    # Save dataset
    dataset = {
        'metadata': {
            'version': '1.0',
            'created_by': 'PCBAI Dataset Collector',
            'total_pairs': len(training_pairs),
        },
        'training_pairs': training_pairs,
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"Dataset saved to: {output_path}")
    print(f"Total training pairs: {len(training_pairs)}")
    print("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
