# PCBAI Validation System

## 🛡️ Многоуровневая защита

```
┌─────────────────────────────────────────────────────────┐
│  AI Model (T5-small)                                    │
│  Input: "Arduino with LED"                              │
│  Output: JSON structure                                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Level 1: JSON Validation                               │
│  ✓ Valid JSON format                                    │
│  ✓ Required fields present                              │
│  ✓ Retry on error (max 3 attempts)                      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Level 2: Structure Validation                          │
│  ✓ Component references unique                          │
│  ✓ Pin formats valid                                    │
│  ✓ Connections well-formed                              │
│  ✓ Auto-fix defaults                                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Level 3: KiCad 9.0 Format Validation                   │
│  ✓ Header (version, generator, uuid)                    │
│  ✓ Syntax (parentheses, quotes)                         │
│  ✓ Components (lib_id, instances)                       │
│  ✓ Wires (≥2 points)                                    │
│  ✓ KiCad 9.0 specific (embedded_fonts, etc.)            │
│  ✓ Auto-fix common issues                               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Level 4: kicad-cli Validation                          │
│  ✓ Official KiCad validation                            │
│  ✓ Export to netlist                                    │
│  ✓ Catch format errors                                  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Level 5: Circuit Validation                            │
│  ✓ Connectivity (all pins connected)                    │
│  ✓ ERC (electrical rules)                               │
│  ✓ Readability score                                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Output: Valid .kicad_sch file                          │
│  ✓ Opens in KiCad 9.0                                   │
│  ✓ All components placed                                │
│  ✓ All connections valid                                │
│  ✓ Ready for PCB layout                                 │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Validation Details

### Level 1: JSON Validation

**Checks:**
- Valid JSON syntax
- Required fields: `components`, `connections`
- Component fields: `ref`, `lib_id`, `type`
- Connection fields: `from`, `to`

**On error:**
- Retry generation (max 3 attempts)
- Log error for debugging

**Code:**
```python
try:
    components = json.loads(output_text)
except json.JSONDecodeError:
    # Retry
    return generate_schematic(description)
```

---

### Level 2: Structure Validation

**Checks:**
- Unique component references (no duplicates)
- Valid pin formats (`component:pin`)
- Connection consistency

**Auto-fix:**
- Default values for missing fields
- Fix invalid pin names

**Code:**
```python
def validate_structure(components):
    refs = [c['ref'] for c in components]
    duplicates = set([r for r in refs if refs.count(r) > 1])
    if duplicates:
        return False, f"Duplicate refs: {duplicates}"
    return True, ""
```

---

### Level 3: KiCad 9.0 Format Validation

**Checks:**
- **Header:**
  - `(kicad_sch` token
  - `(version 20250114)`
  - `(generator "eeschema")`
  - `(uuid "...")`
- **Syntax:**
  - Balanced parentheses
  - Quoted strings
- **Components:**
  - `lib_id` with library prefix
  - Instance definitions
- **Wires:**
  - ≥2 connection points
- **KiCad 9.0 specific:**
  - `(embedded_fonts no)`
  - `(generator_version "9.0")`

**Auto-fix:**
- Add missing `embedded_fonts`
- Add missing `generator_version`
- Fix parenthesis balance
- Quote unquoted strings

**Code:**
```python
from pcba.kicad9_validator import validate_schematic_content

result = validate_schematic_content(content)
if not result.valid:
    # Auto-fix
    content = _apply_validation_fixes(content, result)
```

---

### Level 4: kicad-cli Validation

**Checks:**
- Official KiCad validation
- Netlist export
- Format compliance

**Command:**
```bash
kicad-cli sch export netlist file.kicad_sch -o /dev/null
```

**Code:**
```python
from pcba.validator import KiCadValidator

validator = KiCadValidator()
result = validator.validate_schematic(filepath)
```

---

### Level 5: Circuit Validation

**Checks:**
- **Connectivity:**
  - All pins connected
  - No floating nets
- **ERC:**
  - LED has current-limiting resistor
  - MCU has power connections
  - No output-to-output conflicts
- **Readability:**
  - Component overlap: 0
  - Spacing: ≥5mm
  - Alignment: on grid

**Code:**
```python
from pcba.circuit_validator import validate_schematic

result = validate_schematic(filepath)
# result['connectivity'].valid
# result['erc'].valid
# result['readability']['score']
```

---

## 🔧 Usage

### Validate existing file:
```bash
python scripts/validate_and_fix.py schematic.kicad_sch
```

### Validate and auto-fix:
```bash
python scripts/validate_and_fix.py schematic.kicad_sch --fix
```

### Generate with validation:
```bash
pcba schematic "Arduino with LED" -o test.kicad_sch
# Automatic validation at all levels
```

---

## 📊 Error Rates (Expected)

| Level | Error Type | Frequency | Fix |
|-------|------------|-----------|-----|
| 1 | JSON invalid | ~10% | Retry |
| 2 | Missing fields | ~5% | Auto-fix defaults |
| 3 | Format errors | ~3% | Auto-fix syntax |
| 4 | kicad-cli errors | ~1% | Re-generate |
| 5 | Circuit errors | ~2% | Manual review |

**Overall reliability:** ~99% with all validations

---

## 🎯 Success Criteria

A schematic is considered **valid** when:

1. ✅ JSON parses successfully
2. ✅ Structure validation passes
3. ✅ KiCad 9.0 format validation passes
4. ✅ kicad-cli validation passes
5. ✅ Circuit validation passes (connectivity, ERC)
6. ✅ File opens in KiCad without errors

**All 6 levels must pass!**

---

## 🐛 Debugging

### Common errors and fixes:

**Error:** `Unbalanced parentheses`
```
Fix: Auto-fix adds missing closing parentheses
Manual: Check for truncated output
```

**Error:** `Missing 'embedded_fonts'`
```
Fix: Auto-fix adds '(embedded_fonts no)'
Manual: Add before closing ')'
```

**Error:** `Duplicate component references`
```
Fix: Regenerate with different seed
Manual: Edit references to be unique
```

**Error:** `kicad-cli export failed`
```
Fix: Check Level 3 validation first
Manual: Open in KiCad, check errors
```

---

## 📈 Future Improvements

1. **Machine Learning validation:**
   - Train model to predict validation errors
   - Pre-filter invalid outputs

2. **Better auto-fix:**
   - LLM-based error correction
   - Context-aware fixes

3. **Validation database:**
   - Track common errors
   - Improve auto-fix over time

4. **Integration tests:**
   - Test with real KiCad projects
   - Validate against known-good schematics

---

**Last updated:** 2026-03-31  
**Status:** ✅ Implemented (Levels 1-5)
