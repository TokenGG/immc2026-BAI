"""
Synthetic data generator for the risk model.
"""

import random
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

from ..core import (
    Grid,
    Species,
    SpeciesDensity,
    Season,
    Environment,
    VegetationType,
)


@dataclass
class GridLayoutConfig:
    """Configuration for grid layout generation."""
    grid_width: int = 10
    grid_height: int = 10
    area_width_km: float = 100.0
    area_height_km: float = 100.0


@dataclass
class ProtectedAreaLayout:
    """
    Layout of the protected area with key geographic features.
    """
    boundary_points: List[Tuple[float, float]]
    road_points: List[Tuple[float, float]]
    water_points: List[Tuple[float, float]]


class SyntheticDataGenerator:
    """
    Generates synthetic data for the risk model.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the data generator.

        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)

    def generate_grid_layout(
        self,
        config: Optional[GridLayoutConfig] = None
    ) -> List[Grid]:
        """
        Generate a grid layout for the protected area.

        Args:
            config: Grid layout configuration

        Returns:
            List of Grid objects
        """
        config = config or GridLayoutConfig()
        grids = []

        cell_width = config.area_width_km / config.grid_width
        cell_height = config.area_height_km / config.grid_height

        for row in range(config.grid_height):
            for col in range(config.grid_width):
                grid_id = f"{chr(65 + row)}{col:02d}"
                x = col * cell_width + cell_width / 2
                y = row * cell_height + cell_height / 2

                # Calculate distances (simplified)
                # Distance to boundary: distance to nearest edge
                dist_left = x / config.area_width_km
                dist_right = (config.area_width_km - x) / config.area_width_km
                dist_top = y / config.area_height_km
                dist_bottom = (config.area_height_km - y) / config.area_height_km
                dist_boundary = min(dist_left, dist_right, dist_top, dist_bottom)

                # Distance to road: random but higher near center
                dist_road = random.uniform(0.1, 0.9)
                if 0.3 < x / config.area_width_km < 0.7:
                    dist_road = random.uniform(0.05, 0.4)

                # Distance to water: random clusters
                dist_water = random.uniform(0.1, 0.9)
                water_centers = [(0.2, 0.3), (0.7, 0.6), (0.5, 0.8)]
                for cx, cy in water_centers:
                    dx = (x / config.area_width_km - cx) ** 2
                    dy = (y / config.area_height_km - cy) ** 2
                    if dx + dy < 0.05:
                        dist_water = random.uniform(0.05, 0.3)
                        break

                grids.append(Grid(
                    grid_id=grid_id,
                    x=x,
                    y=y,
                    distance_to_boundary=dist_boundary,
                    distance_to_road=dist_road,
                    distance_to_water=dist_water
                ))

        return grids

    def generate_environment(
        self,
        grid: Grid,
        grid_config: Optional[GridLayoutConfig] = None
    ) -> Environment:
        """
        Generate environmental data for a grid cell.

        Args:
            grid: Grid cell to generate environment for
            grid_config: Grid layout configuration

        Returns:
            Environment object
        """
        config = grid_config or GridLayoutConfig()

        # Fire risk higher in dry areas (edges) and forests
        x_norm = grid.x / config.area_width_km
        y_norm = grid.y / config.area_height_km
        edge_factor = min(x_norm, 1 - x_norm, y_norm, 1 - y_norm)

        # Vegetation type
        veg_random = random.random()
        if veg_random < 0.4:
            vegetation = VegetationType.GRASSLAND
        elif veg_random < 0.75:
            vegetation = VegetationType.FOREST
        else:
            vegetation = VegetationType.SHRUB

        # Fire risk
        base_fire = 0.3
        if vegetation == VegetationType.FOREST:
            base_fire += 0.3
        base_fire += (1 - edge_factor) * 0.2
        fire_risk = max(0.0, min(1.0, base_fire + random.uniform(-0.15, 0.15)))

        # Terrain complexity higher in certain regions
        terrain_complexity = random.uniform(0.1, 0.5)
        if 0.2 < x_norm < 0.5 and 0.6 < y_norm < 0.9:
            terrain_complexity = random.uniform(0.5, 0.9)

        return Environment(
            fire_risk=fire_risk,
            terrain_complexity=terrain_complexity,
            vegetation_type=vegetation
        )

    def generate_species_density(
        self,
        grid: Grid,
        species_config: Optional[Dict[str, Species]] = None,
        grid_config: Optional[GridLayoutConfig] = None
    ) -> SpeciesDensity:
        """
        Generate species density data for a grid cell.

        Args:
            grid: Grid cell to generate density for
            species_config: Species configuration
            grid_config: Grid layout configuration

        Returns:
            SpeciesDensity object
        """
        config = grid_config or GridLayoutConfig()
        x_norm = grid.x / config.area_width_km
        y_norm = grid.y / config.area_height_km

        densities = {}

        # Rhino: near water, away from edges
        rhino_dist = ((x_norm - 0.5) ** 2 + (y_norm - 0.5) ** 2) ** 0.5
        rhino_base = max(0.0, 0.8 - rhino_dist)
        # Higher near water sources
        if grid.distance_to_water < 0.4:
            rhino_base += 0.3
        densities["rhino"] = max(0.0, min(1.0, rhino_base + random.uniform(-0.2, 0.2)))

        # Elephant: wide distribution
        elephant_base = random.uniform(0.2, 0.6)
        if grid.distance_to_water < 0.5:
            elephant_base += 0.2
        densities["elephant"] = max(0.0, min(1.0, elephant_base + random.uniform(-0.15, 0.15)))

        # Bird: everywhere
        bird_base = random.uniform(0.3, 0.7)
        densities["bird"] = max(0.0, min(1.0, bird_base + random.uniform(-0.1, 0.1)))

        return SpeciesDensity(densities=densities)

    def generate_full_dataset(
        self,
        grid_config: Optional[GridLayoutConfig] = None,
        seed: Optional[int] = None
    ) -> Tuple[List[Grid], List[Environment], List[SpeciesDensity]]:
        """
        Generate a complete dataset including grids, environments, and species densities.

        Args:
            grid_config: Grid layout configuration
            seed: Random seed for reproducibility

        Returns:
            Tuple of (grids, environments, species_densities)
        """
        if seed is not None:
            random.seed(seed)

        config = grid_config or GridLayoutConfig()
        grids = self.generate_grid_layout(config)
        environments = [self.generate_environment(g, config) for g in grids]
        species_densities = [self.generate_species_density(g, grid_config=config) for g in grids]

        return grids, environments, species_densities
