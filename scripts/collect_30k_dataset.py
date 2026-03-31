#!/usr/bin/env python3
"""
PCBAI Dataset Collector — Collect 30,000 quality KiCad training pairs.

Sources:
  1. HuggingFace "bshada/open-schematics" (84k schematics) — primary
  2. GitHub repositories with .kicad_sch files — secondary

Features:
  - Checkpoint/resume support
  - Quality filtering and validation
  - Natural language description generation
  - Connection resolution from wire data

Usage:
    python scripts/collect_30k_dataset.py --target 30000
    python scripts/collect_30k_dataset.py --target 100 --source huggingface  # test run
    python scripts/collect_30k_dataset.py --resume  # resume from checkpoint
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from pcba.sexpr_parser import parse_kicad_sch
from pcba.connection_resolver import resolve_connections
from pcba.description_generator import generate_descriptions
from pcba.component_database import get_component_description, get_component_category


# ============================================================================
# Configuration
# ============================================================================

DATASETS_DIR = Path(__file__).parent.parent / 'datasets'
OUTPUT_PATH = DATASETS_DIR / 'training_30k.json'
CHECKPOINT_PATH = DATASETS_DIR / 'collection_progress.json'

# Quality filters
MIN_COMPONENTS = 2
MAX_COMPONENTS = 50
MIN_CONNECTIONS = 1
MIN_DESCRIPTION_LENGTH = 10
MIN_KICAD_VERSION = 20210000  # KiCad 6.0+

# Checkpoint interval
CHECKPOINT_EVERY = 100


# ============================================================================
# Checkpoint Manager
# ============================================================================

class CheckpointManager:
    """Manages checkpoint/resume for data collection."""

    def __init__(self, checkpoint_path: Path):
        self.path = checkpoint_path
        self.state = {
            'processed_hashes': [],
            'huggingface_index': 0,
            'github_repos_done': [],
            'pairs_collected': 0,
            'training_pairs': [],
        }
        self._hash_set = set()

    def load(self) -> bool:
        """Load checkpoint. Returns True if loaded."""
        if self.path.exists():
            try:
                with open(self.path, 'r') as f:
                    self.state = json.load(f)
                self._hash_set = set(self.state.get('processed_hashes', []))
                print(f"Resumed from checkpoint: {self.state['pairs_collected']} pairs collected")
                return True
            except (json.JSONDecodeError, KeyError):
                print("Corrupt checkpoint, starting fresh")
        return False

    def save(self):
        """Save checkpoint."""
        self.state['processed_hashes'] = list(self._hash_set)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, 'w') as f:
            json.dump(self.state, f)

    def is_processed(self, content_hash: str) -> bool:
        return content_hash in self._hash_set

    def mark_processed(self, content_hash: str):
        self._hash_set.add(content_hash)

    def add_pair(self, pair: dict):
        self.state['training_pairs'].append(pair)
        self.state['pairs_collected'] = len(self.state['training_pairs'])

    @property
    def pairs_count(self) -> int:
        return len(self.state.get('training_pairs', []))

    @property
    def training_pairs(self) -> list:
        return self.state.get('training_pairs', [])


# ============================================================================
# Schematic Processing
# ============================================================================

def content_hash(content: str) -> str:
    """SHA256 hash of normalized content."""
    normalized = re.sub(r'\s+', ' ', content.strip())
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def process_schematic(content: str) -> list[dict] | None:
    """
    Process a KiCad schematic into training pairs.

    Returns list of training pairs or None if invalid.
    """
    # Basic format check
    if '(kicad_sch' not in content:
        return None

    # Parse
    parsed = parse_kicad_sch(content)
    if not parsed:
        return None

    # Version check
    version = parsed.get('version')
    if version and version < MIN_KICAD_VERSION:
        return None

    # Component count check
    symbols = parsed.get('symbols', [])
    if len(symbols) < MIN_COMPONENTS or len(symbols) > MAX_COMPONENTS:
        return None

    # Must have wires
    if not parsed.get('wires'):
        return None

    # Resolve connections
    connections = resolve_connections(parsed)
    if len(connections) < MIN_CONNECTIONS:
        return None

    # Build component list for training
    components = []
    for sym in symbols:
        ref = sym.get('ref', '')
        lib_id = sym.get('lib_id', '')
        value = sym.get('value', '')

        if not ref or not lib_id or ref.startswith('#'):
            continue

        comp = {
            'ref': ref,
            'lib_id': lib_id,
            'type': get_component_description(lib_id),
            'value': value,
        }
        components.append(comp)

    if len(components) < MIN_COMPONENTS:
        return None

    # Generate descriptions (2 variants)
    descriptions = generate_descriptions(components, connections, count=2)
    if not descriptions or len(descriptions[0]) < MIN_DESCRIPTION_LENGTH:
        return None

    # Create training pairs
    pairs = []
    output_data = {
        'components': components,
        'connections': connections,
    }

    for desc in descriptions:
        pairs.append({
            'input': desc,
            'output': output_data,
            'metadata': {
                'component_count': len(components),
                'connection_count': len(connections),
                'kicad_version': version,
            }
        })

    return pairs


# ============================================================================
# HuggingFace Source
# ============================================================================

def collect_from_huggingface(
    checkpoint: CheckpointManager,
    target: int,
    limit: int | None = None,
) -> int:
    """
    Collect training pairs from HuggingFace open-schematics dataset.

    Returns number of pairs collected.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        print("Installing datasets library...")
        os.system('pip install datasets -q')
        from datasets import load_dataset

    print("\n" + "=" * 60)
    print("Collecting from HuggingFace: bshada/open-schematics")
    print("=" * 60 + "\n")

    try:
        dataset = load_dataset("bshada/open-schematics", split="train")
    except Exception as e:
        print(f"Error loading dataset: {e}")
        print("Trying alternative: Ju-C/open-schematics...")
        try:
            dataset = load_dataset("Ju-C/open-schematics", split="train")
        except Exception as e2:
            print(f"Alternative also failed: {e2}")
            return 0

    total = len(dataset)
    print(f"Dataset loaded: {total} entries")

    # Inspect columns
    columns = dataset.column_names
    print(f"Columns: {columns}")

    # Find the column with schematic content
    content_column = None
    for col in ['content', 'schematic', 'text', 'kicad_sch', 'data', 'file_content']:
        if col in columns:
            content_column = col
            break

    if not content_column:
        # Try to find by inspecting first row
        sample = dataset[0]
        for col, val in sample.items():
            if isinstance(val, str) and '(kicad_sch' in val:
                content_column = col
                break

    if not content_column:
        print(f"Could not find schematic content column!")
        print(f"Available columns: {columns}")
        # Show sample of first row
        sample = dataset[0]
        for col, val in sample.items():
            val_str = str(val)[:200]
            print(f"  {col}: {val_str}...")
        return 0

    print(f"Using column: '{content_column}'")

    start_index = checkpoint.state.get('huggingface_index', 0)
    collected = 0
    errors = 0

    if limit:
        end_index = min(start_index + limit, total)
    else:
        end_index = total

    for i in range(start_index, end_index):
        if checkpoint.pairs_count >= target:
            print(f"\nTarget reached: {target} pairs")
            break

        try:
            row = dataset[i]
            content = row[content_column]

            if not isinstance(content, str):
                continue

            # Check if already processed
            c_hash = content_hash(content)
            if checkpoint.is_processed(c_hash):
                continue

            # Process schematic
            pairs = process_schematic(content)
            checkpoint.mark_processed(c_hash)

            if pairs:
                for pair in pairs:
                    if checkpoint.pairs_count >= target:
                        break
                    pair['metadata']['source'] = 'huggingface'
                    pair['metadata']['source_index'] = i
                    checkpoint.add_pair(pair)
                    collected += 1

            # Progress
            if (i - start_index + 1) % 100 == 0:
                print(f"  Processed {i - start_index + 1}/{end_index - start_index} | "
                      f"Collected: {collected} | Total: {checkpoint.pairs_count}")

            # Checkpoint
            if (i - start_index + 1) % CHECKPOINT_EVERY == 0:
                checkpoint.state['huggingface_index'] = i + 1
                checkpoint.save()

        except Exception as e:
            errors += 1
            if errors % 100 == 0:
                print(f"  Errors so far: {errors} (last: {e})")
            continue

    # Final checkpoint
    checkpoint.state['huggingface_index'] = end_index
    checkpoint.save()

    print(f"\nHuggingFace collection done: {collected} pairs from {end_index - start_index} schematics")
    return collected


# ============================================================================
# GitHub Source
# ============================================================================

def collect_from_github(
    checkpoint: CheckpointManager,
    target: int,
    token: str | None = None,
) -> int:
    """
    Collect training pairs from GitHub repositories.

    Returns number of pairs collected.
    """
    try:
        import requests
    except ImportError:
        print("Installing requests...")
        os.system('pip install requests -q')
        import requests

    print("\n" + "=" * 60)
    print("Collecting from GitHub repositories")
    print("=" * 60 + "\n")

    token = token or os.environ.get('GITHUB_TOKEN')

    headers = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        headers['Authorization'] = f'token {token}'
        print("Using authenticated requests (5000 req/hour)")
    else:
        print("WARNING: No GITHUB_TOKEN set. Rate limited to 10 req/min.")
        print("Set GITHUB_TOKEN env var for better collection speed.")

    # Search queries
    search_queries = [
        'extension:kicad_sch kicad_sch',
        'extension:kicad_sch version',
        'extension:kicad_sch lib_symbols',
        'kicad schematic path:*.kicad_sch',
    ]

    collected = 0
    done_repos = set(checkpoint.state.get('github_repos_done', []))
    processed_files = set()

    for query in search_queries:
        if checkpoint.pairs_count >= target:
            break

        print(f"\nSearching: '{query}'")

        for page in range(1, 11):  # Max 10 pages per query
            if checkpoint.pairs_count >= target:
                break

            try:
                resp = requests.get(
                    'https://api.github.com/search/code',
                    headers=headers,
                    params={'q': query, 'per_page': 100, 'page': page},
                    timeout=30,
                )

                if resp.status_code == 403:
                    print("Rate limited. Waiting 60 seconds...")
                    time.sleep(60)
                    continue

                if resp.status_code != 200:
                    print(f"Search error: {resp.status_code}")
                    break

                items = resp.json().get('items', [])
                if not items:
                    break

                for item in items:
                    if checkpoint.pairs_count >= target:
                        break

                    repo = item.get('repository', {}).get('full_name', '')
                    file_path = item.get('path', '')
                    file_key = f"{repo}/{file_path}"

                    if file_key in processed_files:
                        continue
                    processed_files.add(file_key)

                    # Download raw content
                    raw_url = item.get('html_url', '').replace(
                        'github.com', 'raw.githubusercontent.com'
                    ).replace('/blob/', '/')

                    if not raw_url:
                        continue

                    try:
                        raw_resp = requests.get(raw_url, timeout=30)
                        if raw_resp.status_code != 200:
                            continue

                        content = raw_resp.text
                        c_hash = content_hash(content)

                        if checkpoint.is_processed(c_hash):
                            continue

                        pairs = process_schematic(content)
                        checkpoint.mark_processed(c_hash)

                        if pairs:
                            for pair in pairs:
                                if checkpoint.pairs_count >= target:
                                    break
                                pair['metadata']['source'] = 'github'
                                pair['metadata']['source_repo'] = repo
                                pair['metadata']['source_file'] = file_path
                                checkpoint.add_pair(pair)
                                collected += 1

                    except Exception:
                        continue

                # Rate limiting
                if not token:
                    time.sleep(6)  # 10 req/min for unauthenticated
                else:
                    time.sleep(1)

            except Exception as e:
                print(f"Search error: {e}")
                continue

        # Checkpoint after each query
        checkpoint.state['github_repos_done'] = list(done_repos)
        checkpoint.save()

    print(f"\nGitHub collection done: {collected} pairs")
    return collected


# ============================================================================
# Dataset Export
# ============================================================================

def export_dataset(checkpoint: CheckpointManager, output_path: Path):
    """Export collected pairs to final dataset JSON."""
    pairs = checkpoint.training_pairs

    dataset = {
        'metadata': {
            'version': '2.0',
            'created_by': 'PCBAI Dataset Collector',
            'total_pairs': len(pairs),
            'format': 'kicad_9.0_compatible',
            'sources': ['huggingface/bshada/open-schematics', 'github'],
        },
        'training_pairs': pairs,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False)

    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"\nDataset exported: {output_path}")
    print(f"  Total pairs: {len(pairs)}")
    print(f"  File size: {size_mb:.1f} MB")


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Collect 30,000 quality KiCad training pairs'
    )
    parser.add_argument(
        '--target', type=int, default=30000,
        help='Target number of training pairs (default: 30000)'
    )
    parser.add_argument(
        '--source', choices=['all', 'huggingface', 'github'], default='all',
        help='Data source to use (default: all)'
    )
    parser.add_argument(
        '--limit', type=int, default=None,
        help='Limit HuggingFace entries to process (for testing)'
    )
    parser.add_argument(
        '--resume', action='store_true',
        help='Resume from last checkpoint'
    )
    parser.add_argument(
        '--output', type=Path, default=OUTPUT_PATH,
        help='Output dataset path'
    )
    parser.add_argument(
        '--github-token', type=str, default=None,
        help='GitHub API token (or set GITHUB_TOKEN env var)'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("PCBAI Dataset Collector")
    print(f"Target: {args.target} training pairs")
    print(f"Source: {args.source}")
    print("=" * 60)

    # Initialize checkpoint
    checkpoint = CheckpointManager(CHECKPOINT_PATH)
    if args.resume:
        checkpoint.load()
    else:
        # Start fresh but keep old checkpoint as backup
        if CHECKPOINT_PATH.exists():
            backup = CHECKPOINT_PATH.with_suffix('.json.bak')
            CHECKPOINT_PATH.rename(backup)
            print(f"Old checkpoint backed up to {backup}")

    # Collect from sources
    if args.source in ('all', 'huggingface'):
        collect_from_huggingface(checkpoint, args.target, limit=args.limit)

    if args.source in ('all', 'github') and checkpoint.pairs_count < args.target:
        collect_from_github(checkpoint, args.target, token=args.github_token)

    # Export final dataset
    if checkpoint.pairs_count > 0:
        export_dataset(checkpoint, args.output)
    else:
        print("\nNo pairs collected! Check data source availability.")

    # Summary
    print("\n" + "=" * 60)
    print("COLLECTION COMPLETE")
    print(f"  Total pairs: {checkpoint.pairs_count}")
    print(f"  Target: {args.target}")
    print(f"  Coverage: {checkpoint.pairs_count / args.target * 100:.1f}%")
    print("=" * 60)

    # Cleanup checkpoint on success
    if checkpoint.pairs_count >= args.target:
        print("\nTarget reached! You can now train the model.")
        print(f"Dataset: {args.output}")


if __name__ == '__main__':
    main()
