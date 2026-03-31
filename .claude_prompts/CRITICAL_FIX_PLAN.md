# PCBAI: CRITICAL FIX - Complete System Overhaul

## ⚠️ CRITICAL PROBLEMS (MUST FIX IMMEDIATELY)

### Problem 0: Incorrect Symbol Generation (MOST CRITICAL)
**Current behavior:** Symbols are generated as text templates in Python code, not loaded from official KiCad libraries.

**Expected:** Symbols MUST be loaded from `.kicad_sym` library files using proper KiCad format.

**Why this matters:**
- Hand-written symbols may have incorrect pin names/positions
- Missing required properties (footprint filters, keywords)
- Not compatible with KiCad's symbol linking system
- Cannot use official KiCad footprints

**Solution:** Use `KiCadLibraryReader` to load symbols from:
```
/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/
  - Device.kicad_sym (R, C, LED, etc.)
  - MCU_Module.kicad_sym (Arduino boards)
  - power.kicad_sym (GND, VCC, etc.)
```

**Reference:**
- KiCad Symbol Format: https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/
- Symbol Libraries: https://gitlab.com/kicad/libraries/kicad-symbols
- `.kicad_sym` file format uses S-expressions with specific structure

---

### Problem 1: Duplicate MCU Components
**Current behavior:** Query "Arduino with two LED" creates BOTH ATmega328P chip AND Arduino UNO board, overlaid on top of each other with all pins connected together.

**Expected:** ONLY Arduino UNO R3 board (which already contains ATmega328P internally).

### Problem 2: Wires Don't Connect to Pins
**Current behavior:** Wires are drawn from component center points, not from actual pins. LEDs show floating wires not connected to anode/cathode pins.

**Expected:** Wires must connect to specific pin coordinates (e.g., LED pin 2/A, Arduino pin D5).

### Problem 3: Missing Ground Connection
**Current behavior:** No GND symbol, no ground connections in circuit.

**Expected:** Complete circuit with GND symbol and proper ground connections.

### Problem 4: No Circuit Validation
**Current behavior:** No check if circuit is electrically correct, readable, or functional.

**Expected:** Multiple validation layers:
1. Symbol existence (✅ Already implemented)
2. Pin connectivity validation
3. ERC (Electrical Rule Check)
4. Circuit readability score
5. Functional correctness check

---

## 🎯 PROJECT GOAL

Build an AI-powered PCB design assistant that:
1. **Understands natural language** → "Arduino with two LED on pin 5"
2. **Generates correct schematics** → Proper symbols, connections, ground
3. **Validates electrical correctness** → ERC, connectivity, readability
4. **Iterates with user** → "Add button on pin 3", "Move components closer"
5. **Exports to PCB routing** → FreeRouting integration

---

## 📋 IMPLEMENTATION PLAN (PRIORITY ORDER)

### PHASE 1: Fix Critical Bugs (DO THIS NOW - HIGH PRIORITY)

#### Task 1.0: Use Official KiCad Symbol Libraries (MOST CRITICAL)
**File:** `src/pcba/schematic_generator.py` or wherever symbols are generated

**Problem:** Symbols are hand-written as Python strings, not loaded from `.kicad_sym` files.

**Current (WRONG):**
```python
def _symbol_resistor(self) -> str:
    return '''(symbol "Device:R"
  (pin_numbers (hide yes))
  ...
)'''  # Hand-written template
```

**Expected (CORRECT):**
```python
from .kicad_library import KiCadLibraryReader

reader = KiCadLibraryReader()
symbol_text = reader.load_symbol('Device:R')
# Returns ACTUAL symbol from Device.kicad_sym file
```

**Implementation:**
1. Check if `KiCadLibraryReader` exists (already created in runtime_verifier.py)
2. Use it to load ALL symbols from libraries:
   ```python
   # In schematic generator
   def generate_lib_symbols(self, components: list) -> list[str]:
       reader = KiCadLibraryReader()
       symbols = []
       
       for comp in components:
           lib_id = comp.get('lib_id')
           symbol = reader.load_symbol(lib_id)
           if symbol:
               symbols.append(symbol)
           else:
               print(f"⚠️ Symbol {lib_id} not found in libraries")
       
       return symbols
   ```

**Validation:**
```bash
# Check symbol comes from library
pcba schematic "Resistor" -o test.kicad_sch
grep -A 50 "lib_symbols" test.kicad_sch
# Should show full symbol definition from Device.kicad_sym
# NOT a Python template
```

**References:**
- https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/#_symbol_section
- https://gitlab.com/kicad/libraries/kicad-symbols/-/blob/master/Device.kicad_sym

---

#### Task 1.1: Prevent Duplicate MCU
**File:** `src/pcba/ai_analyzer.py`

**Problem:** Both `arduino` and `mcu` types created separately.

**Fix:**
```python
# In _fallback_analyze() or _llm_analyze():
if 'arduino' in desc:
    # ONLY create Arduino board, NOT separate ATmega
    components.append({
        'type': 'arduino',
        'lib_id': 'MCU_Module:Arduino_UNO_R3',
        ...
    })
    # DO NOT create separate 'mcu' component!
```

**Validation:**
```bash
pcba schematic "Arduino with LED" -o test.kicad_sch
grep "lib_id" test.kicad_sch
# Should show: MCU_Module:Arduino_UNO_R3 (ONLY ONCE)
# Should NOT show: ATmega328P
```

---

#### Task 1.2: Fix Wire-to-Pin Connections
**File:** `src/pcba/schematic_generator.py` (or wherever wires are generated)

**Problem:** Wires use component center coordinates instead of pin coordinates.

**Current (WRONG):**
```python
# Wire from component center to component center
wire = Wire(x1=comp1.x, y1=comp1.y, x2=comp2.x, y2=comp2.y)
```

**Expected (CORRECT):**
```python
# Wire from specific pin to specific pin
pin1_pos = get_pin_position(comp1, pin_name='D5')
pin2_pos = get_pin_position(comp2, pin_name='1')
wire = Wire(x1=pin1_pos.x, y1=pin1_pos.y, x2=pin2_pos.x, y2=pin2_pos.y)
```

**Implementation:**
1. Load pin positions from KiCad library symbols
2. Store pin coordinates in ComponentNode
3. Generate wires between pin positions, not component centers

**Validation:**
```bash
pcba schematic "Arduino with LED on pin 5" -o test.kicad_sch
open test.kicad_sch
# Visually check: Wire connects to LED anode pin, not LED center
```

---

#### Task 1.3: Add Ground Symbol
**File:** `src/pcba/ai_analyzer.py`

**Problem:** No GND in generated circuits.

**Fix:**
```python
# In analyze(), always add GND if power components exist:
if any(c['type'] in ['led', 'mcu', 'arduino'] for c in components):
    components.append({
        'type': 'power',
        'subtype': 'ground',
        'lib_id': 'power:GND',
        'ref': 'GND1',
    })
```

**Validation:**
```bash
pcba schematic "Arduino with LED" -o test.kicad_sch
grep "power:GND" test.kicad_sch
# Should find GND symbol
```

---

### PHASE 2: Circuit Validation System (MEDIUM PRIORITY)

#### Task 2.1: Connectivity Validator
**File:** `src/pcba/circuit_validator.py` (NEW)

**Purpose:** Check if all components are properly connected.

**Checks:**
1. Every component pin is either:
   - Connected to a wire/net
   - Marked as "no connect" (NC)
2. No floating nets (nets with only one connection)
3. Power pins (VCC, GND) are connected

**Implementation:**
```python
class ConnectivityValidator:
    def validate(self, schematic_path: Path) -> ValidationResult:
        errors = []
        
        # Parse schematic
        components = parse_components(schematic_path)
        wires = parse_wires(schematic_path)
        
        # Build connectivity graph
        graph = build_connectivity_graph(components, wires)
        
        # Check each component
        for comp in components:
            for pin in comp.pins:
                if not graph.is_connected(comp.ref, pin.name):
                    errors.append(f"{comp.ref}:{pin.name} is floating")
        
        return ValidationResult(valid=len(errors)==0, errors=errors)
```

---

#### Task 2.2: ERC (Electrical Rule Check)
**File:** `src/pcba/circuit_validator.py`

**Purpose:** Check electrical correctness.

**Rules:**
1. Output pins should not connect directly to other output pins
2. Power pins (VCC, GND) must connect to power nets
3. LEDs must have current-limiting resistors
4. MCU reset pin should have pull-up resistor

**Implementation:**
```python
class ERCValidator:
    def validate(self, schematic_path: Path) -> ValidationResult:
        errors = []
        
        # Check LED circuits
        leds = find_components_by_type('led')
        for led in leds:
            if not has_series_resistor(led):
                errors.append(f"LED {led.ref} has no current-limiting resistor")
        
        # Check power connections
        mcus = find_components_by_type('mcu')
        for mcu in mcus:
            if not is_pin_connected(mcu, 'VCC'):
                errors.append(f"MCU {mcu.ref} VCC not connected")
            if not is_pin_connected(mcu, 'GND'):
                errors.append(f"MCU {mcu.ref} GND not connected")
        
        return ValidationResult(valid=len(errors)==0, errors=errors)
```

---

#### Task 2.3: Readability Score
**File:** `src/pcba/circuit_validator.py`

**Purpose:** Check if schematic is readable and well-organized.

**Metrics:**
1. Component overlap (should be 0)
2. Wire crossings (minimize)
3. Component spacing (minimum 5mm)
4. Alignment (components on grid)

**Score:** 0-100%

**Implementation:**
```python
class ReadabilityValidator:
    def calculate_score(self, schematic_path: Path) -> float:
        score = 100.0
        
        components = parse_components(schematic_path)
        
        # Check overlaps
        overlaps = count_overlaps(components)
        score -= overlaps * 10
        
        # Check spacing
        too_close = count_too_close(components, min_distance=5.0)
        score -= too_close * 5
        
        # Check alignment
        misaligned = count_misaligned(components)
        score -= misaligned * 2
        
        return max(0.0, score)
```

---

### PHASE 3: AI Training Plan (FOR QWEN CODE - LOW PRIORITY NOW)

**NOTE TO CLAUDE:** DO NOT IMPLEMENT TRAINING NOW. Just create the plan for Qwen Code to execute later.

#### Task 3.1: Dataset Collection Plan (FOR QWEN)

**Goal:** Collect 1000+ correct schematic examples for training.

**Plan for Qwen Code:**
1. Scrape KiCad library examples:
   - Official KiCad example projects
   - GitHub repositories with KiCad schematics
   - Hackaday projects
2. Parse each schematic:
   - Extract components and connections
   - Extract natural language description from README
   - Validate with ERC
3. Create training pairs:
   - Input: "Arduino with two LED on pin 5"
   - Output: Correct schematic JSON

**Deliverable:** Dataset of 1000+ (description, schematic) pairs

---

#### Task 3.2: Model Selection Plan (FOR QWEN)

**Goal:** Choose and configure ML model for circuit generation.

**Plan for Qwen Code:**
1. Research options:
   - Graph Neural Networks (GNN) for circuit graphs
   - Transformer models trained on netlists
   - Fine-tune CodeLlama on schematic generation
2. Compare:
   - Accuracy on test set
   - Inference speed
   - Memory requirements
3. Select best model for our use case

**Deliverable:** Model selection report with recommendation

---

#### Task 3.3: Training Pipeline Plan (FOR QWEN)

**Goal:** Create training pipeline.

**Plan for Qwen Code:**
1. Prepare dataset (from Task 3.1)
2. Implement model (from Task 3.2)
3. Train on GPU cluster
4. Evaluate on test set
5. Export model for inference

**Deliverable:** Trained model + inference code

---

### PHASE 4: Integration (LOW PRIORITY)

#### Task 4.1: Validation Integration
**File:** `src/pcba/schematic.py`

**Add validation after generation:**
```python
def generate_schematic(description: str, output: str) -> Path:
    # ... existing generation code ...
    
    # NEW: Validate generated schematic
    from .circuit_validator import CircuitValidator
    
    validator = CircuitValidator()
    connectivity = validator.validate_connectivity(output_path)
    erc = validator.validate_erc(output_path)
    readability = validator.calculate_readability(output_path)
    
    if not connectivity.valid:
        print(f"⚠️ Connectivity errors: {connectivity.errors}")
        # Auto-fix or ask user
    
    if not erc.valid:
        print(f"⚠️ ERC errors: {erc.errors}")
        # Auto-fix or ask user
    
    print(f"✓ Readability score: {readability}%")
    
    return output_path
```

---

## 📝 PROGRESS TRACKING (SAVE AFTER EACH TASK)

**File:** `.claude_prompts/PROGRESS.md`

**Format:**
```markdown
# Progress Log

## [DATE] - [TASK NAME]

### What was done:
- [List changes]

### Files modified:
- [List files]

### Test results:
```bash
[Test commands and output]
```

### Next steps:
- [What's next]

---

## [DATE] - [NEXT TASK]
...
```

**IMPORTANT:** Update this file after EVERY task. If session ends, Qwen Code can continue from here.

---

## 🚀 IMMEDIATE ACTION ITEMS (DO THESE FIRST)

1. **Fix duplicate MCU** (Task 1.1) - 30 min
2. **Fix wire-to-pin connections** (Task 1.2) - 1 hour
3. **Add ground symbol** (Task 1.3) - 30 min
4. **Test all fixes** - 30 min

**Total time:** ~2.5 hours

**After completion:**
```bash
pcba schematic "Arduino with two LED on pin 5" -o final_test.kicad_sch
open final_test.kicad_sch
# Should show:
# - 1 Arduino UNO R3 (not 2 MCUs)
# - Wires connected to LED pins (not centers)
# - GND symbol present
# - Complete circuit
```

---

## 📞 HANDOFF INSTRUCTIONS (IF SESSION ENDS)

**For Qwen Code:**

1. Read `.claude_prompts/PROGRESS.md` to see what's done
2. Continue with next task in PHASE 1
3. After each task:
   - Test thoroughly
   - Update PROGRESS.md
   - Commit to git

**Priority order:**
1. PHASE 1 (Critical bugs) - DO NOW
2. PHASE 2 (Validation) - AFTER PHASE 1
3. PHASE 3 (AI Training) - QWEN'S MAIN TASK
4. PHASE 4 (Integration) - LAST

**DO NOT:**
- Skip PHASE 1
- Start AI training before bugs are fixed
- Make changes without testing

**ALWAYS:**
- Update PROGRESS.md
- Test after each change
- Commit working code

---

## ✅ SUCCESS CRITERIA

**PHASE 1 Complete when:**
- ✅ No duplicate MCUs
- ✅ Wires connect to pins
- ✅ GND symbol present
- ✅ Test schematic opens correctly in KiCad

**PHASE 2 Complete when:**
- ✅ Connectivity validator works
- ✅ ERC validator works
- ✅ Readability score calculated
- ✅ All validators run automatically

**PHASE 3 Complete when:**
- ✅ Dataset collected (1000+ examples)
- ✅ Model selected and trained
- ✅ Model integrated into pipeline

**PHASE 4 Complete when:**
- ✅ All validators integrated
- ✅ Auto-fix implemented
- ✅ Full end-to-end test passes

---

**START WITH PHASE 1 TASK 1.1 NOW!**
