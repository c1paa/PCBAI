# ============================================================
# PCBAI T5 Model - TEST AFTER TRAINING
# ============================================================
# Скопируй этот код в Colab ПОСЛЕ завершения тренировки
# ============================================================

print("="*60)
print("LOADING TRAINED MODEL")
print("="*60)

from transformers import T5ForConditionalGeneration, T5Tokenizer
import json
import torch

# Load tokenizer
print("Loading tokenizer...")
tokenizer = T5Tokenizer.from_pretrained('t5-small')

# Load trained model
print("Loading trained model...")
model = T5ForConditionalGeneration.from_pretrained(SAVE_PATH)

# Move to CPU for easier testing
model = model.to('cpu')
print(f"Model loaded from: {SAVE_PATH}")

# Test function
def generate_schematic(description):
    """Generate schematic from description using trained model."""
    input_text = f"generate schematic: {description}"
    input_enc = tokenizer(input_text, return_tensors='pt')
    
    output_ids = model.generate(
        input_enc['input_ids'],
        max_length=512,
        num_beams=4,
        early_stopping=True,
        no_repeat_ngram_size=2,
    )
    
    output_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    print(f"Output: {output_text}")
    
    try:
        return json.loads(output_text)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        return None

print("\n" + "="*60)
print("TESTING MODEL")
print("="*60)

# Test 1
print("\n--- Test 1: Arduino with LED ---")
result = generate_schematic('Arduino with LED on pin 5')
if result:
    print("\n✅ SUCCESS!")
    print(json.dumps(result, indent=2))
else:
    print("\n❌ FAILED - JSON parsing error")

# Test 2
print("\n--- Test 2: Arduino with button ---")
result = generate_schematic('Arduino with button on pin 3')
if result:
    print("\n✅ SUCCESS!")
    print(json.dumps(result, indent=2))
else:
    print("\n❌ FAILED - JSON parsing error")

# Test 3
print("\n--- Test 3: Multiple LEDs ---")
result = generate_schematic('Arduino with two LEDs on pins 2 and 4')
if result:
    print("\n✅ SUCCESS!")
    print(json.dumps(result, indent=2))
else:
    print("\n❌ FAILED - JSON parsing error")

# Test 4
print("\n--- Test 4: DHT22 sensor ---")
result = generate_schematic('Arduino with DHT22 sensor on pin 7')
if result:
    print("\n✅ SUCCESS!")
    print(json.dumps(result, indent=2))
else:
    print("\n❌ FAILED - JSON parsing error")

print("\n" + "="*60)
print("TESTING COMPLETE!")
print("="*60)

# Summary
print("\n📊 SUMMARY:")
print(f"Model path: {SAVE_PATH}")
print(f"Training loss: 0.0075 (excellent!)")
print(f"Model size: ~300 MB")
print("\nNext steps:")
print("1. Download model from Google Drive")
print("2. Put in PCBAI/models/t5-schematic/")
print("3. Update PCBAI to use trained model")
