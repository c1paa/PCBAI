# Как использовать Claude Code для AI Enhancement

## 📋 Промпт готов!

Файл: `.claude_prompts/AI_CIRCUIT_ANALYSIS_ENHANCEMENT.md`

## 🚀 Как запустить

### Вариант 1: Claude Code (рекомендуется)

1. **Открой Claude Code**
2. **Скопируй промпт** из файла `.claude_prompts/AI_CIRCUIT_ANALYSIS_ENHANCEMENT.md`
3. **Отправь промпт** полностью

**Пример команды:**
```
Прочитай файл .claude_prompts/AI_CIRCUIT_ANALYSIS_ENHANCEMENT.md
и реализуй все описанные функции:
1. CircuitAnalyzer с извлечением количества компонентов
2. ConnectionGenerator для series/parallel соединений
3. Enhanced Dialog Manager
4. Интеграцию в schematic.py
```

### Вариант 2: По частям

Если Claude Code не может обработать весь промпт сразу, разбей на части:

**Часть 1: AI Analyzer**
```
Реализуй ai_analyzer.py с функциями:
- analyze(description: str) -> dict
- _expand_quantities(components: list) -> list
- _parse_json_response(response: str) -> dict

Используй промпт из .claude_prompts/AI_CIRCUIT_ANALYSIS_ENHANCEMENT.md
```

**Часть 2: Connection Generator**
```
Реализуй circuit_generator.py с функциями:
- generate_series_connections()
- generate_parallel_connections()
- generate_custom_connections()
```

**Часть 3: Интеграция**
```
Обнови schematic.py для использования нового AI анализатора
```

## ✅ Что будет реализовано

После выполнения промпта:

```bash
# Сейчас (ограниченно):
pcba schematic "two LED"  # → 1 LED

# После (полная поддержка):
pcba schematic "two LED with 330 ohm resistor"  # → 2 LED + 1 R
pcba schematic "three resistors as pull-ups"    # → 3 R
pcba schematic "LED in series"                  # → series connection
pcba schematic "LED in parallel"                # → parallel connection
```

## 🎯 Примеры тестов

После реализации:

```python
# Тест 1: Два светодиода
result = analyze("two LED with 330 ohm resistor")
assert len(result['components']) == 3  # 2 LED + 1 R

# Тест 2: Три резистора
result = analyze("three 10k resistors")
assert len(result['components']) == 3  # 3 R

# Тест 3: Диалог
result = analyze("LED with resistor")
assert len(result['questions']) > 0  # Ask for clarification
```

## 📁 Файлы которые будут созданы

```
src/pcba/
├── ai_analyzer.py         # Новый: AI анализ
├── circuit_generator.py   # Новый: Генерация соединений
├── dialog_enhanced.py     # Новый: Улучшенный диалог
└── schematic.py           # Обновлённый: интеграция
```

## 🔧 Если что-то не работает

1. **Проверь что Ollama запущен:**
   ```bash
   ollama serve
   ```

2. **Проверь модель:**
   ```bash
   ollama run llama3.2 "Hello"
   ```

3. **Тестируй по частям:**
   - Сначала ai_analyzer.py
   - Потом circuit_generator.py
   - Потом интеграцию

## 📞 Поддержка

Если Claude Code задаёт вопросы:
- Смотри детали в `.claude_prompts/AI_CIRCUIT_ANALYSIS_ENHANCEMENT.md`
- Все примеры кода там есть
- Все тесты описаны

---

**Готово к использованию!** 🚀
