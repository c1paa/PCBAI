# PCBAI: Модуль генерации схем (schematic.py)

## Контекст проекта

PCBAI - это CLI инструмент для автоматизации проектирования PCB в KiCad.

**Структура проекта:**
```
PCBAI/
├── src/pcba/
│   ├── __init__.py
│   ├── cli.py           # Click CLI, уже есть
│   ├── parser.py        # Парсер .kicad_pcb, уже есть
│   ├── exporter.py      # Экспорт DSN, уже есть
│   ├── routing.py       # FreeRouting, уже есть
│   └── schematic.py     # ← ЭТО НУЖНО НАПИСАТЬ
├── tests/
├── examples/
└── pyproject.toml
```

**Существующие зависимости (pyproject.toml):**
```toml
dependencies = [
    "click>=8.1.0",
    "sexpdata>=1.0.0",
    "requests>=2.31.0",
]
```

---

## Задача

Написать `src/pcba/schematic.py` - модуль для генерации схем KiCad из текстового описания через LLM.

---

## Требования

### 1. Архитектура модуля

Модуль должен содержать 3 основных класса + 1 функция-обёртка:

```python
# src/pcba/schematic.py

class OllamaClient:
    """Клиент для локального LLM через Ollama API."""
    
class SKiDLGenerator:
    """Генерация и исполнение SKiDL кода."""
    
class KiCadSchematicWriter:
    """Запись .kicad_sch файла."""


def generate_schematic(
    description: str,
    output: str | Path,
    model: str = "llama3.2",
    ollama_url: str = "http://localhost:11434"
) -> Path:
    """Main entry point."""
```

---

### 2. OllamaClient

**Методы:**
- `__init__(self, url: str, model: str)`
- `generate(self, prompt: str) -> str` - отправить промпт, получить ответ
- `check_available(self) -> bool` - проверить, доступен ли сервер

**Промпт для LLM (встроенный):**
```
You are an electronics engineer expert in KiCad and SKiDL.
Generate SKiDL Python code for this circuit:

CIRCUIT DESCRIPTION:
{user_description}

REQUIREMENTS:
1. Use only SKiDL library imports (from skidl import *)
2. Define all components with correct values
3. Connect components using & operator
4. Include GND and power connections
5. Output ONLY Python code, no explanations
6. No markdown, no code blocks, just raw Python code

EXAMPLE OUTPUT FORMAT:
from skidl import *

# Circuit: {circuit_name}
R1 = R(value='10k')
C1 = C(value='1uF')
U1 = Part('Regulator', 'LM317')
GND = GND()

# Connections
VCC & R1[1]
R1[2] & C1[1] & U1['OUT']
C1[2] & GND
U1['GND'] & GND

END OF CODE
```

---

### 3. SKiDLGenerator

**Методы:**
- `__init__(self)`
- `parse_skidl_code(self, code: str) -> dict` - распарсить SKiDL код, вернуть структуру:
  ```python
  {
      'components': [
          {'ref': 'R1', 'value': '10k', 'footprint': 'Resistor_SMD:R_0805'},
          {'ref': 'C1', 'value': '1uF', 'footprint': 'Capacitor_SMD:C_0805'},
      ],
      'connections': [
          ['R1:1', 'C1:1', 'VCC'],
          ['R1:2', 'C1:2', 'GND'],
      ],
      'nets': ['VCC', 'GND', 'Net1'],
  }
  ```
- `validate(self, parsed: dict) -> bool` - проверить корректность
- **Важно:** Не исполнять код напрямую (безопасность), использовать парсинг AST

**Реализация через AST:**
```python
import ast

def parse_skidl_code(self, code: str) -> dict:
    tree = ast.parse(code)
    components = []
    connections = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            # R1 = R(value='10k')
            ...
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitAnd):
            # R1[1] & C1[1] & GND
            ...
    
    return {'components': components, 'connections': connections}
```

---

### 4. KiCadSchematicWriter

**Методы:**
- `__init__(self)`
- `write(self, parsed_data: dict, filepath: str | Path) -> None`

**Формат .kicad_sch (S-выражения):**
```lisp
(kicad_sch (version 20240108) (generator pcba)
  (lib_symbols
    (symbol "Resistor_SMD:R_0805" (pin_names (hide))
      (property "Reference" "R" (at 0 0))
      (property "Value" "10k" (at 0 5))
    )
  )
  (symbol (lib_id "Resistor_SMD:R_0805") (at 100 50)
    (unit 1) (in_bom yes) (on_board yes)
    (property "Reference" "R1" (at 100 45))
    (property "Value" "10k" (at 100 55))
    (pin "1" (uuid ...) (at 95 50))
    (pin "2" (uuid ...) (at 105 50))
  )
  (wire (pts (xy 100 50) (xy 120 50)) (net 1))
  (junction (at 120 50))
  (no_connect (at 80 60))
)
```

**Упрощённая реализация (для начала):**
- Генерировать минимальный валидный `.kicad_sch`
- Компоненты как `symbol` блоки
- Соединения как `wire` блоки
- UUID генерировать через `uuid.uuid4()`

---

### 5. generate_schematic() - main функция

**Сигнатура:**
```python
def generate_schematic(
    description: str,
    output: str | Path,
    model: str = "llama3.2",
    ollama_url: str = "http://localhost:11434",
    skip_llm: bool = False,  # Для тестов - использовать заглушку
) -> Path:
    """
    Generate KiCad schematic from text description.
    
    Args:
        description: Natural language circuit description
        output: Output .kicad_sch file path
        model: Ollama model name
        ollama_url: Ollama API URL
        skip_llm: If True, use test mode without LLM
    
    Returns:
        Path to generated .kicad_sch file
    
    Raises:
        RuntimeError: If LLM is not available
        ValueError: If generated code is invalid
    """
```

**Алгоритм:**
1. Проверить доступность Ollama
2. Сгенерировать промпт с описанием схемы
3. Получить SKiDL код от LLM
4. Распарсить код через AST
5. Валидировать структуру
6. Записать `.kicad_sch`
7. Вернуть путь к файлу

---

### 6. Обработка ошибок

```python
class SchematicGenerationError(Exception):
    """Base exception for schematic generation."""

class LLMUnavailableError(SchematicGenerationError):
    """Ollama server not available."""

class InvalidSKiDLCodeError(SchematicGenerationError):
    """Generated SKiDL code is invalid."""

class ComponentNotFoundError(SchematicGenerationError):
    """Component footprint not found in library."""
```

---

### 7. CLI интеграция

Добавить в `src/pcba/cli.py` новую команду:

```python
@main.command()
@click.argument('description')
@click.option('-o', '--output', type=click.Path(), default='output.kicad_sch')
@click.option('--model', default='llama3.2', help='Ollama model')
@click.option('--ollama-url', default='http://localhost:11434')
def schematic(description: str, output: str, model: str, ollama_url: str):
    """Generate schematic from text description.
    
    DESCRIPTION: Circuit description (e.g., "LED with 330Ω resistor to 3.3V")
    
    Example:
        pcba schematic "LED connected to 3.3V via 330 ohm resistor" -o led.kicad_sch
    """
    from .schematic import generate_schematic
    
    try:
        result = generate_schematic(description, output, model, ollama_url)
        click.echo(click.style(f'✓ Schematic generated: {result}', fg='green'))
    except Exception as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'), err=True)
        raise SystemExit(1)
```

---

### 8. Тесты

Создать `tests/test_schematic.py`:

```python
import pytest
from pcba.schematic import (
    OllamaClient,
    SKiDLGenerator,
    KiCadSchematicWriter,
    generate_schematic,
)

class TestSKiDLGenerator:
    def test_parse_simple_circuit(self):
        code = """
from skidl import *
R1 = R(value='10k')
C1 = C(value='1uF')
R1[1] & C1[1]
"""
        gen = SKiDLGenerator()
        result = gen.parse_skidl_code(code)
        assert len(result['components']) == 2
        assert result['components'][0]['ref'] == 'R1'

class TestKiCadSchematicWriter:
    def test_write_minimal_sch(self, tmp_path):
        data = {
            'components': [{'ref': 'R1', 'value': '10k'}],
            'connections': [],
        }
        writer = KiCadSchematicWriter()
        output = tmp_path / 'test.kicad_sch'
        writer.write(data, output)
        assert output.exists()
        content = output.read_text()
        assert '(kicad_sch' in content

class TestGenerateSchematic:
    def test_generate_with_mock_llm(self, tmp_path, monkeypatch):
        # Mock LLM response
        def mock_generate(self, prompt):
            return "from skidl import *\nR1 = R(value='10k')"
        
        monkeypatch.setattr(OllamaClient, 'generate', mock_generate)
        
        result = generate_schematic(
            "10k resistor",
            tmp_path / 'test.kicad_sch',
            skip_llm=True
        )
        assert result.exists()
```

---

### 9. Component Database

Создать простой словарь популярных компонентов:

```python
# В начале файла schematic.py

COMPONENT_FOOTPRINTS = {
    'R': 'Resistor_SMD:R_0805',
    'C': 'Capacitor_SMD:C_0805',
    'L': 'Inductor_SMD:L_0805',
    'D': 'Diode_SMD:D_SOD-323',
    'LED': 'LED_SMD:LED_0805',
    'Q': 'Package_TO_SOT_SMD:SOT-23',
    'U': 'Package_SO:SOIC-8',
    'GND': 'Power:GND',
    'VCC': 'Power:VCC',
}

COMMON_ICs = {
    'LM317': ('Regulator', 'Package_TO_SOT_SMD:SOT-223'),
    'NE555': ('Timer', 'Package_DIP:DIP-8'),
    'ATmega328P': ('MCU', 'Package_QFP:TQFP-32'),
    'AMS1117': ('LDO', 'Package_TO_SOT_SMD:SOT-223'),
}
```

---

### 10. Зависимости

Добавить в `pyproject.toml` (опционально, для тестов):

```toml
[project.optional-dependencies]
schematic = [
    "skidl>=0.1.0",  # Если доступен
]
dev = [
    "pytest>=7.4.0",
    "black>=23.0.0",
    "mypy>=1.5.0",
]
```

---

## Ожидаемый результат

После реализации:

```bash
# Проверка Ollama
pcba check
# → Ollama: ✓ http://localhost:11434

# Генерация схемы
pcba schematic "LED with 330 ohm resistor to 3.3V" -o led.kicad_sch

# Результат
✓ Schematic generated: led.kicad_sch

# Открыть в KiCad
open led.kicad_sch  # macOS
```

---

## Ограничения (документировать в README)

1. **Требуется Ollama** - локальный LLM сервер
2. **Модель llama3.2** (или другая, поддерживающая код)
3. **Упрощённый парсинг** - не весь SKiDL поддерживается
4. **Без исполнения кода** - только AST парсинг для безопасности

---

## Ссылки

- Ollama API: https://github.com/ollama/ollama/blob/main/docs/api.md
- SKiDL: https://github.com/devbisme/skidl
- KiCad S-expr format: https://dev-docs.kicad.org/en/file-formats/
- Python AST: https://docs.python.org/3/library/ast.html

---

## Инструкция по запуску

```bash
# 1. Установить Ollama (если нет)
brew install ollama

# 2. Запустить сервер
ollama serve &

# 3. Скачать модель
ollama pull llama3.2

# 4. Тестировать
curl http://localhost:11434/api/generate -d '{"model":"llama3.2","prompt":"hello"}'

# 5. Использовать PCBAI
pcba schematic "LED circuit" -o test.kicad_sch
```
