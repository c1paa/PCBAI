#!/usr/bin/env python3
"""
Test script for AI schematic generator.
"""

import sys
sys.path.insert(0, '/Users/vladglazunov/Documents/algo/PCBAI/src')

from pcba.schematic import generate_schematic, load_config, load_components

print("=== PCBAI AI Schematic Generator Test ===\n")

# Load config
print("Loading configuration...")
config = load_config()
print(f"Default provider: {config.get('default_provider', 'not set')}")

# Load components
print("Loading component database...")
db = load_components()
print(f"Components in database: {len(db.get('components', []))}")

# Test generation
print("\nGenerating schematic: 'LED with 330 ohm resistor'...")
try:
    result = generate_schematic(
        description="LED with 330 ohm resistor",
        output="/Users/vladglazunov/Documents/algo/PCBAI/examples/test1/ai_test.kicad_sch"
    )
    print(f"✓ Success! Generated: {result}")
    print(f"\nOpen in KiCad: open {result}")
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Check if LLM API is configured (see API_SETUP.md)")
    print("2. For Puter.js: no key needed, should work automatically")
    print("3. For Ollama: ensure 'ollama serve' is running")
