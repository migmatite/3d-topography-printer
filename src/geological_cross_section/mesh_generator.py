"""
Numerical Mesh Generator for Geological Cross-Sections.

This module generates finite difference and finite element meshes
from geological cross-sections for groundwater flow modeling.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
import json
import math

from .cross_section import GeologicalCrossSection, GeologicalLayer


@dataclass
class MeshCell:
    """Represents a single cell in the numerical mesh."""
    id: int
    row: int
    col: int
    x_center: float
    z_center: float
    x_min: float
    x_max: float
    z_min: float
    z_max: float
    width: float
    height: float
    area: float
    layer_name: str
    is_aquifer: bool
    hydraulic_conductivity: float
    is_active: bool = True
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "row": self.row,
            "col": self.col,
            "x_center": self.x_center,
            "z_center": self.z_center,
            "bounds": {
                "x_min": self.x_min,
                "x_max": self.x_max,
                "z_min": self.z_min,
                "z_max": self.z_max
            },
            "width": self.width,
            "height": self.height,
            "area": self.area,
            "layer_name": self.layer_name,
            "is_aquifer": self.is_aquifer,
            "hydraulic_conductivity": self.hydraulic_conductivity,
            "is_active": self.is_active
        }


@dataclass
class MeshNode:
    """Represents a node in a finite element mesh."""
    id: int
    x: float
    z: float
    
    def to_dict(self) -> dict:
        return {"id": self.id, "x": self.x, "z": self.z}


@dataclass
class MeshElement:
    """Represents an element in a finite element mesh."""
    id: int
    node_ids: List[int]
    layer_name: str
    is_aquifer: bool
    hydraulic_conductivity: float
    centroid_x: float
    centroid_z: float
    area: float
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "node_ids": self.node_ids,
            "layer_name": self.layer_name,
            "is_aquifer": self.is_aquifer,
            "hydraulic_conductivity": self.hydraulic_conductivity,
            "centroid": {"x": self.centroid_x, "z": self.centroid_z},
            "area": self.area
        }


@dataclass 
class NumericalMesh:
    """
    A numerical mesh for groundwater modeling.
    
    Supports both structured (finite difference) and unstructured 
    (finite element) mesh representations.
    """
    title: str
    mesh_type: str  # "structured" or "unstructured"
    n_columns: int
    n_rows: int
    n_cells: int
    x_min: float
    x_max: float
    z_min: float
    z_max: float
    
    # For structured mesh (finite difference)
    cells: List[MeshCell] = field(default_factory=list)
    dx: List[float] = field(default_factory=list)  # Column widths
    dz: List[float] = field(default_factory=list)  # Row heights
    
    # For unstructured mesh (finite element)
    nodes: List[MeshNode] = field(default_factory=list)
    elements: List[MeshElement] = field(default_factory=list)
    
    # Layer statistics
    layer_stats: Dict[str, dict] = field(default_factory=dict)
    
    def get_cell(self, row: int, col: int) -> Optional[MeshCell]:
        """Get cell by row and column index."""
        for cell in self.cells:
            if cell.row == row and cell.col == col:
                return cell
        return None
    
    def get_cells_by_layer(self, layer_name: str) -> List[MeshCell]:
        """Get all cells belonging to a specific layer."""
        return [c for c in self.cells if c.layer_name == layer_name]
    
    def get_active_cells(self) -> List[MeshCell]:
        """Get all active cells."""
        return [c for c in self.cells if c.is_active]
    
    def to_dict(self) -> dict:
        """Convert mesh to dictionary."""
        result = {
            "title": self.title,
            "mesh_type": self.mesh_type,
            "dimensions": {
                "n_columns": self.n_columns,
                "n_rows": self.n_rows,
                "n_cells": self.n_cells,
                "n_active_cells": len(self.get_active_cells())
            },
            "bounds": {
                "x_min": self.x_min,
                "x_max": self.x_max,
                "z_min": self.z_min,
                "z_max": self.z_max
            },
            "discretization": {
                "dx": self.dx,
                "dz": self.dz
            },
            "layer_stats": self.layer_stats
        }
        
        if self.mesh_type == "structured":
            result["cells"] = [c.to_dict() for c in self.cells]
        else:
            result["nodes"] = [n.to_dict() for n in self.nodes]
            result["elements"] = [e.to_dict() for e in self.elements]
        
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """Convert mesh to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def generate_svg(self, width: int = 1000, height: int = 500, 
                     show_grid: bool = True, color_by: str = "layer") -> str:
        """
        Generate SVG visualization of the mesh.
        
        Args:
            width: SVG width in pixels
            height: SVG height in pixels
            show_grid: Whether to show grid lines
            color_by: "layer" or "conductivity"
        """
        padding = 60
        plot_width = width - 2 * padding
        plot_height = height - 2 * padding
        
        def scale_x(x: float) -> float:
            return padding + (x - self.x_min) / (self.x_max - self.x_min) * plot_width
        
        def scale_z(z: float) -> float:
            return padding + (self.z_max - z) / (self.z_max - self.z_min) * plot_height
        
        # Color maps
        layer_colors = {
            "Topsoil": "#8B4513",
            "Sand & Gravel (Unconfined Aquifer)": "#f4d03f",
            "Clay (Aquitard)": "#8b7355",
            "Limestone (Confined Aquifer)": "#a0a0a0",
            "Shale (Bedrock)": "#4a4a4a"
        }
        
        def get_conductivity_color(k: float) -> str:
            """Map hydraulic conductivity to color (log scale)."""
            if k <= 0:
                return "#4a4a4a"
            log_k = math.log10(max(k, 0.0001))
            # Normalize to 0-1 range (assuming K from 0.0001 to 100)
            normalized = (log_k + 4) / 6
            normalized = max(0, min(1, normalized))
            # Blue (low K) to Red (high K)
            r = int(255 * normalized)
            b = int(255 * (1 - normalized))
            g = int(100 * (1 - abs(normalized - 0.5) * 2))
            return f"rgb({r},{g},{b})"
        
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
            f'<rect width="{width}" height="{height}" fill="#f8f9fa"/>',
            f'<text x="{width/2}" y="25" text-anchor="middle" font-size="16" font-weight="bold" fill="#333">{self.title} - Numerical Mesh ({self.n_columns}x{self.n_rows})</text>',
        ]
        
        # Draw cells
        for cell in self.cells:
            if not cell.is_active:
                continue
                
            x1 = scale_x(cell.x_min)
            x2 = scale_x(cell.x_max)
            z1 = scale_z(cell.z_max)
            z2 = scale_z(cell.z_min)
            
            if color_by == "layer":
                fill = layer_colors.get(cell.layer_name, "#888888")
            else:
                fill = get_conductivity_color(cell.hydraulic_conductivity)
            
            stroke = "#333" if show_grid else fill
            stroke_width = "0.5" if show_grid else "0"
            
            svg_parts.append(
                f'<rect x="{x1}" y="{z1}" width="{x2-x1}" height="{z2-z1}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" opacity="0.9"/>'
            )
        
        # Draw cell centers (optional, for small meshes)
        if self.n_cells < 500:
            for cell in self.cells:
                if cell.is_active:
                    cx = scale_x(cell.x_center)
                    cz = scale_z(cell.z_center)
                    svg_parts.append(
                        f'<circle cx="{cx}" cy="{cz}" r="1.5" fill="#333" opacity="0.5"/>'
                    )
        
        # Axes
        svg_parts.append(
            f'<line x1="{padding}" y1="{height-padding}" x2="{width-padding}" '
            f'y2="{height-padding}" stroke="#333" stroke-width="2"/>'
        )
        svg_parts.append(
            f'<line x1="{padding}" y1="{padding}" x2="{padding}" '
            f'y2="{height-padding}" stroke="#333" stroke-width="2"/>'
        )
        
        # Axis labels
        for i in range(6):
            # X axis
            x = padding + i * plot_width / 5
            x_val = self.x_min + i * (self.x_max - self.x_min) / 5
            svg_parts.append(
                f'<text x="{x}" y="{height-padding+20}" text-anchor="middle" '
                f'font-size="10" fill="#333">{x_val:.0f}</text>'
            )
            # Z axis
            z = padding + i * plot_height / 5
            z_val = self.z_max - i * (self.z_max - self.z_min) / 5
            svg_parts.append(
                f'<text x="{padding-10}" y="{z+4}" text-anchor="end" '
                f'font-size="10" fill="#333">{z_val:.0f}</text>'
            )
        
        svg_parts.append(
            f'<text x="{width/2}" y="{height-10}" text-anchor="middle" '
            f'font-size="12" fill="#333">Distance (m)</text>'
        )
        svg_parts.append(
            f'<text x="15" y="{height/2}" text-anchor="middle" font-size="12" '
            f'fill="#333" transform="rotate(-90, 15, {height/2})">Elevation (m)</text>'
        )
        
        # Legend
        legend_x = width - 200
        legend_y = padding + 10
        svg_parts.append(
            f'<rect x="{legend_x-10}" y="{legend_y-5}" width="195" height="{len(layer_colors)*22+30}" '
            f'fill="white" stroke="#333" stroke-width="1" rx="5" opacity="0.95"/>'
        )
        svg_parts.append(
            f'<text x="{legend_x}" y="{legend_y+12}" font-size="11" '
            f'font-weight="bold" fill="#333">Legend (by {color_by})</text>'
        )
        
        for i, (name, color) in enumerate(layer_colors.items()):
            ly = legend_y + 25 + i * 22
            svg_parts.append(
                f'<rect x="{legend_x}" y="{ly}" width="15" height="15" fill="{color}" stroke="#333"/>'
            )
            short_name = name[:25] + "..." if len(name) > 25 else name
            svg_parts.append(
                f'<text x="{legend_x+22}" y="{ly+12}" font-size="9" fill="#333">{short_name}</text>'
            )
        
        # Mesh info
        info_y = height - padding - 60
        svg_parts.append(
            f'<text x="{padding+10}" y="{info_y}" font-size="10" fill="#666">'
            f'Cells: {self.n_cells} ({len(self.get_active_cells())} active) | '
            f'Columns: {self.n_columns} | Rows: {self.n_rows}</text>'
        )
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)
    
    def export_to_modflow_arrays(self) -> Dict[str, List[List[float]]]:
        """
        Export mesh properties as MODFLOW-style 2D arrays.
        
        Returns dictionary with:
        - ibound: Active cell array (1=active, 0=inactive)
        - hk: Horizontal hydraulic conductivity
        - top: Top elevation of each cell
        - bot: Bottom elevation of each cell
        """
        # Initialize arrays
        ibound = [[0] * self.n_columns for _ in range(self.n_rows)]
        hk = [[0.0] * self.n_columns for _ in range(self.n_rows)]
        top = [[0.0] * self.n_columns for _ in range(self.n_rows)]
        bot = [[0.0] * self.n_columns for _ in range(self.n_rows)]
        
        for cell in self.cells:
            r, c = cell.row, cell.col
            ibound[r][c] = 1 if cell.is_active else 0
            hk[r][c] = cell.hydraulic_conductivity
            top[r][c] = cell.z_max
            bot[r][c] = cell.z_min
        
        return {
            "ibound": ibound,
            "hk": hk,
            "top": top,
            "bot": bot
        }


class MeshGenerator:
    """
    Generates numerical meshes from geological cross-sections.
    """
    
    def __init__(self, cross_section: GeologicalCrossSection):
        self.cross_section = cross_section
        
    def _interpolate_elevation(self, layer: GeologicalLayer, x: float, 
                                use_top: bool = True) -> float:
        """Interpolate layer elevation at a given x position."""
        x_positions = self.cross_section.x_positions
        elevations = layer.top_elevations if use_top else layer.bottom_elevations
        
        # Find bracketing x values
        for i in range(len(x_positions) - 1):
            if x_positions[i] <= x <= x_positions[i + 1]:
                # Linear interpolation
                t = (x - x_positions[i]) / (x_positions[i + 1] - x_positions[i])
                return elevations[i] + t * (elevations[i + 1] - elevations[i])
        
        # Edge cases
        if x <= x_positions[0]:
            return elevations[0]
        return elevations[-1]
    
    def _get_layer_at_point(self, x: float, z: float) -> Optional[GeologicalLayer]:
        """Determine which geological layer contains a point."""
        for layer in self.cross_section.layers:
            top = self._interpolate_elevation(layer, x, use_top=True)
            bottom = self._interpolate_elevation(layer, x, use_top=False)
            if bottom <= z <= top:
                return layer
        return None
    
    def generate_structured_mesh(self, n_columns: int = 50, n_rows: int = 25,
                                  refine_near_wells: bool = True) -> NumericalMesh:
        """
        Generate a structured (finite difference) mesh.
        
        Args:
            n_columns: Number of columns in the mesh
            n_rows: Number of rows in the mesh
            refine_near_wells: Whether to refine mesh near wells
            
        Returns:
            NumericalMesh object with structured grid
        """
        x_positions = self.cross_section.x_positions
        x_min = min(x_positions)
        x_max = max(x_positions)
        
        # Get elevation range from all layers
        all_elevations = []
        for layer in self.cross_section.layers:
            all_elevations.extend(layer.top_elevations)
            all_elevations.extend(layer.bottom_elevations)
        z_min = min(all_elevations)
        z_max = max(all_elevations)
        
        # Generate column widths (uniform or refined)
        if refine_near_wells and self.cross_section.wells:
            dx = self._generate_refined_spacing(
                x_min, x_max, n_columns,
                [w.x_position for w in self.cross_section.wells]
            )
        else:
            dx = [(x_max - x_min) / n_columns] * n_columns
        
        # Generate row heights (uniform)
        dz = [(z_max - z_min) / n_rows] * n_rows
        
        # Calculate cell boundaries
        x_edges = [x_min]
        for d in dx:
            x_edges.append(x_edges[-1] + d)
        
        z_edges = [z_max]  # Start from top
        for d in dz:
            z_edges.append(z_edges[-1] - d)
        
        # Generate cells
        cells = []
        cell_id = 0
        layer_stats = {}
        
        for row in range(n_rows):
            for col in range(n_columns):
                x_cell_min = x_edges[col]
                x_cell_max = x_edges[col + 1]
                z_cell_max = z_edges[row]
                z_cell_min = z_edges[row + 1]
                
                x_center = (x_cell_min + x_cell_max) / 2
                z_center = (z_cell_min + z_cell_max) / 2
                
                # Determine layer at cell center
                layer = self._get_layer_at_point(x_center, z_center)
                
                if layer:
                    layer_name = layer.name
                    is_aquifer = layer.is_aquifer
                    k = layer.hydraulic_conductivity or 0.0
                    is_active = True
                else:
                    layer_name = "Inactive"
                    is_aquifer = False
                    k = 0.0
                    is_active = False
                
                cell = MeshCell(
                    id=cell_id,
                    row=row,
                    col=col,
                    x_center=x_center,
                    z_center=z_center,
                    x_min=x_cell_min,
                    x_max=x_cell_max,
                    z_min=z_cell_min,
                    z_max=z_cell_max,
                    width=x_cell_max - x_cell_min,
                    height=z_cell_max - z_cell_min,
                    area=(x_cell_max - x_cell_min) * (z_cell_max - z_cell_min),
                    layer_name=layer_name,
                    is_aquifer=is_aquifer,
                    hydraulic_conductivity=k,
                    is_active=is_active
                )
                cells.append(cell)
                cell_id += 1
                
                # Update layer statistics
                if layer_name not in layer_stats:
                    layer_stats[layer_name] = {
                        "cell_count": 0,
                        "total_area": 0.0,
                        "is_aquifer": is_aquifer,
                        "hydraulic_conductivity": k
                    }
                layer_stats[layer_name]["cell_count"] += 1
                layer_stats[layer_name]["total_area"] += cell.area
        
        return NumericalMesh(
            title=self.cross_section.title,
            mesh_type="structured",
            n_columns=n_columns,
            n_rows=n_rows,
            n_cells=len(cells),
            x_min=x_min,
            x_max=x_max,
            z_min=z_min,
            z_max=z_max,
            cells=cells,
            dx=dx,
            dz=dz,
            layer_stats=layer_stats
        )
    
    def _generate_refined_spacing(self, x_min: float, x_max: float, 
                                   n: int, refinement_points: List[float],
                                   refinement_factor: float = 0.5) -> List[float]:
        """Generate variable spacing with refinement near specified points."""
        total_length = x_max - x_min
        base_dx = total_length / n
        
        # Create initial uniform spacing
        dx = [base_dx] * n
        
        # Refine near wells
        for well_x in refinement_points:
            well_col = int((well_x - x_min) / base_dx)
            well_col = max(0, min(n - 1, well_col))
            
            # Refine cells near the well
            for offset in range(-2, 3):
                col = well_col + offset
                if 0 <= col < n:
                    factor = refinement_factor ** (3 - abs(offset))
                    dx[col] *= factor
        
        # Normalize to maintain total length
        current_total = sum(dx)
        scale = total_length / current_total
        dx = [d * scale for d in dx]
        
        return dx
    
    def generate_unstructured_mesh(self, target_element_size: float = 20.0) -> NumericalMesh:
        """
        Generate an unstructured (triangular) mesh.
        
        Args:
            target_element_size: Target size for mesh elements
            
        Returns:
            NumericalMesh object with triangular elements
        """
        x_positions = self.cross_section.x_positions
        x_min = min(x_positions)
        x_max = max(x_positions)
        
        all_elevations = []
        for layer in self.cross_section.layers:
            all_elevations.extend(layer.top_elevations)
            all_elevations.extend(layer.bottom_elevations)
        z_min = min(all_elevations)
        z_max = max(all_elevations)
        
        # Generate nodes on a regular grid first
        n_x = int((x_max - x_min) / target_element_size) + 1
        n_z = int((z_max - z_min) / target_element_size) + 1
        
        dx = (x_max - x_min) / (n_x - 1) if n_x > 1 else 0
        dz = (z_max - z_min) / (n_z - 1) if n_z > 1 else 0
        
        # Create nodes
        nodes = []
        node_id = 0
        node_grid = {}  # (i, j) -> node_id
        
        for j in range(n_z):
            for i in range(n_x):
                x = x_min + i * dx
                z = z_max - j * dz
                nodes.append(MeshNode(id=node_id, x=x, z=z))
                node_grid[(i, j)] = node_id
                node_id += 1
        
        # Create triangular elements
        elements = []
        element_id = 0
        layer_stats = {}
        
        for j in range(n_z - 1):
            for i in range(n_x - 1):
                # Two triangles per quad cell
                n1 = node_grid[(i, j)]
                n2 = node_grid[(i + 1, j)]
                n3 = node_grid[(i, j + 1)]
                n4 = node_grid[(i + 1, j + 1)]
                
                for tri_nodes in [(n1, n2, n3), (n2, n4, n3)]:
                    # Calculate centroid
                    cx = sum(nodes[n].x for n in tri_nodes) / 3
                    cz = sum(nodes[n].z for n in tri_nodes) / 3
                    
                    # Calculate area
                    x1, z1 = nodes[tri_nodes[0]].x, nodes[tri_nodes[0]].z
                    x2, z2 = nodes[tri_nodes[1]].x, nodes[tri_nodes[1]].z
                    x3, z3 = nodes[tri_nodes[2]].x, nodes[tri_nodes[2]].z
                    area = abs((x1 * (z2 - z3) + x2 * (z3 - z1) + x3 * (z1 - z2)) / 2)
                    
                    # Determine layer
                    layer = self._get_layer_at_point(cx, cz)
                    
                    if layer:
                        layer_name = layer.name
                        is_aquifer = layer.is_aquifer
                        k = layer.hydraulic_conductivity or 0.0
                    else:
                        layer_name = "Inactive"
                        is_aquifer = False
                        k = 0.0
                    
                    element = MeshElement(
                        id=element_id,
                        node_ids=list(tri_nodes),
                        layer_name=layer_name,
                        is_aquifer=is_aquifer,
                        hydraulic_conductivity=k,
                        centroid_x=cx,
                        centroid_z=cz,
                        area=area
                    )
                    elements.append(element)
                    element_id += 1
                    
                    # Update stats
                    if layer_name not in layer_stats:
                        layer_stats[layer_name] = {
                            "element_count": 0,
                            "total_area": 0.0,
                            "is_aquifer": is_aquifer,
                            "hydraulic_conductivity": k
                        }
                    layer_stats[layer_name]["element_count"] += 1
                    layer_stats[layer_name]["total_area"] += area
        
        return NumericalMesh(
            title=self.cross_section.title,
            mesh_type="unstructured",
            n_columns=n_x,
            n_rows=n_z,
            n_cells=len(elements),
            x_min=x_min,
            x_max=x_max,
            z_min=z_min,
            z_max=z_max,
            nodes=nodes,
            elements=elements,
            dx=[dx] * (n_x - 1),
            dz=[dz] * (n_z - 1),
            layer_stats=layer_stats
        )


def generate_mesh_from_cross_section(cross_section: GeologicalCrossSection,
                                      n_columns: int = 50,
                                      n_rows: int = 25,
                                      mesh_type: str = "structured") -> NumericalMesh:
    """
    Convenience function to generate a mesh from a cross-section.
    
    Args:
        cross_section: The geological cross-section
        n_columns: Number of columns (for structured) or x-divisions
        n_rows: Number of rows (for structured) or z-divisions
        mesh_type: "structured" or "unstructured"
        
    Returns:
        NumericalMesh object
    """
    generator = MeshGenerator(cross_section)
    
    if mesh_type == "structured":
        return generator.generate_structured_mesh(n_columns, n_rows)
    else:
        # Calculate target element size from n_columns
        x_range = max(cross_section.x_positions) - min(cross_section.x_positions)
        target_size = x_range / n_columns
        return generator.generate_unstructured_mesh(target_size)
