"""
Project-Based AI Assistant.

Works like Claude Code - understands entire KiCad project,
helps iterate on existing designs.
"""

import re
from pathlib import Path
from typing import Any


class ProjectAIAssistant:
    """AI assistant that works with KiCad projects."""

    def __init__(self, project_path: Path | str):
        """Initialize with project path."""
        self.project_path = Path(project_path)
        self.schematics: list[Path] = []
        self.pcbs: list[Path] = []
        self.load_project()

    def load_project(self) -> None:
        """Load all .kicad_sch and .kicad_pcb files."""
        self.schematics = list(self.project_path.glob("**/*.kicad_sch"))
        self.pcbs = list(self.project_path.glob("**/*.kicad_pcb"))

    def analyze_existing_design(self) -> dict[str, Any]:
        """Analyze existing schematic/PCB."""
        analysis = {
            "components": [],
            "nets": [],
            "mcu": None,
            "sensors": [],
            "issues": []
        }

        for sch in self.schematics:
            parsed = self._parse_schematic(sch)
            analysis["components"].extend(parsed["components"])
            analysis["nets"].extend(parsed["nets"])

        # Find MCU
        for comp in analysis["components"]:
            if comp.get("type") == "mcu" or "arduino" in comp.get("name", "").lower():
                analysis["mcu"] = comp
                break

        # Find sensors
        for comp in analysis["components"]:
            if comp.get("type") == "sensor" or any(
                sensor in comp.get("name", "").lower()
                for sensor in ["dht", "bmp", "mpu"]
            ):
                analysis["sensors"].append(comp)

        return analysis

    def _parse_schematic(self, filepath: Path) -> dict[str, Any]:
        """Parse .kicad_sch file."""
        content = filepath.read_text()
        components = []
        nets = []

        # Extract components (simplified parsing)
        symbol_pattern = r'\(symbol\s+\(lib_id\s+"([^"]+)"\).*?\(property\s+"Reference"\s+"([^"]+)"'
        for match in re.finditer(symbol_pattern, content, re.DOTALL):
            lib_id = match.group(1)
            ref = match.group(2)

            comp_type = "unknown"
            if "Device:R" in lib_id:
                comp_type = "resistor"
            elif "Device:LED" in lib_id:
                comp_type = "led"
            elif "Device:C" in lib_id:
                comp_type = "capacitor"
            elif "Arduino" in lib_id or "ATmega" in lib_id:
                comp_type = "mcu"

            components.append({
                "ref": ref,
                "lib_id": lib_id,
                "type": comp_type,
            })

        # Extract nets
        net_pattern = r'\(net\s+(\d+)\s+"([^"]+)"\)'
        for match in re.finditer(net_pattern, content):
            nets.append({
                "code": int(match.group(1)),
                "name": match.group(2),
            })

        return {"components": components, "nets": nets}

    def suggest_improvements(self) -> list[str]:
        """Suggest design improvements."""
        suggestions = []
        analysis = self.analyze_existing_design()

        # Check for missing decoupling capacitors
        mcus = [c for c in analysis["components"] if c["type"] == "mcu"]
        for mcu in mcus:
            if not self._has_decoupling_caps(analysis["components"]):
                suggestions.append(
                    f"Add 100nF decoupling capacitor near {mcu['ref']}"
                )

        # Check for missing pull-up resistors
        i2c_devices = [
            c
            for c in analysis["components"]
            if "I2C" in c.get("interfaces", [])
            or any(
                sensor in c.get("name", "").lower()
                for sensor in ["bmp280", "mpu6050"]
            )
        ]
        if i2c_devices and not self._has_i2c_pullups(analysis["components"]):
            suggestions.append("Add 4.7k pull-up resistors for I2C lines")

        # Check for LED current limiting resistors
        leds = [c for c in analysis["components"] if c["type"] == "led"]
        resistors = [c for c in analysis["components"] if c["type"] == "resistor"]
        if leds and not resistors:
            suggestions.append("Add current-limiting resistors for LEDs")

        return suggestions

    def _has_decoupling_caps(self, components: list[dict]) -> bool:
        """Check if decoupling capacitors exist."""
        caps = [
            c
            for c in components
            if c["type"] == "capacitor" and c.get("value") in ["100nF", "0.1uF"]
        ]
        return len(caps) > 0

    def _has_i2c_pullups(self, components: list[dict]) -> bool:
        """Check if I2C pull-up resistors exist."""
        pullups = [
            c
            for c in components
            if c["type"] == "resistor" and c.get("value") in ["4.7k", "4k7"]
        ]
        return len(pullups) >= 2

    def help_modify(self, request: str) -> dict[str, Any]:
        """Help modify existing design.

        Args:
            request: Natural language request like "Add LED to pin 6"

        Returns:
            Modification plan
        """
        request_lower = request.lower()
        analysis = self.analyze_existing_design()

        if "add" in request_lower and "led" in request_lower:
            # Extract pin number
            pin_match = re.search(r"pin\s*(\d+)", request_lower)
            pin = pin_match.group(1) if pin_match else "5"

            return {
                "action": "add_component",
                "component": {
                    "type": "led",
                    "ref": f"D{len([c for c in analysis['components'] if c['type'] == 'led']) + 1}",
                    "value": "RED",
                    "connection": {"pin": pin, "series_resistor": "330"},
                },
            }

        elif "move" in request_lower or "closer" in request_lower:
            return {
                "action": "reposition",
                "strategy": "compact",
                "description": "Move components closer together",
            }

        elif "check" in request_lower or "work" in request_lower:
            return {
                "action": "validate",
                "checks": ["drc", "erc", "connectivity"],
                "suggestions": self.suggest_improvements(),
            }

        return {"action": "unknown", "message": "Request not understood"}

    def get_project_summary(self) -> str:
        """Get human-readable project summary."""
        analysis = self.analyze_existing_design()

        lines = [
            f"Project: {self.project_path.name}",
            f"Schematics: {len(self.schematics)}",
            f"PCBs: {len(self.pcbs)}",
            f"Components: {len(analysis['components'])}",
        ]

        if analysis["mcu"]:
            lines.append(f"MCU: {analysis['mcu']['ref']} ({analysis['mcu']['lib_id']})")

        if analysis["sensors"]:
            lines.append(f"Sensors: {len(analysis['sensors'])}")

        suggestions = self.suggest_improvements()
        if suggestions:
            lines.append("\nSuggestions:")
            for sug in suggestions:
                lines.append(f"  - {sug}")

        return "\n".join(lines)
