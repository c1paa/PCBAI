"""
Post-Processing Pipeline for Neural Network Output.

Validates, fixes, and converts model output into valid KiCad 9.0 schematics.

Pipeline:
  Stage 1: Parse model output (compact format or JSON)
  Stage 2: Component validation
  Stage 3: Connection validation
  Stage 4: Auto-fix errors
  Stage 5: Generate .kicad_sch file
  Stage 6: Final validation
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .component_database import (
    get_component_info, find_similar_lib_id, validate_pin,
    get_valid_pins, get_component_category,
    CATEGORY_MCU, CATEGORY_MODULE, CATEGORY_PASSIVE,
)


@dataclass
class ProcessingResult:
    """Result of post-processing pipeline."""
    success: bool
    schematic_content: str = ''
    components: list[dict] = field(default_factory=list)
    connections: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    fixes_applied: list[str] = field(default_factory=list)


class SchematicPostprocessor:
    """Post-processing pipeline for model output."""

    def process(self, model_output: str, description: str = '') -> ProcessingResult:
        """
        Run the full post-processing pipeline.

        Args:
            model_output: Raw text output from the model
            description: Original description (for re-query if needed)

        Returns:
            ProcessingResult with validated schematic
        """
        result = ProcessingResult(success=False)

        # Stage 1: Parse output
        parsed = self._parse_output(model_output)
        if not parsed:
            result.errors.append("Failed to parse model output")
            return result

        components = parsed.get('components', [])
        connections = parsed.get('connections', [])

        if not components:
            result.errors.append("No components found in output")
            return result

        # Stage 2: Validate and fix components
        components, comp_fixes = self._validate_components(components)
        result.fixes_applied.extend(comp_fixes)

        # Stage 3: Validate and fix connections
        connections, conn_fixes = self._validate_connections(connections, components)
        result.fixes_applied.extend(conn_fixes)

        # Stage 4: Auto-fix structural issues
        components, connections, struct_fixes = self._auto_fix(components, connections)
        result.fixes_applied.extend(struct_fixes)

        result.components = components
        result.connections = connections

        # Stage 5: Generate .kicad_sch
        try:
            schematic = self._generate_kicad_sch(components, connections)
            result.schematic_content = schematic
        except Exception as e:
            result.errors.append(f"Schematic generation failed: {e}")
            return result

        # Stage 6: Final validation
        validation_errors = self._final_validation(result.schematic_content)
        result.warnings.extend(validation_errors)

        result.success = True
        return result

    # ========================================================================
    # Stage 1: Parse Output
    # ========================================================================

    def _parse_output(self, text: str) -> dict | None:
        """Parse model output (compact format or JSON)."""
        text = text.strip()

        # Try compact format first: COMPONENTS||CONNECTIONS
        if '||' in text:
            return self._parse_compact(text)

        # Try JSON
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

        # Try to recover truncated JSON
        recovered = self._recover_json(text)
        if recovered:
            return recovered

        return None

    def _parse_compact(self, text: str) -> dict | None:
        """Parse compact format: REF|LIB_ID|VALUE;...||FROM-TO;..."""
        try:
            parts = text.split('||')
            if len(parts) != 2:
                return None

            comp_str, conn_str = parts

            components = []
            if comp_str:
                for comp_part in comp_str.split(';'):
                    comp_part = comp_part.strip()
                    if not comp_part:
                        continue
                    fields = comp_part.split('|')
                    if len(fields) >= 2:
                        components.append({
                            'ref': fields[0].strip(),
                            'lib_id': fields[1].strip(),
                            'value': fields[2].strip() if len(fields) > 2 else '',
                        })

            connections = []
            if conn_str:
                for conn_part in conn_str.split(';'):
                    conn_part = conn_part.strip()
                    if not conn_part:
                        continue
                    pins = conn_part.split('-')
                    if len(pins) >= 2:
                        connections.append({
                            'from': pins[0].strip(),
                            'to': pins[1].strip(),
                        })

            return {'components': components, 'connections': connections}
        except Exception:
            return None

    def _recover_json(self, text: str) -> dict | None:
        """Try to recover truncated or malformed JSON."""
        # Remove trailing incomplete parts
        text = text.rstrip()

        # Try adding missing brackets
        for suffix in ['', '}', ']}', '"]}', '"}]}']:
            try:
                data = json.loads(text + suffix)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                continue

        # Try extracting JSON from surrounding text
        match = re.search(r'\{[^{}]*"components"[^{}]*\[.*?\]', text, re.DOTALL)
        if match:
            try:
                json_text = match.group(0)
                # Try to complete it
                for suffix in [']}', '"}]}', '"}],"connections":[]}']:
                    try:
                        return json.loads(json_text + suffix)
                    except json.JSONDecodeError:
                        continue
            except Exception:
                pass

        return None

    # ========================================================================
    # Stage 2: Component Validation
    # ========================================================================

    def _validate_components(self, components: list[dict]) -> tuple[list[dict], list[str]]:
        """Validate and fix component data."""
        fixes = []
        valid_components = []
        seen_refs = set()

        for comp in components:
            ref = comp.get('ref', '')
            lib_id = comp.get('lib_id', '')

            if not ref or not lib_id:
                continue

            # Fix duplicate references
            if ref in seen_refs:
                base = re.match(r'^([A-Z]+)', ref)
                if base:
                    prefix = base.group(1)
                    counter = 1
                    while f"{prefix}{counter}" in seen_refs:
                        counter += 1
                    new_ref = f"{prefix}{counter}"
                    fixes.append(f"Renamed duplicate ref {ref} -> {new_ref}")
                    ref = new_ref
                    comp['ref'] = ref

            seen_refs.add(ref)

            # Fix invalid lib_id
            info = get_component_info(lib_id)
            if not info:
                similar = find_similar_lib_id(lib_id)
                if similar:
                    fixes.append(f"Fixed lib_id: {lib_id} -> {similar}")
                    comp['lib_id'] = similar
                else:
                    fixes.append(f"Unknown lib_id kept: {lib_id}")

            valid_components.append(comp)

        return valid_components, fixes

    # ========================================================================
    # Stage 3: Connection Validation
    # ========================================================================

    def _validate_connections(
        self,
        connections: list[dict],
        components: list[dict],
    ) -> tuple[list[dict], list[str]]:
        """Validate and fix connections."""
        fixes = []
        valid_connections = []
        comp_refs = {c['ref'] for c in components}

        for conn in connections:
            from_str = conn.get('from', '')
            to_str = conn.get('to', '')

            if not from_str or not to_str:
                continue

            # Parse ref:pin
            from_ref, from_pin = self._parse_pin_ref(from_str)
            to_ref, to_pin = self._parse_pin_ref(to_str)

            # Check refs exist
            if from_ref not in comp_refs:
                fixes.append(f"Removed connection: {from_ref} not found")
                continue
            if to_ref not in comp_refs:
                fixes.append(f"Removed connection: {to_ref} not found")
                continue

            # Validate pin references
            from_comp = next((c for c in components if c['ref'] == from_ref), None)
            to_comp = next((c for c in components if c['ref'] == to_ref), None)

            if from_comp:
                from_pin = self._fix_pin_ref(from_comp['lib_id'], from_pin)
            if to_comp:
                to_pin = self._fix_pin_ref(to_comp['lib_id'], to_pin)

            valid_connections.append({
                'from': f"{from_ref}:{from_pin}",
                'to': f"{to_ref}:{to_pin}",
            })

        return valid_connections, fixes

    def _parse_pin_ref(self, pin_str: str) -> tuple[str, str]:
        """Parse 'REF:PIN' into (ref, pin)."""
        if ':' in pin_str:
            parts = pin_str.split(':', 1)
            return parts[0], parts[1]
        return pin_str, '1'

    def _fix_pin_ref(self, lib_id: str, pin: str) -> str:
        """Fix common pin reference errors."""
        # Common aliases
        aliases = {
            'pin1': '1', 'pin2': '2', 'pin3': '3',
            'gpio0': 'IO0', 'gpio1': 'IO1', 'gpio2': 'IO2',
            'gpio4': 'IO4', 'gpio5': 'IO5',
            'gnd': 'GND', 'vcc': 'VCC', 'vdd': 'VDD',
            '5v': '5V', '3v3': '3V3', '3.3v': '3V3',
            'a': 'A', 'k': 'K',
        }

        pin_lower = pin.lower()
        if pin_lower in aliases:
            return aliases[pin_lower]

        return pin

    # ========================================================================
    # Stage 4: Auto-Fix
    # ========================================================================

    def _auto_fix(
        self,
        components: list[dict],
        connections: list[dict],
    ) -> tuple[list[dict], list[dict], list[str]]:
        """Apply structural auto-fixes."""
        fixes = []
        comp_refs = {c['ref'] for c in components}

        # Check for MCU without GND
        mcu_ref = None
        has_gnd = False
        for comp in components:
            cat = get_component_category(comp.get('lib_id', ''))
            if cat in (CATEGORY_MCU, CATEGORY_MODULE):
                mcu_ref = comp['ref']

        for conn in connections:
            if 'GND' in conn['from'] or 'GND' in conn['to']:
                has_gnd = True
                break

        if mcu_ref and not has_gnd:
            # Add GND power symbol and connection
            gnd_ref = '#PWR_GND'
            if gnd_ref not in comp_refs:
                components.append({
                    'ref': gnd_ref,
                    'lib_id': 'power:GND',
                    'value': 'GND',
                })
                connections.append({
                    'from': f"{mcu_ref}:GND",
                    'to': f"{gnd_ref}:1",
                })
                fixes.append(f"Added GND connection for {mcu_ref}")

        # Check LEDs without resistors
        led_refs = [c['ref'] for c in components if 'LED' in c.get('lib_id', '').upper()]
        resistor_refs = [c['ref'] for c in components
                        if c.get('lib_id', '') in ('Device:R', 'Device:R_Small')]

        for led_ref in led_refs:
            # Check if LED connects directly to MCU without resistor in path
            led_has_resistor = False
            for conn in connections:
                from_ref = conn['from'].split(':')[0]
                to_ref = conn['to'].split(':')[0]
                if (from_ref == led_ref and to_ref in resistor_refs) or \
                   (to_ref == led_ref and from_ref in resistor_refs):
                    led_has_resistor = True
                    break

            if not led_has_resistor and resistor_refs:
                # Don't add extra resistor if there are already resistors in circuit
                pass
            elif not led_has_resistor and not resistor_refs and mcu_ref:
                # Add a 330 ohm resistor
                r_counter = 1
                while f"R{r_counter}" in comp_refs:
                    r_counter += 1
                new_r_ref = f"R{r_counter}"

                components.append({
                    'ref': new_r_ref,
                    'lib_id': 'Device:R',
                    'value': '330',
                })
                comp_refs.add(new_r_ref)

                # Re-route: find MCU->LED connection, insert resistor
                for i, conn in enumerate(connections):
                    from_ref = conn['from'].split(':')[0]
                    to_ref = conn['to'].split(':')[0]
                    if from_ref == mcu_ref and to_ref == led_ref:
                        original_from = conn['from']
                        connections[i] = {'from': original_from, 'to': f"{new_r_ref}:1"}
                        connections.append({'from': f"{new_r_ref}:2", 'to': f"{led_ref}:2"})
                        fixes.append(f"Added 330 ohm resistor {new_r_ref} for LED {led_ref}")
                        break
                    elif from_ref == led_ref and to_ref == mcu_ref:
                        original_to = conn['to']
                        connections[i] = {'from': f"{new_r_ref}:1", 'to': original_to}
                        connections.append({'from': f"{led_ref}:1", 'to': f"{new_r_ref}:2"})
                        fixes.append(f"Added 330 ohm resistor {new_r_ref} for LED {led_ref}")
                        break

        # Remove truncated/incomplete components
        components = [c for c in components if c.get('ref') and c.get('lib_id')]

        return components, connections, fixes

    # ========================================================================
    # Stage 5: Generate .kicad_sch
    # ========================================================================

    def _generate_kicad_sch(
        self,
        components: list[dict],
        connections: list[dict],
    ) -> str:
        """Generate a valid KiCad 9.0 .kicad_sch file."""
        import uuid as uuid_mod

        file_uuid = str(uuid_mod.uuid4())

        # Header
        lines = [
            '(kicad_sch',
            '  (version 20250114)',
            '  (generator "eeschema")',
            '  (generator_version "9.0")',
            f'  (uuid "{file_uuid}")',
            '  (paper "A4")',
            '',
        ]

        # Lib symbols section
        lines.append('  (lib_symbols')
        lib_ids_used = set()
        for comp in components:
            lib_id = comp.get('lib_id', '')
            if lib_id in lib_ids_used or lib_id.startswith('power:'):
                continue
            lib_ids_used.add(lib_id)
            symbol_block = self._generate_lib_symbol(lib_id, comp.get('value', ''))
            if symbol_block:
                lines.append(symbol_block)
        lines.append('  )')
        lines.append('')

        # Place components
        x_start, y_start = 100.0, 60.0
        x_spacing, y_spacing = 30.0, 25.0
        col_max = 4

        for i, comp in enumerate(components):
            if comp.get('lib_id', '').startswith('power:'):
                continue

            col = i % col_max
            row = i // col_max
            x = x_start + col * x_spacing
            y = y_start + row * y_spacing

            comp_uuid = str(uuid_mod.uuid4())
            ref = comp.get('ref', f'U{i+1}')
            lib_id = comp.get('lib_id', '')
            value = comp.get('value', lib_id.split(':')[-1] if ':' in lib_id else '')

            lines.append(f'  (symbol')
            lines.append(f'    (lib_id "{lib_id}")')
            lines.append(f'    (at {x:.2f} {y:.2f} 0)')
            lines.append(f'    (unit 1)')
            lines.append(f'    (exclude_from_sim no)')
            lines.append(f'    (in_bom yes)')
            lines.append(f'    (on_board yes)')
            lines.append(f'    (dnp no)')
            lines.append(f'    (uuid "{comp_uuid}")')
            lines.append(f'    (property "Reference" "{ref}" (at {x:.2f} {y - 2:.2f} 0)')
            lines.append(f'      (effects (font (size 1.27 1.27)))')
            lines.append(f'    )')
            lines.append(f'    (property "Value" "{value}" (at {x:.2f} {y + 2:.2f} 0)')
            lines.append(f'      (effects (font (size 1.27 1.27)))')
            lines.append(f'    )')
            lines.append(f'  )')
            lines.append('')

        # Wires for connections (simplified layout)
        for conn in connections:
            from_ref = conn['from'].split(':')[0]
            to_ref = conn['to'].split(':')[0]

            # Find positions
            from_idx = next((i for i, c in enumerate(components) if c['ref'] == from_ref), None)
            to_idx = next((i for i, c in enumerate(components) if c['ref'] == to_ref), None)

            if from_idx is not None and to_idx is not None:
                from_col = from_idx % col_max
                from_row = from_idx // col_max
                to_col = to_idx % col_max
                to_row = to_idx // col_max

                x1 = x_start + from_col * x_spacing + 5
                y1 = y_start + from_row * y_spacing
                x2 = x_start + to_col * x_spacing - 5
                y2 = y_start + to_row * y_spacing

                wire_uuid = str(uuid_mod.uuid4())
                lines.append(f'  (wire (pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f}))')
                lines.append(f'    (stroke (width 0) (type default))')
                lines.append(f'    (uuid "{wire_uuid}")')
                lines.append(f'  )')

        # Sheet instances
        lines.append('')
        lines.append('  (sheet_instances')
        lines.append('    (path "/"')
        lines.append('      (page "1")')
        lines.append('    )')
        lines.append('  )')

        lines.append(')')

        return '\n'.join(lines)

    def _generate_lib_symbol(self, lib_id: str, value: str = '') -> str:
        """Generate a lib_symbol block for a component."""
        from .component_database import get_component_info

        info = get_component_info(lib_id)
        name = lib_id
        ref_prefix = 'U'

        # Determine reference prefix
        if lib_id.startswith('Device:R'):
            ref_prefix = 'R'
        elif lib_id.startswith('Device:C'):
            ref_prefix = 'C'
        elif lib_id.startswith('Device:L'):
            ref_prefix = 'L'
        elif 'LED' in lib_id:
            ref_prefix = 'D'
        elif lib_id.startswith('Device:D'):
            ref_prefix = 'D'
        elif lib_id.startswith('Device:Q'):
            ref_prefix = 'Q'
        elif lib_id.startswith('Connector'):
            ref_prefix = 'J'
        elif lib_id.startswith('Switch'):
            ref_prefix = 'SW'

        lines = []
        lines.append(f'    (symbol "{name}"')
        lines.append(f'      (pin_names (offset 1.016))')
        lines.append(f'      (exclude_from_sim no)')
        lines.append(f'      (in_bom yes)')
        lines.append(f'      (on_board yes)')
        lines.append(f'      (property "Reference" "{ref_prefix}" (at 0 0 0)')
        lines.append(f'        (effects (font (size 1.27 1.27)))')
        lines.append(f'      )')
        lines.append(f'      (property "Value" "{value or name.split(":")[-1]}" (at 0 0 0)')
        lines.append(f'        (effects (font (size 1.27 1.27)))')
        lines.append(f'      )')

        # Generate pins
        if info and info.get('pins'):
            pin_y = 0
            sub_name = name.replace(':', '_') + '_1_1'
            lines.append(f'      (symbol "{sub_name}"')

            for pin in info['pins']:
                pin_num = pin['number']
                pin_name = pin.get('name', pin_num)
                pin_type = pin.get('type', 'passive')

                kicad_type = 'passive'
                if pin_type == 'input':
                    kicad_type = 'input'
                elif pin_type == 'output':
                    kicad_type = 'output'
                elif pin_type == 'bidirectional':
                    kicad_type = 'bidirectional'
                elif pin_type in ('power_in', 'power_out'):
                    kicad_type = 'power_in'

                lines.append(f'        (pin {kicad_type} line (at -5.08 {pin_y:.2f} 0) (length 2.54)')
                lines.append(f'          (name "{pin_name}" (effects (font (size 1.27 1.27))))')
                lines.append(f'          (number "{pin_num}" (effects (font (size 1.27 1.27))))')
                lines.append(f'        )')
                pin_y -= 2.54

            lines.append(f'      )')
        else:
            # Minimal 2-pin symbol
            sub_name = name.replace(':', '_') + '_1_1'
            lines.append(f'      (symbol "{sub_name}"')
            lines.append(f'        (pin passive line (at -5.08 0 0) (length 2.54)')
            lines.append(f'          (name "1" (effects (font (size 1.27 1.27))))')
            lines.append(f'          (number "1" (effects (font (size 1.27 1.27))))')
            lines.append(f'        )')
            lines.append(f'        (pin passive line (at 5.08 0 180) (length 2.54)')
            lines.append(f'          (name "2" (effects (font (size 1.27 1.27))))')
            lines.append(f'          (number "2" (effects (font (size 1.27 1.27))))')
            lines.append(f'        )')
            lines.append(f'      )')

        lines.append(f'    )')
        return '\n'.join(lines)

    # ========================================================================
    # Stage 6: Final Validation
    # ========================================================================

    def _final_validation(self, content: str) -> list[str]:
        """Run final validation checks on generated schematic."""
        warnings = []

        # Basic structure check
        if '(kicad_sch' not in content:
            warnings.append("Missing kicad_sch header")
        if '(version 20250114)' not in content:
            warnings.append("Missing KiCad 9.0 version")
        if '(lib_symbols' not in content:
            warnings.append("Missing lib_symbols section")

        # Check parenthesis balance
        open_count = content.count('(')
        close_count = content.count(')')
        if open_count != close_count:
            warnings.append(f"Parenthesis imbalance: {open_count} open, {close_count} close")

        return warnings
