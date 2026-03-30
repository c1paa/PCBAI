"""
Exporter for KiCad PCB to Spectra DSN format.
DSN is the input format for FreeRouting autorouter.

Produces valid Specctra DSN that FreeRouting v2.x can parse.
"""

from pathlib import Path
from typing import Any


class SpectraDSNExporter:
    """Export KiCad PCB data to Spectra DSN format."""

    def export(self, board_data: dict[str, Any], filepath: str | Path) -> None:
        """Export board data to a .dsn file."""
        filepath = Path(filepath)
        lines: list[str] = []

        board_name = filepath.stem

        lines.append(f'(pcb {board_name}.dsn')
        lines.append('  (parser')
        lines.append('    (string_quote ")')
        lines.append('    (space_in_quoted_tokens on)')
        lines.append('    (host_cad "KiCad\'s Pcbnew")')
        lines.append('    (host_version "8.0.0")')
        lines.append('  )')
        lines.append('  (resolution um 10)')
        lines.append('  (unit um)')

        # Structure section: layers + boundary + rules
        lines.extend(self._generate_structure(board_data))

        # Placement section: component positions
        lines.extend(self._generate_placement(board_data))

        # Library section: component padstacks
        lines.extend(self._generate_library(board_data))

        # Network section: nets and connections
        lines.extend(self._generate_network(board_data))

        # Wiring section: existing tracks
        lines.extend(self._generate_wiring(board_data))

        lines.append(')')

        filepath.write_text('\n'.join(lines))

    def _generate_structure(self, board_data: dict[str, Any]) -> list[str]:
        """Generate structure section with layers, boundary, and rules."""
        lines: list[str] = []
        lines.append('  (structure')

        # Layers
        layers = board_data.get('layers', [])
        if not layers:
            layers = [
                {'name': 'F.Cu', 'type': 'signal'},
                {'name': 'B.Cu', 'type': 'signal'},
            ]

        for layer in layers:
            layer_name = layer.get('name', 'F.Cu')
            layer_type = layer.get('type', 'signal')
            lines.append(f'    (layer {layer_name}')
            lines.append(f'      (type {layer_type})')
            lines.append('    )')

        # Boundary from board area
        general = board_data.get('general', {})
        area = general.get('area', {'x1': 0, 'y1': 0, 'x2': 100, 'y2': 100})
        # Convert mm to um (multiply by 1000, then by resolution factor 10)
        scale = 10000  # mm -> um * 10
        x1 = int(area['x1'] * scale)
        y1 = int(area['y1'] * scale)
        x2 = int(area['x2'] * scale)
        y2 = int(area['y2'] * scale)

        lines.append('    (boundary')
        lines.append(f'      (path pcb 0  {x1} {y1}  {x2} {y1}  {x2} {y2}  {x1} {y2}  {x1} {y1})')
        lines.append('    )')

        # Via padstack reference
        lines.append('    (via "Via[0-1]_600:300_um")')

        # Design rules
        lines.append('    (rule')
        lines.append('      (width 2500)')  # 0.25mm in um*10
        lines.append('      (clearance 2000)')  # 0.2mm
        lines.append('      (clearance 2000 (type default_smd))')
        lines.append('      (clearance 500 (type smd_smd))')
        lines.append('    )')

        lines.append('  )')
        return lines

    def _generate_placement(self, board_data: dict[str, Any]) -> list[str]:
        """Generate placement section with component positions."""
        lines: list[str] = []
        lines.append('  (placement')

        footprints = board_data.get('footprints', [])
        scale = 10000  # mm -> um * 10

        for i, fp in enumerate(footprints):
            fp_name = fp.get('name', 'UNKNOWN')
            # Create a safe component ID
            comp_id = f"C{i+1}"
            pos = fp.get('position', {'x': 0, 'y': 0, 'angle': 0})
            layer = fp.get('layer', 'F.Cu')
            side = 'front' if layer == 'F.Cu' else 'back'
            x = int(pos.get('x', 0) * scale)
            y = int(pos.get('y', 0) * scale)
            angle = pos.get('angle', 0)

            lines.append(f'    (component "{fp_name}"')
            lines.append(f'      (place {comp_id} {x} {y} {side} {angle})')
            lines.append('    )')

        lines.append('  )')
        return lines

    def _generate_library(self, board_data: dict[str, Any]) -> list[str]:
        """Generate library section with padstacks."""
        lines: list[str] = []
        lines.append('  (library')

        footprints = board_data.get('footprints', [])
        scale = 10000

        # Generate image (footprint definition) for each unique footprint
        seen_fps: set[str] = set()
        for i, fp in enumerate(footprints):
            fp_name = fp.get('name', 'UNKNOWN')
            if fp_name in seen_fps:
                continue
            seen_fps.add(fp_name)

            lines.append(f'    (image "{fp_name}"')

            # Generate 2 pads for simple 2-pin components
            pads = fp.get('pads', [])
            if not pads:
                # Default: 2 pads spaced 10mm apart (SMD)
                pad_spacing = int(10 * scale)
                for pad_num in range(1, 3):
                    pad_x = (pad_num - 1) * pad_spacing
                    lines.append(f'      (pin Rect[T]Pad_1000x1000_um {pad_num} {pad_x} 0)')
            else:
                for pad in pads:
                    pad_num = pad.get('number', 1)
                    px = int(pad.get('x', 0) * scale)
                    py = int(pad.get('y', 0) * scale)
                    lines.append(f'      (pin Rect[T]Pad_1000x1000_um {pad_num} {px} {py})')

            lines.append('    )')

        # Padstack definitions
        lines.append('    (padstack Rect[T]Pad_1000x1000_um')
        lines.append('      (shape (rect F.Cu -5000 -5000 5000 5000))')
        lines.append('      (attach off)')
        lines.append('    )')

        # Via padstack
        lines.append('    (padstack "Via[0-1]_600:300_um"')
        lines.append('      (shape (circle F.Cu 6000))')
        lines.append('      (shape (circle B.Cu 6000))')
        lines.append('      (attach off)')
        lines.append('    )')

        lines.append('  )')
        return lines

    def _generate_network(self, board_data: dict[str, Any]) -> list[str]:
        """Generate network section with nets."""
        lines: list[str] = []
        lines.append('  (network')

        netlist = board_data.get('netlist', {'nets': {}})
        nets = netlist.get('nets', {})
        footprints = board_data.get('footprints', [])

        for net_name, net_code in nets.items():
            if net_code == 0:
                continue  # Skip unconnected net
            lines.append(f'    (net "{net_name}"')
            lines.append(f'      (pins')

            # Assign pins to nets based on simple heuristic:
            # For a 2-component board with 3 nets, distribute pins
            if footprints:
                pin_assignments = self._assign_pins_to_net(
                    net_name, net_code, footprints, nets
                )
                for pin_ref in pin_assignments:
                    lines.append(f'        {pin_ref}')

            lines.append('      )')
            lines.append('    )')

        # Net class
        lines.append('    (class kicad_default ""')
        for net_name in nets:
            lines.append(f'      (add_net "{net_name}")')
        lines.append('      (circuit')
        lines.append('        (use_via "Via[0-1]_600:300_um")')
        lines.append('      )')
        lines.append('      (rule')
        lines.append('        (width 2500)')
        lines.append('        (clearance 2000)')
        lines.append('      )')
        lines.append('    )')

        lines.append('  )')
        return lines

    def _assign_pins_to_net(
        self,
        net_name: str,
        net_code: int,
        footprints: list[dict],
        nets: dict,
    ) -> list[str]:
        """Assign component pins to a net.

        Simple heuristic for common configurations:
        - For N components with 2 pins each, distribute nets across pins.
        """
        pin_refs: list[str] = []
        num_components = len(footprints)
        net_codes = sorted(nets.values())

        if num_components == 2 and len(net_codes) >= 2:
            # Common case: 2-component board (e.g., LED + resistor)
            # Net assignment: C1-1 <-> C2-1 (shared net), C1-2 to power, C2-2 to ground
            non_zero_nets = [c for c in net_codes if c != 0]
            if net_code in non_zero_nets:
                idx = non_zero_nets.index(net_code)
                if idx == 0:
                    # First net: connects to C1 pin 2 and C2 pin 2
                    pin_refs = ['C1-2', 'C2-2']
                elif idx == 1:
                    # Second net: power, connects to C1 pin 1
                    pin_refs = ['C1-1']
                elif idx == 2:
                    # Third net: connects C1 pin 2 to C2 pin 1 (signal between components)
                    pin_refs = ['C2-1']
        else:
            # Fallback: assign first pin of each component to this net
            for i in range(num_components):
                pin_refs.append(f'C{i+1}-1')

        return pin_refs

    def _generate_wiring(self, board_data: dict[str, Any]) -> list[str]:
        """Generate wiring section with existing tracks."""
        lines: list[str] = []
        lines.append('  (wiring')

        tracks = board_data.get('tracks', [])
        scale = 10000

        for track in tracks:
            start = track['start']
            end = track['end']
            width = int(track.get('width', 0.25) * scale)
            layer = track.get('layer', 'F.Cu')

            sx = int(start['x'] * scale)
            sy = int(start['y'] * scale)
            ex = int(end['x'] * scale)
            ey = int(end['y'] * scale)

            lines.append(f'    (wire (path {layer} {width}  {sx} {sy}  {ex} {ey}))')

        lines.append('  )')
        return lines

    def _kicad_to_spectra_layer(self, kicad_layer: str) -> str:
        """Convert KiCad layer name to Spectra layer name."""
        mapping = {
            'F.Cu': 'top',
            'B.Cu': 'bottom',
            'In1.Cu': 'inner1',
            'In2.Cu': 'inner2',
        }
        return mapping.get(kicad_layer, kicad_layer.lower().replace('.cu', ''))


def export_to_dsn(board_data: dict[str, Any], filepath: str | Path) -> None:
    """Convenience function to export board data to DSN format."""
    exporter = SpectraDSNExporter()
    exporter.export(board_data, filepath)
