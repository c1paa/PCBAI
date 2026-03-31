# Arduino Symbol Fix - COMPLETE

## Problem
Arduino symbols showed as **question marks** in KiCad because we were using `MCU_Microchip_ATmega:ATmega328P-AU` which **doesn't exist** in KiCad libraries.

## Root Cause Analysis

### KiCad Library Structure
KiCad stores symbols in `.kicad_sym` files located at:
```
/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/
```

### Available MCU Libraries
```
MCU_Module.kicad_sym          ← Arduino boards here
MCU_Microchip_ATmega.kicad_sym ← Only ATmega chips (no AU suffix)
```

### What Exists
```bash
$ grep "(symbol \"Arduino" MCU_Module.kicad_sym
(symbol "Arduino_UNO_R2"
(symbol "Arduino_UNO_R3"      ← THIS EXISTS!
(symbol "Arduino_Leonardo"
(symbol "Arduino_Nano_v3.x"
...
```

### What Doesn't Exist
```bash
$ grep "ATmega328P-AU" MCU_Microchip_ATmega.kicad_sym
(No results - doesn't exist!)
```

## Solution

### 1. Use Arduino_UNO_R3 Instead
Changed from:
```python
"lib_id": "MCU_Microchip_ATmega:ATmega328P-AU"  # ❌ Doesn't exist
```

To:
```python
"lib_id": "MCU_Module:Arduino_UNO_R3"  # ✅ Exists!
```

### 2. Updated Component Database
Removed `atmega328p` entry (doesn't exist) and kept only `arduino` entry.

### 3. Updated LLM Prompt
Added `'arduino'` to valid component types in `ENHANCED_ANALYSIS_PROMPT`.

### 4. Updated Type Detection
Changed fallback from `type='mcu'` to `type='arduino'`.

## Files Modified

| File | Changes |
|------|---------|
| `ai_analyzer.py` | Added 'arduino' type to prompt, changed fallback type |
| `schematic.py` | Removed atmega328p, updated _get_lib_id_for_component |

## Test Results

### Before Fix
```
Lib IDs: MCU_Microchip_ATmega:ATmega328P-AU
KiCad: Question mark symbol ❌
```

### After Fix
```
Lib IDs: MCU_Module:Arduino_UNO_R3
KiCad: Arduino UNO R3 symbol ✓
kicad-cli: PASS ✓
```

## How To Verify

```bash
cd /Users/vladglazunov/Documents/algo/PCBAI
source venv/bin/activate

# Generate schematic
pcba schematic "Arduino with two LED on pin 5" -o test.kicad_sch

# Check lib_ids
grep "lib_id" test.kicad_sch
# Should show: MCU_Module:Arduino_UNO_R3

# Validate
kicad-cli sch export netlist test.kicad_sch -o /dev/null
# Should pass with no errors

# Open in KiCad
open test.kicad_sch
# Arduino symbol should display correctly (no "?")
```

## Lesson Learned

**Always verify symbols exist in KiCad libraries before using them!**

To check if a symbol exists:
```bash
# Search in library files
grep "(symbol \"SYMBOL_NAME\"" /Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/*.kicad_sym

# Or use Python
python -c "from pcba.kicad_library import KiCadLibraryReader; \
  print(KiCadLibraryReader().load_symbol('Library:Symbol') is not None)"
```

## Status
✅ **FIXED** - Arduino UNO R3 now loads correctly from official KiCad libraries!
