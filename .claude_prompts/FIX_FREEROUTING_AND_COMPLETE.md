# PCBAI: Fix FreeRouting Integration & Complete Project

## Контекст

**PCBAI** — CLI инструмент для автоматизации PCB дизайна в KiCad.

**Проект:** `/Users/vladglazunov/Documents/algo/PCBAI`

**Структура:**
```
PCBAI/
├── src/pcba/
│   ├── __init__.py
│   ├── cli.py           # Click CLI (РАБОТАЕТ)
│   ├── parser.py        # Парсер .kicad_pcb (РАБОТАЕТ)
│   ├── exporter.py      # Экспорт в DSN (РАБОТАЕТ)
│   ├── routing.py       # FreeRouting интеграция (СЛОМАНО!)
│   └── schematic.py     # LLM генерация схем (НУЖНО СОЗДАТЬ)
├── tests/
├── examples/
│   └── simple_led.kicad_pcb  # Тестовая плата
├── tools/
│   └── freerouting.jar
├── pyproject.toml
└── README.md
```

---

## ✅ Что УЖЕ РАБОТАЕТ

1. **`pcba --help`** — CLI работает
2. **`pcba check`** — проверка системы (Java 21, FreeRouting)
3. **`pcba inspect examples/simple_led.kicad_pcb`** — показывает информацию о плате
4. **`pcba download-freerouting`** — скачивает FreeRouting JAR

---

## ❌ Что СЛОМАНО (ГЛАВНАЯ ПРОБЛЕМА)

### `pcba route examples/simple_led.kicad_pcb` — НЕ РАБОТАЕТ

**Проблема:** FreeRouting v2.1.0 не запускается в CLI/headless режиме.

**Текущая команда:**
```bash
java -Djava.awt.headless=true -jar freerouting.jar -c examples/simple_led.cmd
```

**Ошибка:**
```
ERROR: Both an input file and an output file must be specified with command line arguments if you are running in CLI mode.
```

**ИЛИ открывается GUI** вместо batch режима.

---

## 🎯 ЗАДАЧИ

### ЗАДАЧА 1: Исправить FreeRouting CLI интеграцию (КРИТИЧНО)

**Проблема:** FreeRouting v2.x изменил CLI интерфейс.

**Что нужно сделать:**

1. **Изучить документацию FreeRouting v2.1.0:**
   - https://github.com/freerouting/freerouting/releases/tag/v2.1.0
   - https://github.com/freerouting/freerouting/blob/master/README.md
   - Найти правильные CLI аргументы для batch режима

2. **Исправить `src/pcba/routing.py`:**
   - Метод `FreeRoutingRunner.run()` должен запускать FreeRouting БЕЗ GUI
   - Должен создавать .ses файл из .dsn
   - Должен работать с Java 21

3. **Возможные решения:**
   - Использовать stdin для передачи команд
   - Создать правильный command file (.cmd)
   - Использовать другие аргументы CLI
   - Если v2.x не работает — скачать старую версию (v1.x) которая работает с CLI

4. **Протестировать:**
   ```bash
   cd /Users/vladglazunov/Documents/algo/PCBAI
   source venv/bin/activate
   pcba route examples/simple_led.kicad_pcb
   ```
   
   **Ожидаемый результат:**
   - FreeRouting запускается без GUI
   - Создаётся `examples/simple_led.ses`
   - Создаётся `examples/simple_led_routed.kicad_pcb`

---

### ЗАДАЧА 2: Создать `schematic.py` — Генерация схем через LLM

**Спецификация:**

```python
# src/pcba/schematic.py

class OllamaClient:
    """Клиент для Ollama API (http://localhost:11434)"""
    - generate(prompt: str) -> str
    - check_available() -> bool

class SKiDLGenerator:
    """Генерация и парсинг SKiDL кода через AST"""
    - parse_skidl_code(code: str) -> dict
    - validate(parsed: dict) -> bool

class KiCadSchematicWriter:
    """Запись .kicad_sch файлов"""
    - write(parsed_data: dict, filepath: str) -> None

def generate_schematic(
    description: str,
    output: str,
    model: str = "llama3.2",
    ollama_url: str = "http://localhost:11434"
) -> Path:
    """Main entry point"""
```

**Требования:**
- Не исполнять код напрямую (безопасность) — использовать AST парсинг
- Поддержка Ollama API
- Генерация валидного `.kicad_sch` формата
- Component database (резисторы, конденсаторы, LED, IC)

**Интеграция в CLI:**
```python
@main.command()
@click.argument('description')
@click.option('-o', '--output', default='output.kicad_sch')
@click.option('--model', default='llama3.2')
def schematic(description: str, output: str, model: str):
    """Generate schematic from text description"""
```

**Тест:**
```bash
pcba schematic "LED with 330 ohm resistor to 3.3V" -o led.kicad_sch
```

---

### ЗАДАЧА 3: Финальное тестирование

После исправлений:

1. **Запустить полный workflow:**
   ```bash
   # 1. Генерация схемы
   pcba schematic "LED circuit with 3.3V power" -o led.kicad_sch
   
   # 2. Инспекция
   pcba inspect examples/simple_led.kicad_pcb
   
   # 3. Разводка
   pcba route examples/simple_led.kicad_pcb
   ```

2. **Проверить результаты:**
   - `examples/simple_led.dsn` — создан
   - `examples/simple_led.ses` — создан
   - `examples/simple_led_routed.kicad_pcb` — создан с дорожками

3. **Запустить тесты:**
   ```bash
   pytest tests/ -v
   ```

---

## 📁 Текущее состояние файлов

### `src/pcba/parser.py` — ✅ РАБОТАЕТ
- Парсит `.kicad_pcb` файлы
- Извлекает: version, general, layers, footprints, tracks, vias, netlist
- Сохраняет обратно в S-expression формат

### `src/pcba/exporter.py` — ✅ РАБОТАЕТ
- Экспортирует board_data в Spectra DSN формат
- Генерирует: image, structure, netlist, settings секции

### `src/pcba/routing.py` — ❌ СЛОМАНО
- `FreeRoutingRunner.run()` — неправильные CLI аргументы
- `SESImporter.import_session()` — не тестировалось
- Нужно исправить для FreeRouting v2.1.0

### `src/pcba/cli.py` — ✅ РАБОТАЕТ
- `pcba route` — вызывает routing.py
- `pcba inspect` — работает
- `pcba download-freerouting` — работает
- `pcba check` — работает
- Нужно добавить `pcba schematic`

### `src/pcba/schematic.py` — ❌ НЕ СУЩЕСТВУЕТ
- Нужно создать с нуля

---

## 🔧 Технические детали

### FreeRouting v2.1.0
- Скачан в: `/Users/vladglazunov/Documents/algo/PCBAI/tools/freerouting.jar`
- Требует Java 21
- CLI интерфейс изменился в v2.x

### Python окружение
- Python 3.10+
- venv: `/Users/vladglazunov/Documents/algo/PCBAI/venv`
- Установлено: click, sexpdata, requests

### Тестовая плата
- `examples/simple_led.kicad_pcb` — простая плата с 2 компонентами
- 2 footprint'а: Resistor_SMD:R_0805, LED_SMD:LED_0805
- 1 track, 1 via, 3 nets

---

## 📋 Чеклист для Claude Code

- [ ] Изучить FreeRouting v2.1.0 CLI документацию
- [ ] Исправить `routing.py` для работы с FreeRouting v2.1.0
- [ ] Протестировать `pcba route examples/simple_led.kicad_pcb`
- [ ] Убедиться что создаётся `.ses` и `.kicad_pcb` с дорожками
- [ ] Создать `schematic.py` с OllamaClient, SKiDLGenerator, KiCadSchematicWriter
- [ ] Добавить `pcba schematic` команду в `cli.py`
- [ ] Создать `tests/test_schematic.py`
- [ ] Запустить `pytest tests/ -v`
- [ ] Запустить полный workflow и убедиться что всё работает

---

## 🚀 Команды для тестирования

```bash
cd /Users/vladglazunov/Documents/algo/PCBAI
source venv/bin/activate

# Проверка системы
pcba check

# Тест разводки
pcba route examples/simple_led.kicad_pcb

# Тест генерации схемы (после создания schematic.py)
pcba schematic "LED with resistor" -o test.kicad_sch

# Тесты
pytest tests/ -v
```

---

## ⚠️ Важно

1. **FreeRouting должен работать БЕЗ GUI** — это критично для CLI инструмента
2. **Не исполнять SKiDL код напрямую** — использовать AST парсинг для безопасности
3. **Все изменения должны быть обратно совместимы** — не ломать существующий код
4. **После каждого изменения тестировать** — запускать команды выше

---

## 📞 Если что-то не работает

1. Проверить версию Java: `java -version` (должна быть 21)
2. Проверить FreeRouting: `ls -la tools/freerouting.jar`
3. Посмотреть логи FreeRouting в stderr
4. Попробовать запустить FreeRouting вручную:
   ```bash
   java -jar tools/freerouting.jar --help
   ```

---

## Ожидаемый результат после работы Claude Code

```bash
$ pcba route examples/simple_led.kicad_pcb
Exported to DSN: examples/simple_led.dsn
Java version: openjdk version "21.0.10"
Running FreeRouting: java -Djava.awt.headless=true -jar tools/freerouting.jar -c examples/simple_led.cmd
✓ Routing complete: examples/simple_led_routed.kicad_pcb

$ ls examples/
simple_led.kicad_pcb
simple_led.dsn
simple_led.ses
simple_led_routed.kicad_pcb  # ← С разведёнными дорожками!
```
