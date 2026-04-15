"""
Species density calculator module.
"""

from typing import Dict, Optional

from ..core.species import Species, SpeciesDensity, Season


class DensityRiskCalculator:
    """
    Calculates conservation value based on weighted species density.
    """

    def __init__(self, species_config: Optional[Dict[str, Species]] = None):
        """
        Initialize the density risk calculator.

        Args:
            species_config: Dictionary mapping species names to Species objects
        """
        self.species_config = species_config or self._get_default_species()

    @staticmethod
    def _get_default_species() -> Dict[str, Species]:
        """Get default species configuration."""
        return {
            "rhino": Species(
                name="rhino",
                weight=0.5,
                rainy_season_multiplier=1.2,
                dry_season_multiplier=1.0
            ),
            "elephant": Species(
                name="elephant",
                weight=0.3,
                rainy_season_multiplier=1.3,
                dry_season_multiplier=0.9
            ),
            "bird": Species(
                name="bird",
                weight=0.2,
                rainy_season_multiplier=1.5,
                dry_season_multiplier=0.8
            ),
        }

    def calculate(
        self,
        density: SpeciesDensity,
        season: Optional[Season] = None
    ) -> float:
        """
        Calculate weighted species density.

        Args:
            density: Species density data
            season: Current season for seasonal adjustment

        Returns:
            Weighted density value (conservation value)
        """
        return density.get_weighted_density(self.species_config, season)

    def calculate_species_breakdown(
        self,
        density: SpeciesDensity,
        season: Optional[Season] = None
    ) -> Dict[str, float]:
        """
        Calculate the contribution of each species to the total density score.

        Args:
            density: Species density data
            season: Current season for seasonal adjustment

        Returns:
            Dictionary mapping species names to their contribution
        """
        breakdown = {}
        for species_name, raw_density in density.densities.items():
            if species_name in self.species_config:
                species = self.species_config[species_name]
                adjusted_density = raw_density
                if season is not None:
                    adjusted_density *= species.get_seasonal_multiplier(season)
                breakdown[species_name] = species.weight * adjusted_density
        return breakdown

    def add_species(self, species: Species) -> None:
        """
        Add or update a species in the configuration.

        Args:
            species: Species object to add
        """
        self.species_config[species.name] = species

    def remove_species(self, species_name: str) -> None:
        """
        Remove a species from the configuration.

        Args:
            species_name: Name of species to remove
        """
        if species_name in self.species_config:
            del self.species_config[species_name]
