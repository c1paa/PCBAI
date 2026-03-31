# PCBAI ML Training Guide

## Overview

This guide explains how to train the AI model for schematic generation.

---

## Prerequisites

1. **Python 3.10+**
2. **GPU recommended** (but CPU works for small datasets)
3. **Dataset** (at least 10 pairs, ideally 100+)

---

## Installation

### Install ML dependencies:
```bash
cd /Users/vladglazunov/Documents/algo/PCBAI
pip install -r requirements_ml.txt
```

### Verify installation:
```bash
python -c "import torch; import transformers; print('✓ ML dependencies installed')"
```

---

## Training

### Step 1: Collect Dataset

If you haven't collected a dataset yet:
```bash
python scripts/collect_dataset.py --output datasets/schematic_generation.json
```

This creates `datasets/schematic_generation.json` with training pairs.

### Step 2: Train Model

Basic training:
```bash
python train.py --epochs 10 --batch_size 8
```

Advanced options:
```bash
python train.py \
  --data datasets/schematic_generation.json \
  --output models/t5-schematic \
  --epochs 20 \
  --batch_size 16 \
  --learning_rate 5e-5 \
  --test_split 0.2
```

### Training Output:

```
============================================================
PCBAI Training Pipeline
============================================================

Dataset: datasets/schematic_generation.json
Training pairs: 27

Loading T5 tokenizer...
Loading dataset...
Dataset split: 21 train, 6 test

============================================================
Starting training...
============================================================

[Training progress...]

✓ Model saved to: models/t5-schematic

============================================================
Evaluation results:
============================================================
eval_loss: 0.2341
eval_runtime: 2.5s

============================================================
Training complete!
============================================================
```

---

## Inference (Using Trained Model)

### Demo mode:
```bash
python train.py --demo --output models/t5-schematic
```

### Programmatic use:
```python
from train import generate_schematic

components = generate_schematic(
    model_path='models/t5-schematic',
    description='Arduino with two LED on pin 5'
)

print(components)
# Output: {'components': [...]}
```

---

## Integration with PCBAI

To use the trained model in PCBAI:

### 1. Update `src/pcba/ai_analyzer.py`:

```python
class TrainedModelAnalyzer:
    def __init__(self, model_path: str):
        from train import generate_schematic
        self.model_path = model_path
    
    def analyze(self, description: str) -> dict:
        components = generate_schematic(self.model_path, description)
        return {
            'components': components['components'],
            'connections': [],  # Use rule-based connection
            'configuration': 'parallel',
        }

# In CircuitAnalyzer.analyze():
if USE_TRAINED_MODEL:
    analyzer = TrainedModelAnalyzer('models/t5-schematic')
    analysis = analyzer.analyze(description)
```

### 2. Set environment variable:
```bash
export PCBAI_USE_TRAINED_MODEL=1
export PCBAI_MODEL_PATH=models/t5-schematic
```

---

## Dataset Expansion

### Current dataset: 27 pairs

### Target: 1000+ pairs

#### Option 1: Scrape GitHub
```python
# scripts/scrape_github.py (TODO)
# Search for KiCad projects
# Download .kicad_sch files
# Extract from README descriptions
```

#### Option 2: Manual creation
Add examples to `examples/` directory:
```bash
# Create new project
mkdir examples/my_circuit
cd examples/my_circuit
# Design in KiCad
# Save schematic
```

Then collect:
```bash
python scripts/collect_dataset.py --output datasets/schematic_generation.json
```

---

## Troubleshooting

### Problem: CUDA out of memory
**Solution:** Reduce batch size
```bash
python train.py --batch_size 4
```

### Problem: Slow training
**Solution:** Use GPU or reduce epochs
```bash
# Check if CUDA available
python -c "import torch; print(torch.cuda.is_available())"

# If False, training on CPU (slow)
# Consider using Google Colab or GPU cloud
```

### Problem: Poor generation quality
**Solution:** Need more training data
- Current: 27 pairs (too small)
- Target: 100+ pairs (minimum)
- Ideal: 1000+ pairs

---

## Performance Metrics

### Training Time (T5-small):
- **27 pairs:** ~5 minutes (10 epochs, CPU)
- **100 pairs:** ~15 minutes (10 epochs, CPU)
- **1000 pairs:** ~2 hours (10 epochs, GPU)

### Inference Time:
- **CPU:** ~500ms per description
- **GPU:** ~50ms per description

### Accuracy:
- **Component extraction:** Target 90%+
- **Connection prediction:** Target 85%+

---

## Next Steps

1. **Collect more data** (target: 1000+ pairs)
2. **Train on GPU** (faster, larger models)
3. **Implement GNN** for connection prediction
4. **Integrate with PCBAI** pipeline
5. **User testing** and iteration

---

**Current Status:** Training pipeline ready, waiting for larger dataset 🚀
