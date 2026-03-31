"""
Connection Resolver for KiCad Schematics.

Takes parsed schematic data and resolves wire-to-pin connectivity,
producing component-to-component connections for training data.
"""

import math
from typing import Any


# Tolerance for matching wire endpoints to pin positions (in mm)
POSITION_TOLERANCE = 0.5


def resolve_connections(parsed_sch: dict) -> list[dict]:
    """
    Resolve connections between components by matching wire endpoints to pin positions.

    Args:
        parsed_sch: Output from sexpr_parser.parse_kicad_sch()

    Returns:
        List of connections: [{"from": "R1:1", "to": "U1:5"}, ...]
    """
    if not parsed_sch:
        return []

    # Build pin position map: (x, y) -> (ref, pin_number)
    pin_map = _build_pin_position_map(parsed_sch)

    # Build wire graph (including junctions)
    wire_graph = _build_wire_graph(parsed_sch)

    # Build label-based connections
    label_connections = _resolve_label_connections(parsed_sch, pin_map, wire_graph)

    # Find connected pin groups via wire paths
    wire_connections = _resolve_wire_connections(pin_map, wire_graph)

    # Merge and deduplicate
    all_connections = wire_connections + label_connections
    return _deduplicate_connections(all_connections)


def _build_pin_position_map(parsed_sch: dict) -> dict[tuple[float, float], tuple[str, str]]:
    """
    Build a map from (x, y) positions to (component_ref, pin_number/name).

    Uses lib_symbol pin definitions + component placement (position + rotation).
    """
    pin_map = {}

    # Build lib_symbol pin data lookup
    lib_pins = {}
    for lib_sym in parsed_sch.get('lib_symbols', []):
        name = lib_sym['name']
        lib_pins[name] = lib_sym.get('pins', [])

    # For each placed component, calculate absolute pin positions
    for sym in parsed_sch.get('symbols', []):
        ref = sym.get('ref', '')
        lib_id = sym.get('lib_id', '')
        comp_x = sym.get('x', 0.0)
        comp_y = sym.get('y', 0.0)
        comp_rot = sym.get('rotation', 0.0)
        unit = sym.get('unit', 1)

        if not ref or ref.startswith('#'):
            continue

        # Find matching lib_symbol
        pins = lib_pins.get(lib_id, [])
        if not pins:
            # Try without library prefix
            for lname, lpins in lib_pins.items():
                if lname == lib_id or lname.endswith(':' + lib_id.split(':')[-1]):
                    pins = lpins
                    break

        for pin in pins:
            pin_x = pin.get('x', 0.0)
            pin_y = pin.get('y', 0.0)
            pin_num = pin.get('number', '')
            pin_name = pin.get('name', '')

            # Apply rotation to pin position relative to component
            abs_x, abs_y = _rotate_point(pin_x, pin_y, comp_rot)
            abs_x += comp_x
            abs_y += comp_y

            # Use pin number as identifier, fallback to name
            pin_id = pin_num or pin_name

            if pin_id:
                key = (_round_coord(abs_x), _round_coord(abs_y))
                pin_map[key] = (ref, pin_id)

    # Also add power symbol positions
    for psym in parsed_sch.get('power_symbols', []):
        name = psym.get('name', '')
        x = psym.get('x', 0.0)
        y = psym.get('y', 0.0)
        lib_id = psym.get('lib_id', '')

        if name:
            key = (_round_coord(x), _round_coord(y))
            # Use power net name as both ref and pin
            pin_map[key] = (name, '1')

    return pin_map


def _build_wire_graph(parsed_sch: dict) -> dict[tuple[float, float], set[tuple[float, float]]]:
    """Build adjacency graph from wires."""
    graph: dict[tuple[float, float], set[tuple[float, float]]] = {}

    for wire in parsed_sch.get('wires', []):
        p1 = (_round_coord(wire['x1']), _round_coord(wire['y1']))
        p2 = (_round_coord(wire['x2']), _round_coord(wire['y2']))

        graph.setdefault(p1, set()).add(p2)
        graph.setdefault(p2, set()).add(p1)

    return graph


def _resolve_wire_connections(
    pin_map: dict[tuple[float, float], tuple[str, str]],
    wire_graph: dict[tuple[float, float], set[tuple[float, float]]]
) -> list[dict]:
    """Find pin-to-pin connections by tracing wire paths."""
    connections = []
    visited_pairs = set()

    # For each pin position, trace through wires to find connected pins
    for pin_pos, (ref, pin_id) in pin_map.items():
        # BFS through wire graph from this pin
        connected_pins = _trace_wire_path(pin_pos, wire_graph, pin_map)

        for other_ref, other_pin in connected_pins:
            if other_ref == ref and other_pin == pin_id:
                continue

            pair_key = tuple(sorted([(ref, pin_id), (other_ref, other_pin)]))
            if pair_key not in visited_pairs:
                visited_pairs.add(pair_key)
                connections.append({
                    'from': f"{ref}:{pin_id}",
                    'to': f"{other_ref}:{other_pin}",
                })

    return connections


def _trace_wire_path(
    start: tuple[float, float],
    wire_graph: dict[tuple[float, float], set[tuple[float, float]]],
    pin_map: dict[tuple[float, float], tuple[str, str]]
) -> list[tuple[str, str]]:
    """BFS from start position through wire graph, collecting connected pins."""
    connected = []
    visited = set()
    queue = []

    # Find wire nodes near the start position
    start_nodes = _find_nearby_nodes(start, wire_graph)
    for node in start_nodes:
        queue.append(node)
        visited.add(node)

    # Also check if start itself is a wire node
    if start in wire_graph:
        if start not in visited:
            queue.append(start)
            visited.add(start)

    while queue:
        current = queue.pop(0)

        # Check if this position has a pin
        pin = _find_nearby_pin(current, pin_map)
        if pin:
            connected.append(pin)

        # Follow wires
        for neighbor in wire_graph.get(current, set()):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return connected


def _resolve_label_connections(
    parsed_sch: dict,
    pin_map: dict[tuple[float, float], tuple[str, str]],
    wire_graph: dict[tuple[float, float], set[tuple[float, float]]]
) -> list[dict]:
    """Resolve connections through net labels (same label name = same net)."""
    connections = []

    # Group labels by name
    label_groups: dict[str, list[tuple[float, float]]] = {}
    for label in parsed_sch.get('labels', []):
        name = label['name']
        pos = (_round_coord(label['x']), _round_coord(label['y']))
        label_groups.setdefault(name, []).append(pos)

    # For each label group, find pins connected to each label position
    for label_name, positions in label_groups.items():
        all_pins = []
        for pos in positions:
            # Find pins reachable from this label position via wires
            nearby_pins = _trace_wire_path(pos, wire_graph, pin_map)
            # Also check direct pin at label position
            direct_pin = _find_nearby_pin(pos, pin_map)
            if direct_pin:
                nearby_pins.append(direct_pin)
            all_pins.extend(nearby_pins)

        # Create connections between all pins in the same label group
        unique_pins = list(set(all_pins))
        for i in range(len(unique_pins)):
            for j in range(i + 1, len(unique_pins)):
                ref_a, pin_a = unique_pins[i]
                ref_b, pin_b = unique_pins[j]
                connections.append({
                    'from': f"{ref_a}:{pin_a}",
                    'to': f"{ref_b}:{pin_b}",
                })

    return connections


def _rotate_point(x: float, y: float, angle_deg: float) -> tuple[float, float]:
    """Rotate point (x, y) by angle degrees around origin."""
    if angle_deg == 0:
        return x, y
    angle_rad = math.radians(angle_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    new_x = x * cos_a - y * sin_a
    new_y = x * sin_a + y * cos_a
    return new_x, new_y


def _round_coord(val: float) -> float:
    """Round coordinate to 2 decimal places for matching."""
    return round(val, 2)


def _find_nearby_nodes(
    pos: tuple[float, float],
    graph: dict[tuple[float, float], set[tuple[float, float]]]
) -> list[tuple[float, float]]:
    """Find wire graph nodes within tolerance of position."""
    result = []
    px, py = pos
    for node in graph:
        nx, ny = node
        if abs(nx - px) <= POSITION_TOLERANCE and abs(ny - py) <= POSITION_TOLERANCE:
            result.append(node)
    return result


def _find_nearby_pin(
    pos: tuple[float, float],
    pin_map: dict[tuple[float, float], tuple[str, str]]
) -> tuple[str, str] | None:
    """Find a pin within tolerance of position."""
    px, py = pos
    for pin_pos, pin_info in pin_map.items():
        nx, ny = pin_pos
        if abs(nx - px) <= POSITION_TOLERANCE and abs(ny - py) <= POSITION_TOLERANCE:
            return pin_info
    return None


def _deduplicate_connections(connections: list[dict]) -> list[dict]:
    """Remove duplicate connections."""
    seen = set()
    result = []
    for conn in connections:
        key = tuple(sorted([conn['from'], conn['to']]))
        if key not in seen:
            seen.add(key)
            result.append(conn)
    return result
