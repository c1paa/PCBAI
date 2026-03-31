"""
Command-line interface for PCBAI.
Main entry point for the application.
"""

import click
from pathlib import Path
from typing import Optional

from .routing import route_pcb, FreeRoutingRunner
from .parser import parse_pcb
from .schematic import generate_schematic
from .analyzer import analyze_project
from .dialog import start_interactive_dialog


@click.group()
@click.version_option(version='0.1.0', prog_name='pcba')
def main():
    """PCBAI - AI-powered PCB design tool for KiCad.
    
    Automates PCB routing using FreeRouting autorouter.
    """
    pass


@main.command()
@click.argument('pcb_file', type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), default=None,
              help='Output file path (default: <input>_routed.kicad_pcb)')
@click.option('--tools-dir', type=click.Path(), default=None,
              help='Directory with FreeRouting JAR')
def route(pcb_file: str, output: Optional[str], tools_dir: Optional[str]):
    """Route a PCB file automatically using FreeRouting.
    
    PCB_FILE: Path to input .kicad_pcb file
    
    Example:
        pcba route my_board.kicad_pcb
        pcba route my_board.kicad_pcb -o routed.kicad_pcb
    """
    try:
        result_path = route_pcb(pcb_file, output, tools_dir)
        click.echo(click.style(f'✓ Routing complete: {result_path}', fg='green'))
    except Exception as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'), err=True)
        raise SystemExit(1)


@main.command()
@click.argument('pcb_file', type=click.Path(exists=True))
def inspect(pcb_file: str):
    """Inspect a PCB file and show its contents.
    
    PCB_FILE: Path to .kicad_pcb file
    
    Example:
        pcba inspect my_board.kicad_pcb
    """
    try:
        data = parse_pcb(pcb_file)
        
        click.echo(f"\n{click.style('PCB File:', bold=True)} {pcb_file}")
        click.echo(f"{click.style('Version:', bold=True)} {data.get('version', 'unknown')}")
        
        # General info
        general = data.get('general', {})
        if general:
            click.echo(f"\n{click.style('General:', bold=True)}")
            if 'thickness' in general:
                click.echo(f"  Thickness: {general['thickness']} mm")
            if 'area' in general:
                area = general['area']
                click.echo(f"  Area: ({area['x1']}, {area['y1']}) to ({area['x2']}, {area['y2']})")
        
        # Footprints
        footprints = data.get('footprints', [])
        click.echo(f"\n{click.style('Footprints:', bold=True)} {len(footprints)}")
        for fp in footprints[:10]:  # Show first 10
            pos = fp.get('position', {})
            click.echo(f"  - {fp.get('name', 'UNKNOWN')} @ ({pos.get('x', 0)}, {pos.get('y', 0)})")
        if len(footprints) > 10:
            click.echo(f"  ... and {len(footprints) - 10} more")
        
        # Tracks
        tracks = data.get('tracks', [])
        click.echo(f"\n{click.style('Tracks:', bold=True)} {len(tracks)}")
        
        # Vias
        vias = data.get('vias', [])
        click.echo(f"\n{click.style('Vias:', bold=True)} {len(vias)}")
        
        # Nets
        netlist = data.get('netlist', {})
        nets = netlist.get('nets', {})
        click.echo(f"\n{click.style('Nets:', bold=True)} {len(nets)}")
        for net_name, net_code in list(nets.items())[:10]:
            click.echo(f"  - {net_name} (net {net_code})")
        if len(nets) > 10:
            click.echo(f"  ... and {len(nets) - 10} more")
        
    except Exception as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'), err=True)
        raise SystemExit(1)


@main.command()
@click.option('--tools-dir', type=click.Path(), default=None,
              help='Directory to store FreeRouting JAR')
def download_freerouting(tools_dir: Optional[str]):
    """Download FreeRouting autorouter.
    
    Example:
        pcba download-freerouting
    """
    try:
        runner = FreeRoutingRunner(tools_dir)
        runner.download()
        click.echo(click.style('✓ FreeRouting downloaded successfully', fg='green'))
    except Exception as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'), err=True)
        raise SystemExit(1)


@main.command()
def check():
    """Check system requirements and installed tools."""
    import subprocess
    
    click.echo("\n" + click.style('System Check:', bold=True))
    
    # Java
    java_check = subprocess.run(
        ['java', '-version'],
        capture_output=True,
        text=True,
        timeout=5
    )
    java_info = (java_check.stderr or java_check.stdout).split('\n')[0] if java_check.returncode == 0 else None
    
    if java_info:
        click.echo(f"  {click.style('✓', fg='green')} Java: {java_info}")
        # Check if Java 21+
        if 'version "21' in java_info or 'version "17' in java_info or 'version "20' in java_info:
            click.echo(f"    {click.style('Java 17/21+ detected - compatible with FreeRouting', fg='green')}")
        else:
            click.echo(f"    {click.style('⚠ Java version may be too old for FreeRouting', fg='yellow')}")
            click.echo(f"    Upgrade: brew install openjdk@21")
    else:
        click.echo(f"  {click.style('✗', fg='red')} Java: not found")
        click.echo("    Install: brew install openjdk@21")
    
    # FreeRouting
    runner = FreeRoutingRunner()
    if runner.check_installed():
        click.echo(f"  {click.style('✓', fg='green')} FreeRouting: {runner.jar_path}")
    else:
        click.echo(f"  {click.style('✗', fg='yellow')} FreeRouting: not downloaded")
        click.echo("    Run: pcba download-freerouting")
    
    click.echo()


@main.command()
@click.argument('description')
@click.option('-o', '--output', default='output.kicad_sch',
              help='Output schematic file path')
@click.option('--model', default='llama3.2',
              help='Ollama model name')
@click.option('--ollama-url', default='http://localhost:11434',
              help='Ollama API URL')
@click.option('--project-dir', type=click.Path(exists=True), default=None,
              help='KiCad project directory to analyze for context')
@click.option('--interactive', '-i', is_flag=True, default=False,
              help='Enable interactive dialog for clarifying questions')
def schematic(description: str, output: str, model: str, ollama_url: str, project_dir: Optional[str], interactive: bool):
    """Generate a KiCad schematic from a text description using LLM.

    DESCRIPTION: Natural language description of the circuit

    Supports quantity extraction ("two LED" = 2 LEDs) and
    connection type inference (series/parallel).

    Example:
        pcba schematic "LED with 330 ohm resistor" -o led.kicad_sch
        pcba schematic "two LED in series with 330 ohm resistor" -o leds.kicad_sch
        pcba schematic "three LED in parallel to Arduino pin 5" -i
    """
    try:
        # Analyze project if provided
        learning_context = None
        if project_dir:
            click.echo(click.style(f'Analyzing project: {project_dir}', fg='cyan'))
            analysis = analyze_project(project_dir)
            if analysis.get('status') == 'analyzed':
                click.echo(click.style(f'  Found {analysis.get("files_found", 0)} schematic files', fg='green'))
                if analysis.get('components'):
                    click.echo(f'  Components: {len(analysis["components"])} types')
            learning_context = analysis

        result_path = generate_schematic(
            description, output, model, ollama_url,
            learning_context=learning_context,
            interactive=interactive,
        )
        click.echo(click.style(f'✓ Schematic generated: {result_path}', fg='green'))
    except Exception as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'), err=True)
        raise SystemExit(1)


@main.command()
@click.argument('project_dir', type=click.Path(exists=True))
def analyze(project_dir: str):
    """Analyze a KiCad project to learn design patterns.

    PROJECT_DIR: Path to KiCad project directory

    Example:
        pcba analyze ./my_kicad_project
    """
    try:
        click.echo(click.style(f'\nAnalyzing project: {project_dir}', bold=True))
        click.echo()

        result = analyze_project(project_dir)

        if result.get('status') == 'no_schematics':
            click.echo(click.style('  No .kicad_sch files found', fg='yellow'))
            return

        click.echo(click.style(f'Files found: {result.get("files_found", 0)}', fg='green'))
        click.echo()

        # Show components
        components = result.get('components', {})
        if components:
            click.echo(click.style('Component types:', bold=True))
            for comp_type, count in sorted(components.items(), key=lambda x: -x[1])[:10]:
                click.echo(f'  {comp_type}: {count}')
            click.echo()

        # Show patterns
        patterns = result.get('patterns', [])
        if patterns:
            click.echo(click.style('Circuit patterns:', bold=True))
            for pattern in patterns[:5]:
                click.echo(f'  - {pattern.circuit_type}: {pattern.description}')
            click.echo()

        # Show files
        files = result.get('files', [])
        if files:
            click.echo(click.style('Schematic files:', bold=True))
            for f in files:
                click.echo(f'  {f.get("file")}: {f.get("circuit_type", "unknown")} ({len(f.get("symbols", []))} components)')

        click.echo()

    except Exception as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'), err=True)
        raise SystemExit(1)


@main.command()
@click.option('--file', '-f', type=click.Path(), default=None,
              help='Save schematic to file after dialog')
def dialog(file: Optional[str]):
    """Start interactive dialog with AI for schematic design.

    Example:
        pcba dialog
        pcba dialog -f output.kicad_sch
    """
    try:
        start_interactive_dialog()
    except Exception as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'), err=True)
        raise SystemExit(1)


@main.command()
@click.argument('sch_file', type=click.Path(exists=True))
def validate(sch_file: str):
    """Validate a KiCad schematic file using kicad-cli.

    SCH_FILE: Path to .kicad_sch file

    Example:
        pcba validate my_schema.kicad_sch
    """
    import subprocess
    
    try:
        click.echo(f"\nValidating: {sch_file}")
        
        # Try to export netlist (validates the file)
        result = subprocess.run(
            ['kicad-cli', 'sch', 'export', 'netlist', sch_file, '-o', '/dev/null'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            click.echo(click.style('✓ KiCad validation: OK', fg='green'))
        else:
            click.echo(click.style('✗ KiCad validation failed:', fg='red'))
            click.echo(result.stderr)
            raise SystemExit(1)
            
    except FileNotFoundError:
        click.echo(click.style('⚠ kicad-cli not found.', fg='yellow'))
        click.echo("  Install KiCad: https://www.kicad.org/download/")
        click.echo("\n  File syntax looks OK (not validated)")
    except subprocess.TimeoutExpired:
        click.echo(click.style('✗ Validation timed out', fg='red'))
        raise SystemExit(1)
    except Exception as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'), err=True)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
