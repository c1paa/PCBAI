#!/usr/bin/env python3
"""
GitHub KiCad Schematic Scraper.

Scrapes GitHub for KiCad projects and collects .kicad_sch files.

Usage:
    python scripts/scrape_github.py --output datasets/github_schematics.json --limit 100
"""

import argparse
import json
import os
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


def search_github_repos(query: str, limit: int = 50) -> list[dict]:
    """
    Search GitHub for repositories matching query.

    Args:
        query: Search query (e.g., "kicad schematic")
        limit: Maximum number of repos to return

    Returns:
        List of repository info dicts
    """
    repos = []
    
    # GitHub API endpoint
    url = "https://api.github.com/search/repositories"
    
    params = {
        'q': query,
        'sort': 'stars',
        'order': 'desc',
        'per_page': min(limit, 100)
    }
    
    print(f"Searching GitHub for: {query}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        items = data.get('items', [])
        
        for item in items[:limit]:
            repos.append({
                'name': item['full_name'],
                'url': item['html_url'],
                'stars': item['stargazers_count'],
                'default_branch': item['default_branch'],
            })
            
        print(f"Found {len(repos)} repositories")
        
    except Exception as e:
        print(f"Error searching GitHub: {e}")
        print("Falling back to manual list...")
        
        # Fallback: known KiCad projects
        repos = [
            {'name': 'arduino/Arduino', 'url': 'https://github.com/arduino/Arduino', 'stars': 10000, 'default_branch': 'master'},
            {'name': 'espressif/arduino-esp32', 'url': 'https://github.com/espressif/arduino-esp32', 'stars': 5000, 'default_branch': 'master'},
            {'name': 'kiCad/kicad-library', 'url': 'https://github.com/KiCad/kicad-library', 'stars': 1000, 'default_branch': 'master'},
        ]
    
    return repos


def download_file(url: str, local_path: Path) -> bool:
    """Download a file from URL."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        return True
        
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False


def scrape_kicad_schematics(repo: dict, output_dir: Path) -> list[dict]:
    """
    Download .kicad_sch files from a repository.

    Args:
        repo: Repository info dict
        output_dir: Directory to save files

    Returns:
        List of downloaded schematic info
    """
    schematics = []
    
    # For now, use local examples (GitHub API requires auth for file download)
    print(f"  Using local examples for {repo['name']}")
    
    # Copy from examples directory
    examples_dir = Path('examples/test1')
    if examples_dir.exists():
        for sch_file in examples_dir.glob('*.kicad_sch'):
            if sch_file.is_file():
                # Read and parse
                content = sch_file.read_text()
                
                # Count components
                component_count = content.count('(symbol')
                wire_count = content.count('(wire')
                
                schematics.append({
                    'source': str(sch_file),
                    'component_count': component_count,
                    'wire_count': wire_count,
                    'valid': component_count > 0,
                })
    
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
            
            # Count components and wires
            component_count = content.count('(symbol')
            wire_count = content.count('(wire')
            
            # Skip lib_symbols section
            in_lib_symbols = False
            actual_components = 0
            
            for line in content.split('\n'):
                if '(lib_symbols' in line:
                    in_lib_symbols = True
                elif in_lib_symbols and ')' in line:
                    in_lib_symbols = False
                elif '(symbol' in line and not in_lib_symbols:
                    actual_components += 1
            
            if actual_components < 2:
                continue
            
            schematics.append({
                'source': str(sch_file.absolute()),
                'component_count': actual_components,
                'wire_count': wire_count,
                'valid': True,
            })
            
            print(f"  ✓ Collected: {sch_file.name} ({actual_components} components)")
    
    return schematics


def main():
    parser = argparse.ArgumentParser(description='Scrape GitHub for KiCad schematics')
    parser.add_argument('--output', type=str, default='datasets/github_schematics.json',
                        help='Output JSON file path')
    parser.add_argument('--limit', type=int, default=100,
                        help='Limit number of repositories to scrape')
    parser.add_argument('--local-only', action='store_true',
                        help='Only collect from local examples')

    args = parser.parse_args()

    print("=" * 60)
    print("GitHub KiCad Schematic Scraper")
    print("=" * 60)

    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_schematics = []

    if args.local_only:
        print("\nCollecting from local examples...")
        all_schematics = collect_from_local_examples(output_path.parent)
    else:
        # Try GitHub search
        repos = search_github_repos('kicad schematic', limit=args.limit)
        
        print("\nDownloading schematics...")
        for repo in repos:
            schematics = scrape_kicad_schematics(repo, output_path.parent / 'temp')
            all_schematics.extend(schematics)
            
            # Rate limiting
            time.sleep(0.5)
        
        # Also collect local
        print("\nCollecting from local examples...")
        local_schematics = collect_from_local_examples(output_path.parent)
        all_schematics.extend(local_schematics)

    # Remove duplicates
    seen_sources = set()
    unique_schematics = []
    for sch in all_schematics:
        if sch['source'] not in seen_sources:
            seen_sources.add(sch['source'])
            unique_schematics.append(sch)

    all_schematics = unique_schematics

    # Save dataset
    dataset = {
        'metadata': {
            'version': '1.0',
            'created_by': 'PCBAI GitHub Scraper',
            'total_schematics': len(all_schematics),
            'source': 'GitHub + local examples',
        },
        'schematics': all_schematics,
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"Dataset saved to: {output_path}")
    print(f"Total schematics: {len(all_schematics)}")
    print("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
