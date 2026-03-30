#!/usr/bin/env python3
"""Quick test of Google API"""

import sys
sys.path.insert(0, '/Users/vladglazunov/Documents/algo/PCBAI/src')

from pcba.schematic import LLMClient, load_config

print("Loading config...")
config = load_config()
print(f"Default provider: {config.get('default_provider')}")
print(f"Google enabled: {config.get('llm_providers', {}).get('google', {}).get('enabled')}")

print("\nCreating LLM client...")
client = LLMClient(config)

print("Testing Google API...")
try:
    response = client.generate("Say hello in one word", provider="google")
    print(f"✓ Success! Response: {response[:100]}")
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nTry fallback to Puter...")
    try:
        response = client.generate("Say hello in one word", provider="puter")
        print(f"✓ Puter works! Response: {response[:100]}")
    except Exception as e2:
        print(f"✗ Puter also failed: {e2}")
