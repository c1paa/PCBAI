#!/usr/bin/env python3
"""
KiCad Schematic Dataset Collector - GitHub Scraper.

Scrapes GitHub for KiCad projects and collects 1000+ .kicad_sch files.

Usage:
    python scripts/collect_1000_dataset.py --output datasets/large_dataset.json --limit 1000
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system('pip install requests')
    import requests


def search_github_kicad_projects(limit: int = 100) -> list[dict]:
    """
    Search GitHub for KiCad projects.

    Args:
        limit: Maximum number of repos to return

    Returns:
        List of repository info dicts
    """
    repos = []
    page = 1
    
    print(f"Searching GitHub for KiCad projects (target: {limit} repos)...")
    
    while len(repos) < limit:
        url = "https://api.github.com/search/repositories"
        params = {
            'q': 'kicad schematic',
            'sort': 'stars',
            'order': 'desc',
            'per_page': min(100, limit - len(repos)),
            'page': page
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                break
            
            for item in items:
                repos.append({
                    'name': item['full_name'],
                    'url': item['html_url'],
                    'stars': item['stargazers_count'],
                    'default_branch': item['default_branch'],
                })
            
            print(f"  Page {page}: Found {len(items)} repos (total: {len(repos)})")
            page += 1
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"Error searching GitHub: {e}")
            break
    
    return repos


def download_raw_file(raw_url: str, local_path: Path) -> bool:
    """Download a raw file from GitHub."""
    try:
        response = requests.get(raw_url, timeout=30)
        response.raise_for_status()
        
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        return True
        
    except Exception as e:
        print(f"Error downloading {raw_url}: {e}")
        return False


def extract_description_from_content(content: str) -> str:
    """Extract or generate description from schematic content."""
    # Count components
    component_count = len(re.findall(r'\(symbol\s+\(lib_id', content))
    wire_count = len(re.findall(r'\(wire', content))
    
    # Generate description
    if component_count < 5:
        desc = "simple circuit"
    elif component_count < 20:
        desc = "medium complexity circuit"
    else:
        desc = "complex circuit"
    
    return f"KiCad schematic with {component_count} components and {wire_count} connections, {desc}"


def scrape_kicad_schematics(repo: dict, output_dir: Path, max_per_repo: int = 10) -> list[dict]:
    """
    Download .kicad_sch files from a repository.

    Args:
        repo: Repository info dict
        output_dir: Directory to save files
        max_per_repo: Maximum schematics per repo

    Returns:
        List of collected schematic info
    """
    schematics = []
    
    repo_name = repo['name'].replace('/', '_')
    repo_dir = output_dir / 'github_schematics' / repo_name
    
    print(f"  Scraping {repo['name']}...")
    
    # Use GitHub API to find .kicad_sch files
    search_url = f"https://api.github.com/search/code"
    params = {
        'q': f'extension:kicad_sch repo:{repo["name"]}',
        'per_page': max_per_repo,
    }
    
    try:
        response = requests.get(search_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        items = data.get('items', [])
        
        for i, item in enumerate(items[:max_per_repo]):
            raw_url = item.get('html_url', '').replace('/blob/', '/raw/')
            
            if not raw_url:
                continue
            
            # Download file
            local_path = repo_dir / f"{i:03d}_{item['name']}"
            
            if download_raw_file(raw_url, local_path):
                # Parse schematic
                content = local_path.read_text()
                
                # Skip if too small
                if len(content) < 1000:
                    continue
                
                # Count components (exclude lib_symbols)
                in_lib_symbols = False
                actual_components = 0
                
                for line in content.split('\n'):
                    if '(lib_symbols' in line:
                        in_lib_symbols = True
                    elif in_lib_symbols and ')' in line:
                        in_lib_symbols = False
                    elif '(symbol' in line and not in_lib_symbols and '(lib_id' in line:
                        actual_components += 1
                
                if actual_components < 2:
                    continue
                
                # Generate description
                description = extract_description_from_content(content)
                
                # Create training pair
                schematics.append({
                    'input': description,
                    'output': {
                        'components': [],  # Would need full parsing
                        'source_file': str(local_path.absolute()),
                    },
                    'metadata': {
                        'repo': repo['name'],
                        'component_count': actual_components,
                    }
                })
                
                print(f"    ✓ {item['name']} ({actual_components} components)")
        
        # Rate limiting
        time.sleep(1)
        
    except Exception as e:
        print(f"    Error: {e}")
    
    return schematics


def collect_from_local_examples(output_dir: Path) -> list[dict]:
    """Collect schematics from local examples directory."""
    schematics = []
    
    examples_dirs = [
        Path('examples/test1'),
        Path('examples'),
    ]
    
    for examples_dir in examples_dirs:
        if not examples_dir.exists():
            continue
            
        for sch_file in examples_dir.glob('**/*.kicad_sch'):
            if not sch_file.is_file():
                continue
                
            content = sch_file.read_text()
            
            # Skip if too small
            if len(content) < 1000:
                continue
            
            # Count components
            in_lib_symbols = False
            actual_components = 0
            
            for line in content.split('\n'):
                if '(lib_symbols' in line:
                    in_lib_symbols = True
                elif in_lib_symbols and ')' in line:
                    in_lib_symbols = False
                elif '(symbol' in line and not in_lib_symbols and '(lib_id' in line:
                    actual_components += 1
            
            if actual_components < 2:
                continue
            
            # Generate description
            description = f"KiCad schematic: {sch_file.stem.replace('_', ' ').replace('-', ' ')}"
            
            schematics.append({
                'input': description,
                'output': {
                    'components': [],
                    'source_file': str(sch_file.absolute()),
                },
                'metadata': {
                    'component_count': actual_components,
                }
            })
            
            print(f"  ✓ Collected: {sch_file.name} ({actual_components} components)")
    
    return schematics


def main():
    parser = argparse.ArgumentParser(description='Collect 1000+ KiCad schematic pairs')
    parser.add_argument('--output', type=str, default='datasets/large_dataset.json',
                        help='Output JSON file path')
    parser.add_argument('--limit', type=int, default=1000,
                        help='Target number of schematic pairs')
    parser.add_argument('--repos', type=int, default=100,
                        help='Number of GitHub repos to scrape')
    parser.add_argument('--local-only', action='store_true',
                        help='Only collect from local examples')

    args = parser.parse_args()

    print("=" * 60)
    print("KiCad Large Dataset Collector")
    print(f"Target: {args.limit} schematic pairs")
    print("=" * 60)

    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_pairs = []

    if not args.local_only:
        # Search GitHub
        repos = search_github_kicad_projects(limit=args.repos)
        
        print(f"\nFound {len(repos)} repositories")
        print("\nScraping schematics...")
        
        for repo in repos:
            schematics = scrape_kicad_schematics(
                repo, 
                output_path.parent,
                max_per_repo=10
            )
            all_pairs.extend(schematics)
            
            print(f"  Total collected: {len(all_pairs)}")
            
            if len(all_pairs) >= args.limit:
                break
            
            # Rate limiting
            time.sleep(0.5)
    
    # Also collect local
    print("\nCollecting from local examples...")
    local_schematics = collect_from_local_examples(output_path.parent)
    all_pairs.extend(local_schematics)

    # Remove duplicates
    seen_sources = set()
    unique_pairs = []
    for pair in all_pairs:
        source = pair['output'].get('source_file', '')
        if source not in seen_sources:
            seen_sources.add(source)
            unique_pairs.append(pair)

    all_pairs = unique_pairs

    # Save dataset
    dataset = {
        'metadata': {
            'version': '1.0',
            'created_by': 'PCBAI Large Dataset Collector',
            'total_pairs': len(all_pairs),
            'source': 'GitHub + local examples',
            'target': args.limit,
        },
        'training_pairs': all_pairs,
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"Dataset saved to: {output_path}")
    print(f"Total training pairs: {len(all_pairs)}")
    
    if len(all_pairs) < args.limit:
        print(f"\n⚠️  Collected {len(all_pairs)}/{args.limit} pairs")
        print("Consider:")
        print("  - Increasing --repos limit")
        print("  - Using GitHub token for higher rate limits")
        print("  - Manual collection from more projects")
    
    print("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
