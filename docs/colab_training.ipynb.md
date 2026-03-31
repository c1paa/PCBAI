# PCBAI T5 Model Training on Google Colab

This notebook trains a T5-small model for schematic component extraction.

## Setup

```python
# Install dependencies
!pip install transformers datasets accelerate torch

# Mount Google Drive (optional, for saving models)
from google.colab import drive
drive.mount('/content/drive')

# Clone PCBAI repo (optional)
!git clone https://github.com/c1paa/PCBAI.git
%cd PCBAI
```

## Load Dataset

```python
import json

# Load main dataset
with open('datasets/schematic_generation.json', 'r') as f:
    dataset = json.load(f)

print(f"Main dataset: {len(dataset.get('training_pairs', []))} pairs")

# Load expanded dataset (if exists)
try:
    with open('datasets/expanded_dataset.json', 'r') as f:
        expanded = json.load(f)
    
    # Handle both formats
    expanded_pairs = expanded.get('training_pairs', expanded.get('schematics', []))
    print(f"Expanded dataset: {len(expanded_pairs)} pairs")
    
    # Combine datasets
    all_pairs = dataset.get('training_pairs', []) + expanded_pairs
    print(f"Total pairs: {len(all_pairs)}")
except FileNotFoundError:
    all_pairs = dataset.get('training_pairs', [])
    print(f"No expanded dataset, using {len(all_pairs)} pairs")
```

## Prepare Data

```python
from torch.utils.data import Dataset, DataLoader
from transformers import T5Tokenizer
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
        
        # Input: description
        input_text = f"generate schematic: {pair['input']}"
        
        # Output: components as JSON
        output_components = {'components': pair['output']['components']}
        output_text = json.dumps(output_components)
        
        # Tokenize
        input_enc = self.tokenizer(
            input_text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        output_enc = self.tokenizer(
            output_text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return {
            'input_ids': input_enc['input_ids'].squeeze(0),
            'attention_mask': input_enc['attention_mask'].squeeze(0),
            'labels': output_enc['input_ids'].squeeze(0)
        }

# Load tokenizer
tokenizer = T5Tokenizer.from_pretrained('t5-small')

# Load dataset
dataset = SchematicDataset(all_pairs, tokenizer)

# Split
train_size = int(0.8 * len(dataset))
test_size = len(dataset) - train_size
train_dataset, test_dataset = torch.utils.data.random_split(dataset, [train_size, test_size])

print(f"Train: {train_size}, Test: {test_size}")
```

## Train Model

```python
from transformers import T5ForConditionalGeneration, Trainer, TrainingArguments

# Load model
model = T5ForConditionalGeneration.from_pretrained('t5-small')

# Training arguments
training_args = TrainingArguments(
    output_dir='./models/t5-schematic',
    num_train_epochs=20,  # More epochs for small dataset
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    learning_rate=1e-4,
    weight_decay=0.01,
    save_steps=50,
    eval_steps=25,
    logging_steps=10,
    eval_strategy='steps',  # Fixed: was 'evaluation_strategy'
    save_total_limit=2,
    load_best_model_at_end=True,
    push_to_hub=False,
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
)

# Train
print("Starting training...")
trainer.train()

# Save
trainer.save_model('./models/t5-schematic')
print("Model saved!")

# Evaluate
eval_results = trainer.evaluate()
print("\nEvaluation results:")
for key, value in eval_results.items():
    print(f"{key}: {value:.4f}")
```

## Test Model

```python
def generate_schematic(model_path, description):
    from transformers import T5ForConditionalGeneration, T5Tokenizer
    
    model = T5ForConditionalGeneration.from_pretrained(model_path)
    tokenizer = T5Tokenizer.from_pretrained(model_path)
    
    input_text = f"generate schematic: {description}"
    input_enc = tokenizer(input_text, return_tensors='pt')
    
    output_ids = model.generate(
        input_enc['input_ids'],
        max_length=512,
        num_beams=4,
        early_stopping=True
    )
    
    output_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    return json.loads(output_text)

# Test
result = generate_schematic('./models/t5-schematic', 'Arduino with LED')
print(json.dumps(result, indent=2))
```

## Upload to HuggingFace (Optional)

```python
# Login to HuggingFace
!huggingface-cli login

# Upload model
trainer.push_to_hub('pcbai-t5-schematic')
```

## Download Trained Model

```python
# From HuggingFace
!git lfs install
!git clone https://huggingface.co/your-username/pcbai-t5-schematic models/t5-schematic
```

---

## Notes

- **Small dataset (27 pairs)**: Use 20+ epochs, small batch size (4)
- **Medium dataset (100+ pairs)**: Use 10 epochs, batch size 8
- **Large dataset (1000+ pairs)**: Use 5 epochs, batch size 16

**Expected training time:**
- 27 pairs: ~5 minutes (T4 GPU)
- 100 pairs: ~15 minutes (T4 GPU)
- 1000 pairs: ~1 hour (T4 GPU)
