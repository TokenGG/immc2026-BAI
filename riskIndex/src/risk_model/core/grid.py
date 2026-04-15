"""
Grid data structure for the risk model.
"""

from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class Grid:
    """
    Represents a single grid cell in the protected area.

    Attributes:
        grid_id: Unique identifier for the grid cell (e.g., "A12")
        x: X coordinate of grid center
        y: Y coordinate of grid center
        distance_to_boundary: Normalized distance to protected area boundary [0, 1]
        distance_to_road: Normalized distance to nearest road [0, 1]
        distance_to_water: Normalized distance to nearest water source [0, 1]
    """
    grid_id: str
    x: float
    y: float
    distance_to_boundary: float
    distance_to_road: float
    distance_to_water: float

    def __post_init__(self):
        """Validate distance values are in [0, 1] range."""
        for attr in ['distance_to_boundary', 'distance_to_road', 'distance_to_water']:
            value = getattr(self, attr)
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"{attr} must be between 0 and 1, got {value}")

    @property
    def proximity_score(self) -> Tuple[float, float, float]:
        """
        Calculate proximity scores (1 - distance, since closer = higher risk).

        Returns:
            Tuple of (boundary_proximity, road_proximity, water_proximity)
        """
        return (
            1.0 - self.distance_to_boundary,
            1.0 - self.distance_to_road,
            1.0 - self.distance_to_water
        )

    def get_position(self) -> Tuple[float, float]:
        """Get grid center coordinates."""
        return (self.x, self.y)
