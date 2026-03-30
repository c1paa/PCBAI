"""
Schematic Analyzer Module.

Analyzes existing KiCad schematic files to learn:
- Component usage patterns
- Connection styles
- Design preferences
"""

import re
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field


@dataclass
class SchematicPattern:
    """Pattern extracted from existing schematic."""
    circuit_type: str
    components: list[dict[str, Any]]
    connections: list[tuple[str, str]]
    description: str


class SchematicAnalyzer:
    """Analyze KiCad schematic files to learn design patterns."""
    
    def __init__(self):
        self.patterns: list[SchematicPattern] = []
        self.component_stats: dict[str, int] = {}
        self.common_connections: list[tuple[str, str]] = []
    
    def analyze_directory(self, project_dir: str | Path) -> dict[str, Any]:
        """Analyze all schematic files in a directory.
        
        Args:
            project_dir: Path to KiCad project directory
            
        Returns:
            Dictionary with analysis results
        """
        project_path = Path(project_dir)
        
        if not project_path.exists():
            raise FileNotFoundError(f"Project directory not found: {project_path}")
        
        # Find all .kicad_sch files
        sch_files = list(project_path.glob('**/*.kicad_sch'))
        
        if not sch_files:
            return {
                'status': 'no_schematics',
                'message': 'No .kicad_sch files found in project',
                'patterns': [],
                'components': {},
            }
        
        results = {
            'status': 'analyzed',
            'files_found': len(sch_files),
            'files': [],
            'patterns': [],
            'components': {},
            'nets': [],
        }
        
        for sch_file in sch_files:
            file_analysis = self.analyze_file(sch_file)
            results['files'].append(file_analysis)
            
            # Aggregate component stats
            for comp_type, count in file_analysis.get('components', {}).items():
                self.component_stats[comp_type] = self.component_stats.get(comp_type, 0) + count
        
        results['components'] = self.component_stats
        results['patterns'] = self.patterns
        
        return results
    
    def analyze_file(self, sch_file: str | Path) -> dict[str, Any]:
        """Analyze a single schematic file.
        
        Args:
            sch_file: Path to .kicad_sch file
            
        Returns:
            Dictionary with file analysis
        """
        sch_path = Path(sch_file)
        
        if not sch_path.exists():
            raise FileNotFoundError(f"Schematic file not found: {sch_path}")
        
        content = sch_path.read_text()
        
        analysis = {
            'file': str(sch_path.name),
            'components': {},
            'nets': [],
            'symbols': [],
        }
        
        # Extract symbols (components)
        symbols = self._extract_symbols(content)
        analysis['symbols'] = symbols
        
        # Count component types
        for symbol in symbols:
            lib_id = symbol.get('lib_id', '')
            if lib_id:
                analysis['components'][lib_id] = analysis['components'].get(lib_id, 0) + 1
        
        # Extract nets
        nets = self._extract_nets(content)
        analysis['nets'] = nets
        
        # Extract wires
        wires = self._extract_wires(content)
        analysis['wires'] = len(wires)
        
        # Try to infer circuit type
        circuit_type = self._infer_circuit_type(analysis)
        analysis['circuit_type'] = circuit_type
        
        # Store pattern
        if symbols:
            self.patterns.append(SchematicPattern(
                circuit_type=circuit_type,
                components=symbols,
                connections=[(w.get('net', ''), '') for w in wires[:10]],
                description=f"{circuit_type} circuit with {len(symbols)} components",
            ))
        
        return analysis
    
    def _extract_symbols(self, content: str) -> list[dict[str, Any]]:
        """Extract component symbols from schematic content."""
        symbols = []
        
        # Match symbol blocks: (symbol (lib_id "...") ...)
        symbol_pattern = r'\(symbol\s+\(lib_id\s+"([^"]+)"\)[^)]*(?:\(at\s+([\d.-]+)\s+([\d.-]+))?'
        
        for match in re.finditer(symbol_pattern, content, re.DOTALL):
            lib_id = match.group(1)
            x = float(match.group(2)) if match.group(2) else 0
            y = float(match.group(3)) if match.group(3) else 0
            
            # Extract reference (e.g., R1, C2)
            ref_match = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', content[match.start():match.start()+500])
            ref = ref_match.group(1) if ref_match else '?'
            
            # Extract value
            value_match = re.search(r'\(property\s+"Value"\s+"([^"]+)"', content[match.start():match.start()+500])
            value = value_match.group(1) if value_match else ''
            
            symbols.append({
                'lib_id': lib_id,
                'ref': ref,
                'value': value,
                'x': x,
                'y': y,
                'type': self._categorize_component(lib_id),
            })
        
        return symbols
    
    def _extract_nets(self, content: str) -> list[dict[str, Any]]:
        """Extract nets from schematic content."""
        nets = []
        
        # Match net labels
        net_pattern = r'\(net\s+(\d+)\s+"([^"]+)"\)'
        
        for match in re.finditer(net_pattern, content):
            nets.append({
                'code': int(match.group(1)),
                'name': match.group(2),
            })
        
        return nets
    
    def _extract_wires(self, content: str) -> list[dict[str, Any]]:
        """Extract wires from schematic content."""
        wires = []
        
        # Match wire blocks
        wire_pattern = r'\(wire\s+\(pts\s+\(xy\s+([\d.-]+)\s+([\d.-]+)\)\s+\(xy\s+([\d.-]+)\s+([\d.-]+)\)\).*?\(net\s+(\d+)\)'
        
        for match in re.finditer(wire_pattern, content, re.DOTALL):
            wires.append({
                'x1': float(match.group(1)),
                'y1': float(match.group(2)),
                'x2': float(match.group(3)),
                'y2': float(match.group(4)),
                'net': int(match.group(5)),
            })
        
        return wires
    
    def _categorize_component(self, lib_id: str) -> str:
        """Categorize component by library ID."""
        lib_id_lower = lib_id.lower()
        
        if 'resistor' in lib_id_lower or ':r' in lib_id_lower:
            return 'resistor'
        elif 'capacitor' in lib_id_lower or ':c' in lib_id_lower:
            return 'capacitor'
        elif 'led' in lib_id_lower:
            return 'led'
        elif 'diode' in lib_id_lower or ':d' in lib_id_lower:
            return 'diode'
        elif 'transistor' in lib_id_lower or 'q_' in lib_id_lower:
            return 'transistor'
        elif 'ic' in lib_id_lower or 'opamp' in lib_id_lower:
            return 'ic'
        elif 'connector' in lib_id_lower or 'conn' in lib_id_lower:
            return 'connector'
        elif 'switch' in lib_id_lower:
            return 'switch'
        elif 'inductor' in lib_id_lower or ':l' in lib_id_lower:
            return 'inductor'
        else:
            return 'other'
    
    def _infer_circuit_type(self, analysis: dict[str, Any]) -> str:
        """Infer circuit type from components."""
        components = analysis.get('components', {})
        symbols = analysis.get('symbols', [])
        
        # Check for common circuit patterns
        component_types = [s.get('type', '') for s in symbols]
        
        if 'transistor' in component_types and 'resistor' in component_types:
            return 'transistor_amplifier'
        elif 'ic' in component_types and '555' in str(symbols):
            return 'timer_circuit'
        elif 'opamp' in str(symbols).lower():
            return 'opamp_circuit'
        elif 'led' in component_types and 'resistor' in component_types:
            return 'led_circuit'
        elif any('regulator' in str(s).lower() for s in symbols):
            return 'power_supply'
        elif any('buck' in str(s).lower() or 'boost' in str(s).lower() for s in symbols):
            return 'dc_dc_converter'
        elif 'microcontroller' in str(symbols).lower() or 'mcu' in str(symbols).lower():
            return 'microcontroller'
        elif len(components) < 5:
            return 'simple_circuit'
        else:
            return 'general_circuit'
    
    def get_learning_context(self) -> str:
        """Generate learning context from analyzed schematics.
        
        Returns:
            Text context to include in LLM prompt
        """
        if not self.patterns:
            return ""
        
        context_lines = [
            "Based on analysis of existing schematics:",
            "",
            "Component usage patterns:",
        ]
        
        for comp_type, count in sorted(self.component_stats.items(), key=lambda x: -x[1])[:10]:
            context_lines.append(f"  - {comp_type}: {count} instances")
        
        context_lines.append("")
        context_lines.append("Circuit patterns found:")
        
        for pattern in self.patterns[:5]:
            context_lines.append(f"  - {pattern.circuit_type}: {pattern.description}")
        
        return "\n".join(context_lines)


def analyze_project(project_dir: str | Path) -> dict[str, Any]:
    """Convenience function to analyze a KiCad project."""
    analyzer = SchematicAnalyzer()
    return analyzer.analyze_directory(project_dir)
