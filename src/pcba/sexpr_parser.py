"""
KiCad S-Expression Parser.

Properly parses .kicad_sch files using recursive parenthesis-depth counting.
Returns structured data for training pair extraction.
"""

import re
from typing import Any


def tokenize_sexpr(text: str) -> list[str]:
    """Tokenize S-expression text into tokens: '(', ')', strings, atoms."""
    tokens = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c in ' \t\n\r':
            i += 1
        elif c == '(':
            tokens.append('(')
            i += 1
        elif c == ')':
            tokens.append(')')
            i += 1
        elif c == '"':
            # Quoted string
            j = i + 1
            while j < n:
                if text[j] == '\\':
                    j += 2
                elif text[j] == '"':
                    break
                else:
                    j += 1
            tokens.append(text[i:j + 1])
            i = j + 1
        else:
            # Atom (unquoted)
            j = i
            while j < n and text[j] not in ' \t\n\r()':
                j += 1
            tokens.append(text[i:j])
            i = j
    return tokens


def parse_sexpr_tokens(tokens: list[str], pos: int = 0) -> tuple[Any, int]:
    """Parse tokens into nested list structure."""
    if pos >= len(tokens):
        return None, pos

    if tokens[pos] == '(':
        result = []
        pos += 1
        while pos < len(tokens) and tokens[pos] != ')':
            child, pos = parse_sexpr_tokens(tokens, pos)
            if child is not None:
                result.append(child)
        if pos < len(tokens):
            pos += 1  # skip ')'
        return result, pos
    else:
        token = tokens[pos]
        if token.startswith('"') and token.endswith('"'):
            return token[1:-1], pos + 1
        return token, pos + 1


def parse_sexpr(text: str) -> list:
    """Parse S-expression text into nested list structure."""
    tokens = tokenize_sexpr(text)
    result, _ = parse_sexpr_tokens(tokens, 0)
    return result if isinstance(result, list) else [result]


def find_nodes(tree: list, tag: str) -> list[list]:
    """Find all child nodes with given tag name."""
    results = []
    if not isinstance(tree, list) or len(tree) == 0:
        return results
    for item in tree:
        if isinstance(item, list) and len(item) > 0 and item[0] == tag:
            results.append(item)
    return results


def find_node(tree: list, tag: str) -> list | None:
    """Find first child node with given tag name."""
    nodes = find_nodes(tree, tag)
    return nodes[0] if nodes else None


def get_property(tree: list, prop_name: str) -> str | None:
    """Get a property value from a symbol node."""
    for item in tree:
        if isinstance(item, list) and len(item) >= 3 and item[0] == 'property':
            if item[1] == prop_name:
                return item[2]
    return None


def parse_kicad_sch(content: str) -> dict:
    """
    Parse a KiCad .kicad_sch file into structured data.

    Returns:
        {
            'version': int,
            'generator': str,
            'uuid': str,
            'lib_symbols': [{'name': str, 'pins': [...]}],
            'symbols': [{'lib_id': str, 'ref': str, 'value': str, 'x': float, 'y': float, 'rotation': float, 'uuid': str, 'unit': int}],
            'wires': [{'x1': float, 'y1': float, 'x2': float, 'y2': float}],
            'labels': [{'name': str, 'x': float, 'y': float}],
            'power_symbols': [{'name': str, 'x': float, 'y': float}],
            'junctions': [{'x': float, 'y': float}],
        }
    """
    try:
        tree = parse_sexpr(content)
    except Exception:
        return None

    if not isinstance(tree, list) or len(tree) == 0 or tree[0] != 'kicad_sch':
        return None

    result = {
        'version': None,
        'generator': None,
        'uuid': None,
        'lib_symbols': [],
        'symbols': [],
        'wires': [],
        'labels': [],
        'power_symbols': [],
        'junctions': [],
    }

    # Extract version
    ver_node = find_node(tree, 'version')
    if ver_node and len(ver_node) > 1:
        try:
            result['version'] = int(ver_node[1])
        except (ValueError, TypeError):
            pass

    # Extract generator
    gen_node = find_node(tree, 'generator')
    if gen_node and len(gen_node) > 1:
        result['generator'] = str(gen_node[1])

    # Extract UUID
    uuid_node = find_node(tree, 'uuid')
    if uuid_node and len(uuid_node) > 1:
        result['uuid'] = str(uuid_node[1])

    # Extract lib_symbols
    lib_syms_node = find_node(tree, 'lib_symbols')
    if lib_syms_node:
        for sym_node in find_nodes(lib_syms_node, 'symbol'):
            lib_sym = _parse_lib_symbol(sym_node)
            if lib_sym:
                result['lib_symbols'].append(lib_sym)

    # Extract component instances (symbol nodes at top level, not inside lib_symbols)
    for item in tree:
        if isinstance(item, list) and len(item) > 0:
            if item[0] == 'symbol':
                sym = _parse_symbol_instance(item)
                if sym:
                    # Check if power symbol
                    if sym.get('is_power'):
                        result['power_symbols'].append({
                            'name': sym.get('value', sym.get('lib_id', '')),
                            'lib_id': sym.get('lib_id', ''),
                            'x': sym['x'],
                            'y': sym['y'],
                        })
                    else:
                        result['symbols'].append(sym)

            elif item[0] == 'wire':
                wire = _parse_wire(item)
                if wire:
                    result['wires'].append(wire)

            elif item[0] == 'label' or item[0] == 'global_label' or item[0] == 'hierarchical_label':
                label = _parse_label(item)
                if label:
                    result['labels'].append(label)

            elif item[0] == 'junction':
                junc = _parse_junction(item)
                if junc:
                    result['junctions'].append(junc)

    return result


def _parse_lib_symbol(node: list) -> dict | None:
    """Parse a lib_symbol definition to extract pin info."""
    if len(node) < 2:
        return None

    name = str(node[1])
    pins = []

    # Recursively find all pins (they can be in sub-symbols like "R_0_1", "R_1_1")
    _collect_pins(node, pins)

    return {'name': name, 'pins': pins}


def _collect_pins(node: list, pins: list):
    """Recursively collect pin definitions from a symbol tree."""
    if not isinstance(node, list):
        return

    for item in node:
        if isinstance(item, list) and len(item) > 0:
            if item[0] == 'pin':
                pin = _parse_pin_def(item)
                if pin:
                    pins.append(pin)
            elif item[0] == 'symbol':
                # Sub-symbol (e.g., "R_0_1")
                _collect_pins(item, pins)


def _parse_pin_def(node: list) -> dict | None:
    """Parse a pin definition: (pin TYPE STYLE (at X Y ROT) (length L) (name "N") (number "N"))"""
    if len(node) < 3:
        return None

    pin_type = str(node[1]) if len(node) > 1 else 'passive'
    pin_style = str(node[2]) if len(node) > 2 else 'line'

    x, y, rotation = 0.0, 0.0, 0.0
    name = ''
    number = ''
    length = 2.54

    for item in node:
        if isinstance(item, list) and len(item) > 0:
            if item[0] == 'at' and len(item) >= 3:
                try:
                    x = float(item[1])
                    y = float(item[2])
                    if len(item) > 3:
                        rotation = float(item[3])
                except (ValueError, TypeError):
                    pass
            elif item[0] == 'name' and len(item) >= 2:
                name = str(item[1])
            elif item[0] == 'number' and len(item) >= 2:
                number = str(item[1])
            elif item[0] == 'length' and len(item) >= 2:
                try:
                    length = float(item[1])
                except (ValueError, TypeError):
                    pass

    return {
        'type': pin_type,
        'style': pin_style,
        'x': x, 'y': y,
        'rotation': rotation,
        'name': name,
        'number': number,
        'length': length,
    }


def _parse_symbol_instance(node: list) -> dict | None:
    """Parse a symbol instance (component placement)."""
    if len(node) < 2:
        return None

    # First check if this has a lib_id (component instance) vs lib_symbols definition
    lib_id_node = find_node(node, 'lib_id')
    if not lib_id_node:
        return None

    lib_id = str(lib_id_node[1]) if len(lib_id_node) > 1 else ''

    # Position
    x, y, rotation = 0.0, 0.0, 0.0
    at_node = find_node(node, 'at')
    if at_node and len(at_node) >= 3:
        try:
            x = float(at_node[1])
            y = float(at_node[2])
            if len(at_node) > 3:
                rotation = float(at_node[3])
        except (ValueError, TypeError):
            pass

    # Unit
    unit = 1
    unit_node = find_node(node, 'unit')
    if unit_node and len(unit_node) > 1:
        try:
            unit = int(unit_node[1])
        except (ValueError, TypeError):
            pass

    # Properties
    ref = get_property(node, 'Reference') or ''
    value = get_property(node, 'Value') or ''
    footprint = get_property(node, 'Footprint') or ''

    # UUID
    uuid_node = find_node(node, 'uuid')
    sym_uuid = str(uuid_node[1]) if uuid_node and len(uuid_node) > 1 else ''

    # Check if power symbol
    is_power = False
    if 'power:' in lib_id.lower() or lib_id.startswith('power:'):
        is_power = True
    # Also check for in_bom/on_board properties
    in_bom = find_node(node, 'in_bom')
    if in_bom and len(in_bom) > 1 and str(in_bom[1]) == 'no':
        # Power symbols typically have in_bom no
        if ref.startswith('#'):
            is_power = True

    # Extract pin instances for this placement
    pin_instances = []
    for item in node:
        if isinstance(item, list) and len(item) > 0 and item[0] == 'pin':
            pin_name = str(item[1]) if len(item) > 1 else ''
            pin_uuid = ''
            uuid_sub = find_node(item, 'uuid')
            if uuid_sub and len(uuid_sub) > 1:
                pin_uuid = str(uuid_sub[1])
            pin_instances.append({'name': pin_name, 'uuid': pin_uuid})

    return {
        'lib_id': lib_id,
        'ref': ref,
        'value': value,
        'footprint': footprint,
        'x': x, 'y': y,
        'rotation': rotation,
        'unit': unit,
        'uuid': sym_uuid,
        'is_power': is_power,
        'pin_instances': pin_instances,
    }


def _parse_wire(node: list) -> dict | None:
    """Parse a wire: (wire (pts (xy X1 Y1) (xy X2 Y2)) ...)"""
    pts_node = find_node(node, 'pts')
    if not pts_node:
        return None

    xy_nodes = find_nodes(pts_node, 'xy')
    if len(xy_nodes) < 2:
        return None

    try:
        x1 = float(xy_nodes[0][1])
        y1 = float(xy_nodes[0][2])
        x2 = float(xy_nodes[1][1])
        y2 = float(xy_nodes[1][2])
        return {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}
    except (ValueError, TypeError, IndexError):
        return None


def _parse_label(node: list) -> dict | None:
    """Parse a label/global_label/hierarchical_label."""
    if len(node) < 2:
        return None

    name = str(node[1])
    x, y = 0.0, 0.0

    at_node = find_node(node, 'at')
    if at_node and len(at_node) >= 3:
        try:
            x = float(at_node[1])
            y = float(at_node[2])
        except (ValueError, TypeError):
            pass

    return {'name': name, 'x': x, 'y': y, 'type': node[0]}


def _parse_junction(node: list) -> dict | None:
    """Parse a junction: (junction (at X Y))"""
    at_node = find_node(node, 'at')
    if at_node and len(at_node) >= 3:
        try:
            return {'x': float(at_node[1]), 'y': float(at_node[2])}
        except (ValueError, TypeError):
            pass
    return None
