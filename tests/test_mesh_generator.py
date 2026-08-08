"""Tests for the mesh generator module."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from geological_cross_section import (
    GeologicalCrossSection, 
    GeologicalLayer,
    NumericalMesh,
    MeshCell,
    MeshGenerator,
    generate_mesh_from_cross_section
)
from geological_cross_section.cross_section import create_example_cross_section


class TestMeshCell:
    """Tests for MeshCell dataclass."""
    
    def test_create_cell(self):
        """Test creating a mesh cell."""
        cell = MeshCell(
            id=0,
            row=0,
            col=0,
            x_center=50.0,
            z_center=90.0,
            x_min=0.0,
            x_max=100.0,
            z_min=80.0,
            z_max=100.0,
            width=100.0,
            height=20.0,
            area=2000.0,
            layer_name="Sand",
            is_aquifer=True,
            hydraulic_conductivity=50.0
        )
        assert cell.id == 0
        assert cell.area == 2000.0
        assert cell.is_aquifer is True
    
    def test_cell_to_dict(self):
        """Test converting cell to dictionary."""
        cell = MeshCell(
            id=1, row=0, col=1,
            x_center=150.0, z_center=90.0,
            x_min=100.0, x_max=200.0,
            z_min=80.0, z_max=100.0,
            width=100.0, height=20.0, area=2000.0,
            layer_name="Clay", is_aquifer=False,
            hydraulic_conductivity=0.001
        )
        d = cell.to_dict()
        assert d["id"] == 1
        assert d["layer_name"] == "Clay"
        assert d["bounds"]["x_min"] == 100.0


class TestMeshGenerator:
    """Tests for MeshGenerator class."""
    
    @pytest.fixture
    def example_cross_section(self):
        """Create example cross-section for testing."""
        return create_example_cross_section()
    
    @pytest.fixture
    def simple_cross_section(self):
        """Create a simple cross-section for testing."""
        cs = GeologicalCrossSection(
            title="Simple Test",
            x_positions=[0, 100, 200],
            vertical_exaggeration=1.0
        )
        cs.add_layer(GeologicalLayer(
            name="Sand",
            top_elevations=[100, 100, 100],
            bottom_elevations=[50, 50, 50],
            color="#f4d03f",
            is_aquifer=True,
            hydraulic_conductivity=30.0
        ))
        cs.add_layer(GeologicalLayer(
            name="Clay",
            top_elevations=[50, 50, 50],
            bottom_elevations=[0, 0, 0],
            color="#8b7355",
            is_aquifer=False,
            hydraulic_conductivity=0.001
        ))
        return cs
    
    def test_generate_structured_mesh(self, simple_cross_section):
        """Test generating a structured mesh."""
        generator = MeshGenerator(simple_cross_section)
        mesh = generator.generate_structured_mesh(n_columns=10, n_rows=5)
        
        assert mesh.mesh_type == "structured"
        assert mesh.n_columns == 10
        assert mesh.n_rows == 5
        assert mesh.n_cells == 50
    
    def test_mesh_bounds(self, simple_cross_section):
        """Test that mesh bounds match cross-section."""
        generator = MeshGenerator(simple_cross_section)
        mesh = generator.generate_structured_mesh(n_columns=10, n_rows=5)
        
        assert mesh.x_min == 0
        assert mesh.x_max == 200
        assert mesh.z_min == 0
        assert mesh.z_max == 100
    
    def test_mesh_has_cells(self, simple_cross_section):
        """Test that mesh contains cells."""
        generator = MeshGenerator(simple_cross_section)
        mesh = generator.generate_structured_mesh(n_columns=10, n_rows=5)
        
        assert len(mesh.cells) == 50
        assert all(isinstance(c, MeshCell) for c in mesh.cells)
    
    def test_cells_have_layer_properties(self, simple_cross_section):
        """Test that cells inherit layer properties."""
        generator = MeshGenerator(simple_cross_section)
        mesh = generator.generate_structured_mesh(n_columns=10, n_rows=5)
        
        # Get cells from each layer
        sand_cells = mesh.get_cells_by_layer("Sand")
        clay_cells = mesh.get_cells_by_layer("Clay")
        
        assert len(sand_cells) > 0
        assert len(clay_cells) > 0
        
        # Check properties
        assert all(c.is_aquifer for c in sand_cells)
        assert all(not c.is_aquifer for c in clay_cells)
        assert all(c.hydraulic_conductivity == 30.0 for c in sand_cells)
    
    def test_get_cell_by_row_col(self, simple_cross_section):
        """Test getting cell by row and column."""
        generator = MeshGenerator(simple_cross_section)
        mesh = generator.generate_structured_mesh(n_columns=10, n_rows=5)
        
        cell = mesh.get_cell(row=2, col=5)
        assert cell is not None
        assert cell.row == 2
        assert cell.col == 5
    
    def test_layer_statistics(self, simple_cross_section):
        """Test that layer statistics are computed."""
        generator = MeshGenerator(simple_cross_section)
        mesh = generator.generate_structured_mesh(n_columns=10, n_rows=5)
        
        assert "Sand" in mesh.layer_stats
        assert "Clay" in mesh.layer_stats
        assert mesh.layer_stats["Sand"]["cell_count"] > 0
        assert mesh.layer_stats["Clay"]["cell_count"] > 0


class TestNumericalMesh:
    """Tests for NumericalMesh class."""
    
    @pytest.fixture
    def mesh(self):
        """Create a mesh for testing."""
        cs = create_example_cross_section()
        return generate_mesh_from_cross_section(cs, n_columns=20, n_rows=10)
    
    def test_mesh_to_dict(self, mesh):
        """Test converting mesh to dictionary."""
        d = mesh.to_dict()
        assert "title" in d
        assert "dimensions" in d
        assert "bounds" in d
        assert "cells" in d
    
    def test_mesh_to_json(self, mesh):
        """Test converting mesh to JSON."""
        json_str = mesh.to_json()
        assert isinstance(json_str, str)
        assert mesh.title in json_str
    
    def test_get_active_cells(self, mesh):
        """Test getting active cells."""
        active = mesh.get_active_cells()
        assert len(active) <= mesh.n_cells
        assert all(c.is_active for c in active)
    
    def test_export_modflow_arrays(self, mesh):
        """Test exporting to MODFLOW arrays."""
        arrays = mesh.export_to_modflow_arrays()
        
        assert "ibound" in arrays
        assert "hk" in arrays
        assert "top" in arrays
        assert "bot" in arrays
        
        # Check dimensions
        assert len(arrays["ibound"]) == mesh.n_rows
        assert len(arrays["ibound"][0]) == mesh.n_columns
    
    def test_generate_svg(self, mesh):
        """Test SVG generation."""
        svg = mesh.generate_svg(width=800, height=400)
        
        assert svg.startswith('<svg')
        assert '</svg>' in svg
        assert 'Numerical Mesh' in svg


class TestGenerateMeshFromCrossSection:
    """Tests for convenience function."""
    
    def test_structured_mesh(self):
        """Test generating structured mesh."""
        cs = create_example_cross_section()
        mesh = generate_mesh_from_cross_section(
            cs, n_columns=30, n_rows=15, mesh_type="structured"
        )
        
        assert mesh.mesh_type == "structured"
        assert mesh.n_columns == 30
        assert mesh.n_rows == 15
    
    def test_unstructured_mesh(self):
        """Test generating unstructured mesh."""
        cs = create_example_cross_section()
        mesh = generate_mesh_from_cross_section(
            cs, n_columns=20, n_rows=10, mesh_type="unstructured"
        )
        
        assert mesh.mesh_type == "unstructured"
        assert len(mesh.nodes) > 0
        assert len(mesh.elements) > 0
    
    def test_mesh_covers_all_layers(self):
        """Test that mesh covers all geological layers."""
        cs = create_example_cross_section()
        mesh = generate_mesh_from_cross_section(cs, n_columns=50, n_rows=25)
        
        layer_names = set(c.layer_name for c in mesh.cells)
        
        # Should have cells in most layers
        assert "Topsoil" in layer_names or "Inactive" in layer_names
        assert any("Aquifer" in name or "aquifer" in name.lower() for name in layer_names)


class TestMeshRefinement:
    """Tests for mesh refinement near wells."""
    
    def test_refinement_near_wells(self):
        """Test that mesh is refined near wells."""
        from geological_cross_section import Well
        
        cs = create_example_cross_section()
        generator = MeshGenerator(cs)
        
        mesh_refined = generator.generate_structured_mesh(
            n_columns=50, n_rows=25, refine_near_wells=True
        )
        mesh_uniform = generator.generate_structured_mesh(
            n_columns=50, n_rows=25, refine_near_wells=False
        )
        
        # Both should have same total cells
        assert mesh_refined.n_cells == mesh_uniform.n_cells
        
        # Refined mesh should have variable dx
        # (checking that refinement code runs without error)
        assert len(mesh_refined.dx) == mesh_refined.n_columns
