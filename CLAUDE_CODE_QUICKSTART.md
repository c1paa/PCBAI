# 🚀 Как использовать промпт для Claude Code

## 📁 Файл готов!

**Файл:** `.claude_prompts/COMPLETE_SYSTEM_FIX_PLAN.md` (800+ строк)

---

## 🎯 ЧТО НУЖНО СДЕЛАТЬ

### 1. Открой Claude Code

Запусти в терминале проекта:
```bash
cd /Users/vladglazunov/Documents/algo/PCBAI
claude
```

Или открой через VS Code / другое IDE.

### 2. Отправь промпт

**Скопируй и отправь ЭТОТ текст:**

```
Прочитай файл .claude_prompts/COMPLETE_SYSTEM_FIX_PLAN.md

Твоя задача — реализовать ВСЁ что там описано, начиная с Phase 1 (критические исправления).

Главное:
1. Исправить Arduino symbol (сейчас "?")
2. Исправить соединения (сейчас нет проводов)
3. Реализовать Text → AI → Graph → Generator → KiCad pipeline
4. Добавить валидацию через kicad-cli

Начни с Phase 1. После каждого исправления:
- Закоммить изменения
- Протестируй с kicad-cli
- Убедись что символы отображаются

Вопросы задавай по мере реализации.
```

### 3. Claude Code начнет работу

Он будет:
1. **Анализировать** текущий код
2. **Исправлять** Phase 1 по приоритету
3. **Тестировать** с `kicad-cli`
4. **Коммитить** после каждого исправления

---

## ✅ ЧТО БУДЕТ ПОСЛЕ РЕАЛИЗАЦИИ

### Сейчас (сломано):
```bash
pcba schematic "Arduino with two LED"
# → 1 LED (не 2)
# → Arduino "?" (не отображается)
# → Нет соединений
```

### После (работает):
```bash
pcba schematic "Arduino with two LED"
# → 2 LED ✅
# → Arduino Uno symbol ✅
# → Все соединения ✅
# → kicad-cli validate passes ✅
```

---

## 📋 ПЛАН CLAUBE CODE (4 фазы)

### Phase 1: Критические исправления
- [ ] Arduino symbol fix
- [ ] Connections fix
- [ ] lib_symbols fix

### Phase 2: Graph Pipeline
- [ ] CircuitGraph class
- [ ] Generator integration
- [ ] Position calculation

### Phase 3: Project AI
- [ ] Project loader
- [ ] Design suggestions
- [ ] Iterative modification

### Phase 4: Testing
- [ ] kicad-cli validation
- [ ] End-to-end tests

---

## 🎯 КРИТЕРИИ УСПЕХА

После реализации:

```bash
# Тест 1: Два светодиода
pcba schematic "two LED with 330 ohm" -o test.kicad_sch
open test.kicad_sch
# → 2 LED, все соединено, нет "?"

# Тест 2: Arduino
pcba schematic "Arduino Uno with LED on pin 5" -o arduino.kicad_sch
open arduino.kicad_sch
# → Arduino symbol, LED подключен

# Тест 3: Валидация
kicad-cli sch export netlist test.kicad_sch -o /dev/null
# → No errors
```

---

## 🔧 ЕСЛИ ЧТО-ТО ИДЕТ НЕ ТАК

### Claude Code задаёт вопросы?
- Смотри детали в `COMPLETE_SYSTEM_FIX_PLAN.md`
- Там есть все спецификации и примеры

### Claude Code не может найти KiCad libraries?
```bash
# Проверь путь
ls /Applications/KiCad/KiCad.app/Contents/Share/kicad/symbols/

# Если нет KiCad — установи
brew install --cask kicad
```

### Тесты не проходят?
```bash
# Запусти тесты
pytest tests/ -v

# Смотри логи
cat tests/test_ai_analyzer.py
```

---

## 📞 СВЯЗЬ МЕЖДУ АГЕНТАМИ

После Claude Code реализует основную часть, можно подключить Qwen Code для:

**Qwen Code агенты:**
- **Planner** — планирует следующие задачи
- **Orchestrator** — координирует работу
- **Executor** — выполняет простые задачи
- **Debugger** — исправляет ошибки
- **DB Agent** — работает с базой компонентов

**Разделение задач:**
- **Claude Code:** Сложные задачи (AI, graph, generator)
- **Qwen Code:** Простые задачи (тесты, документация, рефакторинг)

---

## 🎯 ГЛАВНАЯ ЦЕЛЬ

**Рабочий продукт** где:
1. Пользователь пишет "two LED with Arduino"
2. AI понимает → 2 LED + Arduino
3. Generator создаёт → .kicad_sch с соединениями
4. KiCad открывает → все символы и провода на месте

**Задача Claude Code:** Реализовать это, начиная с Phase 1.

---

**ГОТОВО К ОТПРАВКЕ!** 🚀

Скопируй текст из раздела "2. Отправь промпт" и отправь в Claude Code.
