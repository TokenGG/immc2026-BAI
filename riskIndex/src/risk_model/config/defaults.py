"""
Default configuration values for the risk model.
"""

from dataclasses import dataclass
import math


@dataclass
class RiskWeights:
    """
    Weights for combining different risk components.

    Attributes:
        human_weight: Weight for human risk component
        environmental_weight: Weight for environmental risk component
        density_weight: Weight for species density component
    """
    human_weight: float = 0.4
    environmental_weight: float = 0.3
    density_weight: float = 0.3

    def __post_init__(self):
        """Validate weights sum to 1."""
        total = self.human_weight + self.environmental_weight + self.density_weight
        if not math.isclose(total, 1.0, rel_tol=1e-9):
            raise ValueError(
                f"Risk weights must sum to 1, got {total} "
                f"(human={self.human_weight}, "
                f"environmental={self.environmental_weight}, "
                f"density={self.density_weight})"
            )


# Default configurations
DEFAULT_RISK_WEIGHTS = RiskWeights(
    human_weight=0.4,
    environmental_weight=0.3,
    density_weight=0.3
)
