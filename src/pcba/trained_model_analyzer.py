"""
Trained Model Analyzer - Integration for trained T5 model.

This module integrates the trained T5 model into the PCBAI pipeline.
"""

import json
from pathlib import Path
from typing import Any


class TrainedModelAnalyzer:
    """Analyze circuit descriptions using trained T5 model."""

    def __init__(self, model_path: str | None = None):
        """
        Initialize trained model analyzer.

        Args:
            model_path: Path to trained T5 model
                       If None, uses fallback LLM analyzer
        """
        self.model_path = model_path
        self.model = None
        self.tokenizer = None

        if model_path and Path(model_path).exists():
            self._load_model()

    def _load_model(self):
        """Load trained model and tokenizer."""
        try:
            from transformers import T5ForConditionalGeneration, T5Tokenizer

            print(f"Loading trained model from: {self.model_path}")
            self.tokenizer = T5Tokenizer.from_pretrained(self.model_path)
            self.model = T5ForConditionalGeneration.from_pretrained(self.model_path)
            print("✓ Model loaded successfully")
        except Exception as e:
            print(f"⚠️  Failed to load model: {e}")
            print("Falling back to LLM analyzer")
            self.model = None
            self.tokenizer = None

    def analyze(self, description: str) -> dict[str, Any]:
        """
        Analyze circuit description using trained model.

        Args:
            description: Natural language description

        Returns:
            Analysis dict with components, connections, etc.
        """
        if self.model is None or self.tokenizer is None:
            # Fallback to LLM
            return self._fallback_analysis(description)

        # Prepare input
        input_text = f"generate schematic: {description}"
        input_encoding = self.tokenizer(
            input_text,
            return_tensors='pt',
            max_length=512,
            truncation=True
        )

        # Generate
        output_ids = self.model.generate(
            input_encoding['input_ids'],
            max_length=512,
            num_beams=4,
            early_stopping=True
        )

        # Decode
        output_text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)

        try:
            components_data = json.loads(output_text)
        except json.JSONDecodeError:
            print(f"⚠️  Failed to parse model output, using fallback")
            return self._fallback_analysis(description)

        # Convert to standard format
        return {
            'circuit_type': 'custom',
            'description': description,
            'components': components_data.get('components', []),
            'connections': [],  # Use rule-based connection generator
            'configuration': 'parallel',
            'mcu_pin': None,
            'power': {'positive': '+5V', 'ground': 'GND'},
            'questions': [],
        }

    def _fallback_analysis(self, description: str) -> dict[str, Any]:
        """Fallback to LLM-based analysis."""
        from .ai_analyzer import EnhancedCircuitAnalyzer
        from .schematic import LLMClient, load_config

        config = load_config()
        llm = LLMClient(config)
        analyzer = EnhancedCircuitAnalyzer(llm)

        return analyzer.analyze(description)


def use_trained_model_if_available(description: str) -> dict[str, Any]:
    """
    Analyze description using trained model if available, otherwise use LLM.

    Args:
        description: Circuit description

    Returns:
        Analysis dict
    """
    import os

    model_path = os.environ.get('PCBAI_MODEL_PATH', 'models/t5-schematic')

    if Path(model_path).exists():
        analyzer = TrainedModelAnalyzer(model_path)
        return analyzer.analyze(description)
    else:
        # Fallback to LLM
        from .ai_analyzer import EnhancedCircuitAnalyzer
        from .schematic import LLMClient, load_config

        config = load_config()
        llm = LLMClient(config)
        analyzer = EnhancedCircuitAnalyzer(llm)
        return analyzer.analyze(description)
