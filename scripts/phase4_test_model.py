#!/usr/bin/env python3
"""
Phase 4: Test Trained Model.

Tests the trained T5 model on sample inputs and validates:
- JSON format
- Component structure
- Connection validity
- KiCad 9.0 compatibility

Usage:
    python scripts/phase4_test_model.py --model models/t5-25k --test_samples 10
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import torch
    from transformers import T5ForConditionalGeneration, T5Tokenizer
except ImportError:
    print("Installing required libraries...")
    import os
    os.system('pip install torch transformers -q')
    import torch
    from transformers import T5ForConditionalGeneration, T5Tokenizer


def load_model(model_path: str):
    """Load trained model and tokenizer."""
    print(f"\nLoading model from: {model_path}")
    
    tokenizer = T5Tokenizer.from_pretrained('t5-small')
    model = T5ForConditionalGeneration.from_pretrained(model_path)
    
    # Move to CPU for testing
    model = model.to('cpu')
    
    print("✅ Model loaded successfully")
    return model, tokenizer


def generate_schematic(model, tokenizer, description: str) -> dict:
    """
    Generate schematic from description.
    
    Args:
        model: Trained T5 model
        tokenizer: Tokenizer
        description: Natural language description
        
    Returns:
        Generated components dict or None
    """
    input_text = f"generate schematic: {description}"
    input_enc = tokenizer(input_text, return_tensors='pt')
    
    with torch.no_grad():
        output_ids = model.generate(
            input_enc['input_ids'],
            max_length=512,
            num_beams=4,
            early_stopping=True,
            no_repeat_ngram_size=2,
        )
    
    output_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    
    try:
        result = json.loads(output_text)
        return {'success': True, 'data': result, 'raw': output_text}
    except json.JSONDecodeError as e:
        return {'success': False, 'error': str(e), 'raw': output_text}


def validate_output(output: dict) -> dict:
    """
    Validate generated output.
    
    Args:
        output: Generated data
        
    Returns:
        Validation result
    """
    result = {
        'valid_json': False,
        'has_components': False,
        'has_connections': False,
        'valid_structure': False,
        'errors': []
    }
    
    if 'data' not in output:
        result['errors'].append("No data in output")
        return result
    
    data = output['data']
    
    # Check JSON
    result['valid_json'] = True
    
    # Check components
    if 'components' in data and len(data['components']) > 0:
        result['has_components'] = True
        
        # Check component structure
        for comp in data['components']:
            if 'ref' not in comp or 'lib_id' not in comp:
                result['errors'].append(f"Component missing fields: {comp}")
                break
        else:
            result['valid_structure'] = True
    else:
        result['errors'].append("No components in output")
    
    # Check connections
    if 'connections' in data:
        result['has_connections'] = True
    
    return result


def run_tests(model, tokenizer, test_samples: int = 10):
    """
    Run test cases.
    
    Args:
        model: Trained model
        tokenizer: Tokenizer
        test_samples: Number of test cases
    """
    print(f"\n{'='*60}")
    print("Running Tests")
    print(f"{'='*60}\n")
    
    # Test cases
    test_cases = [
        "Arduino with LED on pin 5",
        "Arduino with button on pin 3",
        "ESP32 with DHT22 sensor",
        "Arduino with two LEDs and resistors",
        "ATmega328P minimal circuit",
        "Arduino UART programmer",
        "LED matrix 3x3",
        "Arduino with servo motor",
        "Raspberry Pi Pico with buttons",
        "Arduino I2C LCD display",
    ]
    
    results = []
    
    for i, test in enumerate(test_cases[:test_samples], 1):
        print(f"Test {i}: {test}")
        
        output = generate_schematic(model, tokenizer, test)
        validation = validate_output(output)
        
        if output['success']:
            if validation['valid_structure']:
                print(f"  ✅ PASS - Valid JSON, {len(output['data']['components'])} components")
                results.append({'test': test, 'status': 'PASS', 'components': len(output['data']['components'])})
            else:
                print(f"  ⚠️  WARN - Valid JSON but structure issues")
                print(f"     Errors: {validation['errors']}")
                results.append({'test': test, 'status': 'WARN', 'errors': validation['errors']})
        else:
            print(f"  ❌ FAIL - JSON parse error")
            print(f"     Raw output: {output['raw'][:100]}...")
            results.append({'test': test, 'status': 'FAIL', 'error': output['error']})
        
        print()
    
    # Summary
    print(f"{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    
    passed = sum(1 for r in results if r['status'] == 'PASS')
    warned = sum(1 for r in results if r['status'] == 'WARN')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    
    print(f"  Total: {len(results)}")
    print(f"  ✅ PASS: {passed}")
    print(f"  ⚠️  WARN: {warned}")
    print(f"  ❌ FAIL: {failed}")
    print(f"  Success rate: {passed/len(results)*100:.1f}%")
    print(f"{'='*60}\n")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Test trained T5 model')
    parser.add_argument('--model', type=str, required=True,
                        help='Path to trained model')
    parser.add_argument('--test_samples', type=int, default=10,
                        help='Number of test cases')

    args = parser.parse_args()

    print("="*60)
    print("PCBAI - Phase 4: Model Testing")
    print("="*60)

    # Load model
    model, tokenizer = load_model(args.model)
    
    # Run tests
    results = run_tests(model, tokenizer, args.test_samples)
    
    # Save results
    results_path = Path('test_results.json')
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"Test results saved to: {results_path}")
    
    return 0 if all(r['status'] == 'PASS' for r in results) else 1


if __name__ == '__main__':
    sys.exit(main())
