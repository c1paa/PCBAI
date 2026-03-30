"""
Parser for KiCad .kicad_pcb files.
Reads and writes PCB files in S-expression format.
"""

import re
from pathlib import Path
from typing import Any


class KiCadPCBParser:
    """Parser for KiCad .kicad_pcb files."""
    
    def __init__(self):
        self.board_data: dict[str, Any] = {}
    
    def parse_file(self, filepath: str | Path) -> dict[str, Any]:
        """Parse a .kicad_pcb file and return structured data."""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"PCB file not found: {filepath}")
        
        content = filepath.read_text()
        return self.parse_content(content)
    
    def parse_content(self, content: str) -> dict[str, Any]:
        """Parse S-expression content."""
        # Remove comments
        content = re.sub(r'\([^;]*;[^\n]*\n', '(', content)
        content = re.sub(r';[^\n]*\n', '\n', content)
        
        self.board_data = {
            'version': self._extract_version(content),
            'general': self._extract_general(content),
            'layers': self._extract_layers(content),
            'footprints': self._extract_footprints(content),
            'tracks': self._extract_tracks(content),
            'vias': self._extract_vias(content),
            'zones': self._extract_zones(content),
            'netlist': self._extract_netlist(content),
        }
        
        return self.board_data
    
    def _extract_version(self, content: str) -> str:
        """Extract KiCad version from file."""
        match = re.search(r'\(version\s+(\d+)\)', content)
        return match.group(1) if match else 'unknown'
    
    def _extract_general(self, content: str) -> dict[str, Any]:
        """Extract general board settings."""
        general = {}
        
        # Extract thickness
        match = re.search(r'\(thickness\s+([\d.]+)\)', content)
        if match:
            general['thickness'] = float(match.group(1))
        
        # Extract board size
        match = re.search(r'\(area\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\)', content)
        if match:
            general['area'] = {
                'x1': float(match.group(1)),
                'y1': float(match.group(2)),
                'x2': float(match.group(3)),
                'y2': float(match.group(4)),
            }
        
        return general
    
    def _extract_layers(self, content: str) -> list[dict[str, Any]]:
        """Extract layer definitions."""
        layers = []
        # Simpler pattern for layers
        layer_pattern = r'\(\d+\s+"([^"]+)"\s+type\s+(\w+)'
        layer_matches = re.findall(layer_pattern, content)

        for match in layer_matches:
            layers.append({
                'name': match[0],
                'type': match[1],
                'align': 'top',  # Default
            })

        return layers
    
    def _extract_footprints(self, content: str) -> list[dict[str, Any]]:
        """Extract footprint definitions."""
        footprints = []

        # Simpler approach: find footprint start positions
        fp_pattern = r'\(footprint\s+"([^"]+)"\s+\(layer\s+(\w+(?:\.\w+)*)\)'

        fp_starts = list(re.finditer(fp_pattern, content))

        for match in fp_starts:
            fp_name = match.group(1)
            fp_layer = match.group(2)

            # Extract position - search after the layer
            pos_match = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.]+))?\)',
                                  content[match.start():match.start()+200])

            footprint = {
                'name': fp_name,
                'layer': fp_layer,
                'position': {
                    'x': float(pos_match.group(1)) if pos_match else 0,
                    'y': float(pos_match.group(2)) if pos_match else 0,
                    'angle': float(pos_match.group(3)) if pos_match and pos_match.group(3) else 0,
                },
                'pads': [],
            }

            footprints.append(footprint)

        return footprints
    
    def _extract_tracks(self, content: str) -> list[dict[str, Any]]:
        """Extract track (segment) definitions."""
        tracks = []

        # Simpler pattern - just extract segment data
        track_pattern = r'\(segment\s+\(start\s+([\d.-]+)\s+([\d.-]+)\)\s+\(end\s+([\d.-]+)\s+([\d.-]+)\)\s+\(width\s+([\d.]+)\)\s+\(layer\s+(\w+(?:\.\w+)*)\)'

        for match in re.finditer(track_pattern, content):
            tracks.append({
                'start': {'x': float(match.group(1)), 'y': float(match.group(2))},
                'end': {'x': float(match.group(3)), 'y': float(match.group(4))},
                'width': float(match.group(5)),
                'layer': match.group(6),
                'net': None,
                'netname': None,
            })

        return tracks
    
    def _extract_vias(self, content: str) -> list[dict[str, Any]]:
        """Extract via definitions."""
        vias = []

        # Simpler pattern for vias
        via_pattern = r'\(via\s+\(at\s+([\d.-]+)\s+([\d.-]+)\)\s+\(size\s+([\d.]+)\)\s+\(drill\s+([\d.]+)\)\s+\(layers\s+(\w+(?:\.\w+)*)\s+(\w+(?:\.\w+)*)\)'

        for match in re.finditer(via_pattern, content):
            vias.append({
                'position': {'x': float(match.group(1)), 'y': float(match.group(2))},
                'size': float(match.group(3)),
                'drill': float(match.group(4)),
                'layers': [match.group(5), match.group(6)],
                'net': None,
                'netname': None,
            })

        return vias
    
    def _extract_zones(self, content: str) -> list[dict[str, Any]]:
        """Extract zone (polygon) definitions."""
        zones = []
        # Simplified: just count zones for now
        zone_count = len(re.findall(r'\(zone\s+\(net\s+', content))
        
        for _ in range(zone_count):
            zones.append({'type': 'polygon'})
        
        return zones
    
    def _extract_netlist(self, content: str) -> dict[str, Any]:
        """Extract netlist information."""
        netlist = {'nets': {}, 'net_codes': {}}
        
        # Extract net definitions
        net_pattern = r'\(net\s+(\d+)\s+"([^"]+)"\)'
        
        for match in re.finditer(net_pattern, content):
            net_code = int(match.group(1))
            net_name = match.group(2)
            netlist['nets'][net_name] = net_code
            netlist['net_codes'][net_code] = net_name
        
        return netlist
    
    def save_file(self, filepath: str | Path, data: dict[str, Any] | None = None) -> None:
        """Save board data to a .kicad_pcb file."""
        filepath = Path(filepath)
        data = data or self.board_data
        
        if not data:
            raise ValueError("No board data to save")
        
        content = self._generate_s_expression(data)
        filepath.write_text(content)
    
    def _generate_s_expression(self, data: dict[str, Any]) -> str:
        """Generate S-expression content from board data (KiCad 9.0 format)."""
        lines = []

        # Header - KiCad 9.0 format
        version = data.get('version', '20241229')
        generator_version = data.get('generator_version', '9.0')
        lines.append('(kicad_pcb')
        lines.append(f'\t(version {version})')
        lines.append(f'\t(generator "pcbnew")')
        lines.append(f'\t(generator_version "{generator_version}")')

        # General section with thickness
        lines.append('\t(general')
        thickness = data.get('general', {}).get('thickness', 1.6)
        lines.append(f'\t\t(thickness {thickness})')
        lines.append('\t\t(legacy_teardrops no)')
        lines.append('\t)')

        # Paper
        lines.append('\t(paper "A4")')

        # Layers - KiCad 9.0 format with all standard layers
        lines.append('\t(layers')
        layers = data.get('layers', [])
        if not layers:
            # Default 2-layer board with standard KiCad layers
            standard_layers = [
                (0, 'F.Cu', 'signal'),
                (2, 'B.Cu', 'signal'),
                (5, 'F.SilkS', 'user'),
                (7, 'B.SilkS', 'user'),
                (1, 'F.Mask', 'user'),
                (3, 'B.Mask', 'user'),
                (13, 'F.Paste', 'user'),
                (15, 'B.Paste', 'user'),
                (25, 'Edge.Cuts', 'user'),
            ]
            for layer_num, name, layer_type in standard_layers:
                lines.append(f'\t\t({layer_num} "{name}" {layer_type})')
        else:
            # Map layer names to standard KiCad numbers
            layer_map = {
                'F.Cu': (0, 'signal'),
                'B.Cu': (2, 'signal'),
                'F.SilkS': (5, 'user'),
                'B.SilkS': (7, 'user'),
                'F.Mask': (1, 'user'),
                'B.Mask': (3, 'user'),
                'F.Paste': (13, 'user'),
                'B.Paste': (15, 'user'),
                'Edge.Cuts': (25, 'user'),
            }
            for layer in layers:
                name = layer.get('name', 'F.Cu')
                if name in layer_map:
                    layer_num, layer_type = layer_map[name]
                    lines.append(f'\t\t({layer_num} "{name}" {layer_type})')

        lines.append('\t)')

        # Setup section
        lines.append('\t(setup')
        lines.append('\t\t(pad_to_mask_clearance 0)')
        lines.append('\t\t(allow_soldermask_bridges_in_footprints no)')
        lines.append('\t)')

        lines.append('')

        # Nets
        netlist = data.get('netlist', {})
        net_codes = netlist.get('net_codes', {})
        if net_codes:
            for net_code, net_name in net_codes.items():
                lines.append(f'\t(net {net_code} "{net_name}")')
            lines.append('')

        # Footprints
        for fp in data.get('footprints', []):
            lines.append(self._footprint_to_sexpr(fp))

        # Tracks
        for track in data.get('tracks', []):
            lines.append(self._track_to_sexpr(track))

        # Vias
        for via in data.get('vias', []):
            lines.append(self._via_to_sexpr(via))

        lines.append(')')

        return '\n'.join(lines)
    
    def _footprint_to_sexpr(self, fp: dict[str, Any]) -> str:
        """Convert footprint to S-expression (KiCad 9.0 format)."""
        pos = fp.get('position', {'x': 0, 'y': 0, 'angle': 0})
        angle_str = f' {pos["angle"]}' if pos.get('angle') else ''
        return f'\t(footprint "{fp["name"]}" (layer "F.Cu") (at {pos["x"]} {pos["y"]}{angle_str}))'

    def _track_to_sexpr(self, track: dict[str, Any]) -> str:
        """Convert track to S-expression (KiCad 9.0 format)."""
        start = track['start']
        end = track['end']
        width = track.get('width', 0.25)
        layer = track.get('layer', 'F.Cu')
        net = track.get('net', 0)

        net_str = f' (net {net})' if net else ''

        return f'\t(segment (start {start["x"]} {start["y"]}) (end {end["x"]} {end["y"]}) (width {width}) (layer "{layer}"){net_str})'

    def _via_to_sexpr(self, via: dict[str, Any]) -> str:
        """Convert via to S-expression (KiCad 9.0 format)."""
        pos = via['position']
        size = via.get('size', 0.6)
        drill = via.get('drill', 0.3)
        layers = via.get('layers', ['F.Cu', 'B.Cu'])
        net = via.get('net', 0)

        net_str = f' (net {net})' if net else ''

        return f'\t(via (at {pos["x"]} {pos["y"]}) (size {size}) (drill {drill}) (layers "{layers[0]}" "{layers[1]}"){net_str})'


def parse_pcb(filepath: str | Path) -> dict[str, Any]:
    """Convenience function to parse a .kicad_pcb file."""
    parser = KiCadPCBParser()
    return parser.parse_file(filepath)


def save_pcb(filepath: str | Path, data: dict[str, Any]) -> None:
    """Convenience function to save board data."""
    parser = KiCadPCBParser()
    parser.save_file(filepath, data)
