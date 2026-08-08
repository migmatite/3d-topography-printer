"""
Geological Cross Section Generator for Groundwater Visualization.

This module provides classes and functions for creating geological
cross-sections that display aquifers, aquitards, water tables, and wells.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import json
from html import escape as html_escape


def xml_escape(text: str) -> str:
    """Escape special XML characters."""
    return html_escape(text, quote=True)


@dataclass
class GeologicalLayer:
    """Represents a geological layer in the cross-section."""
    name: str
    top_elevations: List[float]
    bottom_elevations: List[float]
    color: str
    pattern: str = "solid"
    is_aquifer: bool = False
    hydraulic_conductivity: Optional[float] = None
    description: str = ""
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "top_elevations": self.top_elevations,
            "bottom_elevations": self.bottom_elevations,
            "color": self.color,
            "pattern": self.pattern,
            "is_aquifer": self.is_aquifer,
            "hydraulic_conductivity": self.hydraulic_conductivity,
            "description": self.description
        }


@dataclass
class Well:
    """Represents a well in the cross-section."""
    name: str
    x_position: float
    top_elevation: float
    bottom_elevation: float
    screen_top: float
    screen_bottom: float
    water_level: Optional[float] = None
    well_type: str = "monitoring"
    pumping_rate: Optional[float] = None
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "x_position": self.x_position,
            "top_elevation": self.top_elevation,
            "bottom_elevation": self.bottom_elevation,
            "screen_top": self.screen_top,
            "screen_bottom": self.screen_bottom,
            "water_level": self.water_level,
            "well_type": self.well_type,
            "pumping_rate": self.pumping_rate
        }


@dataclass
class GeologicalCrossSection:
    """
    A geological cross-section for groundwater visualization.
    
    This class manages geological layers, wells, and water table data
    to create comprehensive groundwater cross-section visualizations.
    """
    title: str
    x_positions: List[float]
    vertical_exaggeration: float = 10.0
    layers: List[GeologicalLayer] = field(default_factory=list)
    wells: List[Well] = field(default_factory=list)
    water_table: Optional[List[float]] = None
    flow_arrows: List[Tuple[float, float, float, float]] = field(default_factory=list)
    
    def add_layer(self, layer: GeologicalLayer) -> None:
        """Add a geological layer to the cross-section."""
        if len(layer.top_elevations) != len(self.x_positions):
            raise ValueError(
                f"Layer elevations count ({len(layer.top_elevations)}) "
                f"must match x_positions count ({len(self.x_positions)})"
            )
        self.layers.append(layer)
    
    def add_well(self, well: Well) -> None:
        """Add a well to the cross-section."""
        if not (self.x_positions[0] <= well.x_position <= self.x_positions[-1]):
            raise ValueError(
                f"Well position ({well.x_position}) must be within "
                f"x_positions range ({self.x_positions[0]} - {self.x_positions[-1]})"
            )
        self.wells.append(well)
    
    def set_water_table(self, elevations: List[float]) -> None:
        """Set the water table elevations."""
        if len(elevations) != len(self.x_positions):
            raise ValueError(
                f"Water table elevations count ({len(elevations)}) "
                f"must match x_positions count ({len(self.x_positions)})"
            )
        self.water_table = elevations
    
    def add_flow_arrow(self, x1: float, y1: float, x2: float, y2: float) -> None:
        """Add a groundwater flow arrow."""
        self.flow_arrows.append((x1, y1, x2, y2))
    
    def to_dict(self) -> dict:
        """Convert cross-section to dictionary for serialization."""
        return {
            "title": self.title,
            "x_positions": self.x_positions,
            "vertical_exaggeration": self.vertical_exaggeration,
            "layers": [layer.to_dict() for layer in self.layers],
            "wells": [well.to_dict() for well in self.wells],
            "water_table": self.water_table,
            "flow_arrows": self.flow_arrows
        }
    
    def to_json(self) -> str:
        """Convert cross-section to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def generate_svg(self, width: int = 1200, height: int = 600) -> str:
        """Generate an SVG representation of the cross-section."""
        if not self.layers:
            raise ValueError("No layers defined in cross-section")
        
        padding = 80
        plot_width = width - 2 * padding
        plot_height = height - 2 * padding
        
        all_elevations = []
        for layer in self.layers:
            all_elevations.extend(layer.top_elevations)
            all_elevations.extend(layer.bottom_elevations)
        
        min_elev = min(all_elevations)
        max_elev = max(all_elevations)
        min_x = min(self.x_positions)
        max_x = max(self.x_positions)
        
        def scale_x(x: float) -> float:
            return padding + (x - min_x) / (max_x - min_x) * plot_width
        
        def scale_y(y: float) -> float:
            return padding + (max_elev - y) / (max_elev - min_elev) * plot_height
        
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
            '<defs>',
            '  <pattern id="gravel" patternUnits="userSpaceOnUse" width="20" height="20">',
            '    <rect width="20" height="20" fill="#d4a574"/>',
            '    <circle cx="5" cy="5" r="3" fill="#b8956e"/>',
            '    <circle cx="15" cy="12" r="2" fill="#c9a882"/>',
            '    <circle cx="8" cy="16" r="2.5" fill="#bfa078"/>',
            '  </pattern>',
            '  <pattern id="sand" patternUnits="userSpaceOnUse" width="10" height="10">',
            '    <rect width="10" height="10" fill="#f4d03f"/>',
            '    <circle cx="2" cy="2" r="0.5" fill="#d4b82f"/>',
            '    <circle cx="7" cy="5" r="0.5" fill="#d4b82f"/>',
            '    <circle cx="4" cy="8" r="0.5" fill="#d4b82f"/>',
            '  </pattern>',
            '  <pattern id="clay" patternUnits="userSpaceOnUse" width="20" height="10">',
            '    <rect width="20" height="10" fill="#8b7355"/>',
            '    <line x1="0" y1="5" x2="20" y2="5" stroke="#6b5344" stroke-width="1"/>',
            '  </pattern>',
            '  <pattern id="limestone" patternUnits="userSpaceOnUse" width="30" height="20">',
            '    <rect width="30" height="20" fill="#d3d3d3"/>',
            '    <rect x="0" y="0" width="14" height="9" fill="#c0c0c0" stroke="#a0a0a0" stroke-width="0.5"/>',
            '    <rect x="16" y="0" width="14" height="9" fill="#c8c8c8" stroke="#a0a0a0" stroke-width="0.5"/>',
            '    <rect x="8" y="11" width="14" height="9" fill="#c4c4c4" stroke="#a0a0a0" stroke-width="0.5"/>',
            '  </pattern>',
            '  <pattern id="shale" patternUnits="userSpaceOnUse" width="20" height="8">',
            '    <rect width="20" height="8" fill="#4a4a4a"/>',
            '    <line x1="0" y1="2" x2="20" y2="2" stroke="#3a3a3a" stroke-width="1"/>',
            '    <line x1="0" y1="6" x2="20" y2="6" stroke="#3a3a3a" stroke-width="1"/>',
            '  </pattern>',
            '  <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">',
            '    <polygon points="0 0, 10 3.5, 0 7" fill="#0066cc"/>',
            '  </marker>',
            '</defs>',
            f'<rect width="{width}" height="{height}" fill="#f8f9fa"/>',
            f'<text x="{width/2}" y="30" text-anchor="middle" font-size="20" font-weight="bold" fill="#333">{xml_escape(self.title)}</text>',
        ]
        
        for layer in reversed(self.layers):
            points_top = [f"{scale_x(x)},{scale_y(y)}" 
                         for x, y in zip(self.x_positions, layer.top_elevations)]
            points_bottom = [f"{scale_x(x)},{scale_y(y)}" 
                            for x, y in zip(reversed(self.x_positions), reversed(layer.bottom_elevations))]
            polygon_points = " ".join(points_top + points_bottom)
            
            fill = f"url(#{layer.pattern})" if layer.pattern != "solid" else layer.color
            svg_parts.append(
                f'<polygon points="{polygon_points}" fill="{fill}" stroke="#333" stroke-width="1"/>'
            )
        
        if self.water_table:
            wt_points = " ".join([f"{scale_x(x)},{scale_y(y)}" 
                                 for x, y in zip(self.x_positions, self.water_table)])
            svg_parts.append(
                f'<polyline points="{wt_points}" fill="none" stroke="#0077be" '
                f'stroke-width="3" stroke-dasharray="10,5"/>'
            )
        
        for x1, y1, x2, y2 in self.flow_arrows:
            svg_parts.append(
                f'<line x1="{scale_x(x1)}" y1="{scale_y(y1)}" '
                f'x2="{scale_x(x2)}" y2="{scale_y(y2)}" '
                f'stroke="#0066cc" stroke-width="2" marker-end="url(#arrowhead)"/>'
            )
        
        for well in self.wells:
            wx = scale_x(well.x_position)
            wy_top = scale_y(well.top_elevation)
            wy_bottom = scale_y(well.bottom_elevation)
            wy_screen_top = scale_y(well.screen_top)
            wy_screen_bottom = scale_y(well.screen_bottom)
            
            svg_parts.append(
                f'<rect x="{wx-3}" y="{wy_top}" width="6" height="{wy_bottom-wy_top}" '
                f'fill="#666" stroke="#333" stroke-width="1"/>'
            )
            svg_parts.append(
                f'<rect x="{wx-4}" y="{wy_screen_top}" width="8" height="{wy_screen_bottom-wy_screen_top}" '
                f'fill="none" stroke="#333" stroke-width="2" stroke-dasharray="3,2"/>'
            )
            
            if well.water_level:
                wy_wl = scale_y(well.water_level)
                svg_parts.append(
                    f'<line x1="{wx-6}" y1="{wy_wl}" x2="{wx+6}" y2="{wy_wl}" '
                    f'stroke="#0077be" stroke-width="2"/>'
                )
            
            svg_parts.append(
                f'<text x="{wx}" y="{wy_top-10}" text-anchor="middle" '
                f'font-size="12" fill="#333">{xml_escape(well.name)}</text>'
            )
        
        svg_parts.append(
            f'<line x1="{padding}" y1="{height-padding}" x2="{width-padding}" y2="{height-padding}" '
            f'stroke="#333" stroke-width="2"/>'
        )
        svg_parts.append(
            f'<line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height-padding}" '
            f'stroke="#333" stroke-width="2"/>'
        )
        
        for i in range(6):
            y = padding + i * plot_height / 5
            elev = max_elev - i * (max_elev - min_elev) / 5
            svg_parts.append(
                f'<line x1="{padding-5}" y1="{y}" x2="{padding}" y2="{y}" stroke="#333" stroke-width="1"/>'
            )
            svg_parts.append(
                f'<text x="{padding-10}" y="{y+4}" text-anchor="end" font-size="11" fill="#333">{elev:.0f}</text>'
            )
        
        for i in range(6):
            x = padding + i * plot_width / 5
            dist = min_x + i * (max_x - min_x) / 5
            svg_parts.append(
                f'<line x1="{x}" y1="{height-padding}" x2="{x}" y2="{height-padding+5}" stroke="#333" stroke-width="1"/>'
            )
            svg_parts.append(
                f'<text x="{x}" y="{height-padding+20}" text-anchor="middle" font-size="11" fill="#333">{dist:.0f}</text>'
            )
        
        svg_parts.append(
            f'<text x="{width/2}" y="{height-20}" text-anchor="middle" font-size="14" fill="#333">Distance (m)</text>'
        )
        svg_parts.append(
            f'<text x="20" y="{height/2}" text-anchor="middle" font-size="14" fill="#333" '
            f'transform="rotate(-90, 20, {height/2})">Elevation (m)</text>'
        )
        
        legend_x = width - 180
        legend_y = padding + 20
        svg_parts.append(f'<rect x="{legend_x-10}" y="{legend_y-15}" width="170" height="{len(self.layers)*25+60}" fill="white" stroke="#333" stroke-width="1" rx="5"/>')
        svg_parts.append(f'<text x="{legend_x}" y="{legend_y}" font-size="12" font-weight="bold" fill="#333">Legend</text>')
        
        for i, layer in enumerate(self.layers):
            ly = legend_y + 20 + i * 25
            fill = f"url(#{layer.pattern})" if layer.pattern != "solid" else layer.color
            svg_parts.append(f'<rect x="{legend_x}" y="{ly}" width="20" height="15" fill="{fill}" stroke="#333" stroke-width="1"/>')
            svg_parts.append(f'<text x="{legend_x+30}" y="{ly+12}" font-size="11" fill="#333">{xml_escape(layer.name)}</text>')
        
        wt_y = legend_y + 20 + len(self.layers) * 25
        svg_parts.append(f'<line x1="{legend_x}" y1="{wt_y+7}" x2="{legend_x+20}" y2="{wt_y+7}" stroke="#0077be" stroke-width="3" stroke-dasharray="5,3"/>')
        svg_parts.append(f'<text x="{legend_x+30}" y="{wt_y+12}" font-size="11" fill="#333">Water Table</text>')
        
        svg_parts.append('</svg>')
        
        return '\n'.join(svg_parts)
    
    def generate_html(self, width: int = 1200, height: int = 600) -> str:
        """Generate a complete HTML page with the cross-section visualization."""
        svg_content = self.generate_svg(width, height)
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html_escape(self.title)}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .card {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
            margin-bottom: 20px;
        }}
        .svg-container {{
            padding: 20px;
            background: #f8f9fa;
        }}
        .svg-container svg {{
            width: 100%;
            height: auto;
        }}
        .info-panel {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            padding: 20px;
        }}
        .info-section {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
        }}
        .info-section h3 {{
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        .layer-item, .well-item {{
            display: flex;
            align-items: center;
            padding: 10px;
            margin-bottom: 8px;
            background: white;
            border-radius: 6px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .layer-color {{
            width: 30px;
            height: 30px;
            border-radius: 4px;
            margin-right: 12px;
            border: 1px solid #ddd;
        }}
        .layer-info, .well-info {{
            flex: 1;
        }}
        .layer-name, .well-name {{
            font-weight: 600;
            color: #333;
        }}
        .layer-type, .well-type {{
            font-size: 12px;
            color: #666;
        }}
        .aquifer-badge {{
            background: #0077be;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
            margin-left: 8px;
        }}
        .footer {{
            text-align: center;
            color: white;
            padding: 20px;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌍 {html_escape(self.title)}</h1>
        
        <div class="card">
            <div class="svg-container">
                {svg_content}
            </div>
            
            <div class="info-panel">
                <div class="info-section">
                    <h3>📊 Geological Layers</h3>
                    {"".join(self._generate_layer_html(layer) for layer in self.layers)}
                </div>
                
                <div class="info-section">
                    <h3>🔧 Wells</h3>
                    {"".join(self._generate_well_html(well) for well in self.wells) if self.wells else '<p style="color: #666;">No wells defined</p>'}
                </div>
                
                <div class="info-section">
                    <h3>ℹ️ Cross-Section Info</h3>
                    <p><strong>Horizontal Extent:</strong> {min(self.x_positions):.0f} - {max(self.x_positions):.0f} m</p>
                    <p><strong>Vertical Exaggeration:</strong> {self.vertical_exaggeration}x</p>
                    <p><strong>Number of Layers:</strong> {len(self.layers)}</p>
                    <p><strong>Number of Wells:</strong> {len(self.wells)}</p>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Geological Cross Section Tool</p>
        </div>
    </div>
</body>
</html>'''
        return html
    
    def _generate_layer_html(self, layer: GeologicalLayer) -> str:
        aquifer_badge = '<span class="aquifer-badge">Aquifer</span>' if layer.is_aquifer else ''
        return f'''
        <div class="layer-item">
            <div class="layer-color" style="background-color: {layer.color};"></div>
            <div class="layer-info">
                <div class="layer-name">{html_escape(layer.name)}{aquifer_badge}</div>
                <div class="layer-type">{html_escape(layer.description or layer.pattern.title())}</div>
            </div>
        </div>'''
    
    def _generate_well_html(self, well: Well) -> str:
        details = f"Depth: {well.top_elevation - well.bottom_elevation:.1f}m"
        if well.water_level:
            details += f" | WL: {well.water_level:.1f}m"
        if well.pumping_rate:
            details += f" | Q: {well.pumping_rate:.1f} m³/d"
        return f'''
        <div class="well-item">
            <div class="well-info">
                <div class="well-name">{html_escape(well.name)}</div>
                <div class="well-type">{html_escape(well.well_type.title())} Well | {details}</div>
            </div>
        </div>'''


def create_example_cross_section() -> GeologicalCrossSection:
    """Create an example groundwater cross-section for demonstration."""
    x_positions = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    
    cross_section = GeologicalCrossSection(
        title="Groundwater Cross-Section: Alluvial Valley Aquifer System",
        x_positions=x_positions,
        vertical_exaggeration=10.0
    )
    
    cross_section.add_layer(GeologicalLayer(
        name="Topsoil",
        top_elevations=[105, 104, 103, 100, 98, 97, 98, 100, 102, 104, 105],
        bottom_elevations=[102, 101, 100, 97, 95, 94, 95, 97, 99, 101, 102],
        color="#8B4513",
        pattern="solid",
        is_aquifer=False,
        description="Organic-rich surface soil"
    ))
    
    cross_section.add_layer(GeologicalLayer(
        name="Sand & Gravel (Unconfined Aquifer)",
        top_elevations=[102, 101, 100, 97, 95, 94, 95, 97, 99, 101, 102],
        bottom_elevations=[85, 84, 82, 78, 75, 74, 76, 80, 84, 86, 87],
        color="#d4a574",
        pattern="gravel",
        is_aquifer=True,
        hydraulic_conductivity=50.0,
        description="High-permeability alluvial deposits"
    ))
    
    cross_section.add_layer(GeologicalLayer(
        name="Clay (Aquitard)",
        top_elevations=[85, 84, 82, 78, 75, 74, 76, 80, 84, 86, 87],
        bottom_elevations=[75, 74, 72, 68, 65, 64, 66, 70, 74, 76, 77],
        color="#8b7355",
        pattern="clay",
        is_aquifer=False,
        hydraulic_conductivity=0.001,
        description="Low-permeability confining layer"
    ))
    
    cross_section.add_layer(GeologicalLayer(
        name="Limestone (Confined Aquifer)",
        top_elevations=[75, 74, 72, 68, 65, 64, 66, 70, 74, 76, 77],
        bottom_elevations=[55, 54, 52, 48, 45, 44, 46, 50, 54, 56, 57],
        color="#d3d3d3",
        pattern="limestone",
        is_aquifer=True,
        hydraulic_conductivity=15.0,
        description="Fractured carbonate aquifer"
    ))
    
    cross_section.add_layer(GeologicalLayer(
        name="Shale (Bedrock)",
        top_elevations=[55, 54, 52, 48, 45, 44, 46, 50, 54, 56, 57],
        bottom_elevations=[35, 34, 32, 28, 25, 24, 26, 30, 34, 36, 37],
        color="#4a4a4a",
        pattern="shale",
        is_aquifer=False,
        description="Impermeable basement rock"
    ))
    
    cross_section.set_water_table([98, 97, 95, 92, 90, 89, 90, 92, 95, 97, 98])
    
    cross_section.add_well(Well(
        name="MW-1",
        x_position=200,
        top_elevation=103,
        bottom_elevation=70,
        screen_top=85,
        screen_bottom=75,
        water_level=95,
        well_type="monitoring"
    ))
    
    cross_section.add_well(Well(
        name="PW-1",
        x_position=500,
        top_elevation=97,
        bottom_elevation=50,
        screen_top=65,
        screen_bottom=50,
        water_level=85,
        well_type="production",
        pumping_rate=500.0
    ))
    
    cross_section.add_well(Well(
        name="MW-2",
        x_position=800,
        top_elevation=102,
        bottom_elevation=72,
        screen_top=82,
        screen_bottom=75,
        water_level=94,
        well_type="monitoring"
    ))
    
    cross_section.add_flow_arrow(150, 92, 250, 90)
    cross_section.add_flow_arrow(350, 90, 450, 87)
    cross_section.add_flow_arrow(550, 87, 650, 89)
    cross_section.add_flow_arrow(750, 92, 850, 94)
    
    return cross_section


if __name__ == "__main__":
    cross_section = create_example_cross_section()
    
    html_content = cross_section.generate_html()
    with open("groundwater_cross_section.html", "w") as f:
        f.write(html_content)
    print("Generated: groundwater_cross_section.html")
    
    json_content = cross_section.to_json()
    with open("groundwater_cross_section.json", "w") as f:
        f.write(json_content)
    print("Generated: groundwater_cross_section.json")
