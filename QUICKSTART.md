# PCBAI — Быстрый старт

## 📦 Установка и настройка

### 1. Установка PCBAI

```bash
cd /Users/vladglazunov/Documents/algo/PCBAI
source venv/bin/activate
```

### 2. Установка Ollama (для LLM)

**macOS:**
```bash
brew install ollama
```

**Запуск сервера:**
```bash
ollama serve &
```

**Скачать модель (первый раз):**
```bash
ollama pull llama3.2
```

**Проверка:**
```bash
curl http://localhost:11434/api/generate -d '{"model":"llama3.2","prompt":"hello"}'
```

---

## 🚀 Полный Workflow

### Шаг 1: Анализ существующего проекта (опционально)

Если у тебя есть старые схемы в KiCad папке:

```bash
# Анализируем проект для обучения ИИ
pcba analyze /path/to/your/kicad/project
```

**Пример:**
```bash
pcba analyze examples/test1
```

**Что делает:**
- Читает все `.kicad_sch` файлы
- Изучает какие компоненты ты используешь
- Запоминает стиль соединений
- Использует это при генерации новых схем

---

### Шаг 2: Генерация схемы через LLM

```bash
# Базовая команда
pcba schematic "LED with 330 ohm resistor to 3.3V" -o led.kicad_sch

# С анализом твоего проекта (ИИ учтёт твой стиль)
pcba schematic "Buck converter 5V to 3.3V 1A" \
    --project-dir examples/test1 \
    -o buck.kicad_sch
```

**Примеры описаний:**
- `"LED connected to 3.3V through 330 ohm current limiting resistor"`
- `"Voltage divider with two 10k resistors"`
- `"Common emitter NPN transistor amplifier with biasing resistors"`
- `"LM317 adjustable voltage regulator circuit"`
- `"NE555 timer in astable mode, 1kHz frequency"`

---

### Шаг 3: Редактирование в KiCad

```bash
# Открыть схему в KiCad
open led.kicad_sch  # macOS
# или через GUI KiCad
```

**Что делать:**
1. Проверить схему
2. При необходимости отредактировать
3. Расположить компоненты красиво
4. Сохранить

---

### Шаг 4: Создание PCB из схемы

В KiCad:
1. **File → New → PCB**
2. Сохранить как `led.kicad_pcb`
3. **Tools → Update PCB from Schematic**

Или через CLI (если есть схема):
```bash
# KiCad CLI (если установлен)
kicad-cli sch export netlist led.kicad_sch
```

---

### Шаг 5: Разводка дорожек

```bash
# Автоматическая разводка через FreeRouting
pcba route led.kicad_pcb

# Результат: led_routed.kicad_pcb с дорожками!
```

---

## 📋 Все команды PCBAI

| Команда | Описание |
|---------|----------|
| `pcba check` | Проверка системы (Java, FreeRouting) |
| `pcba download-freerouting` | Скачать FreeRouting |
| `pcba analyze <dir>` | Анализ KiCad проекта для обучения ИИ |
| `pcba schematic "описание"` | Создать схему через LLM |
| `pcba route <file>` | Развести дорожки |
| `pcba inspect <file>` | Показать информацию о PCB |

---

## 🧪 Примеры использования

### Пример 1: Простая LED схема

```bash
# 1. Генерация схемы
pcba schematic "LED with 330 ohm resistor to 3.3V" -o led.kicad_sch

# 2. Открыть в KiCad, сохранить как led.kicad_pcb
# 3. Разводка
pcba route led.kicad_pcb
```

### Пример 2: Buck converter с обучением на проекте

```bash
# 1. Анализ существующего проекта
pcba analyze examples/test1

# 2. Генерация с учётом стиля
pcba schematic "Buck converter 5V to 3.3V using LM2596" \
    --project-dir examples/test1 \
    -o buck.kicad_sch

# 3. Редактирование в KiCad
# 4. Разводка
pcba route buck.kicad_pcb
```

### Пример 3: Усложнённая схема

```bash
# Генерация схемы с несколькими компонентами
pcba schematic "
    Operational amplifier circuit with:
    - LM358 op-amp
    - Two 10k feedback resistors
    - 1uF input coupling capacitor
    - Single 5V supply
" -o opamp.kicad_sch
```

---

## 🔧 Ollama модели

**Рекомендуемые:**
- `llama3.2` — быстрая, хорошая для кода (рекомендую)
- `llama3.1` — более мощная
- `mistral` — альтернатива

**Скачать:**
```bash
ollama pull llama3.2
ollama pull llama3.1
```

**Использовать другую модель:**
```bash
pcba schematic "LED circuit" --model llama3.1 -o out.kicad_sch
```

---

## ❓ Частые вопросы

### Q: Ollama не запускается
```bash
# Проверить
ollama serve

# Если ошибка — переустановить
brew uninstall ollama
brew install ollama
```

### Q: LLM генерирует неверную схему
- Попробуй более подробное описание
- Используй `--project-dir` для обучения на своих схемах
- Попробуй другую модель (`--model llama3.1`)

### Q: Можно ли использовать без Ollama?
Да, но тогда схемы нужно создавать вручную в KiCad.
Ollama нужен только для `pcba schematic`.

### Q: Сколько нужно памяти для Ollama?
- Llama 3.2: ~2GB RAM
- Llama 3.1 8B: ~8GB RAM

---

## 📁 Структура проекта

```
PCBAI/
├── src/pcba/
│   ├── cli.py           # CLI команды
│   ├── analyzer.py      # Анализ схем
│   ├── schematic.py     # Генерация схем (LLM)
│   ├── parser.py        # Парсер PCB
│   ├── exporter.py      # Экспорт DSN
│   └── routing.py       # FreeRouting
├── examples/
│   ├── test1/           # Твой проект
│   └── simple_led.kicad_pcb
└── tools/
    └── freerouting.jar
```

---

## 🎯 Следующие шаги

1. ✅ Настроить Ollama
2. ✅ Протестировать `pcba analyze`
3. ✅ Протестировать `pcba schematic`
4. ✅ Протестировать `pcba route`
