#!/usr/bin/env python3
"""
Training Pipeline for Schematic Generation Model.

Trains a T5-small model for component extraction from natural language descriptions.

Usage:
    python train.py --epochs 10 --batch_size 8 --learning_rate 1e-4
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import T5Tokenizer, T5ForConditionalGeneration, Trainer, TrainingArguments


class SchematicDataset(Dataset):
    """Dataset for schematic generation training."""

    def __init__(self, data_path: str, tokenizer: T5Tokenizer, max_length: int = 512):
        """
        Initialize dataset.

        Args:
            data_path: Path to JSON dataset file
            tokenizer: T5 tokenizer
            max_length: Maximum sequence length
        """
        with open(data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        self.tokenizer = tokenizer
        self.max_length = max_length
        self.training_pairs = self.data.get('training_pairs', [])

    def __len__(self) -> int:
        return len(self.training_pairs)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        pair = self.training_pairs[idx]

        # Input: description
        input_text = f"generate schematic: {pair['input']}"

        # Output: components as JSON string
        output_components = {
            'components': pair['output']['components'],
        }
        output_text = json.dumps(output_components, ensure_ascii=False)

        # Tokenize
        input_encoding = self.tokenizer(
            input_text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        output_encoding = self.tokenizer(
            output_text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        return {
            'input_ids': input_encoding['input_ids'].squeeze(0),
            'attention_mask': input_encoding['attention_mask'].squeeze(0),
            'labels': output_encoding['input_ids'].squeeze(0)
        }


def load_dataset(data_path: str, tokenizer: T5Tokenizer, test_split: float = 0.2):
    """
    Load and split dataset into train/test.

    Args:
        data_path: Path to JSON dataset
        tokenizer: T5 tokenizer
        test_split: Fraction of data for testing

    Returns:
        train_dataset, test_dataset
    """
    dataset = SchematicDataset(data_path, tokenizer)

    # Split
    dataset_size = len(dataset)
    test_size = int(dataset_size * test_split)
    train_size = dataset_size - test_size

    train_dataset, test_dataset = torch.utils.data.random_split(
        dataset, [train_size, test_size]
    )

    print(f"Dataset split: {train_size} train, {test_size} test")

    return train_dataset, test_dataset


def train_model(
    train_dataset: Dataset,
    test_dataset: Dataset,
    output_dir: str,
    epochs: int = 10,
    batch_size: int = 8,
    learning_rate: float = 1e-4,
):
    """
    Train T5 model.

    Args:
        train_dataset: Training dataset
        test_dataset: Test dataset
        output_dir: Directory to save model
        epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Learning rate
    """
    # Initialize model
    model = T5ForConditionalGeneration.from_pretrained('t5-small')

    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=learning_rate,
        weight_decay=0.01,
        save_steps=100,
        eval_steps=50,
        logging_steps=10,
        evaluation_strategy='steps',
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
    print("\n" + "=" * 60)
    print("Starting training...")
    print("=" * 60 + "\n")

    trainer.train()

    # Save model
    trainer.save_model(output_dir)
    print(f"\n✓ Model saved to: {output_dir}")

    # Evaluate
    eval_results = trainer.evaluate()
    print("\n" + "=" * 60)
    print("Evaluation results:")
    print("=" * 60)
    for key, value in eval_results.items():
        print(f"{key}: {value:.4f}")

    return model


def generate_schematic(model_path: str, description: str):
    """
    Generate schematic from description using trained model.

    Args:
        model_path: Path to trained model
        description: Natural language description

    Returns:
        Generated components dict
    """
    # Load model and tokenizer
    model = T5ForConditionalGeneration.from_pretrained(model_path)
    tokenizer = T5Tokenizer.from_pretrained(model_path)

    # Prepare input
    input_text = f"generate schematic: {description}"
    input_encoding = tokenizer(
        input_text,
        return_tensors='pt',
        max_length=512,
        truncation=True
    )

    # Generate
    output_ids = model.generate(
        input_encoding['input_ids'],
        max_length=512,
        num_beams=4,
        early_stopping=True
    )

    # Decode
    output_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    components = json.loads(output_text)

    return components


def main():
    parser = argparse.ArgumentParser(description='Train schematic generation model')
    parser.add_argument('--data', type=str, default='datasets/schematic_generation.json',
                        help='Path to training dataset')
    parser.add_argument('--output', type=str, default='models/t5-schematic',
                        help='Output directory for trained model')
    parser.add_argument('--epochs', type=int, default=10,
                        help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=8,
                        help='Batch size')
    parser.add_argument('--learning_rate', type=float, default=1e-4,
                        help='Learning rate')
    parser.add_argument('--test_split', type=float, default=0.2,
                        help='Test split ratio')
    parser.add_argument('--demo', action='store_true',
                        help='Run demo generation after training')

    args = parser.parse_args()

    print("=" * 60)
    print("PCBAI Training Pipeline")
    print("=" * 60)

    # Check if dataset exists
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"\n⚠️  Dataset not found: {data_path}")
        print("Run: python scripts/collect_dataset.py first")
        return 1

    # Load dataset info
    with open(data_path, 'r', encoding='utf-8') as f:
        dataset_info = json.load(f)
    num_pairs = len(dataset_info.get('training_pairs', []))
    print(f"\nDataset: {data_path}")
    print(f"Training pairs: {num_pairs}")

    if num_pairs < 10:
        print("\n⚠️  Warning: Very small dataset (< 10 pairs)")
        print("For better results, collect at least 100+ pairs")
        print("Continuing with training anyway...")

    # Load tokenizer
    print("\nLoading T5 tokenizer...")
    tokenizer = T5Tokenizer.from_pretrained('t5-small')

    # Load and split dataset
    print("\nLoading dataset...")
    train_dataset, test_dataset = load_dataset(
        str(data_path),
        tokenizer,
        test_split=args.test_split
    )

    # Train model
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    model = train_model(
        train_dataset,
        test_dataset,
        str(output_dir),
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate
    )

    # Demo generation
    if args.demo:
        print("\n" + "=" * 60)
        print("Demo generation")
        print("=" * 60)

        test_descriptions = [
            "Arduino with LED",
            "Two resistors and capacitor",
            "ESP32 with DHT22 sensor",
        ]

        for desc in test_descriptions:
            print(f"\nInput: {desc}")
            try:
                result = generate_schematic(str(output_dir), desc)
                print(f"Output: {json.dumps(result, indent=2)[:200]}...")
            except Exception as e:
                print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)
    print(f"\nModel saved to: {output_dir.absolute()}")
    print("\nTo use the model:")
    print(f"  python train.py --demo --model {output_dir}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
