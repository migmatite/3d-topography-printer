"""Tests for the geological cross-section module."""

import json
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from geological_cross_section import GeologicalCrossSection, GeologicalLayer, Well
from geological_cross_section.cross_section import create_example_cross_section


class TestGeologicalLayer:
    """Tests for GeologicalLayer dataclass."""
    
    def test_create_basic_layer(self):
        """Test creating a basic geological layer."""
        layer = GeologicalLayer(
            name="Sand",
            top_elevations=[100, 100, 100],
            bottom_elevations=[80, 80, 80],
            color="#f4d03f"
        )
        assert layer.name == "Sand"
        assert layer.is_aquifer is False
        assert layer.pattern == "solid"
    
    def test_create_aquifer_layer(self):
        """Test creating an aquifer layer with all properties."""
        layer = GeologicalLayer(
            name="Gravel Aquifer",
            top_elevations=[100, 98, 96],
            bottom_elevations=[70, 68, 66],
            color="#d4a574",
            pattern="gravel",
            is_aquifer=True,
            hydraulic_conductivity=50.0,
            description="High-permeability alluvial deposits"
        )
        assert layer.is_aquifer is True
        assert layer.hydraulic_conductivity == 50.0
        assert layer.pattern == "gravel"
    
    def test_layer_to_dict(self):
        """Test converting layer to dictionary."""
        layer = GeologicalLayer(
            name="Clay",
            top_elevations=[80, 80],
            bottom_elevations=[60, 60],
            color="#8b7355",
            is_aquifer=False
        )
        d = layer.to_dict()
        assert d["name"] == "Clay"
        assert d["color"] == "#8b7355"
        assert d["is_aquifer"] is False


class TestWell:
    """Tests for Well dataclass."""
    
    def test_create_monitoring_well(self):
        """Test creating a monitoring well."""
        well = Well(
            name="MW-1",
            x_position=100,
            top_elevation=105,
            bottom_elevation=70,
            screen_top=85,
            screen_bottom=70,
            water_level=95
        )
        assert well.name == "MW-1"
        assert well.well_type == "monitoring"
        assert well.water_level == 95
    
    def test_create_production_well(self):
        """Test creating a production well."""
        well = Well(
            name="PW-1",
            x_position=500,
            top_elevation=100,
            bottom_elevation=50,
            screen_top=65,
            screen_bottom=50,
            water_level=85,
            well_type="production",
            pumping_rate=500.0
        )
        assert well.well_type == "production"
        assert well.pumping_rate == 500.0
    
    def test_well_to_dict(self):
        """Test converting well to dictionary."""
        well = Well(
            name="MW-2",
            x_position=200,
            top_elevation=100,
            bottom_elevation=60,
            screen_top=80,
            screen_bottom=60
        )
        d = well.to_dict()
        assert d["name"] == "MW-2"
        assert d["x_position"] == 200
        assert d["water_level"] is None


class TestGeologicalCrossSection:
    """Tests for GeologicalCrossSection class."""
    
    @pytest.fixture
    def basic_cross_section(self):
        """Create a basic cross-section for testing."""
        return GeologicalCrossSection(
            title="Test Cross-Section",
            x_positions=[0, 100, 200, 300, 400]
        )
    
    def test_create_cross_section(self, basic_cross_section):
        """Test creating a basic cross-section."""
        assert basic_cross_section.title == "Test Cross-Section"
        assert len(basic_cross_section.x_positions) == 5
        assert basic_cross_section.vertical_exaggeration == 10.0
    
    def test_add_layer(self, basic_cross_section):
        """Test adding a layer to cross-section."""
        layer = GeologicalLayer(
            name="Sand",
            top_elevations=[100, 100, 100, 100, 100],
            bottom_elevations=[80, 80, 80, 80, 80],
            color="#f4d03f"
        )
        basic_cross_section.add_layer(layer)
        assert len(basic_cross_section.layers) == 1
    
    def test_add_layer_wrong_length(self, basic_cross_section):
        """Test that adding layer with wrong elevation count raises error."""
        layer = GeologicalLayer(
            name="Sand",
            top_elevations=[100, 100, 100],  # Only 3 points, need 5
            bottom_elevations=[80, 80, 80],
            color="#f4d03f"
        )
        with pytest.raises(ValueError, match="must match x_positions count"):
            basic_cross_section.add_layer(layer)
    
    def test_add_well(self, basic_cross_section):
        """Test adding a well to cross-section."""
        well = Well(
            name="MW-1",
            x_position=200,
            top_elevation=100,
            bottom_elevation=60,
            screen_top=80,
            screen_bottom=60
        )
        basic_cross_section.add_well(well)
        assert len(basic_cross_section.wells) == 1
    
    def test_add_well_outside_range(self, basic_cross_section):
        """Test that adding well outside x range raises error."""
        well = Well(
            name="MW-1",
            x_position=500,  # Outside range 0-400
            top_elevation=100,
            bottom_elevation=60,
            screen_top=80,
            screen_bottom=60
        )
        with pytest.raises(ValueError, match="must be within x_positions range"):
            basic_cross_section.add_well(well)
    
    def test_set_water_table(self, basic_cross_section):
        """Test setting water table."""
        water_table = [95, 93, 90, 92, 94]
        basic_cross_section.set_water_table(water_table)
        assert basic_cross_section.water_table == water_table
    
    def test_set_water_table_wrong_length(self, basic_cross_section):
        """Test that setting water table with wrong length raises error."""
        with pytest.raises(ValueError, match="must match x_positions count"):
            basic_cross_section.set_water_table([95, 93, 90])
    
    def test_add_flow_arrow(self, basic_cross_section):
        """Test adding flow arrows."""
        basic_cross_section.add_flow_arrow(100, 80, 200, 78)
        assert len(basic_cross_section.flow_arrows) == 1
        assert basic_cross_section.flow_arrows[0] == (100, 80, 200, 78)
    
    def test_to_json(self, basic_cross_section):
        """Test JSON serialization."""
        layer = GeologicalLayer(
            name="Sand",
            top_elevations=[100, 100, 100, 100, 100],
            bottom_elevations=[80, 80, 80, 80, 80],
            color="#f4d03f"
        )
        basic_cross_section.add_layer(layer)
        
        json_str = basic_cross_section.to_json()
        data = json.loads(json_str)
        
        assert data["title"] == "Test Cross-Section"
        assert len(data["layers"]) == 1
        assert data["layers"][0]["name"] == "Sand"
    
    def test_to_dict(self, basic_cross_section):
        """Test dictionary conversion."""
        d = basic_cross_section.to_dict()
        assert "title" in d
        assert "x_positions" in d
        assert "layers" in d
        assert "wells" in d


class TestSVGGeneration:
    """Tests for SVG generation."""
    
    @pytest.fixture
    def cross_section_with_layer(self):
        """Create a cross-section with one layer for SVG testing."""
        cs = GeologicalCrossSection(
            title="SVG Test",
            x_positions=[0, 100, 200]
        )
        layer = GeologicalLayer(
            name="Sand",
            top_elevations=[100, 100, 100],
            bottom_elevations=[80, 80, 80],
            color="#f4d03f"
        )
        cs.add_layer(layer)
        return cs
    
    def test_generate_svg_basic(self, cross_section_with_layer):
        """Test basic SVG generation."""
        svg = cross_section_with_layer.generate_svg()
        assert svg.startswith('<svg')
        assert '</svg>' in svg
        assert 'SVG Test' in svg
    
    def test_generate_svg_contains_layer(self, cross_section_with_layer):
        """Test that SVG contains layer polygon."""
        svg = cross_section_with_layer.generate_svg()
        assert '<polygon' in svg
    
    def test_generate_svg_custom_dimensions(self, cross_section_with_layer):
        """Test SVG with custom dimensions."""
        svg = cross_section_with_layer.generate_svg(width=800, height=400)
        assert 'viewBox="0 0 800 400"' in svg
    
    def test_generate_svg_no_layers_raises_error(self):
        """Test that generating SVG without layers raises error."""
        cs = GeologicalCrossSection(
            title="Empty",
            x_positions=[0, 100, 200]
        )
        with pytest.raises(ValueError, match="No layers defined"):
            cs.generate_svg()


class TestHTMLGeneration:
    """Tests for HTML generation."""
    
    @pytest.fixture
    def complete_cross_section(self):
        """Create a complete cross-section for HTML testing."""
        return create_example_cross_section()
    
    def test_generate_html(self, complete_cross_section):
        """Test HTML generation."""
        html = complete_cross_section.generate_html()
        assert '<!DOCTYPE html>' in html
        assert '<html' in html
        assert '</html>' in html
    
    def test_html_contains_svg(self, complete_cross_section):
        """Test that HTML contains embedded SVG."""
        html = complete_cross_section.generate_html()
        assert '<svg' in html
        assert '</svg>' in html
    
    def test_html_contains_layers_info(self, complete_cross_section):
        """Test that HTML contains layer information."""
        html = complete_cross_section.generate_html()
        assert 'Topsoil' in html
        assert 'Aquifer' in html
    
    def test_html_contains_wells_info(self, complete_cross_section):
        """Test that HTML contains well information."""
        html = complete_cross_section.generate_html()
        assert 'MW-1' in html
        assert 'PW-1' in html


class TestExampleCrossSection:
    """Tests for the example cross-section factory function."""
    
    def test_create_example(self):
        """Test creating example cross-section."""
        cs = create_example_cross_section()
        assert cs.title == "Groundwater Cross-Section: Alluvial Valley Aquifer System"
    
    def test_example_has_layers(self):
        """Test that example has geological layers."""
        cs = create_example_cross_section()
        assert len(cs.layers) == 5
    
    def test_example_has_wells(self):
        """Test that example has wells."""
        cs = create_example_cross_section()
        assert len(cs.wells) == 3
    
    def test_example_has_water_table(self):
        """Test that example has water table."""
        cs = create_example_cross_section()
        assert cs.water_table is not None
    
    def test_example_has_flow_arrows(self):
        """Test that example has flow arrows."""
        cs = create_example_cross_section()
        assert len(cs.flow_arrows) > 0
    
    def test_example_aquifer_layers(self):
        """Test that example has properly marked aquifer layers."""
        cs = create_example_cross_section()
        aquifer_count = sum(1 for layer in cs.layers if layer.is_aquifer)
        assert aquifer_count == 2  # Sand/Gravel and Limestone
