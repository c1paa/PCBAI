# 🚀 Complete Training Guide: 25000 Pairs

## 📋 Overview

This guide walks you through training a high-quality T5 model on 25,000 KiCad schematic pairs.

**Total Time:** ~5-15 hours (depending on GPU)  
**Cost:** Free (Google Colab) or ~$100 (Colab Pro+)

---

## 📥 Phase 1: Download Dataset (30 min)

### Step 1: Open Google Colab
```
https://colab.research.google.com
```

### Step 2: Create New Notebook

### Step 3: Copy and Run This Code

```python
# Phase 1: Download Dataset
!pip install datasets -q

# Clone PCBAI repo
!git clone https://github.com/c1paa/PCBAI.git
%cd PCBAI

# Download 84,000 schematics from HuggingFace
!python scripts/phase1_download_dataset.py \
  --output datasets/open_schematics \
  --limit 25000

# Check results
!ls -lh datasets/open_schematics/
```

**Expected Output:**
```
✅ Dataset saved: datasets/open_schematics/raw
   Total files: 25000
```

---

## 🔍 Phase 2: Create Training Pairs (1-2 hours)

```python
# Phase 2: Validate and create training pairs
!python scripts/phase2_create_training_pairs.py \
  --input datasets/open_schematics/validated \
  --output datasets/training_25k.json \
  --limit 25000

# Check results
!ls -lh datasets/training_25k.json
!python -c "import json; d=json.load(open('datasets/training_25k.json')); print(f'Pairs: {len(d[\"training_pairs\"])}')"
```

**Expected Output:**
```
✅ Phase 2 Complete!
  Total pairs created: 25000
  Dataset saved to: datasets/training_25k.json
  Dataset size: ~50 MB
```

---

## 🤖 Phase 3: Train Model (4-12 hours)

### Option A: Single Colab (Free)

```python
# Phase 3: Train model
!python scripts/phase3_train_model.py \
  --data datasets/training_25k.json \
  --output models/t5-25k \
  --epochs 10 \
  --batch_size 4 \
  --gradient_accumulation 4

# Training will take ~4-12 hours on T4 GPU
```

**Monitoring:**
- Loss should decrease over time
- Check every 1000 steps (~1 hour)
- Expected final loss: < 0.01

### Option B: Multiple Colabs (Faster)

**Split data into 3 parts:**

```python
# Split dataset
import json

with open('datasets/training_25k.json', 'r') as f:
    data = json.load(f)

pairs = data['training_pairs']

# Split into 3
split_size = len(pairs) // 3

for i in range(3):
    start = i * split_size
    end = start + split_size if i < 2 else len(pairs)
    
    split_data = {
        'metadata': data['metadata'],
        'training_pairs': pairs[start:end],
    }
    
    with open(f'datasets/training_split_{i}.json', 'w') as f:
        json.dump(split_data, f)
    
    print(f"Split {i}: {len(pairs[start:end])} pairs")
```

**Then train on 3 different Colabs (different Google accounts):**
```python
# Colab 1:
!python scripts/phase3_train_model.py --data datasets/training_split_0.json --output models/t5-split-0 --epochs 10

# Colab 2:
!python scripts/phase3_train_model.py --data datasets/training_split_1.json --output models/t5-split-1 --epochs 10

# Colab 3:
!python scripts/phase3_train_model.py --data datasets/training_split_2.json --output models/t5-split-2 --epochs 10
```

**Total time:** ~2-4 hours (parallel training)

### Option C: Colab Pro+ (Fastest)

```python
# Same as Option A but with V100/A100 GPU
# Training time: ~2-3 hours
```

---

## ✅ Phase 4: Test Model (30 min)

```python
# Test trained model
!python scripts/phase4_test_model.py \
  --model models/t5-25k \
  --test_samples 10

# Expected output:
# ✅ Test 1: PASS (valid JSON)
# ✅ Test 2: PASS (valid JSON)
# ...
```

---

## 📊 Expected Results

| Metric | Target | Excellent |
|--------|--------|-----------|
| Training loss | < 0.01 | < 0.005 |
| Eval loss | < 0.02 | < 0.01 |
| JSON validity | > 80% | > 95% |
| KiCad 9.0 valid | > 90% | > 98% |

---

## 💾 Download Model

```python
# Download to computer
from google.colab import files
!zip -r t5-25k.zip models/t5-25k
files.download('t5-25k.zip')

# Or save to Google Drive
from google.colab import drive
drive.mount('/content/drive')
!cp -r models/t5-25k /content/drive/MyDrive/PCBAI/models/
```

---

## 🔧 Integration into PCBAI

### Step 1: Extract Model
```bash
# In PCBAI project
unzip t5-25k.zip -p models/
```

### Step 2: Update Code
Edit `src/pcba/schematic.py`:
```python
# Replace LLM with trained model
from .trained_model_analyzer import TrainedModelAnalyzer

analyzer = TrainedModelAnalyzer('models/t5-25k')
circuit_data = analyzer.analyze(description)
```

### Step 3: Test
```bash
pcba schematic "Arduino with LED" -o test.kicad_sch
```

---

## ⚡ Training Speed Comparison

| Method | GPU | Time | Cost |
|--------|-----|------|------|
| Single Colab | T4 | 8-12 hrs | Free |
| 3x Colabs | 3x T4 | 3-4 hrs | Free |
| Colab Pro+ | V100 | 2-3 hrs | ~$100/mo |
| Colab Pro+ | A100 | 1-2 hrs | ~$100/mo |

---

## 🎯 Recommendations

### For Best Results:
1. **Use 25000+ pairs** (not 1000)
2. **Train 10+ epochs** (not 15, diminishing returns)
3. **Use FP16** (2x speedup, same quality)
4. **Monitor loss** (should decrease smoothly)
5. **Test frequently** (every 1000 steps)

### Common Issues:

**Issue:** Training too slow
- **Fix:** Reduce batch_size to 2, enable FP16

**Issue:** Out of memory
- **Fix:** Reduce batch_size, use gradient_accumulation=8

**Issue:** Loss not decreasing
- **Fix:** Check data quality, increase learning_rate

**Issue:** JSON invalid
- **Fix:** More training data, more epochs

---

## 📈 Next Steps After Training

1. **Validate** on held-out test set
2. **Test** in KiCad 9.0
3. **Integrate** into PCBAI
4. **Upload** to HuggingFace Hub
5. **Share** with community

---

**Ready to start? Run Phase 1!** 🚀
