#!/usr/bin/env python3
"""
Phase 1: Download & Validate Open Schematics Dataset.

Downloads 84,000 KiCad schematics from HuggingFace and validates them.

Usage:
    python scripts/phase1_download_dataset.py --output datasets/open_schematics --limit 25000
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from datasets import load_dataset
except ImportError:
    print("Installing datasets library...")
    os.system('pip install datasets -q')
    from datasets import load_dataset


def download_dataset(output_dir: Path, limit: int = None) -> Path:
    """
    Download Open Schematics dataset from HuggingFace.
    
    Args:
        output_dir: Directory to save dataset
        limit: Maximum number of schematics to download (None = all)
        
    Returns:
        Path to downloaded dataset
    """
    print(f"\n{'='*60}")
    print("Phase 1: Downloading Open Schematics Dataset")
    print(f"{'='*60}\n")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading dataset from HuggingFace...")
    print(f"Dataset: bshada/open-schematics (84,000 schematics)")
    
    try:
        # Load dataset
        dataset = load_dataset("bshada/open-schematics", split="train")
        
        if limit:
            print(f"Limiting to {limit} schematics...")
            dataset = dataset.select(range(min(limit, len(dataset))))
        
        print(f"Loaded {len(dataset)} schematics")
        
        # Save to disk
        save_path = output_dir / "raw"
        print(f"Saving to {save_path}...")
        dataset.save_to_disk(str(save_path))
        
        print(f"✅ Dataset saved: {save_path}")
        print(f"   Total files: {len(dataset)}")
        
        return save_path
        
    except Exception as e:
        print(f"❌ Error downloading dataset: {e}")
        print("\nTrying alternative dataset...")
        
        # Fallback to alternative dataset
        try:
            dataset = load_dataset("Ju-C/open-schematics", split="train")
            if limit:
                dataset = dataset.select(range(min(limit, len(dataset))))
            
            save_path = output_dir / "raw"
            dataset.save_to_disk(str(save_path))
            
            print(f"✅ Alternative dataset saved: {save_path}")
            return save_path
            
        except Exception as e2:
            print(f"❌ Error with alternative dataset: {e2}")
            return None


def validate_schematic_file(file_path: Path) -> dict:
    """
    Validate a single KiCad schematic file.
    
    Args:
        file_path: Path to .kicad_sch file
        
    Returns:
        Validation result dict
    """
    result = {
        'valid': False,
        'kicad_version': None,
        'component_count': 0,
        'connection_count': 0,
        'errors': []
    }
    
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Check KiCad version
        import re
        version_match = re.search(r'\(version\s+(\d+)\)', content)
        if version_match:
            version = int(version_match.group(1))
            result['kicad_version'] = version
            
            # KiCad 6.0+ compatible with 9.0
            if version < 20210000:  # KiCad 6.0 version format
                result['errors'].append(f"KiCad version too old: {version}")
                return result
        
        # Count components
        result['component_count'] = len(re.findall(r'\(symbol\s+\(lib_id', content))
        
        # Count connections (wires)
        result['connection_count'] = len(re.findall(r'\(wire', content))
        
        # Check for required sections
        if '(kicad_sch' not in content:
            result['errors'].append("Missing kicad_sch header")
            return result
        
        if '(uuid' not in content:
            result['errors'].append("Missing UUID")
            return result
        
        # Passed validation
        result['valid'] = True
        return result
        
    except Exception as e:
        result['errors'].append(str(e))
        return result


def validate_dataset(raw_dir: Path, output_dir: Path) -> Path:
    """
    Validate all schematics in dataset.
    
    Args:
        raw_dir: Directory with raw dataset
        output_dir: Directory to save validated data
        
    Returns:
        Path to validated dataset
    """
    print(f"\n{'='*60}")
    print("Phase 1: Validating Schematics")
    print(f"{'='*60}\n")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all .kicad_sch files
    sch_files = list(raw_dir.glob('**/*.kicad_sch'))
    
    if not sch_files:
        # Try parquet format
        print("No .kicad_sch files found, checking parquet format...")
        parquet_files = list(raw_dir.glob('**/*.parquet'))
        if parquet_files:
            print(f"Found {len(parquet_files)} parquet files")
            # Will need to extract schematics from parquet
            return extract_from_parquet(raw_dir, output_dir)
        else:
            print("❌ No schematic files found!")
            return None
    
    print(f"Found {len(sch_files)} schematic files")
    print("Validating...\n")
    
    valid_count = 0
    invalid_count = 0
    kicad9_count = 0
    
    validated_data = []
    
    for i, sch_file in enumerate(sch_files):
        if (i + 1) % 1000 == 0:
            print(f"  Processed {i + 1}/{len(sch_files)} files...")
        
        result = validate_schematic_file(sch_file)
        
        if result['valid']:
            valid_count += 1
            
            # Check if KiCad 9.0 compatible (6.0+)
            if result['kicad_version'] and result['kicad_version'] >= 20210000:
                kicad9_count += 1
            
            # Filter: 2-50 components (not too simple, not too complex)
            if 2 <= result['component_count'] <= 50:
                validated_data.append({
                    'file': str(sch_file),
                    'component_count': result['component_count'],
                    'connection_count': result['connection_count'],
                    'kicad_version': result['kicad_version'],
                })
        else:
            invalid_count += 1
    
    # Save validation results
    validation_report = {
        'total_files': len(sch_files),
        'valid_files': valid_count,
        'invalid_files': invalid_count,
        'kicad9_compatible': kicad9_count,
        'filtered_for_training': len(validated_data),
        'validated_data': validated_data,
    }
    
    report_path = output_dir / 'validation_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(validation_report, f, indent=2)
    
    print(f"\n{'='*60}")
    print("Validation Results:")
    print(f"  Total files: {len(sch_files)}")
    print(f"  Valid: {valid_count}")
    print(f"  Invalid: {invalid_count}")
    print(f"  KiCad 9.0 compatible: {kicad9_count}")
    print(f"  Filtered for training: {len(validated_data)}")
    print(f"\nReport saved to: {report_path}")
    print(f"{'='*60}\n")
    
    return output_dir


def extract_from_parquet(raw_dir: Path, output_dir: Path) -> Path:
    """
    Extract schematics from parquet format.
    
    Args:
        raw_dir: Directory with parquet files
        output_dir: Directory to save extracted data
        
    Returns:
        Path to extracted dataset
    """
    print("\nExtracting schematics from parquet format...")
    
    try:
        import pandas as pd
        
        parquet_files = list(raw_dir.glob('**/*.parquet'))
        all_data = []
        
        for pq_file in parquet_files:
            print(f"  Reading {pq_file.name}...")
            df = pd.read_parquet(pq_file)
            
            # Extract relevant columns
            for _, row in df.iterrows():
                # Adjust column names based on actual dataset
                if 'schematic' in row:
                    all_data.append({
                        'schematic': row['schematic'],
                        'source': str(pq_file),
                    })
        
        print(f"Extracted {len(all_data)} schematics")
        
        # Save as JSON
        output_file = output_dir / 'extracted_schematics.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2)
        
        print(f"✅ Saved to: {output_file}")
        return output_dir
        
    except Exception as e:
        print(f"❌ Error extracting from parquet: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Download and validate Open Schematics dataset'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('datasets/open_schematics'),
        help='Output directory for dataset'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of schematics to download'
    )

    args = parser.parse_args()

    print("="*60)
    print("PCBAI - Phase 1: Dataset Download & Validation")
    print("="*60)

    # Download
    raw_dir = download_dataset(args.output, limit=args.limit)
    
    if not raw_dir:
        print("\n❌ Dataset download failed!")
        return 1
    
    # Validate
    validated_dir = validate_dataset(raw_dir, args.output / 'validated')
    
    if not validated_dir:
        print("\n❌ Dataset validation failed!")
        return 1
    
    print("\n✅ Phase 1 Complete!")
    print(f"Next: Run Phase 2 (filter to 25k high-quality pairs)")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
