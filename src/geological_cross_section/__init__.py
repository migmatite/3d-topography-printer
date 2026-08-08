"""
Geological Cross Section for Groundwater Visualization.

This module provides tools for creating and visualizing geological
cross-sections showing groundwater systems, aquifers, and wells.
"""

from .cross_section import GeologicalCrossSection, GeologicalLayer, Well
from .mesh_generator import (
    NumericalMesh, 
    MeshCell, 
    MeshNode, 
    MeshElement,
    MeshGenerator,
    generate_mesh_from_cross_section
)

__all__ = [
    'GeologicalCrossSection', 
    'GeologicalLayer', 
    'Well',
    'NumericalMesh',
    'MeshCell',
    'MeshNode', 
    'MeshElement',
    'MeshGenerator',
    'generate_mesh_from_cross_section'
]
