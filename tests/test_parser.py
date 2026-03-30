"""
Tests for PCBAI parser module.
"""

import pytest
from pathlib import Path
from pcba.parser import KiCadPCBParser, parse_pcb, save_pcb


class TestKiCadPCBParser:
    """Test PCB parser functionality."""
    
    def test_parse_simple_board(self, tmp_path):
        """Test parsing a simple PCB file."""
        # Create a minimal PCB file
        pcb_content = """(kicad_pcb (version 20240108) (generator pcbnew)
  (thickness 1.6)
  (layers
    (0 "F.Cu" type signal)
    (1 "B.Cu" type signal)
  )
  (footprint "Resistor_SMD:R_0805" (layer F.Cu) (at 100 50))
  (segment (start 100 50) (end 110 60) (width 0.25) (layer F.Cu))
  (via (at 50 50) (size 0.6) (drill 0.3) (layers F.Cu B.Cu))
)"""
        
        pcb_file = tmp_path / "test.kicad_pcb"
        pcb_file.write_text(pcb_content)
        
        # Parse
        data = parse_pcb(pcb_file)
        
        # Check
        assert data['version'] == '20240108'
        assert data['general']['thickness'] == 1.6
        assert len(data['footprints']) >= 1
        assert len(data['tracks']) >= 1
        assert len(data['vias']) >= 1
    
    def test_save_board(self, tmp_path):
        """Test saving a PCB file."""
        board_data = {
            'version': '20240108',
            'general': {'thickness': 1.6},
            'layers': [
                {'name': 'F.Cu', 'type': 'signal', 'align': 'top'},
                {'name': 'B.Cu', 'type': 'signal', 'align': 'bottom'},
            ],
            'footprints': [
                {
                    'name': 'Test:Component',
                    'layer': 'F.Cu',
                    'position': {'x': 100, 'y': 50, 'angle': 0},
                }
            ],
            'tracks': [
                {
                    'start': {'x': 100, 'y': 50},
                    'end': {'x': 110, 'y': 60},
                    'width': 0.25,
                    'layer': 'F.Cu',
                }
            ],
            'vias': [
                {
                    'position': {'x': 50, 'y': 50},
                    'size': 0.6,
                    'drill': 0.3,
                    'layers': ['F.Cu', 'B.Cu'],
                }
            ],
        }
        
        pcb_file = tmp_path / "output.kicad_pcb"
        save_pcb(pcb_file, board_data)
        
        # Check file exists and can be parsed
        assert pcb_file.exists()
        data = parse_pcb(pcb_file)
        assert data['version'] == '20240108'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
