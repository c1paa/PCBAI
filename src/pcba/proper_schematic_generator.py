"""
Proper Schematic Generator with correct pin connections.

Generates KiCad schematics where:
- Wires connect to ACTUAL pin positions (not component centers)
- Components don't overlap
- Arduino uses 'A' prefix (not 'U')
- No unnecessary +5V/GND symbols (Arduino has power pins)
"""

import uuid
from pathlib import Path
from typing import Any


# Pin positions for common components (relative to component center)
PIN_POSITIONS = {
    'MCU_Module:Arduino_UNO_R3': {
        # Digital pins (right side)
        'D0': {'x': 12.7, 'y': -7.62},
        'D1': {'x': 12.7, 'y': -5.08},
        'D2': {'x': 12.7, 'y': -2.54},
        'D3': {'x': 12.7, 'y': 0},
        'D4': {'x': 12.7, 'y': 2.54},
        'D5': {'x': 12.7, 'y': 5.08},
        'D6': {'x': 12.7, 'y': 7.62},
        # Power pins (left side)
        '5V': {'x': -12.7, 'y': 7.62},
        'GND': {'x': -12.7, 'y': 5.08},
        '3V3': {'x': -12.7, 'y': 2.54},
    },
    'Device:R': {
        '1': {'x': 0, 'y': 3.81},
        '2': {'x': 0, 'y': -3.81},
    },
    'Device:LED': {
        '1': {'x': -3.81, 'y': 0},  # K (cathode)
        '2': {'x': 3.81, 'y': 0},   # A (anode)
    },
    'Device:C': {
        '1': {'x': 0, 'y': 3.81},
        '2': {'x': 0, 'y': -3.81},
    },
}


def generate_proper_schematic(circuit_data: dict[str, Any]) -> str:
    """
    Generate proper KiCad schematic with correct pin connections.
    
    Args:
        circuit_data: Circuit analysis from AI
        
    Returns:
        KiCad 9.0 schematic S-expression
    """
    components = circuit_data.get('components', [])
    
    # Generate unique UUID for schematic
    project_uuid = str(uuid.uuid4())
    
    lines = []
    lines.append('(kicad_sch')
    lines.append('\t(version 20250114)')
    lines.append('\t(generator "eeschema")')
    lines.append('\t(generator_version "9.0")')
    lines.append(f'\t(uuid "{project_uuid}")')
    lines.append('\t(paper "A4")')
    
    # Generate lib_symbols section (load from libraries)
    lines.append('\t(lib_symbols')
    lines.extend(_generate_lib_symbols(components))
    lines.append('\t)')
    lines.append('')
    
    # Place components with proper positions (no overlap)
    placed_components = _place_components(components)
    
    # Generate component instances
    for comp in placed_components:
        lines.append(_generate_component_instance(comp, project_uuid))
    
    # Generate wires connecting pins
    lines.extend(_generate_wires(placed_components, circuit_data))
    
    # Close schematic
    lines.append('\t(sheet_instances')
    lines.append('\t\t(path "/"')
    lines.append('\t\t\t(page "1")')
    lines.append('\t\t)')
    lines.append('\t)')
    lines.append('\t(embedded_fonts no)')
    lines.append(')')
    
    return '\n'.join(lines)


def _generate_lib_symbols(components: list[dict]) -> list[str]:
    """Generate lib_symbols section loading from KiCad libraries."""
    from .kicad_library import KiCadLibraryReader
    
    reader = KiCadLibraryReader()
    symbols = []
    used_lib_ids = set()
    
    for comp in components:
        lib_id = comp.get('lib_id', '')
        if lib_id and lib_id not in used_lib_ids:
            symbol = reader.load_symbol(lib_id)
            if symbol:
                symbols.append(symbol)
                used_lib_ids.add(lib_id)
    
    return symbols


def _place_components(components: list[dict]) -> list[dict]:
    """
    Place components without overlap.
    
    Returns components with 'x', 'y', 'rotation' added.
    """
    placed = []
    
    # Arduino in center
    arduino_x, arduino_y = 150, 100
    
    # Other components to the right in a column
    component_x = 200
    component_y = 60
    spacing_y = 40
    
    for comp in components:
        lib_id = comp.get('lib_id', '')
        
        if 'Arduino' in lib_id or 'arduino' in comp.get('type', ''):
            # Arduino in center
            comp['x'] = arduino_x
            comp['y'] = arduino_y
            comp['rotation'] = 0
        else:
            # Other components in column to the right
            comp['x'] = component_x
            comp['y'] = component_y
            comp['rotation'] = 0
            component_y += spacing_y
        
        placed.append(comp)
    
    return placed


def _generate_component_instance(comp: dict, project_uuid: str) -> str:
    """Generate component instance S-expression."""
    ref = comp.get('ref', 'U1')
    lib_id = comp.get('lib_id', '')
    value = comp.get('value', '')
    x = comp.get('x', 0)
    y = comp.get('y', 0)
    rotation = comp.get('rotation', 0)
    
    comp_uuid = str(uuid.uuid4())
    
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
		(property "Footprint" ""
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
				(path "/{project_uuid}"
					(reference "{ref}")
					(unit 1)
				)
			)
		)
	)'''


def _generate_wires(components: list[dict], circuit_data: dict) -> list[str]:
    """
    Generate wires connecting component pins.
    
    Uses actual pin positions from PIN_POSITIONS.
    """
    wires = []
    
    # Get connections from circuit_data or generate default
    connections = circuit_data.get('connections', [])
    
    if not connections:
        # Generate default connections for LED circuit
        connections = _generate_default_connections(components)
    
    for conn in connections:
        from_ref = conn.get('from', '')  # e.g., "A1:D5"
        to_ref = conn.get('to', '')      # e.g., "R1:1"
        
        # Get pin positions
        from_pos = _get_pin_position(components, from_ref)
        to_pos = _get_pin_position(components, to_ref)
        
        if from_pos and to_pos:
            wire_uuid = str(uuid.uuid4())
            wires.append(f'''	(wire
		(pts (xy {from_pos[0]} {from_pos[1]}) (xy {to_pos[0]} {to_pos[1]}))
		(stroke
			(width 0)
			(type default)
		)
		(uuid "{wire_uuid}")
	)''')
    
    return wires


def _get_pin_position(components: list[dict], pin_ref: str) -> tuple[float, float] | None:
    """
    Get absolute position of a pin.
    
    Args:
        components: List of placed components
        pin_ref: Pin reference like "A1:D5" or "R1:1"
        
    Returns:
        (x, y) absolute coordinates or None
    """
    if ':' not in pin_ref:
        return None
    
    comp_ref, pin_name = pin_ref.split(':')
    
    # Find component
    comp = None
    for c in components:
        if c.get('ref') == comp_ref:
            comp = c
            break
    
    if not comp:
        return None
    
    lib_id = comp.get('lib_id', '')
    x = comp.get('x', 0)
    y = comp.get('y', 0)
    
    # Get relative pin position
    pin_rel = PIN_POSITIONS.get(lib_id, {}).get(pin_name)
    
    if pin_rel:
        # Absolute position = component position + relative pin position
        return (x + pin_rel['x'], y + pin_rel['y'])
    
    # Default: return component center
    return (x, y)


def _generate_default_connections(components: list[dict]) -> list[dict]:
    """Generate default connections for simple LED circuit."""
    connections = []
    
    # Find Arduino, resistors, LEDs
    arduino = None
    resistors = []
    leds = []
    
    for comp in components:
        lib_id = comp.get('lib_id', '')
        comp_type = comp.get('type', '')
        
        if 'Arduino' in lib_id or comp_type == 'arduino':
            arduino = comp
        elif comp_type == 'resistor':
            resistors.append(comp)
        elif comp_type == 'led':
            leds.append(comp)
    
    if not arduino:
        return connections
    
    arduino_ref = arduino.get('ref', 'A1')
    
    # Connect: Arduino D5 → Resistor → LED → Arduino GND
    for i, (resistor, led) in enumerate(zip(resistors, leds)):
        r_ref = resistor.get('ref', f'R{i+1}')
        l_ref = led.get('ref', f'D{i+1}')
        
        # Arduino D5 → Resistor pin 1
        connections.append({
            'from': f'{arduino_ref}:D5',
            'to': f'{r_ref}:1',
        })
        
        # Resistor pin 2 → LED anode (pin 2)
        connections.append({
            'from': f'{r_ref}:2',
            'to': f'{l_ref}:2',
        })
        
        # LED cathode (pin 1) → Arduino GND
        connections.append({
            'from': f'{l_ref}:1',
            'to': f'{arduino_ref}:GND',
        })
    
    return connections
