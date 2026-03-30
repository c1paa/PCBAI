"""
Tests for schematic generation module.
"""

import pytest
from pathlib import Path
from pcba.schematic import (
    OllamaClient,
    SKiDLGenerator,
    KiCadSchematicWriter,
    SchematicData,
    SchematicComponent,
    SchematicNet,
    COMPONENT_DB,
)


class TestSKiDLGenerator:
    """Test SKiDL code parsing via AST."""

    def test_parse_simple_circuit(self):
        code = """
R1 = resistor("330")
LED1 = led("RED")
VCC = Net("VCC")
GND = Net("GND")
N1 = Net("N1")
VCC += R1[1]
R1[2] += LED1[2]
LED1[1] += GND
"""
        gen = SKiDLGenerator()
        data = gen.parse_skidl_code(code)

        assert len(data.components) == 2
        assert data.components[0].ref == "R1"
        assert data.components[0].comp_type == "resistor"
        assert data.components[0].value == "330"
        assert data.components[1].ref == "LED1"
        assert data.components[1].comp_type == "led"

    def test_parse_markdown_code_block(self):
        code = """Here is the circuit:
```python
R1 = resistor("1k")
C1 = capacitor("100nF")
VCC = Net("VCC")
GND = Net("GND")
VCC += R1[1]
R1[2] += C1[1]
C1[2] += GND
```
"""
        gen = SKiDLGenerator()
        data = gen.parse_skidl_code(code)

        assert len(data.components) == 2
        assert data.components[0].comp_type == "resistor"
        assert data.components[1].comp_type == "capacitor"

    def test_validate_valid_circuit(self):
        data = SchematicData(
            components=[
                SchematicComponent(ref="R1", comp_type="resistor", value="330"),
                SchematicComponent(ref="LED1", comp_type="led", value="RED"),
            ],
            nets=[
                SchematicNet(name="VCC", pins=[("R1", "1")]),
                SchematicNet(name="N1", pins=[("R1", "2"), ("LED1", "2")]),
                SchematicNet(name="GND", pins=[("LED1", "1")]),
            ],
        )
        gen = SKiDLGenerator()
        assert gen.validate(data) is True

    def test_validate_empty_circuit(self):
        gen = SKiDLGenerator()
        assert gen.validate(SchematicData()) is False

    def test_validate_unknown_component(self):
        data = SchematicData(
            components=[
                SchematicComponent(ref="X1", comp_type="nonexistent", value="?"),
            ],
        )
        gen = SKiDLGenerator()
        assert gen.validate(data) is False

    def test_validate_invalid_pin_ref(self):
        data = SchematicData(
            components=[
                SchematicComponent(ref="R1", comp_type="resistor", value="1k"),
            ],
            nets=[
                SchematicNet(name="N1", pins=[("MISSING", "1")]),
            ],
        )
        gen = SKiDLGenerator()
        assert gen.validate(data) is False

    def test_parse_invalid_syntax(self):
        gen = SKiDLGenerator()
        with pytest.raises(ValueError, match="Invalid SKiDL code"):
            gen.parse_skidl_code("this is not { valid python !!!")


class TestKiCadSchematicWriter:
    """Test KiCad schematic file writer."""

    def test_write_simple_schematic(self, tmp_path):
        data = SchematicData(
            components=[
                SchematicComponent(ref="R1", comp_type="resistor", value="330", x=100, y=50),
                SchematicComponent(ref="LED1", comp_type="led", value="RED", x=100, y=100),
            ],
            nets=[
                SchematicNet(name="VCC", pins=[("R1", "1")]),
                SchematicNet(name="N1", pins=[("R1", "2"), ("LED1", "2")]),
            ],
        )

        output = tmp_path / "test.kicad_sch"
        writer = KiCadSchematicWriter()
        writer.write(data, output)

        assert output.exists()
        content = output.read_text()

        # Check file structure
        assert "(kicad_sch" in content
        assert "(version 20231120)" in content
        assert '"R1"' in content
        assert '"LED1"' in content
        assert '"330"' in content
        assert "Device:R" in content
        assert "Device:LED" in content

    def test_write_empty_schematic(self, tmp_path):
        data = SchematicData()
        output = tmp_path / "empty.kicad_sch"
        writer = KiCadSchematicWriter()
        writer.write(data, output)

        assert output.exists()
        content = output.read_text()
        assert "(kicad_sch" in content


class TestComponentDB:
    """Test component database completeness."""

    def test_all_components_have_pins(self):
        for name, info in COMPONENT_DB.items():
            assert 'pins' in info, f"Component {name} missing pins"
            assert len(info['pins']) > 0, f"Component {name} has no pins"

    def test_all_components_have_lib_info(self):
        for name, info in COMPONENT_DB.items():
            assert 'lib' in info, f"Component {name} missing lib"
            assert 'symbol' in info, f"Component {name} missing symbol"
            assert 'value' in info, f"Component {name} missing value"


class TestOllamaClient:
    """Test Ollama client (network-dependent tests skipped if unavailable)."""

    def test_check_unavailable(self):
        client = OllamaClient("http://localhost:99999")
        assert client.check_available() is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
