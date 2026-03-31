# Handoff: PCBAI Phase 1 — Current Progress

## What's Been Done

### Task #11 COMPLETED: `src/pcba/kicad_library.py`
- Created `KiCadLibraryReader` class that reads official KiCad `.kicad_sym` files
- `load_symbol(lib_id)` — extracts full symbol S-expression using parenthesis-depth counting
- `extract_pin_info(lib_id)` — extracts pin positions (number, name, x, y, rotation)
- Tested and working: Device:R, Device:LED, MCU_Module:Arduino_UNO_R3, power:+5V, power:GND all load correctly
- Symbol path: `/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/`

### Task #12 IN PROGRESS: Fix lib_symbols and lib_id mappings in `schematic.py`

**Already done in schematic.py:**
1. Added `from .kicad_library import KiCadLibraryReader` import (line ~10)
2. Added `"arduino"` entry to `KICAD_COMPONENTS` dict with `"lib_id": "MCU_Module:Arduino_UNO_R3"`
3. Changed `atmega328p` lib_id from `MCU_Microchip_ATmega:ATMEGA328P-A` to `MCU_Microchip_ATmega:ATmega328P-AU`

**Still needs to be done in Task #12:**

4. **Fix `_get_lib_id_for_component()` (line ~1435)**:
   - Change line `if 'atmega' in name_lower or 'arduino' in name_lower:` to check for arduino FIRST:
   ```python
   if 'arduino' in name_lower:
       return kicad_db.get('arduino', {}).get('lib_id', 'MCU_Module:Arduino_UNO_R3')
   elif 'atmega' in name_lower:
       return kicad_db.get('atmega328p', {}).get('lib_id', 'MCU_Microchip_ATmega:ATmega328P-AU')
   ```

5. **Replace `_generate_lib_symbols()` method (line ~485)** to use KiCadLibraryReader:
   ```python
   def _generate_lib_symbols(self, components: list[dict]) -> list[str]:
       """Generate library symbols section using official KiCad libraries."""
       reader = KiCadLibraryReader()
       symbols = []
       used_lib_ids = set()

       for comp in components:
           comp_type = comp.get('type', comp.get('category', 'sensor'))
           name = comp.get('name', '')
           value = comp.get('value', '')
           lib_id = self._get_lib_id_for_component(comp_type, name, value)

           if lib_id in used_lib_ids:
               continue
           used_lib_ids.add(lib_id)

           # Try official library first
           symbol_text = reader.load_symbol(lib_id)
           if symbol_text:
               symbols.append(symbol_text)
           else:
               # Fallback to hardcoded templates
               symbol_templates = {
                   'resistor': self._symbol_resistor(),
                   'led': self._symbol_led(),
                   'capacitor': self._symbol_capacitor(),
                   'mcu': self._symbol_generic_ic(),
                   'sensor': self._symbol_generic_sensor(),
               }
               # determine template key
               if 'resistor' in comp_type or 'R' == lib_id.split(':')[-1]:
                   key = 'resistor'
               elif 'led' in comp_type:
                   key = 'led'
               elif 'capacitor' in comp_type:
                   key = 'capacitor'
               elif 'mcu' in comp_type or 'arduino' in name.lower() or 'atmega' in name.lower():
                   key = 'mcu'
               else:
                   key = 'sensor'
               template = symbol_templates.get(key)
               if template:
                   symbols.append(template)

       # Always add power symbols from library
       for power_id in ['power:+5V', 'power:GND']:
           if power_id not in used_lib_ids:
               sym = reader.load_symbol(power_id)
               if sym:
                   symbols.append(sym)
               else:
                   # fallback
                   if '+5V' in power_id:
                       symbols.append(self._symbol_power_5v())
                   else:
                       symbols.append(self._symbol_gnd())
               used_lib_ids.add(power_id)

       return symbols
   ```

---

## Task #13 PENDING: Implement Wire Generation

This is the CRITICAL missing piece. `ConnectionGenerator` creates connection data like:
```python
[{"from": "R1:2", "to": "D1:2", "net": "Net_R1_D1"}, ...]
```
But `SchematicGenerator.generate()` never writes `(wire ...)` statements.

### What needs to be implemented:

1. **`_calculate_positions(components)`** — layout components left-to-right with spacing instead of hardcoded positions in `_generate_component_instance`. Return `dict[ref, (x, y, rotation)]`.

2. **`_generate_wires(connections, positions, pin_db)`** — generate KiCad wire statements. Format:
   ```
   (wire
     (pts (xy 134.62 92.71) (xy 138.43 92.71))
     (stroke (width 0) (type default))
     (uuid "...")
   )
   ```

3. **Pin absolute position calculation**: For each component at `(cx, cy, comp_rot)` with a pin at relative `(px, py, pin_rot)`:
   - Apply rotation transform: if comp_rot=90, swap and negate appropriately
   - `abs_x = cx + px*cos(comp_rot_rad) - py*sin(comp_rot_rad)`
   - `abs_y = cy + px*sin(comp_rot_rad) + py*cos(comp_rot_rad)`

4. **Wire routing**: For non-aligned pins, use L-shaped routing (horizontal then vertical).

5. **Update `generate()` method** to:
   - Call `_calculate_positions()`
   - Store positions, use them in `_generate_component_instance()`
   - After components, generate wires from `circuit_data['connections']`
   - Place power symbols at wire endpoints

### Key pin info (from KiCadLibraryReader tests):
- **Device:R**: pin 1 at (0, 3.81, 270°), pin 2 at (0, -3.81, 90°)
- **Device:LED**: pin 1 (K) at (-3.81, 0, 0°), pin 2 (A) at (3.81, 0, 180°)
- **Arduino**: 32 pins, pin 20 is D5 at (-12.7, 5.08, 0°)

### Connection format from ConnectionGenerator:
- Series: `+5V → R1:1`, `R1:2 → D1:2(A)`, `D1:1(K) → D2:2(A)`, `D2:1(K) → GND`
- Parallel: `+5V → R1:1`, `R1:2 → D1:2(A)`, `R1:2 → D2:2(A)`, `D1:1(K) → GND`, `D2:1(K) → GND`

---

## Task #14 PENDING: Create validator.py and circuit_graph.py

### `src/pcba/validator.py`:
- `ValidationResult` dataclass: `valid`, `errors`, `warnings`
- `validate_schematic(path) -> ValidationResult`
- Uses `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli sch export netlist`

### `src/pcba/circuit_graph.py`:
- `ComponentNode`, `PinInfo`, `ConnectionEdge` dataclasses
- `CircuitGraph` class with `validate()` method
- Centralizes positioning and pin-coordinate logic

---

## Task #15 PENDING: Tests and end-to-end verification

1. `python -m pytest tests/ -v` — all tests pass
2. `pcba schematic "two LED with 330 ohm resistor to Arduino pin 5" -o test.kicad_sch`
3. `grep "(wire" test.kicad_sch` — wires exist
4. `grep "lib_id" test.kicad_sch` — correct lib_ids
5. `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli sch export netlist test.kicad_sch -o /dev/null`
6. Open in KiCad — no "?" symbols

---

## File Locations

| File | Status |
|------|--------|
| `src/pcba/kicad_library.py` | CREATED, WORKING |
| `src/pcba/schematic.py` | PARTIALLY MODIFIED (import added, KICAD_COMPONENTS updated, need _generate_lib_symbols and _get_lib_id_for_component fixes) |
| `src/pcba/ai_analyzer.py` | DONE (previous session) |
| `src/pcba/circuit_generator.py` | DONE (previous session) |
| `src/pcba/dialog_enhanced.py` | DONE (previous session) |
| `src/pcba/validator.py` | NOT CREATED YET |
| `src/pcba/circuit_graph.py` | NOT CREATED YET |

## Plan File
Full plan: `/Users/vladglazunov/.claude/plans/wondrous-inventing-coral.md`

## Reference Schematic
Working example: `examples/test1/test1.kicad_sch` — has correct KiCad 9.0 format with wires, R1, LED, +5V, GND.

## KiCad Paths
- Symbol libraries: `/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/`
- kicad-cli: `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`

## How to Run Tests
```bash
cd /Users/vladglazunov/Documents/algo/PCBAI
python -m pytest tests/ -v
# or specific:
python -m pytest tests/test_ai_analyzer.py tests/test_circuit_generator.py tests/test_dialog_enhanced.py -v
```

## Important Notes
- KiCad 9.0 format version is `20250114`
- In `.kicad_sym` files, symbols named WITHOUT library prefix (`"R"` not `"Device:R"`)
- In schematic files, referenced WITH prefix (`"Device:R"`)
- `KiCadLibraryReader.load_symbol()` already handles this prefix transformation
- Wire UUIDs must be unique — use `uuid.uuid4()`
- Component positions should be on 1.27mm grid for KiCad alignment
