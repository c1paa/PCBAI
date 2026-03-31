#!/usr/bin/env python3
"""
Phase 2: Filter to 25k High-Quality Training Pairs.

Takes validated schematics and creates training pairs with:
- Natural language descriptions
- Component lists
- Connection data
- KiCad 9.0 validation

Usage:
    python scripts/phase2_create_training_pairs.py --input datasets/open_schematics/validated --output datasets/training_25k.json --limit 25000
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# Import KiCad 9.0 validator
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from pcba.kicad9_validator import validate_schematic_content


def extract_components(content: str) -> list[dict]:
    """
    Extract component information from KiCad schematic.
    
    Args:
        content: Schematic file content
        
    Returns:
        List of component dicts
    """
    components = []
    
    # Find all symbol instances
    pattern = r'\(symbol\s+\(lib_id\s+"([^"]+)"\)[^)]*\(property\s+"Reference"\s+"([^"]+)"'
    
    for match in re.finditer(pattern, content, re.DOTALL):
        lib_id = match.group(1)
        ref = match.group(2)
        
        # Extract value
        value_match = re.search(r'\(property\s+"Value"\s+"([^"]+)"', content[match.start():match.start()+500])
        value = value_match.group(1) if value_match else ''
        
        # Determine type
        comp_type = lib_id.split(':')[-1].lower() if ':' in lib_id else 'unknown'
        
        components.append({
            'ref': ref,
            'lib_id': lib_id,
            'type': comp_type,
            'value': value,
        })
    
    return components


def extract_connections(content: str) -> list[dict]:
    """
    Extract connection information from KiCad schematic.
    
    Args:
        content: Schematic file content
        
    Returns:
        List of connection dicts
    """
    connections = []
    
    # Find all wires
    wire_pattern = r'\(wire\s+\(pts\s+\(xy\s+([\d.-]+)\s+([\d.-]+)\)\s+\(xy\s+([\d.-]+)\s+([\d.-]+)\)'
    
    for match in re.finditer(wire_pattern, content):
        connections.append({
            'x1': float(match.group(1)),
            'y1': float(match.group(2)),
            'x2': float(match.group(3)),
            'y2': float(match.group(4)),
        })
    
    # Find net labels
    net_pattern = r'\(net\s+(\d+)\s+"([^"]+)"\)'
    nets = []
    for match in re.finditer(net_pattern, content):
        nets.append({
            'code': int(match.group(1)),
            'name': match.group(2),
        })
    
    return connections


def generate_description(components: list[dict], connections: list[dict]) -> str:
    """
    Generate natural language description from schematic.
    
    Args:
        components: List of components
        connections: List of connections
        
    Returns:
        Natural language description
    """
    # Count component types
    type_counts = {}
    for comp in components:
        comp_type = comp['type']
        type_counts[comp_type] = type_counts.get(comp_type, 0) + 1
    
    # Find main component (MCU, Arduino, etc.)
    main_component = None
    for comp_type in ['arduino', 'esp32', 'mcu', 'raspberry']:
        if comp_type in type_counts:
            main_component = comp_type
            break
    
    # Generate description
    parts = []
    
    if main_component:
        parts.append(main_component.capitalize())
    
    # Add other components
    other_components = [k for k in type_counts.keys() if k != main_component]
    
    if other_components:
        if len(other_components) == 1:
            comp = other_components[0]
            count = type_counts[comp]
            if count > 1:
                parts.append(f"with {count} {comp}s")
            else:
                parts.append(f"with {comp}")
        else:
            comp_list = []
            for comp in other_components:
                count = type_counts[comp]
                if count > 1:
                    comp_list.append(f"{count} {comp}s")
                else:
                    comp_list.append(comp)
            parts.append(f"with {', '.join(comp_list)}")
    
    description = ' '.join(parts)
    
    return description


def validate_training_pair(components: list[dict], connections: list[dict]) -> bool:
    """
    Validate a training pair.
    
    Args:
        components: List of components
        connections: List of connections
        
    Returns:
        True if valid
    """
    # Must have components
    if not components or len(components) < 2:
        return False
    
    # Must have at least one connection
    if not connections or len(connections) < 1:
        return False
    
    # All components must have required fields
    for comp in components:
        if 'ref' not in comp or 'lib_id' not in comp:
            return False
    
    return True


def create_training_pairs(validated_dir: Path, output_path: Path, limit: int = 25000) -> Path:
    """
    Create training pairs from validated schematics.
    
    Args:
        validated_dir: Directory with validated data
        output_path: Path to save training pairs
        limit: Maximum number of pairs
        
    Returns:
        Path to created dataset
    """
    print(f"\n{'='*60}")
    print("Phase 2: Creating Training Pairs")
    print(f"{'='*60}\n")
    
    # Load validation report
    report_path = validated_dir / 'validation_report.json'
    
    if not report_path.exists():
        print(f"❌ Validation report not found: {report_path}")
        return None
    
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    validated_data = report.get('validated_data', [])
    
    print(f"Found {len(validated_data)} validated schematics")
    print(f"Target: {limit} training pairs\n")
    
    training_pairs = []
    processed = 0
    
    for item in validated_data:
        if len(training_pairs) >= limit:
            break
        
        sch_file = Path(item['file'])
        
        if not sch_file.exists():
            continue
        
        try:
            content = sch_file.read_text(encoding='utf-8')
            
            # Validate with KiCad 9.0 validator
            validation = validate_schematic_content(content)
            
            if not validation.valid:
                continue
            
            # Extract components and connections
            components = extract_components(content)
            connections = extract_connections(content)
            
            # Validate training pair
            if not validate_training_pair(components, connections):
                continue
            
            # Generate description
            description = generate_description(components, connections)
            
            # Create training pair
            pair = {
                'input': description,
                'output': {
                    'components': components,
                    'connections': connections,
                },
                'metadata': {
                    'source_file': str(sch_file),
                    'component_count': len(components),
                    'connection_count': len(connections),
                    'kicad_version': item.get('kicad_version'),
                }
            }
            
            training_pairs.append(pair)
            processed += 1
            
            if processed % 100 == 0:
                print(f"  Processed {processed}/{limit} pairs...")
                
        except Exception as e:
            continue
    
    # Save dataset
    dataset = {
        'metadata': {
            'version': '1.0',
            'created_by': 'PCBAI Phase 2',
            'total_pairs': len(training_pairs),
            'source': 'Open Schematics Dataset (HuggingFace)',
            'kicad_version': '9.0 compatible',
        },
        'training_pairs': training_pairs,
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("Phase 2 Complete!")
    print(f"  Total pairs created: {len(training_pairs)}")
    print(f"  Dataset saved to: {output_path}")
    print(f"  Dataset size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"{'='*60}\n")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='Create training pairs from validated schematics'
    )
    parser.add_argument(
        '--input',
        type=Path,
        required=True,
        help='Input directory with validated data'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('datasets/training_25k.json'),
        help='Output path for training pairs JSON'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=25000,
        help='Maximum number of training pairs to create'
    )

    args = parser.parse_args()

    print("="*60)
    print("PCBAI - Phase 2: Create Training Pairs")
    print("="*60)

    # Create pairs
    output_path = create_training_pairs(args.input, args.output, limit=args.limit)
    
    if not output_path:
        print("\n❌ Failed to create training pairs!")
        return 1
    
    print("\n✅ Phase 2 Complete!")
    print(f"Next: Run Phase 3 (optimized training script)")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
