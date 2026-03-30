# Промпт для Claude Code: Генерация схем через LLM + SKiDL

## Задача

Создать модуль `schematic.py` для генерации схем KiCad из текстового описания.

## Требования

### Функционал

1. **LLM Integration**
   - Поддержка локальных LLM через Ollama API (http://localhost:11434)
   - Поддержка OpenAI API (опционально)
   - Генерация SKiDL кода из текстового описания

2. **SKiDL Generator**
   - Парсинг сгенерированного SKiDL кода
   - Исполнение кода в безопасном режиме
   - Генерация `.kicad_sch` файла

3. **Component Database**
   - Простая база популярных компонентов (резисторы, конденсаторы, LED, транзисторы, IC)
   - Маппинг названий на KiCad footprints

### Примеры использования

```python
from pcba.schematic import generate_schematic

# Простой пример
generate_schematic(
    description="LED connected to 3.3V through 330 ohm resistor to GND",
    output="led_circuit.kicad_sch"
)

# С параметрами
generate_schematic(
    description="Buck converter 5V to 3.3V, 1A output",
    output="buck.kicad_sch",
    voltage_in=5.0,
    voltage_out=3.3,
    current=1.0
)
```

### Промпт для LLM

```
You are an electronics engineer. Generate SKiDL Python code for the following circuit:

Description: {user_description}

Requirements:
- Use SKiDL library
- Include all necessary components
- Connect components correctly
- Output ONLY valid Python code with SKiDL imports
- No explanations, just code

Example format:
```python
from skidl import *

# Components
r1 = R(value='10k')
c1 = C(value='1uF')
gnd = GND()

# Connect
r1[1] & c1[1] & gnd

# Generate netlist
netlist('output.net')
```
```

### Структура модуля

```python
# src/pcba/schematic.py

class LLMGenerator:
    - generate_skidl(description: str) -> str
    
class SKiDLRunner:
    - execute(code: str) -> dict
    - save_kicad_sch(data: dict, filepath: str) -> None

def generate_schematic(description: str, output: str, **kwargs) -> Path:
    - Main entry point
```

### Зависимости

Добавить в `pyproject.toml`:
```toml
[project.dependencies]
skidl = "^0.1.0"  # Если есть в PyPI
# или использовать прямой парсинг
```

### Тесты

Создать `tests/test_schematic.py`:
- Тест на генерацию простой схемы (LED + резистор)
- Тест на парсинг SKiDL кода
- Mock для LLM API

## Ограничения

- SKiDL может отсутствовать в PyPI → использовать прямой парсинг S-выражений
- LLM может генерировать некорректный код → добавить валидацию
- Не все компоненты есть в базе → fallback на общие footprints

## Результат

Файл `src/pcba/schematic.py` с полным функционалом генерации схем.
