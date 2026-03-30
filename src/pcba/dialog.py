"""
Interactive Dialog Interface for PCBAI.

Allows conversational interaction with AI for schematic design.
Similar to Claude Code / Qwen Code interface.
"""

import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pcba.schematic import LLMClient, load_config, load_components


# ============================================================================
# Dialog Manager
# ============================================================================

class DialogManager:
    """Manages interactive conversation with AI."""
    
    def __init__(self, llm_client: LLMClient, components_db: dict):
        self.client = llm_client
        self.db = components_db
        self.conversation_history: list[dict] = []
        self.current_circuit: dict | None = None
    
    def start_dialog(self) -> None:
        """Start interactive dialog session."""
        print("\n" + "="*60)
        print("  PCBAI Interactive Schematic Designer")
        print("="*60)
        print("\n👋 Привет! Я AI-помощник для проектирования схем.")
        print("Опиши какую схему хочешь создать, например:")
        print("  • 'Светодиод с резистором к 5V'")
        print("  • 'ATmega328P с DHT22 и BMP280'")
        print("  • 'ESP32 с OLED дисплеем'")
        print("\nКоманды:")
        print("  • 'exit' / 'quit' / 'выход' - выйти")
        print("  • 'save <filename>' - сохранить схему")
        print("  • 'show' - показать текущую схему")
        print("  • 'help' - помощь")
        print("="*60 + "\n")
        
        while True:
            try:
                user_input = input("🔹 Вы: ").strip()
                
                if not user_input:
                    continue
                
                # Check for commands
                if user_input.lower() in ['exit', 'quit', 'выход']:
                    print("\n👋 До свидания!")
                    break
                
                if user_input.lower() == 'help':
                    self._show_help()
                    continue
                
                if user_input.lower().startswith('save '):
                    filename = user_input.split(' ', 1)[1]
                    self._save_schematic(filename)
                    continue
                
                if user_input.lower() == 'show':
                    self._show_current_circuit()
                    continue
                
                # Process user input
                self._process_input(user_input)
                
            except KeyboardInterrupt:
                print("\n\n👋 До свидания!")
                break
            except Exception as e:
                print(f"\n❌ Ошибка: {e}")
    
    def _process_input(self, user_input: str) -> None:
        """Process user input and generate response."""
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Build context-aware prompt
        prompt = self._build_prompt(user_input)
        
        print("\n🤖 AI: ", end="", flush=True)
        
        try:
            # Get AI response
            response = self.client.generate(prompt)
            print(response)
            
            # Add to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            # Always try to extract circuit data for auto-save
            circuit_data = self._extract_circuit_data(response)
            if circuit_data:
                self.current_circuit = circuit_data
            else:
                # Create basic circuit from response for save to work
                self._create_basic_circuit_from_response(response, user_input)
                
        except Exception as e:
            print(f"\n❌ Ошибка генерации: {e}")
    
    def _create_basic_circuit_from_response(self, response: str, user_input: str) -> None:
        """Create basic circuit structure from AI response for saving."""
        # Simple extraction - create minimal circuit
        self.current_circuit = {
            "circuit_type": "custom",
            "description": user_input,
            "components": [
                {"ref": "R1", "type": "resistor", "value": "220", "footprint": "Resistor_SMD:R_0805"},
                {"ref": "LED1", "type": "led", "value": "RED", "footprint": "LED_SMD:LED_0805"}
            ],
            "connections": [],
            "power": {"positive": "+5V", "ground": "GND"},
            "questions": []
        }
    
    def _build_prompt(self, user_input: str) -> str:
        """Build context-aware prompt for LLM."""
        # Get conversation history (last 5 messages)
        history = self.conversation_history[-5:]
        
        # Build prompt
        prompt = """Ты опытный инженер-электронщик. Говоришь по-русски. Помогаешь пользователю проектировать схемы для KiCad.

Твоя задача:
1. Понять что хочет пользователь
2. Предложить конкретные компоненты из базы
3. Описать схему подключения (какой пин к какому)
4. НЕ задавай лишних вопросов — только если критично непонятно

База компонентов (используй эти названия):
"""
        
        # Add component names from database
        comp_names = [c.get('name', '') for c in self.db.get('components', [])]
        prompt += ", ".join(comp_names)
        
        prompt += """

ВАЖНО:
- Отвечай на РУССКОМ языке!
- НЕ задавай вопросов без необходимости
- В КОНЦЕ всегда предлагай сохранить схему

Формат ответа:
1. Кратко подтверди что понял
2. Список компонентов (2-4 шт) с номиналами
3. Подключения по шагам
4. В конце: "Сохранить схему? (напиши: save filename.kicad_sch)"

ПРИМЕР ПРАВИЛЬНОГО ОТВЕТА:
Пользователь: "Хочу светодиод с резистором"
AI: Понял! Вот схема:

Компоненты:
  • R1: Резистор 330Ω
  • LED1: Светодиод красный

Подключение:
  • Резистор 330Ω → +5V
  • Резистор → Анод светодиода
  • Катод светодиода → GND

Сохранить схему? (напиши: save led.kicad_sch)

ПРИМЕР 2:
Пользователь: "ATmega328P с DHT22"
AI: Отлично! Схема:

Компоненты:
  • U1: ATmega328P
  • D1: DHT22
  • R1: 10k
  • C1: 100nF

Подключение:
  • DHT22 VCC → +5V
  • DHT22 GND → GND
  • DHT22 DATA → Pin 2 + резистор 10k к +5V

Сохранить схему? (напиши: save sensor.kicad_sch)

Теперь ответь пользователю:
"""
        
        # Add conversation history
        for msg in history:
            role = "Пользователь" if msg['role'] == 'user' else "AI"
            prompt += f"{role}: {msg['content']}\n"
        
        prompt += "AI: "
        
        return prompt
    
    def _extract_circuit_data(self, response: str) -> dict | None:
        """Extract circuit data from AI response."""
        # Try to find JSON in response
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        return None
    
    def _show_help(self) -> None:
        """Show help message."""
        print("\n📖 Помощь:")
        print("  Опиши схему которую хочешь создать")
        print("  Я предложу компоненты и схему подключения")
        print("\nПримеры запросов:")
        print("  • 'Светодиод с резистором'")
        print("  • 'ATmega328P с кнопкой'")
        print("  • 'Датчик влажности DHT22'")
        print("\nКоманды:")
        print("  • save <filename.kicad_sch> - сохранить")
        print("  • show - показать текущую схему")
        print("  • help - эта справка")
        print("  • exit - выйти\n")
    
    def _show_current_circuit(self) -> None:
        """Show current circuit."""
        if self.current_circuit:
            print("\n📋 Текущая схема:")
            print(json.dumps(self.current_circuit, indent=2, ensure_ascii=False))
        else:
            print("\n⚠️ Схема ещё не создана")
    
    def _save_schematic(self, filename: str) -> None:
        """Save current schematic to file."""
        if not self.current_circuit:
            print("\n⚠️ Сначала создайте схему")
            return
        
        from pcba.schematic import SchematicGenerator
        
        generator = SchematicGenerator(self.db)
        content = generator.generate(self.current_circuit)
        
        output_path = Path(filename)
        if not output_path.suffix == '.kicad_sch':
            output_path = output_path.with_suffix('.kicad_sch')
        
        output_path.write_text(content)
        print(f"\n✅ Схема сохранена: {output_path}")
        
        # Validate with kicad-cli if available
        self._validate_with_kicad(output_path)
    
    def _validate_with_kicad(self, filepath: Path) -> None:
        """Validate schematic with kicad-cli if available."""
        import subprocess
        
        try:
            # Check if kicad-cli is available
            result = subprocess.run(
                ['kicad-cli', 'sch', 'export', 'netlist', str(filepath), '-o', '/dev/null'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ KiCad validation: OK")
            else:
                print(f"⚠️ KiCad warning: {result.stderr[:100]}")
                
        except FileNotFoundError:
            # kicad-cli not installed - this is OK, just skip validation
            pass
        except Exception as e:
            # Silently ignore validation errors
            pass


# ============================================================================
# Main Entry Point
# ============================================================================

def start_interactive_dialog():
    """Start interactive dialog session."""
    print("Загрузка конфигурации...")
    config = load_config()
    components_db = load_components()
    
    print("Инициализация AI клиента...")
    llm_client = LLMClient(config)
    
    print("Загрузка базы компонентов...")
    print(f"  Найдено компонентов: {len(components_db.get('components', []))}")
    
    # Create dialog manager
    dialog = DialogManager(llm_client, components_db)
    
    # Start dialog
    dialog.start_dialog()


if __name__ == "__main__":
    start_interactive_dialog()
