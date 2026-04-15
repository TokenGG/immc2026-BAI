#!/usr/bin/env python3
"""
Generate a square grid map with curved roads and water features.
Supports feature configuration via JSON config file.
"""

import sys
import os
import json
import random
import math
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple, Set

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from matplotlib.collections import PatchCollection


@dataclass
class SquareCoord:
    """Coordinates for square grid."""
    x: int  # column
    y: int  # row

    def to_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)

    def __eq__(self, other):
        return isinstance(other, SquareCoord) and self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))


def load_config(config_path: str) -> Dict[str, Any]:
    """Load feature configuration from JSON file."""
    default_config = {
        "features": {
            "ponds": 1,
            "large_water": 0,
            "forest": 1,
            "shrub": 1,
            "grassland": 1,
            "rhino": 1,
            "elephant": 1,
            "bird": 1,
            "roads": 1,
            "mountain": 0,
            "hills": 0,
            "salt_marsh": 0
        },
        "vegetation_distribution": {
            "grassland_ratio": 0.35,
            "forest_ratio": 0.40,
            "shrub_ratio": 0.25
        },
        "water_config": {
            "pond_count": 3,
            "pond_min_radius": 2.0,
            "pond_max_radius": 4.0,
            "large_water_radius": 8.0,
            "has_river": 1
        },
        "road_config": {
            "main_road_count": 3,
            "curvature": 0.35,
            "branch_probability": 0.12
        },
        "terrain_config": {
            "mountain_count": 2,
            "mountain_radius": 4.0,
            "hill_count": 5,
            "hill_radius": 2.5
        },
        "salt_marsh_config": {
            "salt_marsh_count": 1,
            "salt_marsh_radius": 3.0,
            "min_distance_from_water": 4.0
        }
    }

    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            # Merge user config with defaults
            for key in default_config:
                if key in user_config:
                    default_config[key].update(user_config[key])
            print(f"Loaded configuration from: {config_path}")
        except Exception as e:
            print(f"Warning: Could not load config file {config_path}: {e}")
            print("Using default configuration.")

    return default_config


def is_feature_enabled(config: Dict[str, Any], feature_name: str) -> bool:
    """Check if a feature is enabled in the config."""
    return config.get("features", {}).get(feature_name, 0) == 1


def square_to_pixel(coord: SquareCoord, size: float = 1.0) -> Tuple[float, float]:
    """Convert square grid coordinates to pixel coordinates."""
    return (coord.x * size, coord.y * size)


def generate_square_grid(num_cols: int = 20, num_rows: int = 15) -> List[SquareCoord]:
    """Generate a square grid."""
    squares = []
    for y in range(num_rows):
        for x in range(num_cols):
            squares.append(SquareCoord(x=x, y=y))
    return squares


def get_square_neighbors(coord: SquareCoord, num_cols: int, num_rows: int) -> List[SquareCoord]:
    """Get 8 neighbors of a square (including diagonals)."""
    x, y = coord.x, coord.y
    neighbors = []

    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < num_cols and 0 <= ny < num_rows:
                neighbors.append(SquareCoord(x=nx, y=ny))

    return neighbors


def get_square_neighbors_4way(coord: SquareCoord, num_cols: int, num_rows: int) -> List[SquareCoord]:
    """Get 4 neighbors of a square (up/down/left/right only)."""
    x, y = coord.x, coord.y
    neighbors = []

    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # up, right, down, left

    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < num_cols and 0 <= ny < num_rows:
            neighbors.append(SquareCoord(x=nx, y=ny))

    return neighbors


def square_distance(a: SquareCoord, b: SquareCoord) -> float:
    """Calculate Euclidean distance between two squares."""
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


def generate_curved_road_square(
    start_coord: SquareCoord,
    num_cols: int,
    num_rows: int,
    length: int,
    curvature: float = 0.3,
    branch_prob: float = 0.15
) -> List[List[SquareCoord]]:
    """Generate a curved road on square grid."""
    roads = []
    main_road = [start_coord]
    current = start_coord

    # Directions: 0=up, 1=right, 2=down, 3=left
    current_dir = 1  # Start going right

    for _ in range(length):
        # Get 4-way neighbors
        neighbors = get_square_neighbors_4way(current, num_cols, num_rows)

        if not neighbors:
            break

        # Randomly change direction with some probability
        if random.random() < curvature and len(main_road) > 2:
            prev_coord = main_road[-2] if len(main_road) >= 2 else None
            possible_next = [n for n in neighbors if n != prev_coord]
            if possible_next:
                next_coord = random.choice(possible_next)
            else:
                next_coord = random.choice(neighbors)
        else:
            # Continue in similar direction
            prev_coord = main_road[-2] if len(main_road) >= 2 else None
            possible_next = [n for n in neighbors if n != prev_coord]

            if possible_next and random.random() < 0.7:
                # Prefer direction that continues general trend
                if len(main_road) >= 3:
                    dx_trend = current.x - main_road[-3].x
                    dy_trend = current.y - main_road[-3].y

                    best = None
                    best_score = -float('inf')
                    for n in possible_next:
                        dx = n.x - current.x
                        dy = n.y - current.y
                        score = dx * dx_trend + dy * dy_trend
                        if score > best_score:
                            best_score = score
                            best = n
                    if best:
                        next_coord = best
                    else:
                        next_coord = random.choice(possible_next)
                else:
                    next_coord = random.choice(possible_next)
            elif possible_next:
                next_coord = random.choice(possible_next)
            else:
                next_coord = random.choice(neighbors)

        main_road.append(next_coord)
        current = next_coord

    roads.append(main_road)

    # Generate branches
    for i in range(3, len(main_road) - 3):
        if random.random() < branch_prob:
            branch_point = main_road[i]
            neighbors = get_square_neighbors_4way(branch_point, num_cols, num_rows)

            main_road_set = set(main_road)
            possible_starts = [n for n in neighbors if n not in main_road_set]

            if possible_starts:
                branch_start = random.choice(possible_starts)
                branch_length = random.randint(4, 10)
                branch_road = [branch_point, branch_start]
                current_branch = branch_start

                for _ in range(branch_length):
                    branch_neighbors = get_square_neighbors_4way(current_branch, num_cols, num_rows)
                    branch_road_set = set(branch_road)
                    possible_next = [n for n in branch_neighbors if n not in branch_road_set]

                    if possible_next:
                        # Avoid going back to main road too quickly
                        not_main = [n for n in possible_next if n not in main_road_set]
                        if not_main and random.random() < 0.8:
                            next_branch = random.choice(not_main)
                        else:
                            next_branch = random.choice(possible_next)

                        branch_road.append(next_branch)
                        current_branch = next_branch
                    else:
                        break

                roads.append(branch_road)

    return roads


def generate_square_map_data(
    num_cols: int = 30,
    num_rows: int = 20,
    output_json: str = "square_map_data.json",
    config: Optional[Dict[str, Any]] = None
):
    """Generate square grid map data with feature configuration."""
    if config is None:
        config = load_config(None)

    print(f"Generating square grid: {num_cols} cols × {num_rows} rows...")
    coords = generate_square_grid(num_cols, num_rows)
    coord_set = set(coords)
    print(f"  Total squares: {len(coords)}")

    # Generate roads if enabled
    all_road_coords = set()
    if is_feature_enabled(config, "roads"):
        print("Generating curved roads...")
        road_paths = []
        road_config = config.get("road_config", {})
        num_roads = road_config.get("main_road_count", 3)
        curvature = road_config.get("curvature", 0.35)
        branch_prob = road_config.get("branch_probability", 0.12)

        # Start positions for roads
        start_positions = [
            SquareCoord(x=0, y=num_rows // 2),
            SquareCoord(x=2, y=2),
            SquareCoord(x=num_cols // 2, y=0),
            SquareCoord(x=num_cols - 1, y=num_rows // 2),
            SquareCoord(x=num_cols // 2, y=num_rows - 1),
        ]

        for i in range(min(num_roads, len(start_positions))):
            start = start_positions[i]
            roads = generate_curved_road_square(
                start, num_cols, num_rows,
                length=max(num_cols, num_rows) * 2,
                curvature=curvature,
                branch_prob=branch_prob
            )
            for road in roads:
                road_paths.append(road)
                for c in road:
                    if c in coord_set:
                        all_road_coords.add(c)

        print(f"  Road squares: {len(all_road_coords)}")

    # Pre-assign vegetation types to avoid ponds overlapping with forest/shrub
    veg_dist = config.get("vegetation_distribution", {})
    grassland_ratio = veg_dist.get("grassland_ratio", 0.35)
    forest_ratio = veg_dist.get("forest_ratio", 0.40)
    shrub_ratio = veg_dist.get("shrub_ratio", 0.25)

    # Normalize ratios
    total_ratio = grassland_ratio + forest_ratio + shrub_ratio
    if total_ratio > 0:
        grassland_ratio /= total_ratio
        forest_ratio /= total_ratio
        shrub_ratio /= total_ratio

    # Pre-assign vegetation for each coord
    pre_veg_type = {}
    for coord in coords:
        # Vegetation type - check which types are enabled
        enabled_veg_types = []
        veg_cumulative = []

        if is_feature_enabled(config, "grassland"):
            enabled_veg_types.append("GRASSLAND")
            veg_cumulative.append(grassland_ratio)
        if is_feature_enabled(config, "forest"):
            enabled_veg_types.append("FOREST")
            veg_cumulative.append(grassland_ratio + forest_ratio)
        if is_feature_enabled(config, "shrub"):
            enabled_veg_types.append("SHRUB")
            veg_cumulative.append(1.0)

        if not enabled_veg_types:
            vegetation_type = "GRASSLAND"
        else:
            veg_random = random.random()
            vegetation_type = enabled_veg_types[0]
            for i, cum_prob in enumerate(veg_cumulative):
                if veg_random <= cum_prob:
                    vegetation_type = enabled_veg_types[i]
                    break
        pre_veg_type[coord] = vegetation_type

    # Generate water sources if enabled
    all_water_coords = set()
    water_config = config.get("water_config", {})

    if is_feature_enabled(config, "ponds") or is_feature_enabled(config, "large_water"):
        print("Generating water sources...")

        # Generate ponds
        if is_feature_enabled(config, "ponds"):
            pond_count = water_config.get("pond_count", 3)
            pond_min_r = water_config.get("pond_min_radius", 2.0)
            pond_max_r = water_config.get("pond_max_radius", 4.0)

            for i in range(pond_count):
                # Try to find a valid pond center (not overlapping forest/shrub)
                pond_center = None
                pond_radius = random.uniform(pond_min_r, pond_max_r)
                attempts = 0
                max_attempts = 100

                # Distribute ponds across the map - try candidate positions first
                if pond_count == 1:
                    candidate_positions = [(num_cols // 2, num_rows // 2)]
                elif pond_count == 2:
                    candidate_positions = [(num_cols // 4, num_rows // 3), (num_cols * 3 // 4, num_rows * 2 // 3)]
                else:
                    candidate_positions = [
                        (num_cols // 4, num_rows // 3),
                        (num_cols * 3 // 4, num_rows * 2 // 3),
                        (num_cols // 2, num_rows // 2),
                        (num_cols // 5, num_rows * 3 // 4),
                        (num_cols * 4 // 5, num_rows // 4),
                    ]

                # Try candidate positions first
                for cx, cy in candidate_positions:
                    if pond_center is not None:
                        break
                    test_center = SquareCoord(x=cx, y=cy)

                    # Check if pond would overlap with forest or shrub
                    overlaps_forest_shrub = False
                    for c in coords:
                        if square_distance(c, test_center) <= pond_radius:
                            veg = pre_veg_type.get(c, "GRASSLAND")
                            if veg == "FOREST" or veg == "SHRUB":
                                overlaps_forest_shrub = True
                                break

                    if not overlaps_forest_shrub:
                        pond_center = test_center

                # If no candidate worked, try random positions
                while pond_center is None and attempts < max_attempts:
                    cx = random.randint(int(num_cols * 0.15), int(num_cols * 0.85))
                    cy = random.randint(int(num_rows * 0.15), int(num_rows * 0.85))
                    test_center = SquareCoord(x=cx, y=cy)

                    # Check if pond would overlap with forest or shrub
                    overlaps_forest_shrub = False
                    for c in coords:
                        if square_distance(c, test_center) <= pond_radius:
                            veg = pre_veg_type.get(c, "GRASSLAND")
                            if veg == "FOREST" or veg == "SHRUB":
                                overlaps_forest_shrub = True
                                break

                    if not overlaps_forest_shrub:
                        pond_center = test_center
                    attempts += 1

                # If no valid position found, use last attempt anyway (fallback)
                if pond_center is None:
                    cx, cy = num_cols // 2, num_rows // 2
                    pond_center = SquareCoord(x=cx, y=cy)

                # Add pond coords
                if pond_radius <= 0.5:
                    all_water_coords.add(pond_center)
                else:
                    for c in coords:
                        if square_distance(c, pond_center) <= pond_radius:
                            all_water_coords.add(c)

        # Generate large water body
        if is_feature_enabled(config, "large_water"):
            large_radius = water_config.get("large_water_radius", 8.0)
            large_center = SquareCoord(x=num_cols // 2, y=num_rows // 2)
            for c in coords:
                if square_distance(c, large_center) <= large_radius:
                    all_water_coords.add(c)

        # Generate river
        if water_config.get("has_river", 1) == 1:
            river_coords = []
            river_current = SquareCoord(x=num_cols - 1, y=num_rows - 2)
            river_coords.append(river_current)
            all_water_coords.add(river_current)

            for _ in range(num_cols * 2):
                neighbors = get_square_neighbors_4way(river_current, num_cols, num_rows)
                river_so_far = set(river_coords)

                # Prefer left-moving neighbors
                leftish = [n for n in neighbors if n.x < river_current.x and n not in river_so_far]
                other = [n for n in neighbors if n not in river_so_far and n not in leftish]

                if leftish and random.random() < 0.7:
                    next_river = random.choice(leftish)
                elif other:
                    next_river = random.choice(other)
                else:
                    break

                river_coords.append(next_river)
                all_water_coords.add(next_river)
                river_current = next_river

        print(f"  Water squares: {len(all_water_coords)}")

    # Generate terrain features (mountains and hills)
    all_mountain_coords = set()
    all_hill_coords = set()
    terrain_config = config.get("terrain_config", {})

    if is_feature_enabled(config, "mountain"):
        print("Generating mountains...")
        mountain_count = terrain_config.get("mountain_count", 2)
        mountain_radius = terrain_config.get("mountain_radius", 4.0)

        for i in range(mountain_count):
            if mountain_count == 1:
                cx, cy = num_cols // 2, num_rows // 2
            else:
                positions = [
                    (num_cols // 3, num_rows * 2 // 3),
                    (num_cols * 2 // 3, num_rows // 3),
                ]
                cx, cy = positions[i % len(positions)]

            mountain_center = SquareCoord(x=cx, y=cy)
            for c in coords:
                if square_distance(c, mountain_center) <= mountain_radius:
                    all_mountain_coords.add(c)

        print(f"  Mountain squares: {len(all_mountain_coords)}")

    if is_feature_enabled(config, "hills"):
        print("Generating hills...")
        hill_count = terrain_config.get("hill_count", 5)
        hill_radius = terrain_config.get("hill_radius", 2.5)

        for i in range(hill_count):
            # Random hill positions, avoid mountains
            attempts = 0
            while attempts < 50:
                cx = random.randint(int(num_cols * 0.1), int(num_cols * 0.9))
                cy = random.randint(int(num_rows * 0.1), int(num_rows * 0.9))
                hill_center = SquareCoord(x=cx, y=cy)

                # Check if too close to mountains
                too_close = False
                for m in all_mountain_coords:
                    if square_distance(hill_center, m) < mountain_radius + 2:
                        too_close = True
                        break

                if not too_close:
                    break
                attempts += 1

            for c in coords:
                if square_distance(c, hill_center) <= hill_radius:
                    all_hill_coords.add(c)

        print(f"  Hill squares: {len(all_hill_coords)}")

    # Generate salt marsh if enabled
    all_salt_marsh_coords = set()
    salt_marsh_centers = []
    if is_feature_enabled(config, "salt_marsh"):
        print("Generating salt marshes...")
        salt_marsh_config = config.get("salt_marsh_config", {})
        salt_marsh_count = salt_marsh_config.get("salt_marsh_count", 1)
        salt_marsh_radius = salt_marsh_config.get("salt_marsh_radius", 3.0)
        min_distance_from_water = salt_marsh_config.get("min_distance_from_water", 4.0)

        # Get forbidden area (water, roads, mountains, hills)
        forbidden_coords = set()
        forbidden_coords.update(all_water_coords)
        forbidden_coords.update(all_road_coords)
        forbidden_coords.update(all_mountain_coords)
        forbidden_coords.update(all_hill_coords)

        # Generate salt marsh positions
        for i in range(salt_marsh_count):
            # Try to find a valid center
            valid_center = None
            attempts = 0
            max_attempts = 100

            # Predefined positions to try first
            if salt_marsh_count == 1:
                candidate_positions = [
                    (num_cols // 4, num_rows // 4),
                    (num_cols * 3 // 4, num_rows // 4),
                    (num_cols // 4, num_rows * 3 // 4),
                    (num_cols * 3 // 4, num_rows * 3 // 4),
                ]
            elif salt_marsh_count == 2:
                candidate_positions = [
                    (num_cols // 4, num_rows // 4),
                    (num_cols * 3 // 4, num_rows * 3 // 4),
                ]
            else:
                candidate_positions = []

            # Try candidate positions first
            for cx, cy in candidate_positions:
                if valid_center is not None:
                    break
                test_center = SquareCoord(x=cx, y=cy)

                # Check distance to water
                far_from_water = True
                if all_water_coords:
                    for water_c in all_water_coords:
                        if square_distance(test_center, water_c) < min_distance_from_water:
                            far_from_water = False
                            break

                # Check not overlapping with forbidden features
                not_overlapping = True
                for c in coords:
                    if square_distance(c, test_center) <= salt_marsh_radius:
                        if c in forbidden_coords:
                            not_overlapping = False
                            break

                # Check distance from existing salt marshes
                far_from_other_marshes = True
                for existing_center in salt_marsh_centers:
                    if square_distance(test_center, existing_center) < salt_marsh_radius * 3:
                        far_from_other_marshes = False
                        break

                if far_from_water and not_overlapping and far_from_other_marshes:
                    valid_center = test_center
                    break

            # If no candidate worked, try random positions
            while valid_center is None and attempts < max_attempts:
                cx = random.randint(int(num_cols * 0.15), int(num_cols * 0.85))
                cy = random.randint(int(num_rows * 0.15), int(num_rows * 0.85))
                test_center = SquareCoord(x=cx, y=cy)

                # Check distance to water
                far_from_water = True
                if all_water_coords:
                    for water_c in all_water_coords:
                        if square_distance(test_center, water_c) < min_distance_from_water:
                            far_from_water = False
                            break

                if not far_from_water:
                    attempts += 1
                    continue

                # Check not overlapping with forbidden features
                not_overlapping = True
                for c in coords:
                    if square_distance(c, test_center) <= salt_marsh_radius:
                        if c in forbidden_coords:
                            not_overlapping = False
                            break

                if not not_overlapping:
                    attempts += 1
                    continue

                # Check distance from existing salt marshes
                far_from_other_marshes = True
                for existing_center in salt_marsh_centers:
                    if square_distance(test_center, existing_center) < salt_marsh_radius * 3:
                        far_from_other_marshes = False
                        break

                if far_from_water and not_overlapping and far_from_other_marshes:
                    valid_center = test_center
                attempts += 1

            if valid_center:
                salt_marsh_centers.append(valid_center)
                # Add all coords within radius
                for c in coords:
                    if square_distance(c, valid_center) <= salt_marsh_radius:
                        all_salt_marsh_coords.add(c)

        print(f"  Salt marsh squares: {len(all_salt_marsh_coords)}")

    # Pre-calculate distance to nearest salt marsh for each coord
    dist_to_salt_marsh = {}
    for coord in coords:
        min_dist = float('inf')
        if all_salt_marsh_coords:
            for sm_coord in all_salt_marsh_coords:
                dist = square_distance(coord, sm_coord)
                if dist < min_dist:
                    min_dist = dist
        dist_to_salt_marsh[coord] = min_dist

    # Generate grid data for each square
    print("Generating grid data...")
    grids = []

    for idx, coord in enumerate(coords):
        # Grid ID
        grid_id = f"S{idx:04d}"

        # Calculate distance to water if water exists
        dist_to_water = float('inf')
        if all_water_coords:
            for water_coord in all_water_coords:
                dist = square_distance(coord, water_coord)
                if dist < dist_to_water:
                    dist_to_water = dist

        # Fire risk: higher away from water, near top-right
        if dist_to_water == float('inf'):
            water_factor = 0.5
        else:
            water_factor = min(1.0, dist_to_water / 10.0)
        pos_factor = (coord.x / num_cols) * 0.5 + ((num_rows - coord.y) / num_rows) * 0.5
        fire_risk = 0.1 + 0.7 * water_factor * pos_factor + random.uniform(-0.1, 0.1)
        fire_risk = min(1.0, max(0.0, fire_risk))

        # Terrain complexity: more complex near center, increased by mountains/hills
        center_dist = square_distance(coord, SquareCoord(x=num_cols//2, y=num_rows//2))
        max_center_dist = math.sqrt((num_cols/2)**2 + (num_rows/2)**2)
        terrain_complexity = 0.2 + 0.6 * (1.0 - min(1.0, center_dist / max_center_dist))

        # Increase complexity for mountains and hills
        if coord in all_mountain_coords:
            terrain_complexity = 0.9 + random.uniform(-0.05, 0.05)
        elif coord in all_hill_coords:
            terrain_complexity = 0.7 + random.uniform(-0.1, 0.1)

        terrain_complexity = min(1.0, max(0.0, terrain_complexity + random.uniform(-0.1, 0.1)))

        # Vegetation type - use pre-assigned value
        # For salt marsh coords, set special vegetation type
        if coord in all_salt_marsh_coords:
            vegetation_type = "SALT_MARSH"
        elif coord in all_water_coords or coord in all_road_coords or coord in all_mountain_coords or coord in all_hill_coords:
            # For water/road/mountain/hill coords, use grassland as default
            vegetation_type = "GRASSLAND"
        else:
            # Use pre-assigned vegetation type
            vegetation_type = pre_veg_type.get(coord, "GRASSLAND")

        # Species densities: higher near water, affected by salt marsh
        if dist_to_water == float('inf'):
            water_attraction = 0.3
        else:
            water_attraction = max(0.0, 1.0 - dist_to_water / 8.0)

        # Get distance to salt marsh for this coord
        sm_dist = dist_to_salt_marsh[coord]

        species_densities = {}
        if is_feature_enabled(config, "rhino"):
            # Rhino constraints: only in grassland, water, or roads (land)
            # Not in forest, shrub, mountain, hill, or salt marsh
            is_rhino_habitat = False
            if (vegetation_type == "GRASSLAND" or
                coord in all_water_coords or
                coord in all_road_coords):
                # Not in forest, shrub, mountain, hill, or salt marsh
                if (vegetation_type != "FOREST" and
                    vegetation_type != "SHRUB" and
                    vegetation_type != "SALT_MARSH" and
                    coord not in all_mountain_coords and
                    coord not in all_hill_coords):
                    is_rhino_habitat = True

            if is_rhino_habitat:
                rhino_density = 0.05 + 0.85 * water_attraction * random.uniform(0.5, 1.0)
                # Apply salt marsh effect: exponential decay, 0 at salt marsh
                if all_salt_marsh_coords:
                    # Decay constant - controls how fast density recovers
                    decay_constant = 0.3
                    if sm_dist <= 0.5:  # On salt marsh
                        rhino_density = 0.0
                    else:
                        rhino_density *= math.exp(-decay_constant * max(sm_dist, 0.1))
                species_densities["rhino"] = min(1.0, max(0.0, rhino_density))
            else:
                species_densities["rhino"] = 0.0

        if is_feature_enabled(config, "elephant"):
            # Elephant constraints: in grassland, water, roads (land), and also in forest (probabilistic)
            # Not in shrub, mountain, hill, or salt marsh
            is_elephant_habitat = False
            elephant_probability_factor = 1.0

            if (vegetation_type == "GRASSLAND" or
                coord in all_water_coords or
                coord in all_road_coords):
                # Not in shrub, mountain, hill, or salt marsh
                if (vegetation_type != "SHRUB" and
                    vegetation_type != "SALT_MARSH" and
                    coord not in all_mountain_coords and
                    coord not in all_hill_coords):
                    is_elephant_habitat = True
            elif vegetation_type == "FOREST":
                # Forest is allowed but with reduced probability
                if (vegetation_type != "SALT_MARSH" and
                    coord not in all_mountain_coords and
                    coord not in all_hill_coords):
                    is_elephant_habitat = True
                    elephant_probability_factor = 0.4  # Lower density in forest

            if is_elephant_habitat:
                elephant_density = 0.1 + 0.75 * water_attraction * random.uniform(0.5, 1.0)
                elephant_density *= elephant_probability_factor
                # Apply salt marsh effect: exponential decay, 0 at salt marsh
                if all_salt_marsh_coords:
                    decay_constant = 0.3
                    if sm_dist <= 0.5:  # On salt marsh
                        elephant_density = 0.0
                    else:
                        elephant_density *= math.exp(-decay_constant * max(sm_dist, 0.1))
                species_densities["elephant"] = min(1.0, max(0.0, elephant_density))
            else:
                species_densities["elephant"] = 0.0
        if is_feature_enabled(config, "bird"):
            bird_density = 0.2 + 0.6 * random.uniform(0.5, 1.0)
            # Apply salt marsh effect: exponential increase near salt marsh
            if all_salt_marsh_coords:
                growth_constant = 0.4
                max_bonus = 1.8  # Maximum multiplier near salt marsh
                # As distance increases, multiplier decreases from max_bonus to 1.0
                bird_multiplier = 1.0 + (max_bonus - 1.0) * math.exp(-growth_constant * max(sm_dist, 0.1))
                bird_density *= bird_multiplier
            species_densities["bird"] = min(1.0, bird_density)

        grids.append({
            "grid_id": grid_id,
            "x": coord.x,
            "y": coord.y,
            "fire_risk": fire_risk,
            "terrain_complexity": terrain_complexity,
            "vegetation_type": vegetation_type,
            "species_densities": species_densities
        })

    # Create map_config
    road_locations = [[c.x, c.y] for c in all_road_coords]
    water_locations = [[c.x, c.y] for c in all_water_coords]
    mountain_locations = [[c.x, c.y] for c in all_mountain_coords]
    hill_locations = [[c.x, c.y] for c in all_hill_coords]
    salt_marsh_locations = [[c.x, c.y] for c in all_salt_marsh_coords]

    data = {
        "map_config": {
            "num_cols": num_cols,
            "num_rows": num_rows,
            "boundary_type": "SQUARE",
            "road_locations": road_locations,
            "water_locations": water_locations,
            "mountain_locations": mountain_locations,
            "hill_locations": hill_locations,
            "salt_marsh_locations": salt_marsh_locations
        },
        "square_coords": [[c.x, c.y] for c in coords],
        "grids": grids,
        "time": {
            "hour_of_day": 22,
            "season": "RAINY"
        }
    }

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f)

    print(f"Generated square map data saved to: {output_json}")
    print(f"  Grid size: {num_cols} cols × {num_rows} rows")
    print(f"  Total squares: {len(coords)}")
    print(f"  Road squares: {len(road_locations)}")
    print(f"  Water squares: {len(water_locations)}")
    print(f"  Mountain squares: {len(mountain_locations)}")
    print(f"  Hill squares: {len(hill_locations)}")
    print(f"  Salt marsh squares: {len(salt_marsh_locations)}")

    return data, coords, all_road_coords, all_water_coords, all_mountain_coords, all_hill_coords, all_salt_marsh_coords


def visualize_square_map(
    data: dict,
    coords: List[SquareCoord],
    road_coords: Set[SquareCoord],
    water_coords: Set[SquareCoord],
    mountain_coords: Set[SquareCoord],
    hill_coords: Set[SquareCoord],
    output_path: str = "square_map_features.jpg",
    show_coordinates: bool = False,
    salt_marsh_coords: Optional[Set[SquareCoord]] = None
):
    """Visualize square grid map features."""
    if salt_marsh_coords is None:
        salt_marsh_coords = set()

    square_size = 1.0
    num_cols = data["map_config"]["num_cols"]
    num_rows = data["map_config"]["num_rows"]

    # Create a lookup for grid data by coordinate
    grid_lookup = {}
    for grid in data["grids"]:
        grid_lookup[(grid["x"], grid["y"])] = grid

    fig, ax = plt.subplots(figsize=(16, 12), dpi=100)

    patches = []
    label_data = []

    # Track which features are present
    has_forest = False
    has_grassland = False
    has_shrub = False

    # Track species locations for markers
    rhino_locations = []
    elephant_locations = []
    bird_locations = []

    for coord in coords:
        x, y = square_to_pixel(coord, square_size)

        # Determine color based on priority: water > mountain > hill > road > salt marsh > vegetation
        if coord in water_coords:
            color = [0.3, 0.6, 1.0]  # Blue - water
        elif coord in mountain_coords:
            color = [0.4, 0.4, 0.45]  # Dark gray - mountain
        elif coord in hill_coords:
            color = [0.55, 0.55, 0.6]  # Medium gray - hill
        elif coord in road_coords:
            color = [0.7, 0.55, 0.4]  # Brown - road
        elif coord in salt_marsh_coords:
            color = [0.9, 0.85, 0.6]  # Light tan - salt marsh
        else:
            # Get vegetation type from grid data
            grid_data = grid_lookup.get((coord.x, coord.y))
            if grid_data:
                veg_type = grid_data.get("vegetation_type", "GRASSLAND")
                if veg_type == "FOREST":
                    color = [0.2, 0.6, 0.2]  # Dark green - forest
                    has_forest = True
                elif veg_type == "SHRUB":
                    color = [0.5, 0.7, 0.3]  # Light green - shrub
                    has_shrub = True
                elif veg_type == "SALT_MARSH":
                    color = [0.9, 0.85, 0.6]  # Light tan - salt marsh
                else:  # GRASSLAND
                    color = [0.7, 0.85, 0.5]  # Yellow-green - grassland
                    has_grassland = True
            else:
                color = [0.7, 0.85, 0.5]  # Default to grassland

        # Create square patch
        square_patch = Rectangle(
            (x - square_size/2, y - square_size/2),
            square_size,
            square_size,
            facecolor=color,
            edgecolor=[0.7, 0.7, 0.7],
            linewidth=0
        )
        patches.append(square_patch)
        label_data.append((x, y, coord.x, coord.y, color))

        # Check for species density and mark high density cells
        grid_data = grid_lookup.get((coord.x, coord.y))
        if grid_data:
            species_densities = grid_data.get("species_densities", {})
            # Only show species markers where density is high (> 0.5) and not on water/road
            if coord not in water_coords and coord not in road_coords:
                if species_densities.get("rhino", 0) > 0.5:
                    rhino_locations.append((x, y))
                if species_densities.get("elephant", 0) > 0.5:
                    elephant_locations.append((x, y))
                if species_densities.get("bird", 0) > 0.5:
                    bird_locations.append((x, y))

    # Add all patches
    collection = PatchCollection(patches, match_original=True)
    ax.add_collection(collection)

    # Add coordinate labels if enabled
    if show_coordinates:
        total_grids = num_cols * num_rows
        font_size = 10 if total_grids <= 400 else 8 if total_grids <= 1000 else 6
        for x, y, cx, cy, color in label_data:
            text_color = 'white' if sum(color) < 1.5 else 'black'
            ax.text(
                x, y,
                f"({cx},{cy})",
                ha='center', va='center',
                color=text_color,
                fontsize=font_size,
                fontweight='bold'
            )

    # Add species markers
    marker_size = 120
    marker_edge_width = 1.5
    if rhino_locations:
        rhino_x, rhino_y = zip(*rhino_locations)
        ax.scatter(rhino_x, rhino_y, s=marker_size, c='darkred', marker='D',
                   edgecolor='black', linewidth=marker_edge_width, zorder=10, label='Rhino')
    if elephant_locations:
        elephant_x, elephant_y = zip(*elephant_locations)
        ax.scatter(elephant_x, elephant_y, s=marker_size, c='orange', marker='s',
                   edgecolor='black', linewidth=marker_edge_width, zorder=10, label='Elephant')
    if bird_locations:
        bird_x, bird_y = zip(*bird_locations)
        ax.scatter(bird_x, bird_y, s=marker_size, c='deepskyblue', marker='o',
                   edgecolor='black', linewidth=marker_edge_width, zorder=10, label='Bird')

    # Add legend
    legend_elements = []
    if water_coords:
        legend_elements.append(Patch(facecolor=[0.3, 0.6, 1.0], edgecolor='black', label='Water'))
    if road_coords:
        legend_elements.append(Patch(facecolor=[0.7, 0.55, 0.4], edgecolor='black', label='Road'))
    if mountain_coords:
        legend_elements.append(Patch(facecolor=[0.4, 0.4, 0.45], edgecolor='black', label='Mountain'))
    if hill_coords:
        legend_elements.append(Patch(facecolor=[0.55, 0.55, 0.6], edgecolor='black', label='Hill'))
    if salt_marsh_coords:
        legend_elements.append(Patch(facecolor=[0.9, 0.85, 0.6], edgecolor='black', label='Salt Marsh'))
    if has_forest:
        legend_elements.append(Patch(facecolor=[0.2, 0.6, 0.2], edgecolor='black', label='Forest'))
    if has_shrub:
        legend_elements.append(Patch(facecolor=[0.5, 0.7, 0.3], edgecolor='black', label='Shrub'))
    if has_grassland:
        legend_elements.append(Patch(facecolor=[0.7, 0.85, 0.5], edgecolor='black', label='Grassland'))

    ax.legend(handles=legend_elements, loc='upper right', fontsize=12)

    # Set limits and aspect
    ax.set_aspect('equal')
    all_x, all_y = zip(*[square_to_pixel(c, square_size) for c in coords])
    ax.set_xlim(min(all_x) - 1, max(all_x) + 1)
    ax.set_ylim(min(all_y) - 1, max(all_y) + 1)

    ax.set_title(f"Square Grid\n{num_cols} cols × {num_rows} rows = {len(coords)} squares", fontsize=16, pad=20)
    ax.set_xlabel("X (Column)", fontsize=12)
    ax.set_ylabel("Y (Row)", fontsize=12)
    ax.grid(alpha=0.2, linestyle='--')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Square map features saved to: {output_path}")
    plt.close(fig)


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Square Grid Map Generator - Generate square grid maps with feature config"
    )
    parser.add_argument(
        "--cols", "-c",
        type=int,
        default=30,
        help="Number of columns in square grid (default: 30)"
    )
    parser.add_argument(
        "--rows", "-r",
        type=int,
        default=20,
        help="Number of rows in square grid (default: 20)"
    )
    parser.add_argument(
        "--data", "-d",
        type=str,
        default="square_map_data.json",
        help="Output JSON data file path (default: square_map_data.json)"
    )
    parser.add_argument(
        "--map-image", "-m",
        type=str,
        default="square_map_features.jpg",
        help="Output map features image path (default: square_map_features.jpg)"
    )
    parser.add_argument(
        "--config", "-f",
        type=str,
        default="map_feature_config.json",
        help="Feature configuration JSON file path (default: map_feature_config.json)"
    )
    parser.add_argument(
        "--show-coordinates",
        action="store_true",
        help="Show (x,y) coordinate labels on map"
    )
    parser.add_argument(
        "--no-coordinates",
        action="store_true",
        help="Hide (x,y) coordinate labels on map (default)"
    )

    args = parser.parse_args()

    # Determine final flag values
    show_coordinates = args.show_coordinates

    print("="*70)
    print("  SQUARE GRID MAP GENERATOR")
    print("="*70)

    # Load config
    config = load_config(args.config)

    # Generate data
    print(f"\n[1/2] Generating square grid data: {args.cols} cols × {args.rows} rows...")
    data, coords, road_coords, water_coords, mountain_coords, hill_coords, salt_marsh_coords = generate_square_map_data(
        num_cols=args.cols,
        num_rows=args.rows,
        output_json=args.data,
        config=config
    )

    # Visualize map features
    print(f"\n[2/2] Visualizing square map to: {args.map_image}")
    print(f"  Settings: coordinates={'ON' if show_coordinates else 'OFF'}")
    visualize_square_map(data, coords, road_coords, water_coords, mountain_coords, hill_coords, args.map_image, show_coordinates, salt_marsh_coords)

    # Print summary
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    print(f"  Grid size: {args.cols} cols × {args.rows} rows")
    print(f"  Total squares: {len(coords)}")
    print(f"  Road squares: {len(road_coords)}")
    print(f"  Water squares: {len(water_coords)}")
    print(f"  Mountain squares: {len(mountain_coords)}")
    print(f"  Hill squares: {len(hill_coords)}")
    print(f"  Salt marsh squares: {len(salt_marsh_coords)}")
    print("="*70)
    print("\nGenerated files:")
    print(f"  - {args.data} (square map data)")
    print(f"  - {args.map_image} (map visualization)")


if __name__ == "__main__":
    main()
