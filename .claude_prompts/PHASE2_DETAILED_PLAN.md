# PHASE 2: Circuit Validation System — DETAILED IMPLEMENTATION PLAN

**Priority:** HIGH (do immediately after Phase 1)  
**Executor:** Claude Code → Qwen Code (if session ends)  
**File to create:** `src/pcba/circuit_validator.py`  
**Integration point:** `src/pcba/schematic.py` → `generate_schematic()` (line ~1107)

---

## ARCHITECTURE OVERVIEW

```
generate_schematic()
  ├── analyzer.analyze()        ← Phase 1 (DONE)
  ├── conn_gen.generate()       ← Phase 1 (DONE)
  ├── generator.generate()      ← Phase 1 (DONE)
  ├── output_path.write_text()
  └── CircuitValidator(output_path)   ← Phase 2 (THIS)
        ├── validate_connectivity()   ← Task 2.1
        ├── validate_erc()            ← Task 2.2
        └── calculate_readability()   ← Task 2.3
```

---

## TASK 2.1: Connectivity Validator

### Что делает
Проверяет что ВСЕ пины компонентов подключены к проводам (нет "висящих" пинов).

### Как парсить .kicad_sch файл

Формат файла — S-expressions. Нужно извлечь:

1. **Компоненты** — блоки `(symbol ...)` с `(lib_id ...)` и `(at X Y ROT)`:
```
(symbol
  (lib_id "Device:R")
  (at 80 90 90)      ← позиция и поворот
  (property "Reference" "R1" ...)
)
```

2. **Провода** — блоки `(wire ...)` с двумя точками:
```
(wire
  (pts (xy 76.19 90.0) (xy 137.3 90.0))
)
```

3. **Пины компонентов** — загружать через `KiCadLibraryReader.extract_pin_info(lib_id)`:
```python
reader = KiCadLibraryReader()
pins = reader.extract_pin_info('Device:R')
# → [{'number': '1', 'name': '~', 'x': 0, 'y': 3.81, 'rotation': 270}, ...]
```

4. **Трансформация пинов** — локальные координаты пина → глобальные:
```python
import math
rad = math.radians(comp_rotation)
global_x = comp_x + pin_x * math.cos(rad) - pin_y * math.sin(rad)
global_y = comp_y + pin_x * math.sin(rad) + pin_y * math.cos(rad)
```

### Алгоритм проверки

```python
def validate_connectivity(schematic_path: Path) -> ValidationResult:
    # 1. Парсим файл
    components = parse_components(schematic_path)  # ref, lib_id, x, y, rotation
    wires = parse_wires(schematic_path)             # [(x1,y1), (x2,y2)]
    
    # 2. Для каждого компонента получаем глобальные позиции пинов
    reader = KiCadLibraryReader()
    all_pins = []  # [(ref, pin_num, global_x, global_y)]
    for comp in components:
        pins = reader.extract_pin_info(comp.lib_id)
        for pin in pins:
            gx, gy = transform_pin(comp.x, comp.y, comp.rotation, pin.x, pin.y)
            all_pins.append((comp.ref, pin.number, gx, gy))
    
    # 3. Для каждого пина проверяем: есть ли провод, концы которого в радиусе 1mm от пина
    TOLERANCE = 1.27  # KiCad grid spacing
    errors = []
    for ref, pin_num, px, py in all_pins:
        connected = False
        for (wx1, wy1), (wx2, wy2) in wires:
            if distance(px, py, wx1, wy1) < TOLERANCE or \
               distance(px, py, wx2, wy2) < TOLERANCE:
                connected = True
                break
        if not connected:
            errors.append(f"{ref} pin {pin_num} is not connected to any wire")
    
    return ValidationResult(valid=len(errors)==0, errors=errors)
```

### Парсинг S-expressions

**ВАЖНО:** НЕ использовать regex для парсинга вложенных S-expressions! Использовать подсчёт скобок:

```python
def parse_components(schematic_path: Path) -> list[dict]:
    """Parse component instances from .kicad_sch file."""
    content = schematic_path.read_text()
    components = []
    
    i = 0
    while i < len(content):
        # Ищем начало компонента: (symbol\n  с lib_id (не lib_symbols!)
        # Паттерн: "(symbol" за которым идёт "(lib_id"
        if content[i:i+7] == '(symbol' and '(lib_id' in content[i:i+200]:
            # Находим конец блока подсчётом скобок
            start = i
            depth = 0
            for j in range(i, len(content)):
                if content[j] == '(':
                    depth += 1
                elif content[j] == ')':
                    depth -= 1
                    if depth == 0:
                        block = content[start:j+1]
                        comp = parse_symbol_block(block)
                        if comp:
                            components.append(comp)
                        i = j + 1
                        break
            else:
                i += 1
        else:
            i += 1
    
    return components

def parse_symbol_block(block: str) -> dict | None:
    """Extract lib_id, position, reference from a symbol block."""
    import re
    
    lib_id_match = re.search(r'\(lib_id "([^"]+)"\)', block)
    at_match = re.search(r'\(at ([\d.-]+) ([\d.-]+) (\d+)\)', block)
    ref_match = re.search(r'\(property "Reference" "([^"]+)"', block)
    
    if not lib_id_match or not at_match:
        return None
    
    return {
        'lib_id': lib_id_match.group(1),
        'x': float(at_match.group(1)),
        'y': float(at_match.group(2)),
        'rotation': int(at_match.group(3)),
        'ref': ref_match.group(1) if ref_match else 'U?',
    }

def parse_wires(schematic_path: Path) -> list[tuple]:
    """Parse wire endpoints from .kicad_sch file."""
    import re
    content = schematic_path.read_text()
    wires = []
    
    # Паттерн: (wire (pts (xy X1 Y1) (xy X2 Y2)) ...)
    pattern = r'\(wire\s+\(pts\s+\(xy ([\d.-]+) ([\d.-]+)\)\s+\(xy ([\d.-]+) ([\d.-]+)\)\)'
    for match in re.finditer(pattern, content):
        x1, y1, x2, y2 = [float(match.group(i)) for i in range(1, 5)]
        wires.append(((x1, y1), (x2, y2)))
    
    return wires
```

### Структура результата

```python
from dataclasses import dataclass, field

@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    score: float = 100.0  # For readability
```

---

## TASK 2.2: ERC (Electrical Rule Check)

### Что проверяет

| # | Правило | Как проверить |
|---|---------|---------------|
| 1 | LED без резистора | Найти LED, проследить цепь — есть ли R в серии |
| 2 | Нет питания на MCU | Проверить что VCC/GND пины Arduino подключены |
| 3 | Output→Output конфликт | Два output пина на одном net (не наш случай пока) |
| 4 | Незамкнутая цепь | Цепь от +5V не доходит до GND |

### Алгоритм

```python
def validate_erc(schematic_path: Path) -> ValidationResult:
    errors = []
    warnings = []
    
    components = parse_components(schematic_path)
    wires = parse_wires(schematic_path)
    
    # Строим граф связности
    graph = build_connectivity_graph(components, wires)
    
    # Правило 1: LED без резистора
    leds = [c for c in components if 'LED' in c['lib_id']]
    resistors = [c for c in components if c['lib_id'] == 'Device:R']
    for led in leds:
        # Проверяем: есть ли R в цепи к LED
        connected_refs = graph.get_connected(led['ref'])
        has_resistor = any(r['ref'] in connected_refs for r in resistors)
        if not has_resistor:
            errors.append(f"LED {led['ref']} has no current-limiting resistor!")
    
    # Правило 2: MCU без питания
    mcus = [c for c in components if 'Arduino' in c['lib_id'] or 'ATmega' in c['lib_id']]
    for mcu in mcus:
        connected = graph.get_connected(mcu['ref'])
        has_power = any('PWR' in r or '+5V' in r for r in connected)
        has_gnd = any('GND' in r for r in connected)
        if not has_power:
            warnings.append(f"MCU {mcu['ref']} has no VCC connection")
        if not has_gnd:
            warnings.append(f"MCU {mcu['ref']} has no GND connection")
    
    # Правило 3: Незамкнутая цепь
    power_nodes = [c for c in components if '+5V' in c.get('lib_id', '')]
    gnd_nodes = [c for c in components if 'GND' in c.get('lib_id', '')]
    if power_nodes and gnd_nodes:
        # Проверяем что есть путь от +5V до GND через компоненты
        if not graph.path_exists(power_nodes[0]['ref'], gnd_nodes[0]['ref']):
            errors.append("Circuit is not complete: no path from +5V to GND")
    
    return ValidationResult(valid=len(errors)==0, errors=errors, warnings=warnings)
```

### Граф связности

```python
class ConnectivityGraph:
    """Graph of component connections built from wires and pin positions."""
    
    def __init__(self):
        self.adjacency: dict[str, set[str]] = {}  # ref → set of connected refs
    
    def add_connection(self, ref1: str, ref2: str):
        self.adjacency.setdefault(ref1, set()).add(ref2)
        self.adjacency.setdefault(ref2, set()).add(ref1)
    
    def get_connected(self, ref: str) -> set[str]:
        """Get all refs connected to this component (direct + transitive)."""
        visited = set()
        queue = [ref]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            queue.extend(self.adjacency.get(current, set()))
        return visited
    
    def path_exists(self, ref1: str, ref2: str) -> bool:
        return ref2 in self.get_connected(ref1)

def build_connectivity_graph(components, wires) -> ConnectivityGraph:
    """Build graph by matching wire endpoints to component pins."""
    reader = KiCadLibraryReader()
    graph = ConnectivityGraph()
    TOLERANCE = 1.27
    
    # Собираем все пины с глобальными координатами
    pin_map = []  # [(ref, global_x, global_y)]
    for comp in components:
        pins = reader.extract_pin_info(comp['lib_id'])
        for pin in pins:
            gx, gy = transform_pin(comp['x'], comp['y'], comp['rotation'], pin['x'], pin['y'])
            pin_map.append((comp['ref'], gx, gy))
    
    # Для каждого провода находим какие пины он соединяет
    for (wx1, wy1), (wx2, wy2) in wires:
        refs_at_start = [ref for ref, px, py in pin_map 
                         if abs(px-wx1) < TOLERANCE and abs(py-wy1) < TOLERANCE]
        refs_at_end = [ref for ref, px, py in pin_map 
                       if abs(px-wx2) < TOLERANCE and abs(py-wy2) < TOLERANCE]
        
        # Соединяем все пины на обоих концах провода
        for r1 in refs_at_start:
            for r2 in refs_at_end:
                if r1 != r2:
                    graph.add_connection(r1, r2)
    
    return graph
```

---

## TASK 2.3: Readability Score

### Метрики

| Метрика | Баллы | Как считать |
|---------|-------|-------------|
| Overlap | -20 за каждый | Bounding box overlap между компонентами |
| Spacing | -10 если < 5mm | Расстояние между центрами компонентов |
| Wire crossings | -5 за каждое | Пересечения проводов (segment intersection) |
| Grid alignment | -2 за каждый | Координаты не кратны 2.54mm (KiCad grid) |
| Total | 100 max | max(0, 100 - penalties) |

### Алгоритм

```python
def calculate_readability(schematic_path: Path) -> float:
    components = parse_components(schematic_path)
    wires = parse_wires(schematic_path)
    
    score = 100.0
    
    # 1. Проверка overlaps (bounding box)
    for i, c1 in enumerate(components):
        for c2 in components[i+1:]:
            if bounding_boxes_overlap(c1, c2):
                score -= 20
    
    # 2. Проверка spacing
    for i, c1 in enumerate(components):
        for c2 in components[i+1:]:
            dist = math.sqrt((c1['x']-c2['x'])**2 + (c1['y']-c2['y'])**2)
            if dist < 10:  # Слишком близко (< 10mm)
                score -= 10
    
    # 3. Wire crossings
    for i, w1 in enumerate(wires):
        for w2 in wires[i+1:]:
            if segments_intersect(w1[0], w1[1], w2[0], w2[1]):
                score -= 5
    
    # 4. Grid alignment (KiCad grid = 2.54mm)
    GRID = 2.54
    for comp in components:
        if abs(comp['x'] % GRID) > 0.01 or abs(comp['y'] % GRID) > 0.01:
            score -= 2
    
    return max(0.0, score)

def segments_intersect(p1, p2, p3, p4) -> bool:
    """Check if line segment p1-p2 intersects p3-p4."""
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    
    d1 = cross(p3, p4, p1)
    d2 = cross(p3, p4, p2)
    d3 = cross(p1, p2, p3)
    d4 = cross(p1, p2, p4)
    
    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
       ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return True
    return False

def bounding_boxes_overlap(c1, c2) -> bool:
    """Check if two component bounding boxes overlap."""
    # Примерные размеры компонентов (можно уточнить из библиотеки)
    SIZE = {'Device:R': (2, 8), 'Device:LED': (8, 5), 'Device:C': (2, 8)}
    DEFAULT_SIZE = (15, 30)  # Для Arduino и др.
    
    s1 = SIZE.get(c1['lib_id'], DEFAULT_SIZE)
    s2 = SIZE.get(c2['lib_id'], DEFAULT_SIZE)
    
    # Учёт поворота
    if c1['rotation'] == 90 or c1['rotation'] == 270:
        s1 = (s1[1], s1[0])
    if c2['rotation'] == 90 or c2['rotation'] == 270:
        s2 = (s2[1], s2[0])
    
    # AABB overlap
    return not (c1['x'] + s1[0]/2 < c2['x'] - s2[0]/2 or
                c1['x'] - s1[0]/2 > c2['x'] + s2[0]/2 or
                c1['y'] + s1[1]/2 < c2['y'] - s2[1]/2 or
                c1['y'] - s1[1]/2 > c2['y'] + s2[1]/2)
```

---

## TASK 2.4: Integration into generate_schematic()

### Файл: `src/pcba/schematic.py`, функция `generate_schematic()` (~строка 1107)

### Изменения:

```python
# ПОСЛЕ записи файла (output_path.write_text(content)):

from .circuit_validator import CircuitValidator

validator = CircuitValidator()

# Connectivity check
connectivity = validator.validate_connectivity(output_path)
if not connectivity.valid:
    print(f"\n  Connectivity issues:")
    for err in connectivity.errors:
        print(f"    - {err}")

# ERC check
erc = validator.validate_erc(output_path)
if not erc.valid:
    print(f"\n  ERC errors:")
    for err in erc.errors:
        print(f"    - {err}")
for warn in erc.warnings:
    print(f"    ! {warn}")

# Readability score
readability = validator.calculate_readability(output_path)
print(f"  Readability score: {readability:.0f}%")
```

---

## ПОЛНАЯ СТРУКТУРА ФАЙЛА `circuit_validator.py`

```python
"""
Circuit validation system for KiCad schematics.

Validates connectivity, electrical rules, and readability.
"""

import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .kicad_library import KiCadLibraryReader


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    score: float = 100.0


class ConnectivityGraph:
    # ... (код выше)


def parse_components(schematic_path: Path) -> list[dict]:
    # ... (код выше)

def parse_wires(schematic_path: Path) -> list[tuple]:
    # ... (код выше)

def transform_pin(comp_x, comp_y, comp_rotation, pin_x, pin_y):
    rad = math.radians(comp_rotation)
    gx = comp_x + pin_x * math.cos(rad) - pin_y * math.sin(rad)
    gy = comp_y + pin_x * math.sin(rad) + pin_y * math.cos(rad)
    return round(gx, 2), round(gy, 2)

def build_connectivity_graph(components, wires) -> ConnectivityGraph:
    # ... (код выше)


class CircuitValidator:
    """Main validator combining all checks."""
    
    def validate_connectivity(self, schematic_path: Path) -> ValidationResult:
        # ... (код выше)
    
    def validate_erc(self, schematic_path: Path) -> ValidationResult:
        # ... (код выше)
    
    def calculate_readability(self, schematic_path: Path) -> float:
        # ... (код выше)
    
    def validate_all(self, schematic_path: Path) -> dict:
        """Run all validators and return combined results."""
        return {
            'connectivity': self.validate_connectivity(schematic_path),
            'erc': self.validate_erc(schematic_path),
            'readability': self.calculate_readability(schematic_path),
        }
```

---

## ПОРЯДОК РЕАЛИЗАЦИИ

1. Создать `src/pcba/circuit_validator.py` с `ValidationResult` и helper-функциями
2. Реализовать `parse_components()` и `parse_wires()`
3. Реализовать `transform_pin()` и `build_connectivity_graph()`
4. Реализовать `validate_connectivity()`
5. Реализовать `validate_erc()`
6. Реализовать `calculate_readability()`
7. Добавить `CircuitValidator` с `validate_all()`
8. Интегрировать в `generate_schematic()`
9. Тестирование:
   ```bash
   python3 -c "
   from src.pcba.circuit_validator import CircuitValidator
   v = CircuitValidator()
   r = v.validate_all('/tmp/final_test.kicad_sch')
   print(r)
   "
   ```

---

## ТЕСТЫ

```bash
# Тест 1: Простая схема LED+R
pcba schematic "LED with 330 ohm resistor" -o /tmp/test_validate.kicad_sch
python3 -c "from src.pcba.circuit_validator import CircuitValidator; v=CircuitValidator(); print(v.validate_all(Path('/tmp/test_validate.kicad_sch')))"

# Тест 2: Arduino с LED
pcba schematic "Arduino with two LED on pin 5" -o /tmp/test_validate2.kicad_sch
python3 -c "from src.pcba.circuit_validator import CircuitValidator; v=CircuitValidator(); print(v.validate_all(Path('/tmp/test_validate2.kicad_sch')))"

# Ожидаемый результат:
# connectivity: valid=True (или warnings для неподключённых пинов Arduino)
# erc: valid=True, warnings=[] 
# readability: 80-100%
```
