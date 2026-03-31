# ============================================================
# PCBAI T5 Model Training — 30,000 pairs
# ============================================================
# Optimized for Google Colab with T4 GPU
#
# How to use:
#   1. Open Google Colab: https://colab.research.google.com
#   2. Set runtime: Runtime -> Change runtime type -> T4 GPU
#   3. Upload training_30k.json to your Google Drive at:
#      MyDrive/PCBAI/datasets/training_30k.json
#   4. Copy-paste this entire file into a Colab cell and run
# ============================================================

# ============================
# Section 1: Setup
# ============================

print("=" * 60)
print("PCBAI T5 Model Training — 30k pairs")
print("=" * 60)

print("\n[1/7] Installing dependencies...")
!pip install transformers datasets accelerate torch sentencepiece -q

import json
import os
import random
import numpy as np
import torch
from pathlib import Path

# Reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

# Check GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)
    gpu_mem = torch.cuda.get_device_properties(0).total_mem / 1024**3
    print(f"GPU: {gpu_name} ({gpu_mem:.1f} GB)")
else:
    print("WARNING: No GPU detected! Training will be very slow.")

# Mount Google Drive
print("\n[2/7] Mounting Google Drive...")
from google.colab import drive
try:
    drive.mount('/content/drive')
    DRIVE_DIR = Path('/content/drive/MyDrive/PCBAI')
    DRIVE_DIR.mkdir(parents=True, exist_ok=True)
    SAVE_PATH = str(DRIVE_DIR / 'models' / 't5-kicad-30k')
    DATASET_PATH = str(DRIVE_DIR / 'datasets' / 'training_30k.json')
    print(f"Drive mounted. Model will save to: {SAVE_PATH}")
except Exception as e:
    print(f"Drive mount failed: {e}")
    print("Saving locally instead (will be lost when session ends!)")
    SAVE_PATH = './models/t5-kicad-30k'
    DATASET_PATH = './training_30k.json'

# ============================
# Section 2: Load Dataset
# ============================

print(f"\n[3/7] Loading dataset from {DATASET_PATH}...")

if not os.path.exists(DATASET_PATH):
    print(f"ERROR: Dataset not found at {DATASET_PATH}")
    print("Please upload training_30k.json to your Google Drive at:")
    print("  MyDrive/PCBAI/datasets/training_30k.json")
    print("\nOr upload it directly to this Colab session.")
    raise FileNotFoundError(DATASET_PATH)

with open(DATASET_PATH, 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

all_pairs = raw_data['training_pairs']
print(f"Loaded {len(all_pairs)} training pairs")

# ============================
# Section 3: Compact Format
# ============================
# JSON is too verbose for T5's 512-token limit.
# We use a compact delimiter format:
#   Components: REF|LIB_ID|VALUE;REF|LIB_ID|VALUE;...
#   Connections: REF:PIN-REF:PIN;REF:PIN-REF:PIN;...
#   Full: COMPONENTS||CONNECTIONS
#
# Example: R1|Device:R|330;D1|Device:LED|RED||A1:D5-R1:1;R1:2-D1:2

print("\n[4/7] Preparing data in compact format...")

def to_compact_format(output_data: dict) -> str:
    """Convert JSON output to compact format for T5."""
    components = output_data.get('components', [])
    connections = output_data.get('connections', [])

    # Components
    comp_parts = []
    for c in components:
        ref = c.get('ref', '')
        lib_id = c.get('lib_id', '')
        value = c.get('value', '')
        comp_parts.append(f"{ref}|{lib_id}|{value}")
    comp_str = ';'.join(comp_parts)

    # Connections
    conn_parts = []
    for c in connections:
        from_pin = c.get('from', '')
        to_pin = c.get('to', '')
        conn_parts.append(f"{from_pin}-{to_pin}")
    conn_str = ';'.join(conn_parts)

    return f"{comp_str}||{conn_str}"


def from_compact_format(text: str) -> dict | None:
    """Parse compact format back to structured dict."""
    try:
        parts = text.split('||')
        if len(parts) != 2:
            return None

        comp_str, conn_str = parts

        components = []
        if comp_str:
            for comp_part in comp_str.split(';'):
                fields = comp_part.split('|')
                if len(fields) >= 2:
                    components.append({
                        'ref': fields[0],
                        'lib_id': fields[1],
                        'value': fields[2] if len(fields) > 2 else '',
                    })

        connections = []
        if conn_str:
            for conn_part in conn_str.split(';'):
                pins = conn_part.split('-')
                if len(pins) >= 2:
                    connections.append({
                        'from': pins[0],
                        'to': pins[1],
                    })

        return {'components': components, 'connections': connections}
    except Exception:
        return None


# Prepare training data
train_inputs = []
train_outputs = []

for pair in all_pairs:
    input_text = f"generate schematic: {pair['input']}"
    output_text = to_compact_format(pair['output'])

    # Skip if too long (rough estimate: 4 chars per token)
    if len(output_text) > 1800:  # ~450 tokens
        continue

    train_inputs.append(input_text)
    train_outputs.append(output_text)

print(f"Prepared {len(train_inputs)} pairs after length filtering")

# Train/eval split
split_idx = int(0.95 * len(train_inputs))
train_data = {'input': train_inputs[:split_idx], 'output': train_outputs[:split_idx]}
eval_data = {'input': train_inputs[split_idx:], 'output': train_outputs[split_idx:]}
print(f"Train: {len(train_data['input'])}, Eval: {len(eval_data['input'])}")

# ============================
# Section 4: Tokenizer + Model
# ============================

print("\n[5/7] Loading model and tokenizer...")

from transformers import T5Tokenizer, T5ForConditionalGeneration

tokenizer = T5Tokenizer.from_pretrained('t5-small')

# Add KiCad-specific tokens for better encoding
KICAD_SPECIAL_TOKENS = [
    # Common lib_ids as single tokens
    'Device:R', 'Device:C', 'Device:LED', 'Device:D', 'Device:L',
    'Device:R_Small', 'Device:C_Small', 'Device:C_Polarized',
    'Device:LED_Small', 'Device:D_Zener', 'Device:D_Schottky',
    'Device:Crystal', 'Device:Fuse', 'Device:Buzzer',
    'Device:Q_NPN_BCE', 'Device:Q_PNP_BCE',
    'Device:Q_NMOS_GDS', 'Device:Q_PMOS_GDS',
    'MCU_Module:Arduino_UNO_R3', 'MCU_Module:Arduino_Nano_v3.x',
    'MCU_Microchip_ATmega:ATmega328P-PU',
    'RF_Module:ESP32-WROOM-32', 'RF_Module:ESP-12E',
    'Sensor:DHT11', 'Sensor:BME280', 'Sensor:BMP280',
    'Timer:NE555',
    '74xx:74HC595', '74xx:74HC04',
    'Amplifier_Operational:LM358', 'Amplifier_Operational:LM741',
    'Regulator_Linear:LM7805_TO220', 'Regulator_Linear:AMS1117-3.3',
    'Driver_Motor:L293D',
    'Display_Character:HD44780',
    'Switch:SW_Push', 'Switch:SW_SPDT',
    'Connector_Generic:Conn_01x02', 'Connector_Generic:Conn_01x03',
    'Connector_Generic:Conn_01x04', 'Connector_Generic:Conn_01x06',
    'Connector:USB_B_Micro', 'Connector:USB_C_Receptacle',
    'Connector:Barrel_Jack',
    'power:GND', 'power:VCC', 'power:+3V3', 'power:+5V',
    'Memory_EEPROM:AT24CS02',
    'Isolator:PC817',
    # Delimiters
    '||',
]

num_added = tokenizer.add_tokens(KICAD_SPECIAL_TOKENS)
print(f"Added {num_added} KiCad-specific tokens to tokenizer")

model = T5ForConditionalGeneration.from_pretrained('t5-small')
model.resize_token_embeddings(len(tokenizer))
print(f"Model loaded. Vocab size: {len(tokenizer)}")

# ============================
# Section 5: Dataset Class
# ============================

from torch.utils.data import Dataset

class SchematicDataset(Dataset):
    def __init__(self, inputs, outputs, tokenizer, max_input_len=256, max_output_len=512):
        self.inputs = inputs
        self.outputs = outputs
        self.tokenizer = tokenizer
        self.max_input_len = max_input_len
        self.max_output_len = max_output_len

    def __len__(self):
        return len(self.inputs)

    def __getitem__(self, idx):
        input_enc = self.tokenizer(
            self.inputs[idx],
            max_length=self.max_input_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt',
        )
        output_enc = self.tokenizer(
            self.outputs[idx],
            max_length=self.max_output_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt',
        )

        labels = output_enc['input_ids'].squeeze(0)
        # Replace padding token id with -100 so it's ignored in loss
        labels[labels == self.tokenizer.pad_token_id] = -100

        return {
            'input_ids': input_enc['input_ids'].squeeze(0),
            'attention_mask': input_enc['attention_mask'].squeeze(0),
            'labels': labels,
        }

train_dataset = SchematicDataset(train_data['input'], train_data['output'], tokenizer)
eval_dataset = SchematicDataset(eval_data['input'], eval_data['output'], tokenizer)

# Verify a sample
sample = train_dataset[0]
print(f"\nSample input tokens: {sample['input_ids'].shape}")
print(f"Sample output tokens: {sample['labels'].shape}")
print(f"Sample input: {train_data['input'][0][:80]}...")
print(f"Sample output: {train_data['output'][0][:80]}...")

# ============================
# Section 6: Training
# ============================

print("\n[6/7] Starting training...")

from transformers import Trainer, TrainingArguments, EarlyStoppingCallback

# Calculate steps
total_samples = len(train_dataset)
batch_size = 8
grad_accum = 4
effective_batch = batch_size * grad_accum
steps_per_epoch = total_samples // effective_batch
total_epochs = 15
total_steps = steps_per_epoch * total_epochs
warmup_steps = min(500, total_steps // 10)

print(f"Training config:")
print(f"  Samples: {total_samples}")
print(f"  Batch size: {batch_size} x {grad_accum} = {effective_batch} effective")
print(f"  Steps/epoch: {steps_per_epoch}")
print(f"  Total epochs: {total_epochs}")
print(f"  Total steps: {total_steps}")
print(f"  Warmup steps: {warmup_steps}")
print(f"  FP16: {torch.cuda.is_available()}")

training_args = TrainingArguments(
    output_dir=SAVE_PATH,
    num_train_epochs=total_epochs,
    per_device_train_batch_size=batch_size,
    per_device_eval_batch_size=batch_size,
    gradient_accumulation_steps=grad_accum,

    # Optimizer
    learning_rate=3e-4,
    weight_decay=0.01,
    warmup_steps=warmup_steps,
    lr_scheduler_type='cosine',

    # FP16
    fp16=torch.cuda.is_available(),

    # Evaluation & saving
    eval_strategy='steps',
    eval_steps=max(500, steps_per_epoch),
    save_steps=max(2000, steps_per_epoch * 2),
    save_total_limit=3,
    load_best_model_at_end=True,
    metric_for_best_model='eval_loss',
    greater_is_better=False,

    # Logging
    logging_steps=50,
    logging_first_step=True,
    report_to='none',

    # Misc
    dataloader_num_workers=2,
    seed=SEED,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
)

# Train!
train_result = trainer.train()
print(f"\nTraining complete!")
print(f"  Total steps: {train_result.global_step}")
print(f"  Final loss: {train_result.training_loss:.4f}")

# Save best model
trainer.save_model(SAVE_PATH)
tokenizer.save_pretrained(SAVE_PATH)
print(f"Model + tokenizer saved to: {SAVE_PATH}")

# ============================
# Section 7: Evaluation & Testing
# ============================

print("\n[7/7] Evaluating and testing...")

# Eval metrics
eval_results = trainer.evaluate()
print("\nEval results:")
for key, value in eval_results.items():
    print(f"  {key}: {value:.4f}")

# Test generation
model.eval()

def generate_schematic(description: str, max_length: int = 512) -> str:
    """Generate schematic from description."""
    input_text = f"generate schematic: {description}"
    input_enc = tokenizer(input_text, return_tensors='pt').to(device)

    with torch.no_grad():
        output_ids = model.generate(
            input_enc['input_ids'],
            max_length=max_length,
            num_beams=4,
            early_stopping=True,
            no_repeat_ngram_size=3,
            length_penalty=1.0,
        )

    return tokenizer.decode(output_ids[0], skip_special_tokens=True)


# Test prompts
test_prompts = [
    "Arduino UNO with LED on pin D5",
    "Arduino with DHT22 temperature sensor",
    "ESP32 with BMP280 pressure sensor via I2C",
    "555 timer astable circuit",
    "Arduino Nano with 3 LEDs and push button",
    "ESP32 with OLED display",
    "Motor control with L293D and Arduino",
    "Voltage regulator 7805 with filter capacitors",
    "Arduino with relay module",
    "ESP8266 with DHT11 sensor",
]

print("\n" + "=" * 60)
print("TEST RESULTS")
print("=" * 60)

parse_success = 0
for i, prompt in enumerate(test_prompts):
    print(f"\nTest {i+1}: {prompt}")
    output = generate_schematic(prompt)
    print(f"  Raw: {output[:120]}...")

    parsed = from_compact_format(output)
    if parsed:
        print(f"  Components: {len(parsed['components'])}")
        print(f"  Connections: {len(parsed['connections'])}")
        for comp in parsed['components'][:3]:
            print(f"    - {comp['ref']}: {comp['lib_id']} ({comp.get('value', '')})")
        parse_success += 1
    else:
        print(f"  PARSE FAILED")

print(f"\n{'=' * 60}")
print(f"Parse success rate: {parse_success}/{len(test_prompts)} ({parse_success/len(test_prompts)*100:.0f}%)")
print(f"{'=' * 60}")

# ============================
# Final Summary
# ============================

print(f"""
{'=' * 60}
TRAINING COMPLETE!
{'=' * 60}

Model saved to: {SAVE_PATH}
  - pytorch_model.bin  (~240 MB)
  - tokenizer files
  - config.json

To use the model in PCBAI:
  1. Download the model folder from Google Drive
  2. Place it in: PCBAI/models/t5-kicad-30k/
  3. Run: pcba dialog  (it will auto-detect the trained model)

Compact format reference:
  Input:  "generate schematic: Arduino with LED"
  Output: "A1|MCU_Module:Arduino_UNO_R3|;R1|Device:R|330;D1|Device:LED|||A1:D5-R1:1;R1:2-D1:2;D1:1-A1:GND"

{'=' * 60}
""")
