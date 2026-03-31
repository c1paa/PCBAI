"""
Circuit Graph Representation.

Centralized graph structure for circuit components and connections.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PinInfo:
    """Information about a component pin."""
    name: str
    type: str  # "input", "output", "power", "ground", "passive"
    connected_to: str | None = None
    x: float = 0.0
    y: float = 0.0
    rotation: float = 0.0


@dataclass
class ComponentNode:
    """A component in the circuit graph."""
    ref: str
    type: str
    lib_id: str
    footprint: str
    value: str
    pins: dict[str, PinInfo] = field(default_factory=dict)
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)  # (x, y, rotation)
    quantity: int = 1


@dataclass
class ConnectionEdge:
    """A connection between two component pins."""
    from_pin: str  # Format: "R1:1" or "Arduino:Pin5"
    to_pin: str    # Format: "LED1:A"
    net: str       # Net name
    wire_points: list[tuple[float, float]] = field(default_factory=list)


class CircuitGraph:
    """Graph representation of an electrical circuit."""

    def __init__(self):
        """Initialize empty circuit graph."""
        self.nodes: dict[str, ComponentNode] = {}
        self.edges: list[ConnectionEdge] = []
        self.nets: dict[str, list[str]] = {}  # net_name -> [pin_refs]

    def add_component(self, comp: dict) -> None:
        """Add a component to the graph."""
        ref = comp.get('ref', 'U1')
        
        # Create pins based on type
        pins = self._create_pins_for_type(comp.get('type', 'unknown'))
        
        node = ComponentNode(
            ref=ref,
            type=comp.get('type', 'unknown'),
            lib_id=comp.get('lib_id', ''),
            footprint=comp.get('footprint', ''),
            value=comp.get('value', ''),
            pins=pins,
            quantity=comp.get('quantity', 1)
        )
        
        self.nodes[ref] = node

    def _create_pins_for_type(self, comp_type: str) -> dict[str, PinInfo]:
        """Create default pins for component type."""
        if comp_type == 'resistor':
            return {
                '1': PinInfo(name='1', type='passive'),
                '2': PinInfo(name='2', type='passive'),
            }
        elif comp_type == 'led':
            return {
                '1': PinInfo(name='K', type='passive'),  # Cathode
                '2': PinInfo(name='A', type='passive'),  # Anode
            }
        elif comp_type == 'capacitor':
            return {
                '1': PinInfo(name='1', type='passive'),
                '2': PinInfo(name='2', type='passive'),
            }
        elif comp_type == 'mcu':
            # Generic MCU with common pins
            return {
                'VCC': PinInfo(name='VCC', type='power'),
                'GND': PinInfo(name='GND', type='ground'),
                'D5': PinInfo(name='D5', type='io'),
                'D13': PinInfo(name='D13', type='io'),
            }
        else:
            return {
                '1': PinInfo(name='1', type='passive'),
                '2': PinInfo(name='2', type='passive'),
            }

    def add_connection(self, from_pin: str, to_pin: str, net: str) -> None:
        """Add a connection between two pins."""
        edge = ConnectionEdge(
            from_pin=from_pin,
            to_pin=to_pin,
            net=net
        )
        self.edges.append(edge)
        
        # Update net database
        if net not in self.nets:
            self.nets[net] = []
        self.nets[net].extend([from_pin, to_pin])
        
        # Update pin connections
        from_parts = from_pin.split(':')
        to_parts = to_pin.split(':')
        
        if len(from_parts) == 2 and from_parts[0] in self.nodes:
            node = self.nodes[from_parts[0]]
            if from_parts[1] in node.pins:
                node.pins[from_parts[1]].connected_to = to_pin
        
        if len(to_parts) == 2 and to_parts[0] in self.nodes:
            node = self.nodes[to_parts[0]]
            if to_parts[1] in node.pins:
                node.pins[to_parts[1]].connected_to = from_pin

    def validate(self) -> list[str]:
        """Validate the circuit graph.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check all components have required pins
        for ref, node in self.nodes.items():
            if not node.pins:
                errors.append(f"Component {ref} has no pins")
        
        # Check all connections reference valid pins
        for edge in self.edges:
            from_parts = edge.from_pin.split(':')
            to_parts = edge.to_pin.split(':')
            
            if len(from_parts) == 2:
                if from_parts[0] not in self.nodes:
                    errors.append(f"Connection from unknown component: {from_parts[0]}")
                elif from_parts[1] not in self.nodes[from_parts[0]].pins:
                    errors.append(f"Connection from unknown pin: {edge.from_pin}")
            
            if len(to_parts) == 2:
                if to_parts[0] not in self.nodes:
                    errors.append(f"Connection to unknown component: {to_parts[0]}")
                elif to_parts[1] not in self.nodes[to_parts[0]].pins:
                    errors.append(f"Connection to unknown pin: {edge.to_pin}")
        
        # Check for floating nets (connected to only one pin)
        for net, pins in self.nets.items():
            if len(pins) < 2 and net not in ['GND', 'VCC', '+5V']:
                errors.append(f"Net {net} is connected to only one pin: {pins}")
        
        return errors

    def get_positioned_graph(self) -> dict[str, Any]:
        """Get graph with calculated positions.
        
        Returns:
            Dict with nodes, edges, and positions for schematic generation
        """
        # Simple auto-positioning: left-to-right layout
        mcus = [n for n in self.nodes.values() if n.type == 'mcu']
        others = [n for n in self.nodes.values() if n.type != 'mcu']
        
        # Place MCU in center
        mcu_x, mcu_y = 150, 100
        for mcu in mcus:
            mcu.position = (mcu_x, mcu_y, 0)
        
        # Place others left-to-right
        start_x = 80
        y_level = 90
        spacing = 40
        
        for i, node in enumerate(others):
            x = start_x + (i * spacing)
            rotation = 90 if node.type == 'resistor' else 0
            node.position = (x, y_level, rotation)
        
        return {
            'nodes': list(self.nodes.values()),
            'edges': self.edges,
            'nets': self.nets
        }

    @classmethod
    def from_ai_analysis(cls, analysis: dict[str, Any]) -> 'CircuitGraph':
        """Create CircuitGraph from AI analysis result.
        
        Args:
            analysis: Dict from EnhancedCircuitAnalyzer.analyze()
            
        Returns:
            Populated CircuitGraph
        """
        graph = cls()
        
        # Add components
        for comp in analysis.get('components', []):
            graph.add_component(comp)
        
        # Add connections
        for conn in analysis.get('connections', []):
            graph.add_connection(
                from_pin=conn.get('from', ''),
                to_pin=conn.get('to', ''),
                net=conn.get('net', '')
            )
        
        return graph
