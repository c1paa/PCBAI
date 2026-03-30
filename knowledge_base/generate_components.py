#!/usr/bin/env python3
"""
Component Database Generator using AI.

Generates component data in the required JSON format using LLM.
"""

import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any


# ============================================================================
# LLM Client (supports multiple providers)
# ============================================================================

class LLMClient:
    """Multi-provider LLM client."""
    
    def __init__(self, provider: str = "google", api_key: str | None = None):
        """
        Initialize LLM client.
        
        Args:
            provider: "google", "groq", "puter", or "ollama"
            api_key: API key (not needed for puter/ollama)
        """
        self.provider = provider
        self.api_key = api_key
        
        # Endpoints
        self.endpoints = {
            "google": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            "groq": "https://api.groq.com/openai/v1/chat/completions",
            "ollama": "http://localhost:11434/api/generate",
        }
        
        # Default models
        self.models = {
            "google": "gemini-2.0-flash",
            "groq": "llama-3.1-70b-versatile",
            "ollama": "llama3.2",
            "puter": "gemini-pro",
        }
    
    def generate(self, prompt: str, model: str | None = None) -> str:
        """Generate text from LLM."""
        if self.provider == "puter":
            return self._generate_puter(prompt)
        elif self.provider == "ollama":
            return self._generate_ollama(prompt, model)
        elif self.provider == "google":
            return self._generate_google(prompt, model)
        elif self.provider == "groq":
            return self._generate_groq(prompt, model)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def _generate_google(self, prompt: str, model: str | None) -> str:
        """Generate using Google AI Studio."""
        model = model or self.models["google"]
        url = f"{self.endpoints['google']}?key={self.api_key}"
        
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result["candidates"][0]["content"]["parts"][0]["text"]
    
    def _generate_groq(self, prompt: str, model: str | None) -> str:
        """Generate using Groq Cloud."""
        model = model or self.models["groq"]
        url = self.endpoints["groq"]
        
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        )
        
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result["choices"][0]["message"]["content"]
    
    def _generate_ollama(self, prompt: str, model: str | None) -> str:
        """Generate using Ollama (local)."""
        model = model or self.models["ollama"]
        url = self.endpoints["ollama"]
        
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result.get("response", "")
    
    def _generate_puter(self, prompt: str) -> str:
        """Generate using Puter.js (free, no key needed)."""
        # Puter.js uses a different approach - we'll use their REST API
        # This is a simplified version - in production, use puter.js library
        url = "https://api.puter.com/v1/completion"
        
        data = {
            "model": self.models["puter"],
            "prompt": prompt,
            "max_tokens": 2000
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result.get("text", "")
        except Exception as e:
            # Fallback to ollama if puter fails
            print(f"Puter failed: {e}, falling back to Ollama...")
            return self._generate_ollama(prompt, None)


# ============================================================================
# Component Generation Prompts
# ============================================================================

COMPONENT_GENERATION_PROMPT = r'''You are an electronics engineer creating a component database.

Generate a JSON entry for the following electronic component.

IMPORTANT: Output ONLY valid JSON, no explanations, no markdown code blocks.

The JSON must follow this exact structure:
{
  "id": "category_componentname",
  "name": "Component Name",
  "category": "sensor|mcu|module|passive|connector|etc",
  "subcategory": "optional subcategory",
  "manufacturer": "Manufacturer Name",
  "description": "Brief description",
  
  "package": {
    "type": "Package type (e.g., TQFP-32, LGA-8, SOT-23)",
    "kiCad_footprint": "KiCad footprint name from library",
    "alternatives": ["alternative packages"]
  },
  
  "kiCad_lib_id": "Library:ComponentName",
  
  "pins": [
    {"num": 1, "name": "Pin Name", "type": "power|signal|ground|no_connect", "functions": ["function1", "function2"], "description": "Pin description"}
  ],
  
  "power": {
    "voltage_min": 0.0,
    "voltage_max": 5.0,
    "voltage_typical": 3.3,
    "current_max": "100mA"
  },
  
  "interfaces": {
    "I2C": {
      "count": 1,
      "pins": {"SDA": "PinName", "SCL": "PinName"},
      "addresses": ["0x00"],
      "pullup_required": true,
      "pullup_value": "4.7k"
    }
  },
  
  "design_rules": [
    {
      "rule": "rule_name",
      "description": "What is needed",
      "components": [{"type": "resistor", "value": "10k", "placement": "where"}]
    }
  ],
  
  "typical_applications": ["Application 1", "Application 2"],
  "datasheet_url": "https://..."
}

Component to generate: {component_name}

Additional context: {context}

Generate the JSON now:
'''


# ============================================================================
# Component Database Generator
# ============================================================================

class ComponentDatabaseGenerator:
    """Generate component database using AI."""
    
    def __init__(self, llm_client: LLMClient):
        self.client = llm_client
        self.base_db_path = Path(__file__).parent
    
    def generate_component(self, component_name: str, context: str = "") -> dict[str, Any]:
        """Generate data for a single component."""
        prompt = COMPONENT_GENERATION_PROMPT.format(
            component_name=component_name,
            context=context or f"Popular component used in embedded systems"
        )
        
        print(f"Generating data for: {component_name}")
        
        response = self.client.generate(prompt)
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            raise ValueError(f"Could not parse JSON from response: {response[:200]}")
    
    def generate_batch(self, components: list[str], output_file: str = "components.json") -> dict:
        """Generate data for multiple components."""
        # Load existing database
        db_path = self.base_db_path / output_file
        if db_path.exists():
            with open(db_path) as f:
                db = json.load(f)
        else:
            db = {
                "metadata": {
                    "version": "1.0.0",
                    "created": "2026-03-30",
                    "description": "PCBAI Component Knowledge Base"
                },
                "components": [],
                "passive_components": {
                    "resistors": {"default_footprint": "Resistor_SMD:R_0805"},
                    "capacitors": {"default_footprint": "Capacitor_SMD:C_0805"},
                    "leds": {"default_footprint": "LED_SMD:LED_0805"}
                },
                "design_rules": {}
            }
        
        # Generate each component
        for comp in components:
            try:
                comp_data = self.generate_component(comp)
                db["components"].append(comp_data)
                print(f"✓ Added: {comp_data.get('name', comp)}")
                
                # Save after each component (in case of failure)
                with open(db_path, 'w') as f:
                    json.dump(db, f, indent=2)
                    
            except Exception as e:
                print(f"✗ Failed to generate {comp}: {e}")
        
        print(f"\nDatabase saved to: {db_path}")
        print(f"Total components: {len(db['components'])}")
        
        return db


# ============================================================================
# Main - Example Usage
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Configuration
    PROVIDER = "google"  # "google", "groq", "ollama", or "puter"
    API_KEY = ""  # Set your API key for google/groq
    
    # Components to generate
    COMPONENTS_TO_ADD = [
        "ESP32-WROOM-32",
        "HC-SR04 ultrasonic sensor",
        "NRF24L01 wireless module",
        "RC522 RFID module",
        "OLED display 0.96 inch I2C",
        "LM317 voltage regulator",
        "AMS1117-3.3 LDO",
        "USB Type-C connector",
        "MicroSD card socket",
        "L293D motor driver",
    ]
    
    # Initialize client
    if not API_KEY and PROVIDER in ["google", "groq"]:
        print(f"Error: API key required for {PROVIDER}")
        print("Set API_KEY variable or use 'ollama' or 'puter' provider")
        sys.exit(1)
    
    client = LLMClient(provider=PROVIDER, api_key=API_KEY)
    generator = ComponentDatabaseGenerator(client)
    
    # Generate components
    print("=== PCBAI Component Database Generator ===\n")
    generator.generate_batch(COMPONENTS_TO_ADD)
