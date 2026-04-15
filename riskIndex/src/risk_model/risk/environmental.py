"""
Environmental risk calculator module.
"""

import math
from dataclasses import dataclass
from typing import Optional

from ..core.environment import Environment


@dataclass
class EnvironmentalRiskWeights:
    """
    Weights for environmental risk calculation.

    Attributes:
        fire_weight: Weight for fire risk
        terrain_weight: Weight for terrain complexity
    """
    fire_weight: float = 0.6
    terrain_weight: float = 0.4

    def __post_init__(self):
        """Validate weights sum to 1."""
        total = self.fire_weight + self.terrain_weight
        if not math.isclose(total, 1.0, rel_tol=1e-9):
            raise ValueError(
                f"Weights must sum to 1, got {total} "
                f"(fire={self.fire_weight}, terrain={self.terrain_weight})"
            )


class EnvironmentalRiskCalculator:
    """
    Calculates environmental risk based on fire risk and terrain complexity.
    """

    def __init__(self, weights: Optional[EnvironmentalRiskWeights] = None):
        """
        Initialize the environmental risk calculator.

        Args:
            weights: Weight configuration for environmental risk factors
        """
        self.weights = weights or EnvironmentalRiskWeights()

    def calculate(self, environment: Environment) -> float:
        """
        Calculate environmental risk for a grid cell.

        Args:
            environment: Environmental conditions for the grid cell

        Returns:
            Environmental risk value [0, 1]
        """
        fire_risk = environment.get_fire_risk_factor()
        terrain_risk = environment.get_terrain_risk_factor()

        return (
            self.weights.fire_weight * fire_risk +
            self.weights.terrain_weight * terrain_risk
        )

    def calculate_component_breakdown(
        self,
        environment: Environment
    ) -> tuple[float, float]:
        """
        Calculate the individual components of environmental risk.

        Args:
            environment: Environmental conditions for the grid cell

        Returns:
            Tuple of (fire_risk_component, terrain_risk_component)
        """
        fire_risk = environment.get_fire_risk_factor()
        terrain_risk = environment.get_terrain_risk_factor()

        return (
            self.weights.fire_weight * fire_risk,
            self.weights.terrain_weight * terrain_risk
        )
