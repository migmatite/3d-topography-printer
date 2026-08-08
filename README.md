# 3D Topography Printer

Project to generate 3D printable topography models.

## Features

### Geological Cross-Section for Groundwater

Create professional geological cross-sections for groundwater visualization with:

- **Multiple geological layers** with customizable patterns (gravel, sand, clay, limestone, shale)
- **Water table visualization** with dashed line styling
- **Well representations** (monitoring and production wells with screens)
- **Groundwater flow arrows** showing flow direction
- **Interactive HTML output** with toggleable elements
- **SVG and JSON export** options

#### Quick Start

```python
from geological_cross_section import GeologicalCrossSection, GeologicalLayer, Well
from geological_cross_section.cross_section import create_example_cross_section

# Create an example cross-section
cross_section = create_example_cross_section()

# Generate HTML visualization
html_content = cross_section.generate_html()
with open("groundwater_cross_section.html", "w") as f:
    f.write(html_content)
```

#### Command Line Usage

```bash
# Generate example cross-section as HTML
python -m geological_cross_section.cli --example --output example.html

# Generate from JSON configuration
python -m geological_cross_section.cli --config examples/sample_config.json --output output.html

# Generate SVG only
python -m geological_cross_section.cli --example --format svg --output example.svg
```

#### Creating Custom Cross-Sections

```python
from geological_cross_section import GeologicalCrossSection, GeologicalLayer, Well

# Define x positions along the cross-section (in meters)
x_positions = [0, 100, 200, 300, 400, 500]

# Create the cross-section
cross_section = GeologicalCrossSection(
    title="My Groundwater Cross-Section",
    x_positions=x_positions,
    vertical_exaggeration=10.0
)

# Add geological layers (from top to bottom)
cross_section.add_layer(GeologicalLayer(
    name="Sand & Gravel Aquifer",
    top_elevations=[100, 98, 96, 95, 97, 99],
    bottom_elevations=[70, 68, 66, 65, 67, 69],
    color="#d4a574",
    pattern="gravel",
    is_aquifer=True,
    hydraulic_conductivity=50.0,
    description="Unconfined aquifer"
))

# Add wells
cross_section.add_well(Well(
    name="MW-1",
    x_position=200,
    top_elevation=96,
    bottom_elevation=60,
    screen_top=75,
    screen_bottom=60,
    water_level=90,
    well_type="monitoring"
))

# Set water table
cross_section.set_water_table([95, 93, 91, 90, 92, 94])

# Add flow arrows
cross_section.add_flow_arrow(100, 90, 200, 88)

# Generate output
html = cross_section.generate_html()
svg = cross_section.generate_svg()
json_data = cross_section.to_json()
```

#### Available Patterns

- `solid` - Solid fill color
- `gravel` - Gravel/pebble texture for alluvial deposits
- `sand` - Fine dot pattern for sand
- `clay` - Horizontal lines for clay/silt
- `limestone` - Block pattern for carbite rocks
- `shale` - Thin horizontal lines for shale

## Installation

```bash
pip install -r requirements.txt
```

## Running Tests

```bash
pytest tests/ -v
```

## Examples

See the `examples/` directory for:
- `groundwater_cross_section.html` - Interactive visualization
- `sample_config.json` - Example JSON configuration for a coastal aquifer
