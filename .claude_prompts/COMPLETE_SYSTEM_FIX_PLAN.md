# PCBAI: Complete System Architecture & Implementation Plan

## 🎯 PROJECT VISION

**PCBAI** — AI-powered PCB design assistant that works like Claude Code/Qwen Code for electronics.

**Core Idea:** User describes circuit in natural language → AI understands → Generates complete KiCad schematic → Auto-routes PCB.

**Key Features:**
1. **Natural Language Input** — "two LED with 330 ohm resistor to Arduino pin 5"
2. **AI Understanding** — Extract components, quantities, connections, configuration
3. **Graph Representation** — Circuit as graph with nodes (components) and edges (connections)
4. **KiCad Generation** — Convert graph to .kicad_sch format
5. **Auto-Routing** — FreeRouting integration for PCB traces
6. **Project-Based AI** — AI works directly in project folder, helps iterate on design

---

## ❌ CURRENT PROBLEMS (CRITICAL)

### Problem 1: Arduino Shows as Question Mark
**Issue:** MCU symbol not rendering correctly in KiCad  
**Expected:** ATmega328P or Arduino Uno symbol displays correctly  
**Actual:** Question mark symbol

### Problem 2: No Connections
**Issue:** Components placed but wires not drawn between them  
**Expected:** Complete schematic with wires connecting all components  
**Actual:** Floating components with no connections

### Problem 3: AI → Graph → Generator Flow Broken
**Issue:** AI analysis output not properly converted to schematic  
**Expected:** Clean pipeline: Text → AI → Graph → Generator → .kicad_sch  
**Actual:** Components generated but connections lost

### Problem 4: No Project Context
**Issue:** AI doesn't understand existing project structure  
**Expected:** AI can read existing .kicad_sch/.kicad_pcb files and help modify  
**Actual:** Each generation is independent, no iteration

---

## ✅ REQUIRED SYSTEM ARCHITECTURE

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  User Input: "two LED with 330 ohm to Arduino pin 5"            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  AI Circuit Analyzer (LLM via Ollama/Gemini)                    │
│  - Extract components with quantities                           │
│  - Extract connections                                          │
│  - Determine configuration (series/parallel)                    │
│  - Ask clarifying questions if needed                           │
│                                                                  │
│  Output Format (JSON):                                          │
│  {                                                              │
│    "components": [...],                                         │
│    "connections": [...],                                        │
│    "mcu": {...},                                                │
│    "configuration": "series"                                    │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Circuit Graph Builder                                          │
│  - Convert JSON to graph structure                              │
│  - Nodes: Components (with pins)                                │
│  - Edges: Connections (nets)                                    │
│  - Validate: DRC rules, connectivity                            │
│                                                                  │
│  Format:                                                        │
│  {                                                              │
│    "nodes": [                                                   │
│      {"id": "R1", "type": "resistor", "pins": {"1": ..., "2": ...}},
│      {"id": "LED1", "type": "led", "pins": {"A": ..., "K": ...}}
│    ],                                                           │
│    "edges": [                                                   │
│      {"from": "Arduino:5", "to": "R1:1", "net": "Net_1"},       │
│      {"from": "R1:2", "to": "LED1:A", "net": "Net_2"}           │
│    ]                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  KiCad Schematic Generator                                      │
│  - Convert graph to .kicad_sch S-expressions                    │
│  - lib_symbols: Define all used symbols                         │
│  - symbol instances: Place components with positions            │
│  - wires: Draw connections between pins                         │
│  - labels: Add net labels                                       │
│                                                                  │
│  Output: Valid KiCad 9.0 .kicad_sch file                        │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  KiCad Validation (kicad-cli)                                   │
│  - Run: kicad-cli sch export netlist file.kicad_sch             │
│  - Check: No errors, all symbols valid                          │
│  - Verify: All connections present                              │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  User Opens in KiCad                                            │
│  - All symbols render correctly (no "?")                        │
│  - All connections visible                                      │
│  - Components positioned logically                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 DETAILED SPECIFICATIONS

### 1. AI Circuit Analyzer

**File:** `src/pcba/ai_analyzer.py`

**Class:** `EnhancedCircuitAnalyzer`

**Input:**
```python
description: str = "two LED with 330 ohm resistor to Arduino pin 5"
```

**Output (JSON):**
```json
{
  "circuit_type": "led_array",
  "components": [
    {
      "ref": "R1",
      "type": "resistor",
      "value": "330",
      "footprint": "Resistor_SMD:R_0805",
      "lib_id": "Device:R",
      "quantity": 1,
      "pins": {"1": "input", "2": "output"}
    },
    {
      "ref": "LED1",
      "type": "led",
      "value": "RED",
      "footprint": "LED_SMD:LED_0805",
      "lib_id": "Device:LED",
      "quantity": 1,
      "pins": {"A": "anode", "K": "cathode"}
    },
    {
      "ref": "LED2",
      "type": "led",
      "value": "RED",
      "footprint": "LED_SMD:LED_0805",
      "lib_id": "Device:LED",
      "quantity": 1,
      "pins": {"A": "anode", "K": "cathode"}
    },
    {
      "ref": "U1",
      "type": "mcu",
      "value": "Arduino Uno",
      "footprint": "Module_Arduino:Arduino_Uno_R3_Shield",
      "lib_id": "Module_Arduino:Arduino_Uno_R3",
      "quantity": 1,
      "pins": {
        "5": {"name": "D5", "type": "GPIO"},
        "VCC": {"name": "5V", "type": "power_out"},
        "GND": {"name": "GND", "type": "ground"}
      }
    }
  ],
  "connections": [
    {"from": "U1:5", "to": "R1:1", "net": "Net_D5_R1"},
    {"from": "R1:2", "to": "LED1:A", "net": "Net_R1_LED1"},
    {"from": "LED1:K", "to": "LED2:A", "net": "Net_LED1_LED2"},
    {"from": "LED2:K", "to": "U1:GND", "net": "GND"}
  ],
  "mcu": {
    "type": "Arduino Uno",
    "lib_id": "Module_Arduino:Arduino_Uno_R3",
    "footprint": "Module_Arduino:Arduino_Uno_R3_Shield",
    "pins_used": ["5", "GND", "VCC"]
  },
  "configuration": "series",
  "power": {
    "positive": "+5V",
    "ground": "GND"
  },
  "questions": []
}
```

**LLM Prompt Template:**
```python
prompt = """
Ты опытный инженер-электронщик. Проанализируй описание схемы и извлеки ВСЮ информацию.

ПРАВИЛА:
1. "two LED" = 2 светодиода (LED1, LED2)
2. "330 ohm resistor" = резистор 330Ω (R1)
3. "Arduino pin 5" = MCU с пином D5
4. "in series" = последовательное соединение
5. "in parallel" = параллельное соединение

ФОРМАТ ОТВЕТА (только JSON, без markdown):
{
  "components": [
    {"ref": "R1", "type": "resistor", "value": "330", "quantity": 1, "lib_id": "Device:R"}
  ],
  "connections": [
    {"from": "U1:5", "to": "R1:1", "net": "Net_1"}
  ],
  "mcu": {"type": "Arduino Uno", "lib_id": "Module_Arduino:Arduino_Uno_R3"},
  "configuration": "series",
  "questions": []
}

ВХОД: {user_description}
"""
```

---

### 2. Circuit Graph Builder

**File:** `src/pcba/circuit_graph.py` (NEW)

**Class:** `CircuitGraph`

**Purpose:** Convert AI JSON output to graph structure with validation.

**Structure:**
```python
@dataclass
class ComponentNode:
    ref: str
    type: str
    lib_id: str
    footprint: str
    value: str
    pins: dict[str, PinInfo]
    position: tuple[float, float] | None = None

@dataclass
class PinInfo:
    name: str
    type: str  # "input", "output", "power", "ground", "passive"
    connected_to: str | None = None

@dataclass
class ConnectionEdge:
    from_pin: str  # "R1:1"
    to_pin: str    # "LED1:A"
    net: str       # "Net_1"

class CircuitGraph:
    nodes: dict[str, ComponentNode]
    edges: list[ConnectionEdge]
    nets: dict[str, list[str]]  # net_name -> [pin_refs]
    
    def add_component(self, comp: dict) -> None: ...
    def add_connection(self, from_pin: str, to_pin: str, net: str) -> None: ...
    def validate(self) -> list[str]:  # Returns list of errors
        - Check all pins connected
        - Check no floating nets
        - Check power connections
        - Check DRC rules
    def get_positioned_graph(self) -> dict:  # For schematic generator
        - Calculate optimal positions
        - Center MCU
        - Arrange components around MCU
        - Minimize wire crossings
```

---

### 3. KiCad Schematic Generator

**File:** `src/pcba/schematic_generator.py` (REPLACE existing schematic.py)

**Class:** `KiCadSchematicGenerator`

**Input:** `CircuitGraph` object

**Output:** Valid KiCad 9.0 .kicad_sch file

**Key Methods:**
```python
def generate(self, graph: CircuitGraph) -> str:
    """Generate complete .kicad_sch content."""
    lines = []
    lines.append("(kicad_sch")
    lines.append("\t(version 20250114)")
    lines.append("\t(generator \"eeschema\")")
    lines.append("\t(generator_version \"9.0\")")
    lines.append(f"\t(uuid \"{uuid.uuid4()}\")")
    lines.append("\t(paper \"A4\")")
    
    # lib_symbols section
    lines.append("\t(lib_symbols")
    for lib_id in graph.get_unique_lib_ids():
        symbol_def = self._get_symbol_definition(lib_id)
        lines.append(symbol_def)
    lines.append("\t)")
    
    # Component instances
    for node in graph.get_positioned_nodes():
        lines.append(self._generate_symbol_instance(node))
    
    # Wires (connections)
    for edge in graph.edges:
        lines.append(self._generate_wire(edge))
    
    # Power flags
    lines.extend(self._generate_power_flags(graph.nets))
    
    lines.append("\t(sheet_instances")
    lines.append("\t\t(path \"/\"")
    lines.append("\t\t\t(page \"1\")")
    lines.append("\t\t)")
    lines.append("\t)")
    lines.append("\t(embedded_fonts no)")
    lines.append(")")
    
    return "\n".join(lines)
```

**Critical: Symbol Definitions**

Must match EXACTLY KiCad 9.0 format from official libraries:

```python
def _get_symbol_definition(self, lib_id: str) -> str:
    """Get symbol definition from official KiCad libraries."""
    
    # Use official KiCad library paths
    official_libs = {
        "Device:R": "/usr/share/kicad/symbols/Device.kicad_sym",
        "Device:LED": "/usr/share/kicad/symbols/Device.kicad_sym",
        "Device:C": "/usr/share/kicad/symbols/Device.kicad_sym",
        "Module_Arduino:Arduino_Uno_R3": "/usr/share/kicad/symbols/Module_Arduino.kicad_sym",
        # ... etc
    }
    
    # Load from file or use cached definition
    if lib_id in official_libs:
        return self._load_symbol_from_file(official_libs[lib_id], lib_id)
    else:
        # Generate generic symbol
        return self._generate_generic_symbol(lib_id)
```

**Symbol Format (MUST MATCH test1.kicad_sch):**
```lisp
(symbol "Device:R"
  (pin_numbers
    (hide yes)
  )
  (pin_names
    (offset 0)
  )
  (exclude_from_sim no)
  (in_bom yes)
  (on_board yes)
  (property "Reference" "R"
    (at 2.032 0 90)
    (effects
      (font
        (size 1.27 1.27)
      )
    )
  )
  ...
  (symbol "R_0_1"
    (rectangle
      (start -1.016 -2.54)
      (end 1.016 2.54)
      ...
    )
  )
  (symbol "R_1_1"
    (pin passive line
      (at 0 3.81 270)
      (length 1.27)
      (name "~"
        (effects
          (font
            (size 1.27 1.27)
          )
        )
      )
      (number "1"
        (effects
          (font
            (size 1.27 1.27)
          )
        )
      )
    )
    ...
  )
  (embedded_fonts no)
)
```

---

### 4. KiCad CLI Validation

**File:** `src/pcba/validator.py` (NEW)

**Class:** `KiCadValidator`

**Purpose:** Validate generated schematic before returning to user.

**Methods:**
```python
def validate_schematic(self, filepath: Path) -> ValidationResult:
    """Run kicad-cli validation."""
    
    # Check syntax
    result = subprocess.run(
        ["kicad-cli", "sch", "export", "netlist", str(filepath), "-o", "/dev/null"],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        return ValidationResult(
            valid=False,
            errors=[result.stderr],
            warnings=[]
        )
    
    # Check for question marks (missing symbols)
    content = filepath.read_text()
    if "??" in content or "QuestionMark" in content:
        return ValidationResult(
            valid=False,
            errors=["Missing symbol definitions detected"],
            warnings=[]
        )
    
    # Check all components have lib_id
    if "(lib_id \"\")" in content:
        return ValidationResult(
            valid=False,
            errors=["Components with empty lib_id"],
            warnings=[]
        )
    
    return ValidationResult(valid=True, errors=[], warnings=[])
```

---

### 5. Project-Based AI Assistant

**File:** `src/pcba/project_ai.py` (NEW)

**Class:** `ProjectAIAssistant`

**Purpose:** Work like Claude Code — understand entire project, help iterate.

**Features:**
```python
class ProjectAIAssistant:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.schematics: list[Path] = []
        self.pcbs: list[Path] = []
        self.load_project()
    
    def load_project(self) -> None:
        """Load all .kicad_sch and .kicad_pcb files."""
        self.schematics = list(self.project_path.glob("**/*.kicad_sch"))
        self.pcbs = list(self.project_path.glob("**/*.kicad_pcb"))
    
    def analyze_existing_design(self) -> dict:
        """Analyze existing schematic/PCB."""
        analysis = {
            "components": [],
            "nets": [],
            "mcu": None,
            "sensors": [],
            "issues": []
        }
        
        for sch in self.schematics:
            parsed = self._parse_schematic(sch)
            analysis["components"].extend(parsed["components"])
            analysis["nets"].extend(parsed["nets"])
        
        return analysis
    
    def suggest_improvements(self) -> list[str]:
        """Suggest design improvements."""
        suggestions = []
        
        # Check for missing decoupling capacitors
        mcus = [c for c in self.components if c["type"] == "mcu"]
        for mcu in mcus:
            if not self._has_decoupling_caps(mcu):
                suggestions.append(f"Add 100nF decoupling capacitor near {mcu['ref']}")
        
        # Check for missing pull-up resistors
        i2c_devices = [c for c in self.components if "I2C" in c.get("interfaces", [])]
        if i2c_devices and not self._has_i2c_pullups():
            suggestions.append("Add 4.7k pull-up resistors for I2C lines")
        
        return suggestions
    
    def help_modify(self, request: str) -> None:
        """Help modify existing design."""
        # "Add another LED to pin 6"
        # "Move all components closer together"
        # "Check if this circuit will work"
        pass
```

---

## 📋 IMPLEMENTATION PLAN (FOR CLAUDE CODE)

### Phase 1: Fix Critical Issues (PRIORITY 1)

**Task 1.1: Fix Arduino Symbol**
- [ ] Find correct lib_id for Arduino Uno in official KiCad libraries
- [ ] Use `Module_Arduino:Arduino_Uno_R3` or `MCU_Microchip_ATmega:ATMEGA328P-AU`
- [ ] Verify symbol renders in KiCad with `kicad-cli`
- [ ] Test: Generate schematic with Arduino, open in KiCad, no "?"

**Task 1.2: Fix Connections**
- [ ] Implement `CircuitGraph` class
- [ ] Ensure all connections from AI are converted to wires
- [ ] Verify wire coordinates match pin positions
- [ ] Test: Generate schematic, check all components connected

**Task 1.3: Fix lib_symbols Generation**
- [ ] Load symbol definitions from official KiCad library files
- [ ] Cache commonly used symbols
- [ ] Ensure ALL used symbols are in lib_symbols section
- [ ] Test: Generate schematic, grep for all lib_ids in lib_symbols

### Phase 2: Implement Graph Pipeline (PRIORITY 2)

**Task 2.1: CircuitGraph Class**
- [ ] Create `src/pcba/circuit_graph.py`
- [ ] Implement `ComponentNode`, `PinInfo`, `ConnectionEdge`
- [ ] Implement graph validation
- [ ] Implement position calculation

**Task 2.2: Generator Integration**
- [ ] Update `schematic.py` to use `CircuitGraph`
- [ ] Ensure graph → KiCad conversion preserves all connections
- [ ] Test with complex circuits (3+ components)

### Phase 3: Project-Based AI (PRIORITY 3)

**Task 3.1: Project Loader**
- [ ] Create `src/pcba/project_ai.py`
- [ ] Implement `.kicad_sch` parsing
- [ ] Implement `.kicad_pcb` parsing
- [ ] Store in project context

**Task 3.2: AI Iteration**
- [ ] "Add LED to pin 6" → modify existing schematic
- [ ] "Move components closer" → reposition
- [ ] "Check if works" → DRC + ERC simulation

### Phase 4: Testing & Validation (PRIORITY 4)

**Task 4.1: kicad-cli Integration**
- [ ] Run validation after every generation
- [ ] Parse errors and show to user
- [ ] Auto-fix common issues

**Task 4.2: End-to-End Tests**
- [ ] Test: "two LED" → 2 LEDs in KiCad
- [ ] Test: "Arduino with sensor" → Arduino + sensor connected
- [ ] Test: "LED in parallel" → parallel connection

---

## 🎯 SUCCESS CRITERIA

### Must Have (Phase 1):
- ✅ Arduino symbol renders correctly (no "?")
- ✅ All components connected with wires
- ✅ "two LED" → 2 LEDs in schematic
- ✅ `kicad-cli validate` passes

### Should Have (Phase 2):
- ✅ Graph pipeline working
- ✅ Complex circuits (5+ components) generate correctly
- ✅ Series/parallel connections correct

### Nice to Have (Phase 3):
- ✅ Project-based AI assistance
- ✅ Design suggestions
- ✅ Iterative modification

---

## 📚 RESOURCES

### Official KiCad Resources:
- **Symbol Libraries:** https://gitlab.com/kicad/libraries/kicad-symbols
- **Footprint Libraries:** https://gitlab.com/kicad/libraries/kicad-footprints
- **Schematic Format:** https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/
- **KiCad CLI:** https://docs.kicad.org/9.0/en/cli/cli.html

### Library Paths (macOS):
```
/Applications/KiCad/KiCad.app/Contents/Share/kicad/symbols/
  - Device.kicad_sym (R, C, LED, etc.)
  - Module_Arduino.kicad_sym (Arduino boards)
  - MCU_Microchip_ATmega.kicad_sym (ATmega chips)
```

### Library Paths (Linux):
```
/usr/share/kicad/symbols/
  - Device.kicad_sym
  - Module_Arduino.kicad_sym
  - MCU_Microchip_ATmega.kicad_sym
```

### Library Paths (Windows):
```
C:\Program Files\KiCad\9.0\share\kicad\symbols\
  - Device.kicad_sym
  - Module_Arduino.kicad_sym
  - MCU_Microchip_ATmega.kicad_sym
```

---

## 🚀 IMMEDIATE ACTION ITEMS

1. **Check current schematic output:**
   ```bash
   cd /Users/vladglazunov/Documents/algo/PCBAI
   source venv/bin/activate
   pcba schematic "Arduino with LED" -o test.kicad_sch
   
   # Check for issues
   grep "lib_id" test.kicad_sch | head -10
   grep "(wire" test.kicad_sch | head -10
   
   # Validate
   kicad-cli sch export netlist test.kicad_sch -o /dev/null
   ```

2. **Check official KiCad libraries:**
   ```bash
   # Find Arduino symbol
   grep -r "Arduino_Uno" /Applications/KiCad/KiCad.app/Contents/Share/kicad/symbols/
   
   # Check symbol format
   head -200 /Applications/KiCad/KiCad.app/Contents/Share/kicad/symbols/Device.kicad_sym
   ```

3. **Fix based on findings:**
   - If lib_id wrong → update ai_analyzer.py
   - If symbol missing → update schematic_generator.py
   - If connections missing → update circuit_graph.py

---

**YOUR TASK:** Implement all of the above. Start with Phase 1 (critical fixes), then Phase 2 (graph pipeline), then Phase 3 (project AI).

**Priority:** Working product over perfect code. Test after every change with `kicad-cli`.

**Git:** Commit after each working milestone. Use descriptive messages.

**Goal:** User types "two LED with Arduino" → Gets working schematic with 2 LEDs connected correctly.
