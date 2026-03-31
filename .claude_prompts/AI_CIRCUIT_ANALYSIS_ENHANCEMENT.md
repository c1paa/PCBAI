# PCBAI: AI Circuit Analysis Enhancement

## Задача

Реализовать **полноценный AI-анализ** описания схемы чтобы ИИ понимал:
1. **Количество компонентов** ("two LED" = 2 светодиода)
2. **Тип соединения** (последовательно/параллельно)
3. **Конкретные пины** для подключения
4. **Диалог с пользователем** для уточнения деталей

## Текущая Проблема

**Вход:** `"two LED with 330 ohm resistor to Arduino pin 5"`  
**Текущий результат:** 1 LED, 1 резистор  
**Ожидаемый результат:** 2 LED, 1 резистор, правильное соединение

## Требования

### 1. AI Circuit Analyzer (LLM + Ollama)

**Функция:** `analyze_circuit_description(description: str) -> dict`

**Что должна делать:**
- Извлекать **количество** каждого компонента
- Определять **тип соединения** (series/parallel)
- Извлекать **значения** компонентов
- Определять **подключение к МК** (какой пин)
- Задавать **уточняющие вопросы** если что-то непонятно

**Пример входа:**
```
"two LED with 330 ohm resistor to Arduino pin 5"
```

**Пример выхода (JSON):**
```json
{
  "circuit_type": "led_array",
  "components": [
    {
      "ref": "LED1",
      "type": "led",
      "value": "RED",
      "footprint": "LED_SMD:LED_0805",
      "quantity": 1
    },
    {
      "ref": "LED2",
      "type": "led",
      "value": "RED",
      "footprint": "LED_SMD:LED_0805",
      "quantity": 1
    },
    {
      "ref": "R1",
      "type": "resistor",
      "value": "330",
      "footprint": "Resistor_SMD:R_0805",
      "quantity": 1
    }
  ],
  "connections": [
    {
      "from": "Arduino:Pin5",
      "to": "R1:1",
      "net": "Net_Arduino_Pin5"
    },
    {
      "from": "R1:2",
      "to": "LED1:A",
      "net": "Net_R1_LED1"
    },
    {
      "from": "LED1:K",
      "to": "LED2:A",
      "net": "Net_LED1_LED2"
    },
    {
      "from": "LED2:K",
      "to": "GND",
      "net": "GND"
    }
  ],
  "power": {
    "positive": "+5V",
    "ground": "GND"
  },
  "questions": [],
  "configuration": "series"
}
```

### 2. Enhanced LLM Prompt

**Использовать Ollama/Gemini с правильным промптом:**

```
Ты опытный инженер-электронщик. Твоя задача - проанализировать описание схемы и извлечь ВСЮ информацию.

ВХОДНЫЕ ДАННЫЕ:
Пользователь описывает схему естественным языком.

ТВОЯ ЗАДАЧА:
1. Извлечь КАЖДЫЙ компонент с количеством
2. Определить значения компонентов
3. Определить тип соединения (последовательно/параллельно)
4. Определить подключения к микроконтроллеру
5. Задать уточняющие вопросы если что-то непонятно

ПРАВИЛА ИЗВЛЕЧЕНИЯ КОЛИЧЕСТВА:
- "two LED" = 2 светодиода
- "3 resistors" = 3 резистора
- "LED" (без числа) = 1 светодиод
- "a LED" = 1 светодиод
- "an LED" = 1 светодиод

ПРАВИЛА СОЕДИНЕНИЯ:
- Если несколько LED без указания типа соединения → предложить параллельное
- Если "in series" → последовательное
- Если "in parallel" → параллельное

ФОРМАТ ОТВЕТА (ТОЛЬКО JSON, без markdown):
{
  "components": [
    {
      "ref": "LED1",
      "type": "led",
      "value": "RED",
      "footprint": "LED_SMD:LED_0805",
      "quantity": 1,
      "pins": {
        "A": "anode",
        "K": "cathode"
      }
    }
  ],
  "connections": [
    {
      "from": "component:pin",
      "to": "component:pin",
      "net": "net_name"
    }
  ],
  "configuration": "series|parallel|custom",
  "questions": ["What color are the LEDs?"],
  "power": {"positive": "+5V", "ground": "GND"}
}

ПРИМЕР ВХОДА:
"two LED with 330 ohm resistor to Arduino pin 5"

ПРИМЕР ВЫХОДА:
{
  "components": [
    {"ref": "R1", "type": "resistor", "value": "330", "quantity": 1},
    {"ref": "LED1", "type": "led", "value": "RED", "quantity": 1},
    {"ref": "LED2", "type": "led", "value": "RED", "quantity": 1}
  ],
  "connections": [
    {"from": "Arduino:Pin5", "to": "R1:1"},
    {"from": "R1:2", "to": "LED1:A"},
    {"from": "LED1:K", "to": "LED2:A"},
    {"from": "LED2:K", "to": "GND"}
  ],
  "configuration": "series",
  "questions": [],
  "power": {"positive": "+5V", "ground": "GND"}
}

ТЕПЕРЬ ПРОАНАЛИЗИРУЙ:
{user_description}
```

### 3. Component Instance Generator

**Функция:** `generate_component_instances(ai_analysis: dict) -> list[dict]`

**Что должна делать:**
- Создавать **нужное количество** экземпляров каждого компонента
- Генерировать **уникальные ref** (LED1, LED2, R1, R2...)
- Расставлять **правильные значения**
- Создавать **правильные подключения**

**Пример:**
```python
# Вход от AI
{
  "components": [
    {"type": "led", "quantity": 2, "value": "RED"}
  ]
}

# Выход
[
  {"ref": "LED1", "type": "led", "value": "RED", ...},
  {"ref": "LED2", "type": "led", "value": "RED", ...}
]
```

### 4. Connection Router

**Функция:** `generate_connections(components: list, configuration: str) -> list[dict]`

**Что должна делать:**
- Автоматически генерировать соединения на основе конфигурации
- Для **series**: R1 → LED1 → LED2 → GND
- Для **parallel**: R1 → (LED1 || LED2) → GND
- Для **custom**: использовать явные подключения от AI

### 5. Dialog Manager Enhancement

**Функция:** `ask_clarifying_questions(questions: list) -> dict`

**Что должна делать:**
- Задавать вопросы пользователю в диалоге
- Сохранять ответы
- Обновлять анализ на основе ответов

**Пример диалога:**
```
AI: How should the 2 LEDs be connected?
    1) In series (one after another)
    2) In parallel (side by side)
    
You: 1

AI: What color are the LEDs?
    1) Red
    2) Green
    3) Blue
    4) White
    
You: 1

AI: Generating schematic with 2 red LEDs in series...
```

## Реализация

### Файловая структура:
```
src/pcba/
├── ai_analyzer.py         # Новый файл: AI анализ
├── circuit_generator.py   # Новый файл: Генерация соединений
├── dialog_enhanced.py     # Новый файл: Улучшенный диалог
└── schematic.py           # Обновить: использовать новый анализ
```

### ai_analyzer.py:
```python
import json
import re
from typing import Any
from .llm_client import LLMClient

class CircuitAnalyzer:
    def __init__(self, llm_client: LLMClient):
        self.client = llm_client
        self.prompt_template = """..."""  # Промпт выше
    
    def analyze(self, description: str) -> dict[str, Any]:
        """Analyze circuit description and return structured data."""
        prompt = self.prompt_template.format(user_description=description)
        response = self.client.generate(prompt)
        
        # Parse JSON from response
        analysis = self._parse_json_response(response)
        
        # Expand components by quantity
        analysis['components'] = self._expand_quantities(analysis['components'])
        
        return analysis
    
    def _expand_quantities(self, components: list[dict]) -> list[dict]:
        """Expand components with quantity > 1 into individual instances."""
        expanded = []
        counters = {}  # LED -> 2, R -> 1, etc.
        
        for comp in components:
            quantity = comp.get('quantity', 1)
            comp_type = comp.get('type', 'unknown')
            
            # Initialize counter
            if comp_type not in counters:
                counters[comp_type] = 0
            
            # Create 'quantity' instances
            for i in range(quantity):
                counters[comp_type] += 1
                instance = comp.copy()
                instance['ref'] = f"{comp_type.upper()}{counters[comp_type]}"
                instance['quantity'] = 1
                expanded.append(instance)
        
        return expanded
    
    def _parse_json_response(self, response: str) -> dict:
        """Extract JSON from LLM response."""
        # Find JSON in response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {}
```

### circuit_generator.py:
```python
from typing import Any

class ConnectionGenerator:
    def generate_connections(
        self,
        components: list[dict],
        configuration: str,
        mcu_pin: str | None = None
    ) -> list[dict]:
        """Generate connections based on configuration."""
        
        if configuration == 'series':
            return self._generate_series_connections(components, mcu_pin)
        elif configuration == 'parallel':
            return self._generate_parallel_connections(components, mcu_pin)
        else:
            return self._generate_custom_connections(components, mcu_pin)
    
    def _generate_series_connections(
        self,
        components: list[dict],
        mcu_pin: str | None
    ) -> list[dict]:
        """Generate series connections: MCU → R1 → LED1 → LED2 → GND"""
        connections = []
        
        # Find resistor and LEDs
        resistors = [c for c in components if c['type'] == 'resistor']
        leds = [c for c in components if c['type'] == 'led']
        
        if not resistors or not leds:
            return connections
        
        R1 = resistors[0]['ref']
        
        # MCU pin → R1
        if mcu_pin:
            connections.append({
                'from': f'Arduino:{mcu_pin}',
                'to': f'{R1}:1',
                'net': f'Net_{mcu_pin}_{R1}'
            })
        
        # R1 → LED1
        connections.append({
            'from': f'{R1}:2',
            'to': f'{leds[0]["ref"]}:A',
            'net': f'Net_{R1}_LED1'
        })
        
        # LED1 → LED2 → LED3 ...
        for i in range(len(leds) - 1):
            connections.append({
                'from': f'{leds[i]["ref"]}:K',
                'to': f'{leds[i+1]["ref"]}:A',
                'net': f'Net_LED{i+1}_LED{i+2}'
            })
        
        # Last LED → GND
        connections.append({
            'from': f'{leds[-1]["ref"]}:K',
            'to': 'GND',
            'net': 'GND'
        })
        
        return connections
    
    def _generate_parallel_connections(self, ...):
        """Generate parallel connections: MCU → R1 → (LED1 || LED2) → GND"""
        # Similar logic for parallel
        pass
```

## Тестирование

### Тест 1: Два светодиода
```python
analyzer = CircuitAnalyzer(llm_client)
result = analyzer.analyze("two LED with 330 ohm resistor to Arduino pin 5")

assert len(result['components']) == 3  # 2 LED + 1 R
assert result['components'][0]['ref'] == 'LED1'
assert result['components'][1]['ref'] == 'LED2'
assert result['components'][2]['ref'] == 'R1'
```

### Тест 2: Три резистора
```python
result = analyzer.analyze("three 10k resistors as pull-ups")

assert len(result['components']) == 3
assert result['components'][0]['ref'] == 'R1'
assert result['components'][1]['ref'] == 'R2'
assert result['components'][2]['ref'] == 'R3'
```

## Интеграция

### Обновить schematic.py:
```python
from .ai_analyzer import CircuitAnalyzer
from .circuit_generator import ConnectionGenerator

def generate_schematic(description: str, output: str, ...) -> Path:
    # Initialize AI analyzer
    analyzer = CircuitAnalyzer(llm_client)
    
    # Analyze description
    analysis = analyzer.analyze(description)
    
    # Ask clarifying questions if any
    if analysis.get('questions'):
        answers = dialog_manager.ask_questions(analysis['questions'])
        analysis = analyzer.update_with_answers(analysis, answers)
    
    # Generate connections
    conn_generator = ConnectionGenerator()
    connections = conn_generator.generate_connections(
        analysis['components'],
        analysis.get('configuration', 'parallel'),
        mcu_pin=analysis.get('mcu_pin')
    )
    
    # Generate schematic with ALL components and connections
    generator = SchematicGenerator()
    content = generator.generate(
        components=analysis['components'],
        connections=connections,
        power=analysis['power']
    )
    
    # Write file
    output_path.write_text(content)
    return output_path
```

## Критерии Приемки

- [ ] `"two LED"` → 2 светодиода в схеме
- [ ] `"three resistors"` → 3 резистора
- [ ] `"LED in series"` → последовательное соединение
- [ ] `"LED in parallel"` → параллельное соединение
- [ ] Диалог задаёт уточняющие вопросы
- [ ] Все компоненты правильно подключены
- [ ] Схема открывается в KiCad без ошибок

## Сложности и Решения

### Сложность 1: LLM может не вернуть правильное количество
**Решение:** Явно указывать в промпте правила извлечения количества

### Сложность 2: Разные варианты написания
**Решение:** Использовать regex для извлечения чисел ("2 led", "two led", "two LEDs")

### Сложность 3: Неясное соединение
**Решение:** Задавать уточняющий вопрос через dialog manager

## Ресурсы

- Ollama API: https://github.com/ollama/ollama/blob/main/docs/api.md
- KiCad schematic format: https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/
- Component libraries: https://gitlab.com/kicad/libraries/kicad-symbols
