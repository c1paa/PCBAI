# PCBAI Project Status

## ✅ Готово

### Структура проекта
- [x] Directory structure (src/pcba, tests, examples, tools)
- [x] pyproject.toml с зависимостями
- [x] .gitignore
- [x] README.md
- [x] setup.sh / setup.bat

### Модули
- [x] `parser.py` - Парсер .kicad_pcb файлов
  - Чтение S-выражений
  - Извлечение footprints, tracks, vias, nets
  - Сохранение в .kicad_pcb
  
- [x] `exporter.py` - Экспорт в Spectra DSN
  - Генерация DSN формата
  - Маппинг слоёв KiCad → Spectra
  
- [x] `routing.py` - Интеграция FreeRouting
  - Скачивание FreeRouting JAR
  - Запуск из CLI
  - Импорт .ses обратно в .kicad_pcb
  
- [x] `cli.py` - CLI интерфейс
  - `pcba route <file>` - разводка
  - `pcba inspect <file>` - инспекция
  - `pcba download-freerouting` - скачать
  - `pcba check` - проверка системы

### Тесты
- [x] `tests/test_parser.py` - тесты парсера

### Примеры
- [x] `examples/simple_led.kicad_pcb` - тестовая плата

---

## 🔄 В работе

### Модуль генерации схем (schematic.py)
- [ ] LLM integration (Ollama API)
- [ ] SKiDL code generation
- [ ] Component database
- [ ] .kicad_sch generator

**Промпт для Claude Code:** `.claude_prompts/schematic_generation.md`

---

## ⏳ Планируется

### Улучшения
- [ ] Улучшенный парсер DSN/SES (более точный)
- [ ] Поддержка дифференциальных пар
- [ ] Length matching
- [ ] BGA fanout
- [ ] Power plane routing

### Интеграции
- [ ] Ollama API для локальных LLM
- [ ] OpenAI API (опционально)
- [ ] SKiDL библиотека
- [ ] KiCad Python API (pcbnew)

### Тесты
- [ ] integration tests с реальными платами
- [ ] test_schematic.py
- [ ] test_routing.py

### Документация
- [ ] API documentation
- [ ] Tutorial для начинающих
- [ ] Примеры использования

---

## 🚀 Как использовать сейчас

### 1. Установка
```bash
cd PCBAI
chmod +x setup.sh
./setup.sh  # macOS/Linux
# или
setup.bat  # Windows
```

### 2. Активация
```bash
source venv/bin/activate  # macOS/Linux
# или
venv\Scripts\activate  # Windows
```

### 3. Проверка
```bash
pcba check
pcba download-freerouting
```

### 4. Тест
```bash
pcba inspect examples/simple_led.kicad_pcb
pcba route examples/simple_led.kicad_pcb
```

---

## 📦 Зависимости

### Основные
- click>=8.1.0 - CLI framework
- sexpdata>=1.0.0 - S-expression parsing
- requests>=2.31.0 - HTTP requests (для LLM и скачивания)

### Для разработки
- pytest>=7.4.0 - тесты
- black>=23.0.0 - форматирование
- mypy>=1.5.0 - type checking

### Внешние
- Java (для FreeRouting)
- KiCad (опционально, для просмотра)
- Ollama (опционально, для LLM)

---

## 🎯 Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│  User: pcba route board.kicad_pcb                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  cli.py                                                     │
│  └─> routing.py: route_pcb()                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  parser.py: parse_pcb() → board_data                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  exporter.py: export_to_dsn() → board.dsn                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  routing.py: FreeRoutingRunner.run()                        │
│  └─> java -jar freerouting.jar -de board.dsn                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  routing.py: SESImporter.import_session()                   │
│  └─> board.ses → routed_tracks                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  parser.py: save_pcb() → board_routed.kicad_pcb             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Следующие шаги

1. **Запустить setup.sh** для установки зависимостей
2. **Протестировать `pcba inspect`** на примере
3. **Протестировать `pcba route`** (нужна Java)
4. **Создать schematic.py** (через Claude Code)
5. **Интегрировать LLM** для генерации схем
