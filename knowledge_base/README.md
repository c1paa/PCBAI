# PCBAI Knowledge Base

База знаний компонентов для AI-генератора схем.

## 📁 Структура

```
knowledge_base/
├── components.json       # Основная база компонентов
├── rules.json            # Правила проектирования
├── generate_components.py # Скрипт генерации через AI
└── README.md             # Этот файл
```

## 🔧 Использование

### Генерация компонентов через AI

1. **Выберите провайдер:**
   - `google` — Gemini 2.0 Flash (бесплатно, 15 RPM)
   - `groq` — Llama 3.1 70B (бесплатно, 30 RPM)
   - `ollama` — Локальная Llama 3.2 (безлимитно)
   - `puter` — Gemini через Puter.js (безлимитно)

2. **Запустите генератор:**

```bash
cd knowledge_base

# Отредактируйте generate_components.py
# Укажите PROVIDER и API_KEY (если нужен)

# Запуск
python generate_components.py
```

3. **Компоненты для добавления:**

В скрипте указан список `COMPONENTS_TO_ADD`. Добавьте свои:

```python
COMPONENTS_TO_ADD = [
    "ESP32-WROOM-32",
    "Arduino Nano",
    "Raspberry Pi Pico",
    "STM32F103C8T6",
    # Ваши компоненты...
]
```

## 📊 Формат компонента

```json
{
  "id": "mcu_atmega328p",
  "name": "ATmega328P",
  "category": "microcontroller",
  "description": "8-bit AVR microcontroller",
  
  "package": {
    "type": "TQFP-32",
    "kiCad_footprint": "Package_QFP:TQFP-32_7x7mm_P0.8mm"
  },
  
  "kiCad_lib_id": "MCU_Microchip_ATmega:ATmega328P",
  
  "pins": [
    {"num": 1, "name": "PD3", "functions": ["GPIO", "INT1"]}
  ],
  
  "power": {
    "voltage_min": 1.8,
    "voltage_max": 5.5,
    "voltage_typical": 5.0
  },
  
  "interfaces": {
    "UART": {"count": 1, "pins": {"TX": "PD1", "RX": "PD0"}},
    "I2C": {"count": 1, "pins": {"SDA": "PC4", "SCL": "PC5"}}
  },
  
  "design_rules": [
    {
      "rule": "decoupling_capacitor",
      "description": "Place 100nF capacitor near VCC",
      "components": [{"type": "capacitor", "value": "100nF"}]
    }
  ]
}
```

## 🎯 Уже добавленные компоненты

### Микроконтроллеры
- ✅ ATmega328P

### Сенсоры
- ✅ DHT22 (температура/влажность)
- ✅ BMP280 (давление/температура)
- ✅ MPU-6050 (акселерометр/гироскоп)

### Пассивные компоненты
- ✅ Резисторы (default footprints)
- ✅ Конденсаторы (default footprints)
- ✅ Светодиоды (default footprints)

## 📝 Получение API ключей

### Google AI Studio (Gemini)
1. https://aistudio.google.com/app/apikey
2. Create API key
3. Копируйте ключ в `generate_components.py`

### Groq Cloud
1. https://console.groq.com/keys
2. Create API key
3. Копируйте ключ в `generate_components.py`

### Ollama (локально)
```bash
# Установка
brew install ollama

# Запуск
ollama serve &

# Скачать модель
ollama pull llama3.2
```

### Puter.js (без ключа)
Ничего не нужно, работает без регистрации!

## 🚀 Следующие шаги

1. Запустить генератор для добавления 10-20 компонентов
2. Проверить сгенерированные данные
3. Добавить правила проектирования в `rules.json`
4. Интегрировать с AI-генератором схем
