# Настройка LLM API для PCBAI

## 📋 Обзор

PCBAI использует LLM (Large Language Models) для:
- Анализа описания схемы
- Извлечения компонентов и их параметров
- Генерации структуры схемы

## 🔑 Бесплатные API провайдеры

### 1. Google AI Studio (Gemini) — РЕКОМЕНДУЕТСЯ

**Лимиты:** 15 запросов/минуту, 1M токенов/месяц

**Получение ключа:**
1. Перейти на https://aistudio.google.com/app/apikey
2. Войти через Google аккаунт
3. Нажать "Create API Key"
4. Скопировать ключ

**Настройка:**
```bash
cd /Users/vladglazunov/Documents/algo/PCBAI/knowledge_base

# Отредактировать config.json
nano config.json

# Добавить ключ:
{
  "llm_providers": {
    "google": {
      "enabled": true,
      "api_key": "ВАШ_КЛЮЧ_ЗДЕСЬ"
    }
  }
}
```

**Тест:**
```bash
python -c "from knowledge_base.generate_components import LLMClient; c = LLMClient('google', 'ВАШ_КЛЮЧ'); print(c.generate('Hello'))"
```

---

### 2. Groq Cloud (Llama 3.1 70B)

**Лимиты:** 30 запросов/минуту, 6000 запросов/день

**Получение ключа:**
1. Перейти на https://console.groq.com/keys
2. Зарегистрироваться
3. Создать API key
4. Скопировать ключ

**Настройка:**
```json
{
  "llm_providers": {
    "groq": {
      "enabled": true,
      "api_key": "ВАШ_КЛЮЧ_GROQ"
    }
  }
}
```

---

### 3. Puter.js (Gemini) — БЕЗ КЛЮЧА

**Лимиты:** Безлимитно (free tier)

**Настройка:** Не требуется! Работает без API ключа.

```json
{
  "llm_providers": {
    "puter": {
      "enabled": true
    }
  },
  "default_provider": "puter"
}
```

---

### 4. Ollama (Локально) — БЕЗ ЛИМИТОВ

**Лимиты:** Нет (локальный запуск)

**Установка на macOS:**
```bash
# Установка через Homebrew
brew install ollama

# Запуск сервера
ollama serve &

# Скачать модель
ollama pull llama3.2

# Проверка
ollama run llama3.2 "Привет!"
```

**Настройка:**
```json
{
  "llm_providers": {
    "ollama": {
      "enabled": true,
      "model": "llama3.2"
    }
  },
  "default_provider": "ollama"
}
```

---

## 🎯 Рекомендуемая конфигурация

Для начала используйте **Puter.js** (без ключа, безлимитно):

```json
{
  "default_provider": "puter",
  "fallback_provider": "ollama",
  "llm_providers": {
    "google": {"enabled": false, "api_key": ""},
    "groq": {"enabled": false, "api_key": ""},
    "ollama": {"enabled": false},
    "puter": {"enabled": true}
  }
}
```

Для продакшена используйте **Google AI Studio** (быстро, надёжно):

```json
{
  "default_provider": "google",
  "fallback_provider": "puter",
  "llm_providers": {
    "google": {"enabled": true, "api_key": "YOUR_KEY"},
    "groq": {"enabled": true, "api_key": "YOUR_KEY"},
    "ollama": {"enabled": false},
    "puter": {"enabled": true}
  }
}
```

---

## 🧪 Тестирование

### Тест 1: Простая схема
```bash
cd /Users/vladglazunov/Documents/algo/PCBAI
source venv/bin/activate

pcba schematic "LED with 330 ohm resistor" -o test_led.kicad_sch
open test_led.kicad_sch
```

### Тест 2: Схема с MCU
```bash
pcba schematic "ATmega328P with DHT22 sensor" -o test_mcu.kicad_sch
open test_mcu.kicad_sch
```

### Тест 3: Несколько компонентов
```bash
pcba schematic "ESP32 with BMP280 and OLED display" -o test_esp.kicad_sch
open test_esp.kicad_sch
```

---

## ❓ Troubleshooting

### Ошибка: "All LLM providers failed"

**Причина:** Не настроен API ключ или не запущен Ollama.

**Решение:**
1. Проверьте `knowledge_base/config.json`
2. Убедитесь что `default_provider` имеет valid ключ
3. Или используйте `puter` (не требует ключа)

### Ошибка: "Could not parse JSON"

**Причина:** LLM вернул некорректный JSON.

**Решение:** Попробовать другую модель:
```python
# В generate_schematic() изменить prompt
# Или использовать другой provider
```

### Ollama слишком медленная

**Решение:** Использовать облачный API (Google/Groq).

---

## 📊 Сравнение провайдеров

| Провайдер | Модель | Скорость | Качество | Лимиты | Ключ |
|-----------|--------|----------|----------|--------|------|
| Google | Gemini 2.0 | ⚡⚡⚡ | ⭐⭐⭐⭐ | 15 RPM | ✅ |
| Groq | Llama 70B | ⚡⚡⚡⚡ | ⭐⭐⭐⭐⭐ | 30 RPM | ✅ |
| Puter | Gemini | ⚡⚡ | ⭐⭐⭐ | ∞ | ❌ |
| Ollama | Llama 3.2 | ⚡ | ⭐⭐ | ∞ | ❌ |

---

## 🚀 Следующие шаги

1. Настроить API ключ (рекомендуется Google или Puter)
2. Протестировать генерацию простых схем
3. Добавить компоненты в базу знаний
4. Интегрировать с диалоговым режимом
