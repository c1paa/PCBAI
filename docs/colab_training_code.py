# ============================================================
# PCBAI T5 Model Training - 1000+ pairs
# ============================================================
# Скопируй весь этот код в Google Colab и запусти
# https://colab.research.google.com
# ============================================================

print("Installing dependencies...")
!pip install transformers datasets accelerate torch -q

print("Mounting Google Drive (optional)...")
from google.colab import drive
try:
    drive.mount('/content/drive')
    SAVE_PATH = '/content/drive/MyDrive/PCBAI/models/t5-schematic'
except:
    SAVE_PATH = './models/t5-schematic'
    print("Drive not mounted, saving locally")

print("Downloading dataset from GitHub...")
!mkdir -p datasets
!wget -q https://raw.githubusercontent.com/c1paa/PCBAI/main/datasets/synthetic_dataset.json -O datasets/synthetic_dataset.json
!wget -q https://raw.githubusercontent.com/c1paa/PCBAI/main/datasets/schematic_generation.json -O datasets/schematic_generation.json

print("Loading datasets...")
import json

with open('datasets/synthetic_dataset.json', 'r') as f:
    synthetic = json.load(f)

with open('datasets/schematic_generation.json', 'r') as f:
    original = json.load(f)

all_pairs = original['training_pairs'] + synthetic['training_pairs']
print(f"TOTAL training pairs: {len(all_pairs)}")

print("\nPreparing data...")
from torch.utils.data import Dataset, DataLoader
from transformers import T5Tokenizer, T5ForConditionalGeneration, Trainer, TrainingArguments
import torch

class SchematicDataset(Dataset):
    def __init__(self, pairs, tokenizer, max_length=512):
        self.pairs = pairs
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.pairs)
    
    def __getitem__(self, idx):
        pair = self.pairs[idx]
        input_text = f"generate schematic: {pair['input']}"
        output_components = {'components': pair['output']['components']}
        output_text = json.dumps(output_components)
        
        input_enc = self.tokenizer(input_text, max_length=self.max_length, padding='max_length', truncation=True, return_tensors='pt')
        output_enc = self.tokenizer(output_text, max_length=self.max_length, padding='max_length', truncation=True, return_tensors='pt')
        
        return {
            'input_ids': input_enc['input_ids'].squeeze(0),
            'attention_mask': input_enc['attention_mask'].squeeze(0),
            'labels': output_enc['input_ids'].squeeze(0)
        }

tokenizer = T5Tokenizer.from_pretrained('t5-small')
dataset = SchematicDataset(all_pairs, tokenizer)

train_size = int(0.9 * len(dataset))
test_size = len(dataset) - train_size
train_dataset, test_dataset = torch.utils.data.random_split(dataset, [train_size, test_size])

print(f"Train: {train_size}, Test: {test_size}")

print("\nLoading model...")
model = T5ForConditionalGeneration.from_pretrained('t5-small')

print("\nStarting training (10-15 minutes)...")
training_args = TrainingArguments(
    output_dir=SAVE_PATH,
    num_train_epochs=15,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    learning_rate=1e-4,
    weight_decay=0.01,
    save_steps=100,
    eval_steps=50,
    logging_steps=10,
    eval_strategy='steps',
    save_total_limit=2,
    load_best_model_at_end=True,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
)

trainer.train()
trainer.save_model(SAVE_PATH)

print("\n" + "="*60)
print("TRAINING COMPLETE!")
print("="*60)

eval_results = trainer.evaluate()
print("\nEvaluation results:")
for key, value in eval_results.items():
    print(f"{key}: {value:.4f}")

print(f"\nModel saved to: {SAVE_PATH}")

# Test
print("\n" + "="*60)
print("TESTING MODEL")
print("="*60)

def generate_schematic(description):
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
    except:
        print("JSON parse error - model needs more training")
        return None

print("\nTest 1: Arduino with LED")
result = generate_schematic('Arduino with LED on pin 5')

print("\nTest 2: Arduino with button")
result = generate_schematic('Arduino with button on pin 3')

print("\n" + "="*60)
print("ALL DONE!")
print("="*60)
