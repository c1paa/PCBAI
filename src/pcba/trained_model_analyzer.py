"""
Trained Model Analyzer — Integration for trained T5 model with post-processing.

Uses the trained T5 model to generate schematics from descriptions,
then runs the postprocessor pipeline to validate and fix output.
"""

import json
import os
from pathlib import Path
from typing import Any

from .postprocessor import SchematicPostprocessor, ProcessingResult


class TrainedModelAnalyzer:
    """Analyze circuit descriptions using trained T5 model."""

    def __init__(self, model_path: str | None = None):
        """
        Initialize trained model analyzer.

        Args:
            model_path: Path to trained T5 model directory.
                       If None, uses fallback LLM analyzer.
        """
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.postprocessor = SchematicPostprocessor()

        if model_path and Path(model_path).exists():
            self._load_model()

    def _load_model(self):
        """Load trained model and tokenizer."""
        try:
            from transformers import T5ForConditionalGeneration, T5Tokenizer

            print(f"Loading trained model from: {self.model_path}")
            self.tokenizer = T5Tokenizer.from_pretrained(self.model_path)
            self.model = T5ForConditionalGeneration.from_pretrained(self.model_path)
            print("Model loaded successfully")
        except Exception as e:
            print(f"Failed to load model: {e}")
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
            return self._fallback_analysis(description)

        # Generate with model
        raw_output = self._generate(description)

        # Post-process
        result = self.postprocessor.process(raw_output, description)

        if result.success:
            return {
                'circuit_type': 'custom',
                'description': description,
                'components': result.components,
                'connections': result.connections,
                'configuration': 'parallel',
                'mcu_pin': None,
                'power': {'positive': '+5V', 'ground': 'GND'},
                'questions': [],
                'schematic_content': result.schematic_content,
                'fixes_applied': result.fixes_applied,
                'warnings': result.warnings,
            }

        # If postprocessor failed, try fallback
        print(f"Post-processing failed: {result.errors}")
        return self._fallback_analysis(description)

    def generate_schematic(self, description: str) -> ProcessingResult:
        """
        Generate a complete .kicad_sch file from description.

        Args:
            description: Natural language description

        Returns:
            ProcessingResult with schematic content
        """
        if self.model is None or self.tokenizer is None:
            return ProcessingResult(
                success=False,
                errors=["Model not loaded"],
            )

        raw_output = self._generate(description)
        return self.postprocessor.process(raw_output, description)

    def _generate(self, description: str) -> str:
        """Generate raw model output."""
        input_text = f"generate schematic: {description}"
        input_encoding = self.tokenizer(
            input_text,
            return_tensors='pt',
            max_length=256,
            truncation=True,
        )

        output_ids = self.model.generate(
            input_encoding['input_ids'],
            max_length=512,
            num_beams=4,
            early_stopping=True,
            no_repeat_ngram_size=3,
            length_penalty=1.0,
        )

        return self.tokenizer.decode(output_ids[0], skip_special_tokens=True)

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
    # Check multiple possible model paths
    model_paths = [
        os.environ.get('PCBAI_MODEL_PATH', ''),
        'models/t5-kicad-30k',
        'models/t5-schematic',
    ]

    for model_path in model_paths:
        if model_path and Path(model_path).exists():
            analyzer = TrainedModelAnalyzer(model_path)
            return analyzer.analyze(description)

    # Fallback to LLM
    from .ai_analyzer import EnhancedCircuitAnalyzer
    from .schematic import LLMClient, load_config

    config = load_config()
    llm = LLMClient(config)
    analyzer = EnhancedCircuitAnalyzer(llm)
    return analyzer.analyze(description)
