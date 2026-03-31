# PCBAI - План по сбору 1000+ датасета

## 🎯 Цель

Собрать **1000+ пар** (описание → схема) для качественной тренировки T5 модели.

---

## 📊 Текущий статус

- **Есть:** 27 пар (мало)
- **Нужно:** 1000+ пар
- **Проблема:** GitHub API дает ~10-20 пар на 100 репозиториев

---

## 🔧 Инструменты

### 1. Скрипт для сбора

```bash
python scripts/collect_1000_dataset.py --limit 1000 --repos 200
```

**Проблемы:**
- GitHub API rate limit (10 запросов/мин без токена)
- Не все репозитории имеют .kicad_sch файлы
- Нужно парсить компоненты из схем

---

## 🚀 План действий

### Этап 1: Автоматический сбор (GitHub API)

```bash
# С токеном (больше лимитов)
python scripts/collect_1000_dataset.py \
  --output datasets/large_dataset.json \
  --limit 1000 \
  --repos 500
```

**Ожидаемо:** 50-100 пар за 1 час

### Этап 2: Ручной сбор (известные проекты)

Собрать с популярных KiCad проектов:

1. **Arduino** - https://github.com/arduino/Arduino
2. **ESP32** - https://github.com/espressif/arduino-esp32
3. **KiCad Library** - https://github.com/KiCad/kicad-library
4. **Adafruit** - https://github.com/adafruit
5. **SparkFun** - https://github.com/sparkfun

**Ожидаемо:** 100-200 пар

### Этап 3: Синтетические данные

Сгенерировать искусственные схемы:

```python
# Комбинировать компоненты
components = ['Arduino', 'LED', 'Resistor', 'Button', 'Sensor']
for combo in combinations(components, 2-5):
    generate_schematic(combo)
```

**Ожидаемо:** 500-700 пар

### Этап 4: Использование готовых датасетов

Поискать готовые датасеты:
- https://huggingface.co/datasets
- https://www.kaggle.com/datasets
- Academic papers

---

## 📈 Прогресс

| Источник | Ожидаемо | Реально | Статус |
|----------|----------|---------|--------|
| GitHub API | 100 | 0 | ⏳ Pending |
| Manual repos | 200 | 0 | ⏳ Pending |
| Synthetic | 700 | 0 | ⏳ Pending |
| **TOTAL** | **1000** | **0** | ⏳ **0%** |

---

## ⏱️ Время

- **Этап 1:** 1-2 часа (скрипт)
- **Этап 2:** 2-3 часа (ручной сбор)
- **Этап 3:** 1-2 часа (генерация)
- **Этап 4:** 1-2 часа (поиск)

**Итого:** 5-9 часов

---

## 🎯 Критерии успеха

- [ ] 1000+ уникальных пар
- [ ] JSON формат совместим с train.py
- [ ] Разнообразие схем (простые → сложные)
- [ ] Корректные описания

---

## 🔄 Следующие шаги

1. Запустить `collect_1000_dataset.py`
2. Проверить качество данных
3. Обновить Colab notebook
4. Переобучить модель

---

**Ready to start!**
