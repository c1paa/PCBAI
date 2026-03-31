# QWEN CODE EXECUTION PLAN - AI Training & Advanced Features

**Priority:** LOW (execute AFTER Claude Code completes PHASE 1)

**Estimated time:** 2-3 days

---

## 🎯 YOUR MISSION

You are Qwen Code. Your task is to implement AI training and advanced features AFTER Claude Code fixes the critical bugs in PHASE 1.

**DO NOT START UNTIL:**
- ✅ PHASE 1 complete (check `.claude_prompts/PROGRESS.md`)
- ✅ No duplicate MCUs
- ✅ Wires connect to pins
- ✅ GND symbol works

---

## 📋 YOUR TASKS (IN ORDER)

### TASK 1: Dataset Collection (4-6 hours)

**Goal:** Collect 1000+ correct schematic examples.

**Steps:**

1. **Scrape KiCad examples:**
   ```python
   # Search GitHub for KiCad projects
   # Download .kicad_sch files
   # Extract descriptions from README.md
   ```

2. **Parse schematics:**
   ```python
   from pcba.parser import parse_schematic
   
   for sch_file in schematic_files:
       data = parse_schematic(sch_file)
       # Extract components, connections
       # Validate with ERC
   ```

3. **Create training pairs:**
   ```python
   training_data = []
   for project in projects:
       pair = {
           'input': project.description,  # "Arduino weather station"
           'output': project.schematic_json,  # Component list + connections
       }
       training_data.append(pair)
   ```

4. **Save dataset:**
   ```python
   import json
   with open('datasets/schematic_generation.json', 'w') as f:
       json.dump(training_data, f, indent=2)
   ```

**Deliverable:** `datasets/schematic_generation.json` with 1000+ examples

---

### TASK 2: Model Selection Research (2-3 hours)

**Goal:** Choose best ML model for circuit generation.

**Research options:**

1. **Graph Neural Networks (GNN):**
   - Pros: Natural for circuit graphs
   - Cons: Complex to implement
   - Libraries: PyTorch Geometric, DGL

2. **Transformer on Netlists:**
   - Pros: Good at sequence generation
   - Cons: May not capture graph structure
   - Libraries: HuggingFace Transformers

3. **Fine-tune CodeLlama:**
   - Pros: Already knows code structure
   - Cons: Large, slow inference
   - Libraries: llama.cpp, vLLM

**Comparison table:**

| Model | Accuracy | Speed | Memory | Recommendation |
|-------|----------|-------|--------|----------------|
| GNN | High | Medium | Low | ⭐⭐⭐⭐ |
| Transformer | Medium | Fast | Medium | ⭐⭐⭐ |
| CodeLlama | High | Slow | High | ⭐⭐ |

**Deliverable:** `docs/model_selection.md` with recommendation

---

### TASK 3: Training Pipeline (6-8 hours)

**Goal:** Create training pipeline.

**Steps:**

1. **Prepare dataset:**
   ```python
   from torch.utils.data import Dataset, DataLoader
   
   class SchematicDataset(Dataset):
       def __init__(self, json_path):
           with open(json_path) as f:
               self.data = json.load(f)
       
       def __len__(self):
           return len(self.data)
       
       def __getitem__(self, idx):
           item = self.data[idx]
           # Tokenize input
           # Parse output to graph
           return input_tokens, output_graph
   ```

2. **Implement model:**
   ```python
   import torch
   import torch.nn as nn
   
   class SchematicGenerator(nn.Module):
       def __init__(self, ...):
           super().__init__()
           # Define architecture
       
       def forward(self, input_text):
           # Generate schematic graph
           return output_graph
   ```

3. **Training loop:**
   ```python
   model = SchematicGenerator(...)
   optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
   
   for epoch in range(num_epochs):
       for batch in dataloader:
           input_text, target_graph = batch
           
           optimizer.zero_grad()
           output = model(input_text)
           loss = criterion(output, target_graph)
           loss.backward()
           optimizer.step()
   ```

4. **Evaluation:**
   ```python
   model.eval()
   with torch.no_grad():
       for test_item in test_set:
           output = model(test_item.input)
           # Compare with ground truth
           accuracy = calculate_accuracy(output, test_item.target)
   ```

**Deliverable:** `train.py` - working training script

---

### TASK 4: Model Integration (3-4 hours)

**Goal:** Integrate trained model into PCBAI pipeline.

**Steps:**

1. **Save model:**
   ```python
   torch.save(model.state_dict(), 'models/schematic_generator.pt')
   ```

2. **Load in PCBAI:**
   ```python
   # In src/pcba/ai_analyzer.py
   class AISchematicGenerator:
       def __init__(self, model_path):
           self.model = SchematicGenerator(...)
           self.model.load_state_dict(torch.load(model_path))
           self.model.eval()
       
       def generate(self, description: str) -> dict:
           # Tokenize description
           # Run model
           # Return schematic JSON
   ```

3. **Replace current AI:**
   ```python
   # Replace LLM-based generation with trained model
   def analyze(description: str) -> dict:
       if USE_TRAINED_MODEL:
           return trained_model.generate(description)
       else:
           return llm_analyze(description)  # Fallback
   ```

**Deliverable:** Integrated model in `ai_analyzer.py`

---

### TASK 5: Validation System (4-5 hours)

**Goal:** Implement PHASE 2 validators from Claude's plan.

**Files to create:**
- `src/pcba/circuit_validator.py`

**Validators to implement:**

1. **ConnectivityValidator:**
   ```python
   class ConnectivityValidator:
       def validate(self, schematic_path: Path) -> ValidationResult:
           # Build graph from schematic
           # Check all pins connected
           # Check no floating nets
   ```

2. **ERCValidator:**
   ```python
   class ERCValidator:
       def validate(self, schematic_path: Path) -> ValidationResult:
           # Check electrical rules
           # LED has resistor
           # MCU has power
           # No output-to-output connections
   ```

3. **ReadabilityValidator:**
   ```python
   class ReadabilityValidator:
       def calculate_score(self, schematic_path: Path) -> float:
           # Check overlaps
           # Check spacing
           # Check alignment
           # Return 0-100 score
   ```

**Deliverable:** Working validators with tests

---

### TASK 6: Auto-Fix System (3-4 hours)

**Goal:** Automatically fix common errors.

**Fixes to implement:**

1. **Add missing GND:**
   ```python
   def add_missing_ground(components: list) -> list:
       # Find unconnected GND pins
       # Add GND symbol
       # Connect to GND pins
   ```

2. **Add pull-up resistors:**
   ```python
   def add_pullup_resistors(components: list, connections: list) -> list:
       # Find I2C lines without pull-ups
       # Add 4.7k resistors
       # Connect to VCC
   ```

3. **Add current-limiting resistors:**
   ```python
   def add_led_resistors(components: list, connections: list) -> list:
       # Find LEDs without series resistors
       # Calculate resistor value (R = (Vcc - Vf) / If)
       # Add resistor in series
   ```

**Deliverable:** Auto-fix functions in `circuit_validator.py`

---

## 📝 PROGRESS TRACKING

**Update this file after each task:**

```markdown
# Qwen Code Progress Log

## [DATE] - TASK 1: Dataset Collection

### Progress:
- [x] Scraped 500 KiCad projects from GitHub
- [x] Parsed all schematics
- [ ] Need 500 more examples
- [ ] Create training pairs

### Files created:
- `datasets/schematic_generation.json` (500 examples)

### Next:
- Continue scraping
- Target: 1000 examples

---

## [DATE] - TASK 1: Dataset Collection (COMPLETE)

### Results:
- ✅ 1247 examples collected
- ✅ All validated with ERC
- ✅ Training pairs created

### Files:
- `datasets/schematic_generation.json` (1247 examples, 5.2 MB)

### Next:
- Start TASK 2: Model Selection

---

## [DATE] - TASK 2: Model Selection

### Research:
- Compared GNN, Transformer, CodeLlama
- Selected GNN for circuit graphs

### Files:
- `docs/model_selection.md`

### Next:
- Start TASK 3: Training Pipeline
```

---

## 🚀 TESTING REQUIREMENTS

**After EACH task:**

1. **Unit tests:**
   ```bash
   python -m pytest tests/test_dataset.py -v
   python -m pytest tests/test_model.py -v
   ```

2. **Integration tests:**
   ```bash
   pcba schematic "Arduino with LED" -o test.kicad_sch
   kicad-cli sch export netlist test.kicad_sch -o /dev/null
   ```

3. **Quality checks:**
   - No duplicate components
   - Wires connect to pins
   - GND present
   - ERC passes

---

## ⚠️ IMPORTANT RULES

1. **DO NOT start until PHASE 1 complete**
   - Check `.claude_prompts/PROGRESS.md`
   - Verify no critical bugs

2. **Test after EVERY change**
   - Unit tests
   - Integration tests
   - Manual KiCad check

3. **Update progress log**
   - After each task
   - Include test results
   - Note any issues

4. **Commit working code**
   - Git commit after each task
   - Descriptive messages
   - Push to main

---

## 🎯 SUCCESS CRITERIA

**All tasks complete when:**

- ✅ Dataset: 1000+ examples
- ✅ Model trained and integrated
- ✅ Validators working
- ✅ Auto-fix implemented
- ✅ All tests pass
- ✅ End-to-end test:
  ```bash
  pcba schematic "Arduino weather station with DHT22" -o weather.kicad_sch
  # Should generate correct schematic automatically
  ```

---

**START WITH TASK 1 AFTER CLAUDE FINISHES PHASE 1!**
