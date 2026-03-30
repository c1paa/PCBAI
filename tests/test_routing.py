"""
Tests for routing module.
"""

import pytest
from pathlib import Path
from pcba.routing import FreeRoutingRunner, SESImporter
from pcba.exporter import export_to_dsn, SpectraDSNExporter
from pcba.parser import parse_pcb


class TestSpectraDSNExporter:
    """Test DSN export format."""

    def test_export_basic_structure(self, tmp_path):
        board_data = {
            'version': '20240108',
            'general': {'thickness': 1.6, 'area': {'x1': 0, 'y1': 0, 'x2': 50, 'y2': 50}},
            'layers': [
                {'name': 'F.Cu', 'type': 'signal'},
                {'name': 'B.Cu', 'type': 'signal'},
            ],
            'footprints': [
                {'name': 'Device:R_0805', 'layer': 'F.Cu',
                 'position': {'x': 10, 'y': 20, 'angle': 0}},
            ],
            'tracks': [],
            'vias': [],
            'netlist': {'nets': {'GND': 1, 'VCC': 2}},
        }

        dsn_file = tmp_path / "test.dsn"
        export_to_dsn(board_data, dsn_file)

        content = dsn_file.read_text()

        # Check Specctra DSN structure
        assert content.startswith("(pcb test.dsn")
        assert "(parser" in content
        assert "(resolution um 10)" in content
        assert "(unit um)" in content
        assert "(structure" in content
        assert "(layer F.Cu" in content
        assert "(layer B.Cu" in content
        assert "(boundary" in content
        assert "(placement" in content
        assert "(library" in content
        assert "(network" in content
        assert "(wiring" in content

    def test_export_with_tracks(self, tmp_path):
        board_data = {
            'general': {'area': {'x1': 0, 'y1': 0, 'x2': 100, 'y2': 100}},
            'layers': [{'name': 'F.Cu', 'type': 'signal'}],
            'footprints': [],
            'tracks': [
                {'start': {'x': 10, 'y': 20}, 'end': {'x': 30, 'y': 40},
                 'width': 0.25, 'layer': 'F.Cu'},
            ],
            'vias': [],
            'netlist': {'nets': {}},
        }

        dsn_file = tmp_path / "tracks.dsn"
        export_to_dsn(board_data, dsn_file)
        content = dsn_file.read_text()

        assert "(wire (path F.Cu 2500" in content


class TestSESImporter:
    """Test SES file parsing."""

    def test_parse_ses_wires(self, tmp_path):
        ses_content = """(session test
  (routes
    (resolution um 10)
    (network_out
      (net TestNet
        (wire
          (path F.Cu 25000
            1000000 2000000
            3000000 2000000
          )
        )
      )
    )
  )
)"""
        ses_file = tmp_path / "test.ses"
        ses_file.write_text(ses_content)

        importer = SESImporter()
        result = importer._parse_ses_file(ses_file)

        assert len(result['tracks']) == 1
        track = result['tracks'][0]
        assert track['layer'] == 'F.Cu'
        assert track['width'] == 0.25
        assert track['start']['x'] == 10.0
        assert track['start']['y'] == 20.0
        assert track['end']['x'] == 30.0
        assert track['end']['y'] == 20.0

    def test_parse_ses_vias(self, tmp_path):
        ses_content = """(session test
  (routes
    (resolution um 10)
    (network_out
      (net TestNet
        (via "Via[0-1]_600:300_um" 5000000 5000000
        )
      )
    )
  )
)"""
        ses_file = tmp_path / "test_via.ses"
        ses_file.write_text(ses_content)

        importer = SESImporter()
        result = importer._parse_ses_file(ses_file)

        assert len(result['vias']) == 1
        via = result['vias'][0]
        assert via['position']['x'] == 50.0
        assert via['position']['y'] == 50.0


class TestFreeRoutingRunner:
    """Test FreeRouting runner (non-execution tests)."""

    def test_check_installed_missing(self, tmp_path):
        runner = FreeRoutingRunner(tmp_path / "nonexistent")
        assert runner.check_installed() is False

    def test_check_installed_exists(self, tmp_path):
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        (tools_dir / "freerouting.jar").write_text("dummy")
        runner = FreeRoutingRunner(tools_dir)
        assert runner.check_installed() is True

    def test_run_missing_dsn(self, tmp_path):
        runner = FreeRoutingRunner(tmp_path)
        with pytest.raises(FileNotFoundError):
            runner.run(tmp_path / "nonexistent.dsn")


class TestExportFromRealPCB:
    """Test exporting real PCB file to DSN."""

    def test_export_simple_led(self):
        pcb_file = Path(__file__).parent.parent / "examples" / "simple_led.kicad_pcb"
        if not pcb_file.exists():
            pytest.skip("simple_led.kicad_pcb not found")

        board_data = parse_pcb(pcb_file)
        assert len(board_data['footprints']) == 2
        assert len(board_data['netlist']['nets']) >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
