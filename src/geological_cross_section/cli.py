#!/usr/bin/env python3
"""
Command-line interface for generating geological cross-sections.
"""

import argparse
import json
import sys
from pathlib import Path

from .cross_section import (
    GeologicalCrossSection,
    GeologicalLayer,
    Well,
    create_example_cross_section
)


def main():
    parser = argparse.ArgumentParser(
        description="Generate geological cross-sections for groundwater visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate example cross-section
  python -m geological_cross_section.cli --example --output example.html

  # Generate from JSON configuration
  python -m geological_cross_section.cli --config config.json --output output.html

  # Generate SVG only
  python -m geological_cross_section.cli --example --format svg --output example.svg
        """
    )
    
    parser.add_argument(
        "--example",
        action="store_true",
        help="Generate an example cross-section"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to JSON configuration file"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="groundwater_cross_section.html",
        help="Output file path (default: groundwater_cross_section.html)"
    )
    
    parser.add_argument(
        "--format",
        choices=["html", "svg", "json"],
        default="html",
        help="Output format (default: html)"
    )
    
    parser.add_argument(
        "--width",
        type=int,
        default=1200,
        help="SVG width in pixels (default: 1200)"
    )
    
    parser.add_argument(
        "--height",
        type=int,
        default=600,
        help="SVG height in pixels (default: 600)"
    )
    
    args = parser.parse_args()
    
    if not args.example and not args.config:
        parser.error("Either --example or --config must be specified")
    
    if args.example:
        cross_section = create_example_cross_section()
    else:
        cross_section = load_from_config(args.config)
    
    if args.format == "html":
        content = cross_section.generate_html(args.width, args.height)
    elif args.format == "svg":
        content = cross_section.generate_svg(args.width, args.height)
    elif args.format == "json":
        content = cross_section.to_json()
    
    output_path = Path(args.output)
    output_path.write_text(content)
    print(f"Generated: {output_path}")


def load_from_config(config_path: str) -> GeologicalCrossSection:
    """Load cross-section from JSON configuration file."""
    with open(config_path) as f:
        config = json.load(f)
    
    cross_section = GeologicalCrossSection(
        title=config.get("title", "Geological Cross-Section"),
        x_positions=config["x_positions"],
        vertical_exaggeration=config.get("vertical_exaggeration", 10.0)
    )
    
    for layer_config in config.get("layers", []):
        layer = GeologicalLayer(
            name=layer_config["name"],
            top_elevations=layer_config["top_elevations"],
            bottom_elevations=layer_config["bottom_elevations"],
            color=layer_config.get("color", "#888888"),
            pattern=layer_config.get("pattern", "solid"),
            is_aquifer=layer_config.get("is_aquifer", False),
            hydraulic_conductivity=layer_config.get("hydraulic_conductivity"),
            description=layer_config.get("description", "")
        )
        cross_section.add_layer(layer)
    
    for well_config in config.get("wells", []):
        well = Well(
            name=well_config["name"],
            x_position=well_config["x_position"],
            top_elevation=well_config["top_elevation"],
            bottom_elevation=well_config["bottom_elevation"],
            screen_top=well_config["screen_top"],
            screen_bottom=well_config["screen_bottom"],
            water_level=well_config.get("water_level"),
            well_type=well_config.get("well_type", "monitoring"),
            pumping_rate=well_config.get("pumping_rate")
        )
        cross_section.add_well(well)
    
    if "water_table" in config:
        cross_section.set_water_table(config["water_table"])
    
    for arrow in config.get("flow_arrows", []):
        cross_section.add_flow_arrow(*arrow)
    
    return cross_section


if __name__ == "__main__":
    main()
