# QWEN CODE - START HERE

## ✅ COMPLETED WORK (Claude Code)

### PHASE 1: Critical Bugs - 100% COMPLETE
- ✅ Task 1.0: Symbols loaded from official KiCad `.kicad_sym` libraries
- ✅ Task 1.1: No duplicate MCU (Arduino only, not ATmega + Arduino)
- ✅ Task 1.2: Wires connect to actual pin positions
- ✅ Task 1.3: GND and +5V symbols present
- ✅ Task 1.4: All tests PASS, kicad-cli validation PASS

### PHASE 2: Validation System - 100% COMPLETE
- ✅ Task 2.1: Connectivity Validator (checks all pins connected)
- ✅ Task 2.2: ERC Validator (LED resistors, MCU power)
- ✅ Task 2.3: Readability Score (overlap, spacing, alignment)
- ✅ Task 2.4: Integrated into generate_schematic()

**Test output:**
```
✓ Connectivity: PASS
✓ ERC: PASS
✓ Readability: 88.0% (Good)
✓ kicad-cli: PASS
```

---

## 🎯 YOUR MISSION: PHASE 3 - AI Training

**Priority:** LOW (only start after verifying PHASE 1-2 work)

**Goal:** Train AI model to generate better schematics from natural language.

### Task 3.1: Dataset Collection (4-6 hours)

**Goal:** Collect 1000+ correct schematic examples.

**Steps:**
1. Scrape GitHub for KiCad projects
2. Parse `.kicad_sch` files
3. Extract descriptions from README.md
4. Create training pairs: (description → schematic JSON)

**File:** `scripts/collect_dataset.py`

**Deliverable:** `datasets/schematic_generation.json` (1000+ examples)

---

### Task 3.2: Model Selection (2-3 hours)

**Goal:** Choose best ML model for circuit generation.

**Research:**
- Graph Neural Networks (GNN)
- Transformer on netlists
- Fine-tune CodeLlama

**File:** `docs/model_selection.md`

**Deliverable:** Model selection report with recommendation

---

### Task 3.3: Training Pipeline (6-8 hours)

**Goal:** Create training pipeline.

**Files:**
- `src/pcba/ai_trainer.py` - Training logic
- `train.py` - Main training script

**Deliverable:** Trained model + inference code

---

### Task 3.4: Model Integration (3-4 hours)

**Goal:** Integrate trained model into PCBAI.

**File:** `src/pcba/ai_analyzer.py`

**Changes:**
- Add `TrainedModelAnalyzer` class
- Use trained model instead of LLM (or as fallback)

**Deliverable:** Integrated model in pipeline

---

## 📊 CURRENT PROJECT STATUS

**Files:**
- `src/pcba/schematic.py` - Main generator (working)
- `src/pcba/ai_analyzer.py` - AI analysis (working)
- `src/pcba/circuit_validator.py` - Validation (NEW, working)
- `src/pcba/runtime_verifier.py` - Symbol verification (working)
- `src/pcba/kicad_library.py` - Library reader (working)

**Test command:**
```bash
cd /Users/vladglazunov/Documents/algo/PCBAI
source venv/bin/activate
pcba schematic "Arduino with two LED on pin 5" -o test.kicad_sch
```

**Expected output:**
```
Analyzing circuit: Arduino with two LED on pin 5
  Validating schematic...
  ✓ Connectivity: PASS
  ✓ ERC: PASS
  ✓ Readability: 88.0% (Good)
✓ Schematic generated: test.kicad_sch
```

---

## 🚀 HOW TO START

1. **Verify PHASE 1-2 work:**
   ```bash
   pcba schematic "Arduino with LED" -o test.kicad_sch
   # Should show all validations PASS
   ```

2. **Read QWEN_CODE_PLAN.md:**
   ```bash
   cat .claude_prompts/QWEN_CODE_PLAN.md
   ```

3. **Start with Task 3.1:**
   ```bash
   mkdir -p datasets scripts
   # Create scripts/collect_dataset.py
   ```

4. **Update PROGRESS.md after each task:**
   ```markdown
   ## [DATE] - Task 3.1: Dataset Collection
   
   ### Progress:
   - [x] Scraped 500 projects
   - [ ] Need 500 more
   
   ### Files created:
   - `datasets/schematic_generation.json` (500 examples)
   ```

---

## ⚠️ IMPORTANT RULES

1. **Test after EVERY change**
2. **Update PROGRESS.md** after each task
3. **Git commit** working code
4. **DO NOT break PHASE 1-2** functionality

---

**START WITH TASK 3.1 AFTER VERIFYING PHASE 1-2 WORK!**

Good luck! 🚀
