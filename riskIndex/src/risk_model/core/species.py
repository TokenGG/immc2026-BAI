"""
Species data structure for the risk model.
"""

from dataclasses import dataclass
from typing import Dict, Optional

from .environment import Season


@dataclass
class Species:
    """
    Represents a species with its conservation weight.

    Attributes:
        name: Name of the species
        weight: Conservation weight (higher = more important)
        rainy_season_multiplier: Density multiplier for rainy season
        dry_season_multiplier: Density multiplier for dry season
    """
    name: str
    weight: float
    rainy_season_multiplier: float = 1.0
    dry_season_multiplier: float = 1.0

    def __post_init__(self):
        """Validate weight is positive."""
        if self.weight <= 0:
            raise ValueError(f"Species weight must be positive, got {self.weight}")

    def get_seasonal_multiplier(self, season: Season) -> float:
        """Get the density multiplier for a given season."""
        if season == Season.RAINY:
            return self.rainy_season_multiplier
        return self.dry_season_multiplier


@dataclass
class SpeciesDensity:
    """
    Manages species density data for grid cells.

    Attributes:
        densities: Dictionary mapping species name to normalized density [0, 1]
    """
    densities: Dict[str, float]

    def __post_init__(self):
        """Validate density values are in [0, 1] range."""
        for species_name, density in self.densities.items():
            if not (0.0 <= density <= 1.0):
                raise ValueError(
                    f"Density for {species_name} must be between 0 and 1, got {density}"
                )

    def get_weighted_density(
        self,
        species_weights: Dict[str, Species],
        season: Optional[Season] = None
    ) -> float:
        """
        Calculate weighted species density.

        Args:
            species_weights: Dictionary of Species objects
            season: Current season for seasonal adjustment

        Returns:
            Weighted density value
        """
        total = 0.0
        for species_name, density in self.densities.items():
            if species_name in species_weights:
                species = species_weights[species_name]
                adjusted_density = density
                if season is not None:
                    adjusted_density *= species.get_seasonal_multiplier(season)
                total += species.weight * adjusted_density
        return total

    def get_density(self, species_name: str) -> float:
        """Get density for a specific species."""
        return self.densities.get(species_name, 0.0)
