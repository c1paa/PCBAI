"""
FreeRouting integration module.
Handles downloading, running, and importing results from FreeRouting autorouter.

Compatible with FreeRouting v2.1.0 CLI interface.
"""

import re
import subprocess
import shutil
from pathlib import Path
from typing import Any

from .parser import KiCadPCBParser, parse_pcb
from .exporter import export_to_dsn


class FreeRoutingRunner:
    """Run FreeRouting autorouter from command line."""

    # Latest release v2.1.0 from GitHub
    DEFAULT_URL = "https://github.com/freerouting/freerouting/releases/download/v2.1.0/freerouting-2.1.0.jar"

    def __init__(self, tools_dir: str | Path | None = None):
        if tools_dir:
            self.tools_dir = Path(tools_dir)
        else:
            self.tools_dir = Path(__file__).parent.parent.parent / 'tools'

        self.tools_dir.mkdir(parents=True, exist_ok=True)
        self.jar_path = self.tools_dir / 'freerouting.jar'

    def check_installed(self) -> bool:
        """Check if FreeRouting JAR exists."""
        return self.jar_path.exists()

    def download(self) -> None:
        """Download FreeRouting JAR file."""
        import requests

        print(f"Downloading FreeRouting from {self.DEFAULT_URL}...")
        response = requests.get(self.DEFAULT_URL, stream=True)
        response.raise_for_status()

        with open(self.jar_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Downloaded to {self.jar_path}")

    def ensure_installed(self) -> None:
        """Ensure FreeRouting is installed, download if needed."""
        if not self.check_installed():
            self.download()

    def check_java(self) -> bool:
        """Check if Java is installed and get version."""
        java_path = shutil.which('java')
        if not java_path:
            return False

        try:
            result = subprocess.run(
                ['java', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            version_output = result.stderr or result.stdout
            print(f"Java version: {version_output.split(chr(10))[0]}")
            return True
        except Exception:
            return False

    def run(self, dsn_file: str | Path, output_dir: str | Path | None = None) -> Path:
        """Run FreeRouting on a DSN file.

        Uses FreeRouting v2.x CLI: --gui.enabled=false -de input.dsn -do output.ses

        Args:
            dsn_file: Path to input .dsn file
            output_dir: Directory for output files. Defaults to same as DSN

        Returns:
            Path to output .ses file
        """
        dsn_path = Path(dsn_file).resolve()

        if not dsn_path.exists():
            raise FileNotFoundError(f"DSN file not found: {dsn_path}")

        if not self.check_java():
            raise RuntimeError("Java is not installed. Please install Java 21+ to use FreeRouting.")

        self.ensure_installed()

        output_dir_path = Path(output_dir) if output_dir else dsn_path.parent
        output_dir_path.mkdir(parents=True, exist_ok=True)

        ses_path = output_dir_path / f"{dsn_path.stem}.ses"

        # FreeRouting v2.x CLI arguments
        cmd = [
            'java',
            '-jar', str(self.jar_path.resolve()),
            '--gui.enabled=false',
            '-de', str(dsn_path),
            '-do', str(ses_path.resolve()),
            '-mp', '100',      # max passes
            '-mt', '1',        # single thread for reliability
            '-da',             # disable analytics
        ]

        print(f"Running FreeRouting: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            # Log output for debugging
            if result.stdout:
                print(f"FreeRouting stdout: {result.stdout[:500]}")
            if result.stderr:
                print(f"FreeRouting stderr: {result.stderr[:500]}")

            if result.returncode != 0:
                # FreeRouting might return non-zero even on partial success
                if not ses_path.exists():
                    raise RuntimeError(
                        f"FreeRouting failed (exit code {result.returncode}): "
                        f"{result.stderr or result.stdout}"
                    )

            if not ses_path.exists():
                raise RuntimeError(
                    "FreeRouting completed but no .ses file was created. "
                    "Check DSN file format."
                )

            print(f"Routing complete: {ses_path}")
            return ses_path

        except subprocess.TimeoutExpired:
            raise RuntimeError("FreeRouting timed out after 5 minutes")


class SESImporter:
    """Import Specctra Session (.ses) file back to KiCad PCB."""

    def __init__(self):
        self.parser = KiCadPCBParser()

    def import_session(
        self,
        ses_file: str | Path,
        original_pcb: str | Path,
        output_pcb: str | Path,
    ) -> None:
        """Import routed session back to KiCad PCB format.

        Args:
            ses_file: Path to .ses file from FreeRouting
            original_pcb: Path to original .kicad_pcb file
            output_pcb: Path to save routed .kicad_pcb file
        """
        ses_path = Path(ses_file)
        original_path = Path(original_pcb)
        output_path = Path(output_pcb)

        if not ses_path.exists():
            raise FileNotFoundError(f"SES file not found: {ses_path}")

        if not original_path.exists():
            raise FileNotFoundError(f"Original PCB file not found: {original_path}")

        # Parse original PCB
        board_data = self.parser.parse_file(original_path)

        # Parse SES file and extract routed tracks
        routed_tracks = self._parse_ses_file(ses_path)

        # Merge routed tracks with original (keep original if no new ones)
        if routed_tracks['tracks']:
            board_data['tracks'] = routed_tracks['tracks']
        if routed_tracks['vias']:
            board_data['vias'] = routed_tracks['vias']

        # Save updated PCB
        self.parser.save_file(output_path, board_data)
        print(f"Routed PCB saved to: {output_path}")

    def _parse_ses_file(self, ses_path: Path) -> dict[str, Any]:
        """Parse Specctra Session file.

        SES files from FreeRouting v2.x use coordinates that are 10x the DSN units.
        With DSN resolution (um 10), SES scale is 100000 units per mm.
        Wire format: (wire (path LAYER WIDTH X1 Y1 X2 Y2 ...))
        Via format: (via "padstack" X Y)
        """
        content = ses_path.read_text()

        tracks: list[dict] = []
        vias: list[dict] = []

        # FreeRouting v2.x SES output: 100000 units = 1mm
        scale = 100000

        # Parse wires: (wire (path LAYER WIDTH X1 Y1 X2 Y2 ...))
        # Coordinates can span multiple lines
        wire_pattern = r'\(path\s+(\S+)\s+(\d+)\s+([\d\s-]+?)\s*\)'
        for match in re.finditer(wire_pattern, content):
            layer = match.group(1)
            width = int(match.group(2)) / scale
            coords_str = match.group(3).strip()
            nums = [int(c) for c in coords_str.split()]

            if len(nums) < 4:
                continue

            # Create segments between consecutive point pairs
            points = [(nums[j] / scale, nums[j + 1] / scale)
                      for j in range(0, len(nums), 2)]

            for k in range(len(points) - 1):
                tracks.append({
                    'start': {'x': round(points[k][0], 4), 'y': round(points[k][1], 4)},
                    'end': {'x': round(points[k + 1][0], 4), 'y': round(points[k + 1][1], 4)},
                    'width': round(width, 4),
                    'layer': layer,
                })

        # Parse vias: (via "padstack_name" X Y)
        via_pattern = r'\(via\s+"[^"]+"\s+(-?\d+)\s+(-?\d+)'
        for match in re.finditer(via_pattern, content):
            vias.append({
                'position': {
                    'x': round(int(match.group(1)) / scale, 4),
                    'y': round(int(match.group(2)) / scale, 4),
                },
                'size': 0.6,
                'drill': 0.3,
                'layers': ['F.Cu', 'B.Cu'],
            })

        return {'tracks': tracks, 'vias': vias}


def route_pcb(
    pcb_file: str | Path,
    output_file: str | Path | None = None,
    tools_dir: str | Path | None = None,
) -> Path:
    """Convenience function to route a PCB file using FreeRouting.

    Args:
        pcb_file: Path to input .kicad_pcb file
        output_file: Path for output routed PCB. Defaults to input_routed.kicad_pcb
        tools_dir: Directory with FreeRouting JAR

    Returns:
        Path to routed PCB file
    """
    pcb_path = Path(pcb_file)

    if output_file:
        output_path = Path(output_file)
    else:
        output_path = pcb_path.parent / f"{pcb_path.stem}_routed.kicad_pcb"

    # Parse PCB
    parser = KiCadPCBParser()
    board_data = parser.parse_file(pcb_path)

    # Export to DSN
    dsn_path = pcb_path.parent / f"{pcb_path.stem}.dsn"
    export_to_dsn(board_data, dsn_path)
    print(f"Exported to DSN: {dsn_path}")

    # Run FreeRouting
    runner = FreeRoutingRunner(tools_dir)
    ses_path = runner.run(dsn_path)

    # Import back to PCB
    importer = SESImporter()
    importer.import_session(ses_path, pcb_path, output_path)

    return output_path
