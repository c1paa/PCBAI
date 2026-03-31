# 📋 Prompt Files Created for Claude Code

## Files Location
`.claude_prompts/` directory

---

## 1. CRITICAL_FIX_PLAN.md (MAIN PROMPT)

**Purpose:** Fix all critical bugs in current implementation

**What it contains:**
- **Task 1.0:** Use official KiCad symbol libraries (MOST CRITICAL)
  - Load from `.kicad_sym` files
  - NOT hand-written templates
- Problem 1: Duplicate MCU (ATmega + Arduino overlaid)
- Problem 2: Wires don't connect to pins
- Problem 3: No ground symbol
- Problem 4: No circuit validation

**PHASE 1 Tasks (DO FIRST):**
1. **Task 1.0:** Load symbols from KiCad libraries - 1 hour ⭐⭐⭐
2. Task 1.1: Fix duplicate MCU - 30 min
3. Task 1.2: Fix wire-to-pin connections - 1 hour
4. Task 1.3: Add ground symbol - 30 min
5. Task 1.4: Test all fixes - 30 min

**Expected result:**
```bash
pcba schematic "Arduino with two LED on pin 5" -o test.kicad_sch

# Check symbols from libraries:
grep -A 50 "lib_symbols" test.kicad_sch
# Should show symbols from Device.kicad_sym, MCU_Module.kicad_sym

# Check no duplicates:
grep "lib_id" test.kicad_sch
# Should show: MCU_Module:Arduino_UNO_R3 (ONLY ONCE)

# Check connections:
open test.kicad_sch
# Wires connect to LED pins, not centers
# GND symbol present
```

---

## 2. QWEN_CODE_PLAN.md (FOR LATER)

**Purpose:** AI training and advanced features (AFTER PHASE 1)

**Tasks:**
1. Dataset collection (1000+ schematic examples)
2. Model selection research
3. Training pipeline implementation
4. Model integration
5. Validation system
6. Auto-fix system

**DO NOT START until PHASE 1 complete**

---

## 3. PROGRESS.md (TRACKING)

**Purpose:** Track progress after each task

**How to use:**
1. Read before starting work
2. Check what's done
3. Continue with next task
4. Update after completion:
   ```markdown
   ## [DATE] - Task 1.1: Fix Duplicate MCU
   
   ### What was done:
   - [Changes]
   
   ### Test results:
   ```bash
   [Test commands]
   ```
   
   ### Next:
   - [Next task]
   ```

---

## 🚀 HOW TO USE

### For Claude Code:

1. **Read:** `.claude_prompts/CRITICAL_FIX_PLAN.md`
2. **Start with:** PHASE 1 Task 1.1
3. **After each task:**
   - Test thoroughly
   - Update `PROGRESS.md`
   - Commit to git

### For Qwen Code:

1. **Read:** `.claude_prompts/QWEN_CODE_PLAN.md`
2. **Check:** `PROGRESS.md` to see if PHASE 1 complete
3. **Start with:** TASK 1 (Dataset Collection)
4. **After each task:**
   - Test
   - Update `PROGRESS.md`
   - Commit

---

## 📊 CURRENT STATUS

**Phase:** PHASE 1 (Critical Bugs)  
**Progress:** 0%  
**Next task:** Fix duplicate MCU (Task 1.1)

---

## ⚠️ IMPORTANT

**Claude Code MUST:**
1. Fix PHASE 1 bugs FIRST
2. Test after each fix
3. Update PROGRESS.md
4. Commit working code

**Qwen Code MUST:**
1. Wait for PHASE 1 complete
2. Check PROGRESS.md before starting
3. Follow QWEN_CODE_PLAN.md
4. Update PROGRESS.md

**DO NOT:**
- Skip PHASE 1
- Start AI training before bugs fixed
- Make changes without testing
- Forget to update PROGRESS.md

---

## 🎯 SUCCESS CRITERIA

**PHASE 1 Complete when:**
```bash
pcba schematic "Arduino with two LED on pin 5" -o test.kicad_sch
grep "lib_id" test.kicad_sch
# Should show:
# - MCU_Module:Arduino_UNO_R3 (ONLY ONCE)
# - Device:LED
# - Device:R
# Should NOT show:
# - ATmega328P
```

**Open in KiCad:**
- No question marks
- Wires connect to pins
- GND symbol visible
- Complete circuit

---

**START WITH PHASE 1 TASK 1.1 NOW!**
