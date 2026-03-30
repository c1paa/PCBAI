# PCBAI — AI-Powered PCB Design Assistant

**PCBAI** — это интеллектуальный помощник для проектирования электронных схем в KiCad с использованием искусственного интеллекта.

## 🎯 Возможности

### ✅ Сейчас работает:
- **Генерация схем по описанию** — "LED with 330 ohm resistor"
- **Автоматическая разводка дорожек** — через FreeRouting
- **Инспекция PCB файлов** — анализ существующих плат
- **База знаний компонентов** — ATmega328P, DHT22, BMP280, MPU-6050

### 🔄 В разработке:
- **Диалоговый режим** — ИИ задаёт уточняющие вопросы
- **Поиск компонентов в интернете** — автоматическое добавление в базу
- **RAG архитектура** — умный поиск по базе знаний
- **Генерация символов** — создание новых символов KiCad

---

## 🚀 Быстрый старт

### 1. Установка

```bash
cd /Users/vladglazunov/Documents/algo/PCBAI

# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -e .
```

### 2. Настройка LLM API

**Вариант A: Puter.js (без ключа, безлимитно)**
```bash
# knowledge_base/config.json
{
  "default_provider": "puter"
}
```

**Вариант B: Google AI Studio (требуется ключ)**
1. Получить ключ: https://aistudio.google.com/app/apikey
2. Добавить в `knowledge_base/config.json`:
```json
{
  "default_provider": "google",
  "api_keys": {"google": "YOUR_KEY"}
}
```

**Вариант C: Ollama (локально, безлимитно)**
```bash
brew install ollama
ollama serve &
ollama pull llama3.2
```

См. подробную инструкцию в [API_SETUP.md](API_SETUP.md)

### 3. Генерация схемы

```bash
# Простая схема
pcba schematic "LED with 330 ohm resistor to 5V" -o led.kicad_sch

# Схема с микроконтроллером
pcba schematic "ATmega328P with DHT22 and BMP280" -o sensor_node.kicad_sch

# Открыть в KiCad
open led.kicad_sch
```

### 4. Разводка дорожек

```bash
# Создать PCB из схемы (в KiCad GUI)
# File → New → PCB → сохранить как led.kicad_pcb
# Tools → Update PCB from Schematic

# Автоматическая разводка
pcba route led.kicad_pcb

# Открыть результат
open led_routed.kicad_pcb
```

---

## 📋 Команды

| Команда | Описание | Пример |
|---------|----------|--------|
| `pcba dialog` | **Интерактивный диалог с AI** | `pcba dialog` |
| `pcba schematic "описание"` | Создать схему через AI | `pcba schematic "LED circuit"` |
| `pcba route <file>` | Развести дорожки | `pcba route board.kicad_pcb` |
| `pcba validate <file>` | **Проверить в KiCad** | `pcba validate schema.kicad_sch` |
| `pcba inspect <file>` | Показать информацию | `pcba inspect board.kicad_pcb` |
| `pcba check` | Проверка системы | `pcba check` |

---

## 🧠 Как это работает

### Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│  Пользователь: "ATmega328P с DHT22 и BMP280"                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  LLM Client (Google/Groq/Puter/Ollama)                      │
│  - Анализирует описание                                     │
│  - Извлекает компоненты                                     │
│  - Определяет интерфейсы                                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Knowledge Base (components.json)                           │
│  - Поиск компонентов                                        │
│  - Pinout, интерфейсы                                       │
│  - Правила проектирования                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Schematic Generator                                        │
│  - Генерация .kicad_sch в формате KiCad 9.0                 │
│  - Символы, компоненты, соединения                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  KiCad .kicad_sch файл                                      │
└─────────────────────────────────────────────────────────────┘
```

### Пример AI анализа

**Вход:** `"ATmega328P с DHT22 и BMP280"`

**AI извлекает:**
```json
{
  "components": [
    {"ref": "U1", "name": "ATmega328P", "category": "mcu"},
    {"ref": "D1", "name": "DHT22", "category": "sensor"},
    {"ref": "U2", "name": "BMP280", "category": "sensor"},
    {"ref": "R1", "type": "resistor", "value": "10k", "purpose": "DHT22 pullup"},
    {"ref": "R2", "type": "resistor", "value": "4.7k", "purpose": "I2C pullup"},
    {"ref": "C1", "type": "capacitor", "value": "100nF", "purpose": "decoupling"}
  ],
  "interfaces": ["I2C for BMP280", "1-wire for DHT22"],
  "power": {"positive": "+5V", "ground": "GND"}
}
```

**Результат:** Готовая `.kicad_sch` схема со всеми компонентами!

---

## 📁 Структура проекта

```
PCBAI/
├── src/pcba/
│   ├── cli.py              # CLI интерфейс
│   ├── schematic.py        # AI генератор схем
│   ├── parser.py           # Парсер .kicad_pcb
│   ├── exporter.py         # Экспорт в DSN
│   └── routing.py          # FreeRouting интеграция
│
├── knowledge_base/
│   ├── components.json     # База компонентов
│   ├── config.json         # Настройки LLM API
│   ├── generate_components.py  # Генератор базы через AI
│   └── README.md
│
├── examples/
│   ├── test1/              # Пример проекта
│   └── simple_led.kicad_pcb
│
├── tools/
│   └── freerouting.jar     # FreeRouting autorouter
│
├── tests/
├── README.md
├── API_SETUP.md            # Настройка API ключей
└── pyproject.toml
```

---

## 🗄️ База знаний

### Добавленные компоненты:

**Микроконтроллеры:**
- ✅ ATmega328P (Arduino Uno/Nano)

**Сенсоры:**
- ✅ DHT22 (температура/влажность)
- ✅ BMP280 (давление/температура)
- ✅ MPU-6050 (акселерометр/гироскоп)

**Пассивные компоненты:**
- ✅ Резисторы, конденсаторы, светодиоды

### Добавить новый компонент:

```bash
cd knowledge_base

# Отредактировать generate_components.py
# Добавить в COMPONENTS_TO_ADD:
COMPONENTS_TO_ADD = [
    "ESP32-WROOM-32",
    "HC-SR04 ultrasonic sensor",
    # ...
]

# Запустить генерацию
python generate_components.py
```

См. [knowledge_base/README.md](knowledge_base/README.md)

---

## 🔧 Настройка LLM API

### Рекомендуемые провайдеры:

| Провайдер | Модель | Лимиты | Ключ | Скорость |
|-----------|--------|--------|------|----------|
| **Puter.js** | Gemini | ∞ | ❌ | ⚡⚡ |
| **Google AI** | Gemini 2.0 | 15 RPM | ✅ | ⚡⚡⚡ |
| **Groq** | Llama 70B | 30 RPM | ✅ | ⚡⚡⚡⚡ |
| **Ollama** | Llama 3.2 | ∞ | ❌ | ⚡ |

**Быстрый старт (без ключа):**
```json
{
  "default_provider": "puter"
}
```

**Для продакшена:**
```json
{
  "default_provider": "google",
  "api_keys": {"google": "YOUR_KEY"}
}
```

Полная инструкция: [API_SETUP.md](API_SETUP.md)

---

## 🧪 Тестирование

### Тест 1: Простая схема
```bash
pcba schematic "LED with 330 ohm resistor" -o test1.kicad_sch
open test1.kicad_sch  # Должно открыться без ошибок
```

### Тест 2: Схема с MCU
```bash
pcba schematic "ATmega328P with DHT22" -o test2.kicad_sch
open test2.kicad_sch
```

### Тест 3: Разводка
```bash
pcba route examples/simple_led.kicad_pcb
open examples/simple_led_routed.kicad_pcb
```

---

## 📊 Roadmap

### Этап 1: База знаний ✅ (Март 2026)
- [x] JSON структура базы компонентов
- [x] Скрипт генерации через AI
- [x] Первые 4 компонента
- [ ] 20+ компонентов
- [ ] Веб-скрейпер для datasheet

### Этап 2: LLM API ✅ (Март 2026)
- [x] Мульти-провайдер клиент
- [x] Google AI Studio интеграция
- [x] Groq Cloud интеграция
- [x] Puter.js (без ключа)
- [x] Ollama локальная
- [ ] Автоматический fallback

### Этап 3: RAG + Диалог (Апрель 2026)
- [ ] ChromaDB векторная база
- [ ] Умный поиск компонентов
- [ ] Диалоговый режим
- [ ] Уточняющие вопросы

### Этап 4: Генерация символов (Май 2026)
- [ ] Парсинг существующих библиотек
- [ ] Генерация из pinout
- [ ] DRC проверка

### Этап 5: Тестирование (Июнь 2026)
- [ ] Юнит тесты
- [ ] Интеграционные тесты
- [ ] Валидация в KiCad

---

## 🤝 Вклад в проект

### Добавить компонент в базу:
1. Fork проекта
2. Добавить JSON в `knowledge_base/components.json`
3. Создать pull request

### Улучшить AI:
1. Предложить лучший prompt для анализа
2. Добавить поддержку новых интерфейсов
3. Улучшить генерацию символов

---

## 📚 Документация

- [API_SETUP.md](API_SETUP.md) — Настройка LLM API
- [knowledge_base/README.md](knowledge_base/README.md) — База компонентов
- [PROJECT_STATUS.md](PROJECT_STATUS.md) — Текущий статус
- [FINAL_STATUS.md](FINAL_STATUS.md) — Полное описание

---

## 📝 Лицензия

MIT License

---

## 💡 Примеры использования

### Пример 1: Датчик температуры
```bash
pcba schematic "DHT22 temperature sensor with ATmega328P" -o temp_sensor.kicad_sch
```

### Пример 2: Метеостанция
```bash
pcba schematic "Weather station with BMP280 and DHT22 on ESP32" -o weather.kicad_sch
```

### Пример 3: LED индикатор
```bash
pcba schematic "3 LEDs with current limiting resistors to 5V" -o leds.kicad_sch
```

---

## ⚠️ Ограничения

### Текущие:
- ❌ Нет диалогового режима (ИИ не задаёт вопросы)
- ❌ Ограниченная база компонентов (~4 шт)
- ❌ Нет поиска в интернете
- ❌ Простая генерация соединений

### Планируется:
- ✅ Диалоговый режим (Q2 2026)
- ✅ 50+ компонентов в базе (Q2 2026)
- ✅ Автоматический поиск datasheet (Q3 2026)
- ✅ Умная генерация соединений (Q2 2026)

---

## 📞 Поддержка

Вопросы и предложения: [GitHub Issues](https://github.com/yourusername/pcba/issues)
