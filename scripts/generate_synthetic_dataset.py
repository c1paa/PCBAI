#!/usr/bin/env python3
"""
Synthetic Schematic Dataset Generator.

Generates 1000+ synthetic training pairs by combining components in various ways.

Usage:
    python scripts/generate_synthetic_dataset.py --output datasets/synthetic_dataset.json --limit 1000
"""

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any


# Component templates
COMPONENTS = {
    'arduino': {
        'lib_id': 'MCU_Module:Arduino_UNO_R3',
        'ref': 'A',
        'pins': ['D0', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D12', 'D13', '5V', 'GND', '3V3'],
    },
    'esp32': {
        'lib_id': 'MCU_Espressif:ESP32_DevKit',
        'ref': 'U',
        'pins': ['GPIO0', 'GPIO1', 'GPIO2', 'GPIO3', 'GPIO4', 'GPIO5', 'VIN', 'GND', '3V3'],
    },
    'led': {
        'lib_id': 'Device:LED',
        'ref': 'D',
        'pins': ['1', '2'],
        'colors': ['RED', 'GREEN', 'BLUE', 'YELLOW', 'WHITE'],
    },
    'resistor': {
        'lib_id': 'Device:R',
        'ref': 'R',
        'pins': ['1', '2'],
        'values': ['220', '330', '470', '1k', '4.7k', '10k'],
    },
    'button': {
        'lib_id': 'Switch:SW_Push',
        'ref': 'SW',
        'pins': ['1', '2'],
    },
    'capacitor': {
        'lib_id': 'Device:C',
        'ref': 'C',
        'pins': ['1', '2'],
        'values': ['100nF', '1uF', '10uF'],
    },
    'dht22': {
        'lib_id': 'Sensor:DHT11',
        'ref': 'U',
        'pins': ['VCC', 'DATA', 'NC', 'GND'],
    },
    'buzzer': {
        'lib_id': 'Device:Buzzer',
        'ref': 'BZ',
        'pins': ['1', '2'],
    },
}

# Connection templates
CONNECTION_TEMPLATES = [
    # LED circuit
    {
        'components': ['arduino', 'resistor', 'led'],
        'connections': [
            ('{arduino_0}:D{arduino_pin}', '{resistor_1}:1'),
            ('{resistor_1}:2', '{led_2}:2'),
            ('{led_2}:1', '{arduino_0}:GND'),
        ],
        'description_template': 'Arduino with LED on pin {arduino_pin}',
    },
    # Button circuit
    {
        'components': ['arduino', 'button', 'resistor'],
        'connections': [
            ('{arduino_0}:D{arduino_pin}', '{button_1}:1'),
            ('{button_1}:1', '{resistor_2}:1'),
            ('{resistor_2}:2', '{arduino_0}:GND'),
            ('{button_1}:2', '{arduino_0}:5V'),
        ],
        'description_template': 'Arduino with button on pin {arduino_pin}',
    },
    # LED + Button
    {
        'components': ['arduino', 'resistor', 'led', 'button'],
        'connections': [
            ('{arduino_0}:D{arduino_pin1}', '{resistor_1}:1'),
            ('{resistor_1}:2', '{led_2}:2'),
            ('{led_2}:1', '{arduino_0}:GND'),
            ('{arduino_0}:D{arduino_pin2}', '{button_3}:1'),
            ('{button_3}:2', '{arduino_0}:GND'),
        ],
        'description_template': 'Arduino with LED on pin {arduino_pin1} and button on pin {arduino_pin2}',
    },
    # Multiple LEDs
    {
        'components': ['arduino', 'resistor', 'led', 'led', 'led'],
        'connections': [
            ('{arduino_0}:D{arduino_pin1}', '{resistor_1}:1'),
            ('{resistor_1}:2', '{led_2}:2'),
            ('{led_2}:1', '{arduino_0}:GND'),
            ('{arduino_0}:D{arduino_pin2}', '{led_3}:2'),
            ('{led_3}:1', '{arduino_0}:GND'),
            ('{arduino_0}:D{arduino_pin3}', '{led_4}:2'),
            ('{led_4}:1', '{arduino_0}:GND'),
        ],
        'description_template': 'Arduino with three LEDs on pins {arduino_pin1}, {arduino_pin2}, {arduino_pin3}',
    },
    # DHT22 sensor
    {
        'components': ['arduino', 'dht22', 'resistor'],
        'connections': [
            ('{arduino_0}:5V', '{dht22_1}:VCC'),
            ('{arduino_0}:GND', '{dht22_1}:GND'),
            ('{arduino_0}:D{arduino_pin}', '{dht22_1}:DATA'),
            ('{arduino_0}:D{arduino_pin}', '{dht22_1}:DATA'),
        ],
        'description_template': 'Arduino with DHT22 sensor on pin {arduino_pin}',
    },
]


def generate_circuit(template: dict) -> dict[str, Any]:
    """Generate a circuit from template."""
    
    # Select components
    components = []
    pin_map = {}
    comp_refs = {}
    
    for i, comp_type in enumerate(template['components']):
        comp_template = COMPONENTS[comp_type]
        
        # Create unique instance
        ref = f"{comp_template['ref']}{i+1}"
        comp = {
            'type': comp_type,
            'lib_id': comp_template['lib_id'],
            'ref': ref,
            'pins': comp_template['pins'].copy(),
        }
        
        # Add random values
        if 'values' in comp_template:
            comp['value'] = random.choice(comp_template['values'])
        if 'colors' in comp_template:
            comp['color'] = random.choice(comp_template['colors'])
        
        components.append(comp)
        comp_refs[comp_type] = ref
        
        # Assign pins
        if comp_type in ['arduino', 'esp32']:
            # Generate multiple pin assignments for templates with multiple pins
            available_pins = [p for p in comp_template['pins'] if p.startswith('D')]
            pin_map[f'{comp_type}_pin'] = random.choice(available_pins)
            pin_map[f'{comp_type}_pin1'] = random.choice(available_pins)
            pin_map[f'{comp_type}_pin2'] = random.choice(available_pins)
            pin_map[f'{comp_type}_pin3'] = random.choice(available_pins)
    
    # Generate connections
    connections = []
    format_args = {**pin_map, **comp_refs}
    
    # Also add type_index format
    for i, comp in enumerate(components):
        format_args[f"{comp['type']}_{i}"] = comp['ref']
    
    for conn_template in template['connections']:
        from_pin = conn_template[0].format(**format_args)
        to_pin = conn_template[1].format(**format_args)
        connections.append({'from': from_pin, 'to': to_pin})
    
    # Generate description
    description = template['description_template'].format(**pin_map)
    
    return {
        'input': description,
        'output': {
            'components': components,
            'connections': connections,
        },
        'metadata': {
            'component_count': len(components),
            'connection_count': len(connections),
            'synthetic': True,
        }
    }


def main():
    parser = argparse.ArgumentParser(description='Generate synthetic schematic dataset')
    parser.add_argument('--output', type=str, default='datasets/synthetic_dataset.json',
                        help='Output JSON file path')
    parser.add_argument('--limit', type=int, default=1000,
                        help='Number of synthetic pairs to generate')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility')

    args = parser.parse_args()

    print("=" * 60)
    print("Synthetic Schematic Dataset Generator")
    print(f"Target: {args.limit} pairs")
    print("=" * 60)

    # Set seed
    random.seed(args.seed)

    # Generate pairs
    all_pairs = []
    
    print("\nGenerating synthetic circuits...")
    for i in range(args.limit):
        # Select random template
        template = random.choice(CONNECTION_TEMPLATES)
        
        # Generate circuit
        pair = generate_circuit(template)
        all_pairs.append(pair)
        
        if (i + 1) % 100 == 0:
            print(f"  Generated {i + 1}/{args.limit} pairs")

    # Save dataset
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    dataset = {
        'metadata': {
            'version': '1.0',
            'created_by': 'PCBAI Synthetic Generator',
            'total_pairs': len(all_pairs),
            'source': 'Synthetic generation',
            'seed': args.seed,
        },
        'training_pairs': all_pairs,
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"Dataset saved to: {output_path}")
    print(f"Total training pairs: {len(all_pairs)}")
    
    # Statistics
    avg_components = sum(p['metadata']['component_count'] for p in all_pairs) / len(all_pairs)
    avg_connections = sum(p['metadata']['connection_count'] for p in all_pairs) / len(all_pairs)
    
    print(f"Average components: {avg_components:.1f}")
    print(f"Average connections: {avg_connections:.1f}")
    print("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
