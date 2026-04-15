#!/usr/bin/env python3
"""
Visualize risk heatmap from wrapper script output JSON.
Supports both square and hexagon grids.
"""

import sys
import os
import json
import argparse
import math
from typing import List, Dict, Any, Optional, Tuple

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch, RegularPolygon
from matplotlib.collections import PatchCollection
from matplotlib.colors import LinearSegmentedColormap


def load_results_from_json(filepath: str) -> Dict[str, Any]:
    """Load risk calculation results from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_relative_luminance(r: float, g: float, b: float) -> float:
    """
    Calculate relative luminance of a color (sRGB).
    Uses WCAG formula: https://www.w3.org/WAI/WCAG21/Techniques/general/G17.html

    Args:
        r, g, b: Color values in [0, 1] range

    Returns:
        Relative luminance value
    """
    def linearize(v: float) -> float:
        if v <= 0.03928:
            return v / 12.92
        else:
            return ((v + 0.055) / 1.055) ** 2.4

    r_lin = linearize(r)
    g_lin = linearize(g)
    b_lin = linearize(b)

    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def get_contrast_color(facecolor: Tuple[float, float, float]) -> str:
    """
    Get the color (black or white) that has maximum contrast with the given facecolor.

    Args:
        facecolor: RGB tuple with values in [0, 1] range

    Returns:
        'black' or 'white', whichever has better contrast
    """
    luminance = get_relative_luminance(facecolor[0], facecolor[1], facecolor[2])
    return 'white' if luminance < 0.5 else 'black'


def calculate_font_size(num_cols: int, num_rows: int) -> int:
    """
    Calculate appropriate font size based on grid dimensions.

    Args:
        num_cols: Number of columns
        num_rows: Number of rows

    Returns:
        Font size in points
    """
    total_grids = num_cols * num_rows

    if total_grids <= 25:
        return 24
    elif total_grids <= 100:
        return 16
    elif total_grids <= 400:
        return 10
    elif total_grids <= 1000:
        return 7
    else:
        return 5


def calculate_figure_size(num_cols: int, num_rows: int, grid_type: str = 'square') -> Tuple[float, float]:
    """
    Calculate appropriate figure size based on grid dimensions.

    Args:
        num_cols: Number of columns
        num_rows: Number of rows
        grid_type: 'square' or 'hex'

    Returns:
        Tuple of (width, height) in inches
    """
    total_grids = num_cols * num_rows

    if total_grids > 1000:
        # For large grids, use smaller figure
        scale_factor = 0.4
    elif total_grids > 400:
        scale_factor = 0.6
    else:
        scale_factor = 1.0

    if grid_type == 'hex':
        # Pointy-topped hexagons, even-q:
        # width per column: 1.5 * radius
        # height per row: sqrt(3) * radius
        base_width = 1.5 * scale_factor
        base_height = math.sqrt(3) * scale_factor
    else:
        base_width = 1.0 * scale_factor
        base_height = 1.0 * scale_factor

    width = max(10, num_cols * base_width + 4)
    height = max(8, num_rows * base_height + 3)
    return (width, height)


def calculate_dpi(num_cols: int, num_rows: int) -> int:
    """
    Calculate appropriate DPI based on grid size.

    Args:
        num_cols: Number of columns
        num_rows: Number of rows

    Returns:
        DPI value
    """
    total_grids = num_cols * num_rows
    if total_grids > 2000:
        return 100
    elif total_grids > 1000:
        return 120
    else:
        return 150


def should_show_labels(num_cols: int, num_rows: int, user_request: bool) -> bool:
    """
    Determine if labels should be shown based on grid size.

    Args:
        num_cols: Number of columns
        num_rows: Number of rows
        user_request: Whether user requested labels

    Returns:
        True if labels should be shown
    """
    total_grids = num_cols * num_rows
    if total_grids > 500:
        return False  # Auto-disable for large grids
    return user_request


# ============================================================================
# Hexagon Grid Functions (Even-Q Offset Coordinates)
# ============================================================================

def hex_to_pixel_offset(col: int, row: int, size: float = 1.0) -> Tuple[float, float]:
    """
    Convert even-q offset hex coordinates to pixel coordinates.
    Uses pointy-topped hexagons with even-q offset.

    Args:
        col: Column (x) in offset coordinates
        row: Row (y) in offset coordinates
        size: Hexagon radius (distance from center to vertex)

    Returns:
        (x, y) pixel coordinates
    """
    # Even-q offset coordinates for pointy-topped hexagons
    x = size * (3/2 * col)
    y = size * (math.sqrt(3) * (row + 0.5 * (col % 2)))
    return (x, y)


def get_hex_grid_bounds(num_cols: int, num_rows: int, size: float = 1.0) -> Tuple[float, float, float, float]:
    """
    Calculate the bounding box for a hexagon grid (pointy-topped, even-q).

    Args:
        num_cols: Number of columns
        num_rows: Number of rows
        size: Hexagon radius

    Returns:
        (x_min, x_max, y_min, y_max)
    """
    # Calculate bounds by sampling corner points
    all_x = []
    all_y = []

    # Sample corners and key points
    sample_coords = [
        (0, 0),
        (num_cols - 1, 0),
        (0, num_rows - 1),
        (num_cols - 1, num_rows - 1),
    ]

    for col, row in sample_coords:
        x, y = hex_to_pixel_offset(col, row, size)
        all_x.append(x)
        all_y.append(y)

    x_min = min(all_x) - size
    x_max = max(all_x) + size
    y_min = min(all_y) - size
    y_max = max(all_y) + size

    return (x_min, x_max, y_min, y_max)


# ============================================================================
# Visualization Functions
# ============================================================================

def visualize_risk_heatmap_square(
    results_data: Dict[str, Any],
    input_data: Optional[Dict[str, Any]] = None,
    output_path: str = "risk_heatmap_from_json.jpg",
    show_labels: bool = True,
    show_coordinates: bool = False,
    show_features: bool = False
):
    """
    Visualize risk heatmap with square grid.

    Args:
        results_data: Output from risk_model_wrapper.py
        input_data: Optional input data with road/water locations
        output_path: Output image path
        show_labels: Whether to show risk value labels
        show_coordinates: Whether to show (x,y) coordinate labels
        show_features: Whether to overlay road/water features
    """
    results = results_data.get("results", [])

    if not results:
        print("No results found in JSON file!")
        return

    # Try to determine grid size
    num_cols = None
    num_rows = None
    road_coords = set()
    water_coords = set()
    mountain_coords = set()
    hill_coords = set()
    salt_marsh_coords = set()

    # Collect species locations
    rhino_locations = []
    elephant_locations = []
    bird_locations = []

    if input_data:
        map_config = input_data.get("map_config", {})
        num_cols = map_config.get("num_cols") or map_config.get("map_width")
        num_rows = map_config.get("num_rows") or map_config.get("map_height")

        if show_features:
            road_locations = map_config.get("road_locations", [])
            water_locations = map_config.get("water_locations", [])
            mountain_locations = map_config.get("mountain_locations", [])
            hill_locations = map_config.get("hill_locations", [])
            salt_marsh_locations = map_config.get("salt_marsh_locations", [])
            road_coords = set((loc[0], loc[1]) for loc in road_locations)
            water_coords = set((loc[0], loc[1]) for loc in water_locations)
            mountain_coords = set((loc[0], loc[1]) for loc in mountain_locations)
            hill_coords = set((loc[0], loc[1]) for loc in hill_locations)
            salt_marsh_coords = set((loc[0], loc[1]) for loc in salt_marsh_locations)

        # Collect species locations from original grids
        original_grids = input_data.get("original_grids", [])
        if not original_grids:
            # Try to get from grids if original_grids not available
            original_grids = input_data.get("grids", [])

        for grid in original_grids:
            x = grid.get("hex_col") or grid.get("x", 0)
            y = grid.get("hex_row") or grid.get("y", 0)
            species_densities = grid.get("species_densities", {})

            # Threshold for showing species (only show high density)
            rhino_density = species_densities.get("rhino", 0)
            elephant_density = species_densities.get("elephant", 0)
            bird_density = species_densities.get("bird", 0)

            if rhino_density > 0.5:
                rhino_locations.append((x, y))
            if elephant_density > 0.5:
                elephant_locations.append((x, y))
            if bird_density > 0.5:
                bird_locations.append((x, y))

    # If grid size not found, try to infer from data coordinates
    if num_cols is None or num_rows is None:
        xs = []
        ys = []
        for result in results:
            x = result.get("x")
            y = result.get("y")
            if x is not None:
                xs.append(x)
            if y is not None:
                ys.append(y)

        if xs and ys:
            num_cols = max(xs) + 1
            num_rows = max(ys) + 1
            print(f"Inferred grid size from coordinates: {num_cols} cols × {num_rows} rows")
        else:
            n = len(results)
            num_cols = int(np.ceil(np.sqrt(n * 1.5)))
            num_rows = int(np.ceil(n / num_cols))
            print(f"Warning: Grid size not specified. Using {num_cols} cols × {num_rows} rows.")

    # Create risk grid and store face colors
    risk_grid = np.full((num_rows, num_cols), np.nan)
    grid_data = {}
    face_colors = {}

    # Custom colormap
    colors = [
        (0.0, '#00aa00'),   # Green - low risk
        (0.3, '#88cc00'),
        (0.5, '#ffff00'),   # Yellow - medium risk
        (0.7, '#ff8800'),
        (1.0, '#ff0000')    # Red - high risk
    ]
    cmap = LinearSegmentedColormap.from_list('risk_gradient', colors)

    # First pass: collect all data and calculate face colors
    for idx, result in enumerate(results):
        grid_id = result.get("grid_id", f"G{idx:04d}")
        norm_risk = result.get("normalized_risk", 0.0)

        # Try to find coordinates
        x, y = None, None
        x = result.get("x")
        y = result.get("y")

        if (x is None or y is None) and input_data:
            grids = input_data.get("grids", [])
            if idx < len(grids):
                g = grids[idx]
                x = g.get("hex_col") or g.get("x")
                y = g.get("hex_row") or g.get("y")

        if x is None or y is None:
            x = idx % num_cols
            y = idx // num_cols

        if 0 <= x < num_cols and 0 <= y < num_rows:
            risk_grid[y, x] = norm_risk
            grid_data[(x, y)] = {
                "grid_id": grid_id,
                "risk": norm_risk
            }

            # Calculate face color
            is_road = (x, y) in road_coords
            is_water = (x, y) in water_coords
            is_mountain = (x, y) in mountain_coords
            is_hill = (x, y) in hill_coords
            is_salt_marsh = (x, y) in salt_marsh_coords
            base_color = cmap(norm_risk)

            if show_features and is_water:
                water_color = (0.3, 0.6, 1.0, 1.0)
                facecolor = tuple(0.4 * water_color[i] + 0.6 * base_color[i] for i in range(3))
            elif show_features and is_mountain:
                mountain_color = (0.4, 0.4, 0.45, 1.0)
                facecolor = tuple(0.4 * mountain_color[i] + 0.6 * base_color[i] for i in range(3))
            elif show_features and is_hill:
                hill_color = (0.55, 0.55, 0.6, 1.0)
                facecolor = tuple(0.4 * hill_color[i] + 0.6 * base_color[i] for i in range(3))
            elif show_features and is_salt_marsh:
                salt_marsh_color = (0.76, 0.7, 0.5, 1.0)
                facecolor = tuple(0.4 * salt_marsh_color[i] + 0.6 * base_color[i] for i in range(3))
            elif show_features and is_road:
                road_color = (0.7, 0.55, 0.4, 1.0)
                facecolor = tuple(0.4 * road_color[i] + 0.6 * base_color[i] for i in range(3))
            else:
                facecolor = base_color[:3]

            face_colors[(x, y)] = facecolor

    # Calculate visualization parameters
    square_size = 1.0
    fig_size = calculate_figure_size(num_cols, num_rows, 'square')
    font_size = calculate_font_size(num_cols, num_rows)
    dpi = calculate_dpi(num_cols, num_rows)

    # Auto-disable labels for large grids
    actual_show_labels = should_show_labels(num_cols, num_rows, show_labels)
    if actual_show_labels != show_labels:
        print(f"  Auto-disabling labels for large grid ({num_cols}x{num_rows}={num_cols*num_rows} grids)")

    # Create visualization
    fig, ax = plt.subplots(figsize=fig_size, dpi=dpi)

    for y in range(num_rows):
        for x in range(num_cols):
            risk = risk_grid[y, x]
            if np.isnan(risk):
                continue

            facecolor = face_colors.get((x, y), cmap(risk)[:3])
            square_patch = Rectangle(
                (x * square_size - square_size/2, y * square_size - square_size/2),
                square_size,
                square_size,
                facecolor=facecolor,
                linewidth=0,
                antialiased=False
            )
            ax.add_patch(square_patch)

    # Add labels (risk values and/or coordinates)
    if actual_show_labels or show_coordinates:
        for (x, y), data in grid_data.items():
            risk = data["risk"]
            facecolor = face_colors.get((x, y), (0.5, 0.5, 0.5))
            text_color = get_contrast_color(facecolor)

            center_x = x * square_size
            center_y = y * square_size

            if actual_show_labels and show_coordinates:
                # Show both: risk above coordinates
                ax.text(
                    center_x,
                    center_y + 0.15,
                    f"{risk:.2f}",
                    ha='center',
                    va='bottom',
                    color=text_color,
                    fontsize=font_size * 0.9,
                    fontweight='bold'
                )
                ax.text(
                    center_x,
                    center_y - 0.15,
                    f"({x},{y})",
                    ha='center',
                    va='top',
                    color=text_color,
                    fontsize=font_size * 0.8
                )
            elif actual_show_labels:
                # Show only risk
                ax.text(
                    center_x,
                    center_y,
                    f"{risk:.2f}",
                    ha='center',
                    va='center',
                    color=text_color,
                    fontsize=font_size,
                    fontweight='bold'
                )
            elif show_coordinates:
                # Show only coordinates
                ax.text(
                    center_x,
                    center_y,
                    f"({x},{y})",
                    ha='center',
                    va='center',
                    color=text_color,
                    fontsize=font_size,
                    fontweight='bold'
                )

    # Add species markers on top
    marker_size = square_size * 0.4
    if show_features:
        # Rhino - triangle up
        for (x, y) in rhino_locations:
            center_x = x * square_size
            center_y = y * square_size
            ax.scatter(center_x, center_y, marker='^', color='#8B4513', s=marker_size*30, zorder=10, linewidth=0.5, edgecolor='black')
        # Elephant - square
        for (x, y) in elephant_locations:
            center_x = x * square_size
            center_y = y * square_size
            ax.scatter(center_x, center_y, marker='s', color='#696969', s=marker_size*30, zorder=10, linewidth=0.5, edgecolor='black')
        # Bird - circle
        for (x, y) in bird_locations:
            center_x = x * square_size
            center_y = y * square_size
            ax.scatter(center_x, center_y, marker='o', color='#1E90FF', s=marker_size*20, zorder=10, linewidth=0.5, edgecolor='black')

    # Add colorbar
    from matplotlib.cm import ScalarMappable
    from matplotlib.lines import Line2D
    sm = ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=1))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Normalized Risk', rotation=270, labelpad=20, fontsize=12)

    # Add legend for features
    if show_features and (road_coords or water_coords or mountain_coords or hill_coords or salt_marsh_coords or rhino_locations or elephant_locations or bird_locations):
        legend_elements = []
        if road_coords:
            legend_elements.append(Patch(facecolor=[0.7, 0.55, 0.4], edgecolor='black', label='Road'))
        if water_coords:
            legend_elements.append(Patch(facecolor=[0.3, 0.6, 1.0], edgecolor='black', label='Water'))
        if mountain_coords:
            legend_elements.append(Patch(facecolor=[0.4, 0.4, 0.45], edgecolor='black', label='Mountain'))
        if hill_coords:
            legend_elements.append(Patch(facecolor=[0.55, 0.55, 0.6], edgecolor='black', label='Hill'))
        if salt_marsh_coords:
            legend_elements.append(Patch(facecolor=[0.76, 0.7, 0.5], edgecolor='black', label='Salt Marsh'))
        if rhino_locations:
            legend_elements.append(Line2D([0], [0], marker='^', color='w', markerfacecolor='#8B4513', markeredgecolor='black', markersize=10, label='Rhino'))
        if elephant_locations:
            legend_elements.append(Line2D([0], [0], marker='s', color='w', markerfacecolor='#696969', markeredgecolor='black', markersize=10, label='Elephant'))
        if bird_locations:
            legend_elements.append(Line2D([0], [0], marker='o', color='w', markerfacecolor='#1E90FF', markeredgecolor='black', markersize=8, label='Bird'))
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper right', fontsize=10)

    # Set limits and aspect
    ax.set_aspect('equal')
    ax.set_xlim(-0.5, num_cols * square_size - 0.5)
    ax.set_ylim(-0.5, num_rows * square_size - 0.5)

    ax.set_title(f"Risk Heatmap (Square Grid)\n{num_cols} cols × {num_rows} rows, {len(results)} grids", fontsize=16, pad=20)
    ax.set_xlabel("X (Column)", fontsize=12)
    ax.set_ylabel("Y (Row)", fontsize=12)
    ax.grid(alpha=0.2, linestyle='--')

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
    print(f"Risk heatmap saved to: {output_path}")
    plt.close(fig)


def visualize_risk_heatmap_hex(
    results_data: Dict[str, Any],
    input_data: Optional[Dict[str, Any]] = None,
    output_path: str = "risk_heatmap_from_json.jpg",
    show_labels: bool = True,
    show_coordinates: bool = False,
    show_features: bool = False
):
    """
    Visualize risk heatmap with hexagon grid (even-q offset coordinates).

    Args:
        results_data: Output from risk_model_wrapper.py
        input_data: Optional input data with road/water locations
        output_path: Output image path
        show_labels: Whether to show risk value labels
        show_coordinates: Whether to show (x,y) coordinate labels
        show_features: Whether to overlay road/water features
    """
    results = results_data.get("results", [])

    if not results:
        print("No results found in JSON file!")
        return

    # Try to determine grid size
    num_cols = None
    num_rows = None
    road_coords = set()
    water_coords = set()
    mountain_coords = set()
    hill_coords = set()
    salt_marsh_coords = set()

    # Collect species locations
    rhino_locations = []
    elephant_locations = []
    bird_locations = []

    if input_data:
        map_config = input_data.get("map_config", {})
        num_cols = map_config.get("num_cols") or map_config.get("map_width")
        num_rows = map_config.get("num_rows") or map_config.get("map_height")

        if show_features:
            road_locations = map_config.get("road_locations", [])
            water_locations = map_config.get("water_locations", [])
            mountain_locations = map_config.get("mountain_locations", [])
            hill_locations = map_config.get("hill_locations", [])
            salt_marsh_locations = map_config.get("salt_marsh_locations", [])
            road_coords = set((loc[0], loc[1]) for loc in road_locations)
            water_coords = set((loc[0], loc[1]) for loc in water_locations)
            mountain_coords = set((loc[0], loc[1]) for loc in mountain_locations)
            hill_coords = set((loc[0], loc[1]) for loc in hill_locations)
            salt_marsh_coords = set((loc[0], loc[1]) for loc in salt_marsh_locations)

        # Collect species locations from original grids
        original_grids = input_data.get("original_grids", [])
        if not original_grids:
            # Try to get from grids if original_grids not available
            original_grids = input_data.get("grids", [])

        for grid in original_grids:
            x = grid.get("hex_col") or grid.get("x", 0)
            y = grid.get("hex_row") or grid.get("y", 0)
            species_densities = grid.get("species_densities", {})

            # Threshold for showing species (only show high density)
            rhino_density = species_densities.get("rhino", 0)
            elephant_density = species_densities.get("elephant", 0)
            bird_density = species_densities.get("bird", 0)

            if rhino_density > 0.5:
                rhino_locations.append((x, y))
            if elephant_density > 0.5:
                elephant_locations.append((x, y))
            if bird_density > 0.5:
                bird_locations.append((x, y))

    # If grid size not found, try to infer from data coordinates
    if num_cols is None or num_rows is None:
        xs = []
        ys = []
        for result in results:
            x = result.get("x")
            y = result.get("y")
            if x is not None:
                xs.append(x)
            if y is not None:
                ys.append(y)

        if xs and ys:
            num_cols = max(xs) + 1
            num_rows = max(ys) + 1
            print(f"Inferred grid size from coordinates: {num_cols} cols × {num_rows} rows")
        else:
            n = len(results)
            num_cols = int(np.ceil(np.sqrt(n * 1.5)))
            num_rows = int(np.ceil(n / num_cols))
            print(f"Warning: Grid size not specified. Using {num_cols} cols × {num_rows} rows.")

    # Store grid data and face colors
    grid_data = {}
    face_colors = {}
    hex_size = 1.0

    # Custom colormap
    colors = [
        (0.0, '#00aa00'),   # Green - low risk
        (0.3, '#88cc00'),
        (0.5, '#ffff00'),   # Yellow - medium risk
        (0.7, '#ff8800'),
        (1.0, '#ff0000')    # Red - high risk
    ]
    cmap = LinearSegmentedColormap.from_list('risk_gradient', colors)

    # First pass: collect all data and calculate face colors
    for idx, result in enumerate(results):
        grid_id = result.get("grid_id", f"G{idx:04d}")
        norm_risk = result.get("normalized_risk", 0.0)

        # Try to find coordinates (using x, y as col, row)
        x, y = None, None
        x = result.get("x")
        y = result.get("y")

        if (x is None or y is None) and input_data:
            grids = input_data.get("grids", [])
            if idx < len(grids):
                g = grids[idx]
                x = g.get("hex_col") or g.get("x")
                y = g.get("hex_row") or g.get("y")

        if x is None or y is None:
            x = idx % num_cols
            y = idx // num_cols

        if 0 <= x < num_cols and 0 <= y < num_rows:
            grid_data[(x, y)] = {
                "grid_id": grid_id,
                "risk": norm_risk
            }

            # Calculate face color
            is_road = (x, y) in road_coords
            is_water = (x, y) in water_coords
            is_mountain = (x, y) in mountain_coords
            is_hill = (x, y) in hill_coords
            is_salt_marsh = (x, y) in salt_marsh_coords
            base_color = cmap(norm_risk)

            if show_features and is_water:
                water_color = (0.3, 0.6, 1.0, 1.0)
                facecolor = tuple(0.4 * water_color[i] + 0.6 * base_color[i] for i in range(3))
            elif show_features and is_mountain:
                mountain_color = (0.4, 0.4, 0.45, 1.0)
                facecolor = tuple(0.4 * mountain_color[i] + 0.6 * base_color[i] for i in range(3))
            elif show_features and is_hill:
                hill_color = (0.55, 0.55, 0.6, 1.0)
                facecolor = tuple(0.4 * hill_color[i] + 0.6 * base_color[i] for i in range(3))
            elif show_features and is_salt_marsh:
                salt_marsh_color = (0.76, 0.7, 0.5, 1.0)
                facecolor = tuple(0.4 * salt_marsh_color[i] + 0.6 * base_color[i] for i in range(3))
            elif show_features and is_road:
                road_color = (0.7, 0.55, 0.4, 1.0)
                facecolor = tuple(0.4 * road_color[i] + 0.6 * base_color[i] for i in range(3))
            else:
                facecolor = base_color[:3]

            face_colors[(x, y)] = facecolor

    # Calculate visualization parameters
    fig_size = calculate_figure_size(num_cols, num_rows, 'hex')
    font_size = calculate_font_size(num_cols, num_rows)
    dpi = calculate_dpi(num_cols, num_rows)

    # Auto-disable labels for large grids
    actual_show_labels = should_show_labels(num_cols, num_rows, show_labels)
    if actual_show_labels != show_labels:
        print(f"  Auto-disabling labels for large grid ({num_cols}x{num_rows}={num_cols*num_rows} grids)")

    # Create visualization
    fig, ax = plt.subplots(figsize=fig_size, dpi=dpi)

    for (x, y), data in grid_data.items():
        risk = data["risk"]
        facecolor = face_colors.get((x, y), cmap(risk)[:3])

        # Get pixel position
        px, py = hex_to_pixel_offset(x, y, hex_size)

        # Create hexagon patch (pointy-topped)
        # Use exact radius, add each patch individually to avoid PatchCollection issues
        hex_patch = RegularPolygon(
            (px, py),
            numVertices=6,
            radius=hex_size,
            orientation=math.pi/2,  # Pointy-topped with proper orientation
            facecolor=facecolor,
            linewidth=0,
            antialiased=False
        )
        ax.add_patch(hex_patch)

    # Add labels (risk values and/or coordinates)
    if actual_show_labels or show_coordinates:
        for (x, y), data in grid_data.items():
            risk = data["risk"]
            facecolor = face_colors.get((x, y), (0.5, 0.5, 0.5))
            text_color = get_contrast_color(facecolor)

            px, py = hex_to_pixel_offset(x, y, hex_size)
            hex_height = hex_size * math.sqrt(3)

            if actual_show_labels and show_coordinates:
                # Show both: risk above coordinates
                ax.text(
                    px,
                    py + hex_height * 0.15,
                    f"{risk:.2f}",
                    ha='center',
                    va='bottom',
                    color=text_color,
                    fontsize=font_size * 0.9,
                    fontweight='bold'
                )
                ax.text(
                    px,
                    py - hex_height * 0.15,
                    f"({x},{y})",
                    ha='center',
                    va='top',
                    color=text_color,
                    fontsize=font_size * 0.8
                )
            elif actual_show_labels:
                # Show only risk
                ax.text(
                    px,
                    py,
                    f"{risk:.2f}",
                    ha='center',
                    va='center',
                    color=text_color,
                    fontsize=font_size,
                    fontweight='bold'
                )
            elif show_coordinates:
                # Show only coordinates
                ax.text(
                    px,
                    py,
                    f"({x},{y})",
                    ha='center',
                    va='center',
                    color=text_color,
                    fontsize=font_size,
                    fontweight='bold'
                )

    # Add species markers on top
    marker_size = hex_size * 0.4
    if show_features:
        # Rhino - triangle up
        for (x, y) in rhino_locations:
            px, py = hex_to_pixel_offset(x, y, hex_size)
            ax.scatter(px, py, marker='^', color='#8B4513', s=marker_size*30, zorder=10, linewidth=0.5, edgecolor='black')
        # Elephant - square
        for (x, y) in elephant_locations:
            px, py = hex_to_pixel_offset(x, y, hex_size)
            ax.scatter(px, py, marker='s', color='#696969', s=marker_size*30, zorder=10, linewidth=0.5, edgecolor='black')
        # Bird - circle
        for (x, y) in bird_locations:
            px, py = hex_to_pixel_offset(x, y, hex_size)
            ax.scatter(px, py, marker='o', color='#1E90FF', s=marker_size*20, zorder=10, linewidth=0.5, edgecolor='black')

    # Add colorbar
    from matplotlib.cm import ScalarMappable
    from matplotlib.lines import Line2D
    sm = ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=1))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Normalized Risk', rotation=270, labelpad=20, fontsize=12)

    # Add legend for features
    if show_features and (road_coords or water_coords or mountain_coords or hill_coords or salt_marsh_coords or rhino_locations or elephant_locations or bird_locations):
        legend_elements = []
        if road_coords:
            legend_elements.append(Patch(facecolor=[0.7, 0.55, 0.4], edgecolor='black', label='Road'))
        if water_coords:
            legend_elements.append(Patch(facecolor=[0.3, 0.6, 1.0], edgecolor='black', label='Water'))
        if mountain_coords:
            legend_elements.append(Patch(facecolor=[0.4, 0.4, 0.45], edgecolor='black', label='Mountain'))
        if hill_coords:
            legend_elements.append(Patch(facecolor=[0.55, 0.55, 0.6], edgecolor='black', label='Hill'))
        if salt_marsh_coords:
            legend_elements.append(Patch(facecolor=[0.76, 0.7, 0.5], edgecolor='black', label='Salt Marsh'))
        if rhino_locations:
            legend_elements.append(Line2D([0], [0], marker='^', color='w', markerfacecolor='#8B4513', markeredgecolor='black', markersize=10, label='Rhino'))
        if elephant_locations:
            legend_elements.append(Line2D([0], [0], marker='s', color='w', markerfacecolor='#696969', markeredgecolor='black', markersize=10, label='Elephant'))
        if bird_locations:
            legend_elements.append(Line2D([0], [0], marker='o', color='w', markerfacecolor='#1E90FF', markeredgecolor='black', markersize=8, label='Bird'))
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper right', fontsize=10)

    # Set limits and aspect
    ax.set_aspect('equal')
    x_min, x_max, y_min, y_max = get_hex_grid_bounds(num_cols, num_rows, hex_size)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    ax.set_title(f"Risk Heatmap (Hexagon Grid)\n{num_cols} cols × {num_rows} rows, {len(results)} grids", fontsize=16, pad=20)
    ax.set_xlabel("X (Column)", fontsize=12)
    ax.set_ylabel("Y (Row)", fontsize=12)
    ax.grid(alpha=0.2, linestyle='--')

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
    print(f"Risk heatmap saved to: {output_path}")
    plt.close(fig)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Visualize Risk Heatmap from JSON - Generate risk heatmap from wrapper script output"
    )
    parser.add_argument(
        "--results", "-r",
        type=str,
        required=True,
        help="Path to risk results JSON file (from risk_model_wrapper.py)"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=None,
        help="Optional path to input data JSON (for road/water overlay)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="risk_heatmap_from_json.jpg",
        help="Output heatmap image path (default: risk_heatmap_from_json.jpg)"
    )
    parser.add_argument(
        "--grid-type", "-g",
        type=str,
        choices=["square", "hex"],
        default="square",
        help="Grid type: 'square' (default) or 'hex' for hexagon grid"
    )
    parser.add_argument(
        "--show-labels",
        action="store_true",
        default=True,
        help="Show risk value labels on heatmap (default: True)"
    )
    parser.add_argument(
        "--no-labels",
        action="store_true",
        help="Hide risk value labels on heatmap"
    )
    parser.add_argument(
        "--show-features",
        action="store_true",
        help="Show road/water feature overlays"
    )
    parser.add_argument(
        "--no-features",
        action="store_true",
        help="Hide road/water feature overlays (default)"
    )
    parser.add_argument(
        "--show-coordinates",
        action="store_true",
        help="Show (x,y) coordinate labels on heatmap"
    )
    parser.add_argument(
        "--no-coordinates",
        action="store_true",
        help="Hide (x,y) coordinate labels on heatmap (default)"
    )

    args = parser.parse_args()

    # Determine final flag values
    show_labels = args.show_labels and not args.no_labels
    # Default: no features unless --show-features is specified
    show_features = args.show_features
    # Default: no coordinates unless --show-coordinates is specified
    show_coordinates = args.show_coordinates

    print("="*70)
    print("  RISK HEATMAP VISUALIZER")
    print("="*70)

    # Load results
    print(f"\n[1/3] Loading risk results from: {args.results}")
    results_data = load_results_from_json(args.results)
    print(f"  Loaded {len(results_data.get('results', []))} grid results")

    # Load input data if provided
    input_data = None
    if args.input:
        print(f"\n[2/3] Loading input data from: {args.input}")
        input_data = load_results_from_json(args.input)
        print("  Input data loaded")
    else:
        print("\n[2/3] No input data provided (no road/water overlay)")

    # Generate heatmap
    print(f"\n[3/3] Generating heatmap to: {args.output}")
    print(f"  Settings: grid-type={args.grid_type}, labels={'ON' if show_labels else 'OFF'}, coordinates={'ON' if show_coordinates else 'OFF'}, features={'ON' if show_features else 'OFF'}")

    if args.grid_type == 'hex':
        visualize_risk_heatmap_hex(
            results_data,
            input_data=input_data,
            output_path=args.output,
            show_labels=show_labels,
            show_coordinates=show_coordinates,
            show_features=show_features
        )
    else:
        visualize_risk_heatmap_square(
            results_data,
            input_data=input_data,
            output_path=args.output,
            show_labels=show_labels,
            show_coordinates=show_coordinates,
            show_features=show_features
        )

    print("\n" + "="*70)
    print("  COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
