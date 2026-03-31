# Model Selection for Schematic Generation

**Task:** 3.2 - Choose best ML model for circuit generation

**Date:** 2026-03-31

---

## Problem Statement

Generate KiCad schematics from natural language descriptions:
- Input: "Arduino with two LED on pin 5"
- Output: Structured schematic (components + connections)

This is a **graph generation problem**:
- Components = nodes
- Wires = edges
- Pin connections = node attributes

---

## Model Options

### 1. Graph Neural Networks (GNN)

**Architecture:**
- Encoder: Text → Graph embedding
- Decoder: Graph embedding → Component graph
- Model: Graph Transformer or GAT (Graph Attention Network)

**Pros:**
- ✅ Natural for circuit graphs
- ✅ Captures connectivity patterns
- ✅ State-of-the-art for graph generation

**Cons:**
- ❌ Complex to implement
- ❌ Requires graph libraries (PyTorch Geometric, DGL)
- ❌ Training data needs graph format

**Libraries:**
- PyTorch Geometric
- Deep Graph Library (DGL)
- GraphGym

**Estimated accuracy:** High (85-95%)
**Estimated speed:** Medium (100-500ms inference)
**Memory:** Low-Medium (100-500MB)

**Recommendation:** ⭐⭐⭐⭐ (4/5)

---

### 2. Transformer on Netlists

**Architecture:**
- Encoder: Text description (BERT-style)
- Decoder: Netlist sequence (Transformer decoder)
- Output: Sequential list of components + connections

**Pros:**
- ✅ Good at sequence generation
- ✅ Standard Transformer architecture
- ✅ Easy to implement with HuggingFace

**Cons:**
- ❌ May not capture graph structure well
- ❌ Sequential output may miss connectivity
- ❌ Needs post-processing to validate connections

**Libraries:**
- HuggingFace Transformers
- Fairseq
- ESPnet

**Estimated accuracy:** Medium-High (75-85%)
**Estimated speed:** Fast (50-200ms inference)
**Memory:** Medium (200-800MB)

**Recommendation:** ⭐⭐⭐⭐ (4/5)

---

### 3. Fine-tune CodeLlama on Schematics

**Architecture:**
- Base: CodeLlama 7B or 13B
- Fine-tune on (description, schematic JSON) pairs
- Output: JSON schematic

**Pros:**
- ✅ Already knows code/JSON structure
- ✅ High quality generation
- ✅ Can handle complex descriptions

**Cons:**
- ❌ Very large (7-13B parameters)
- ❌ Slow inference (1-5 seconds)
- ❌ High memory (8-16GB GPU)
- ❌ Overkill for this task

**Libraries:**
- llama.cpp
- vLLM
- HuggingFace Transformers

**Estimated accuracy:** High (85-95%)
**Estimated speed:** Slow (1000-5000ms inference)
**Memory:** High (8-16GB)

**Recommendation:** ⭐⭐ (2/5)

---

### 4. Hybrid Approach (Recommended)

**Architecture:**
1. **LLM (small)** for component extraction:
   - Input: "Arduino with two LED on pin 5"
   - Output: List of components (Arduino, LED x2, Resistor)

2. **GNN/Rule-based** for connection generation:
   - Input: Component list
   - Output: Connections based on learned patterns

3. **Validator** for ERC/DRC checks:
   - Input: Generated schematic
   - Output: Validated + fixed schematic

**Pros:**
- ✅ Best of both worlds
- ✅ LLM handles natural language
- ✅ GNN handles connectivity
- ✅ Validator ensures correctness
- ✅ Modular and debuggable

**Cons:**
- ❌ More complex pipeline
- ❌ Multiple models to train

**Implementation:**
- LLM: Fine-tuned T5-small or BART-base
- GNN: Graph Transformer or GAT
- Validator: Existing circuit_validator.py

**Estimated accuracy:** Very High (90-98%)
**Estimated speed:** Medium (200-600ms)
**Memory:** Medium (500MB-1GB)

**Recommendation:** ⭐⭐⭐⭐⭐ (5/5) **← BEST CHOICE**

---

## Comparison Table

| Model | Accuracy | Speed | Memory | Complexity | Overall |
|-------|----------|-------|--------|------------|---------|
| GNN | 85-95% | Medium | Low | High | 4/5 |
| Transformer | 75-85% | Fast | Medium | Medium | 4/5 |
| CodeLlama | 85-95% | Slow | High | Low | 2/5 |
| **Hybrid** | **90-98%** | **Medium** | **Medium** | **High** | **5/5** |

---

## Final Recommendation

**Use Hybrid Approach:**

1. **Phase 1 (Immediate):** Use existing LLM (Ollama) for component extraction
   - No training needed
   - Works now with current dataset (27 pairs)

2. **Phase 2 (Short-term):** Train small T5/BART for component extraction
   - Dataset: Current 27 pairs + more from GitHub
   - Target: 500+ pairs
   - Model: T5-small (60M parameters)

3. **Phase 3 (Long-term):** Add GNN for connection prediction
   - Learn connection patterns from dataset
   - Graph Transformer architecture
   - Target: 1000+ pairs

---

## Implementation Plan

### Week 1: LLM Component Extraction
- [ ] Fine-tune T5-small on (description → components)
- [ ] Train on current dataset (27 pairs)
- [ ] Evaluate accuracy

### Week 2-3: Expand Dataset
- [ ] Scrape GitHub for KiCad projects
- [ ] Parse 1000+ schematics
- [ ] Create training pairs

### Week 4-6: GNN Connection Prediction
- [ ] Implement Graph Transformer
- [ ] Train on connection patterns
- [ ] Integrate with LLM extractor

### Week 7: Integration
- [ ] Combine LLM + GNN + Validator
- [ ] End-to-end testing
- [ ] Deploy to PCBAI

---

## Resources

**Datasets:**
- Current: 27 pairs (PCBAI examples)
- Target: 1000+ pairs (GitHub scraping)

**Compute:**
- Training: GPU cluster (NVIDIA V100/A100)
- Inference: CPU or small GPU

**Code:**
- GNN: https://pytorch-geometric.readthedocs.io/
- Transformers: https://huggingface.co/docs/transformers/

---

**Decision:** Start with Hybrid Approach using existing LLM, then train dedicated models.

**Next Task:** 3.3 - Training Pipeline
