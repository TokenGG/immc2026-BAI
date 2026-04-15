"""
Environmental data structure for the risk model.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class VegetationType(Enum):
    """Vegetation type enumeration."""
    GRASSLAND = "grassland"
    FOREST = "forest"
    SHRUB = "shrub"


class Season(Enum):
    """Season enumeration."""
    DRY = "dry"
    RAINY = "rainy"


@dataclass
class Environment:
    """
    Environmental conditions for a grid cell.

    Attributes:
        fire_risk: Fire risk index [0, 1], higher = more dangerous
        terrain_complexity: Terrain complexity [0, 1], higher = more complex
        vegetation_type: Type of vegetation in the area
    """
    fire_risk: float
    terrain_complexity: float
    vegetation_type: VegetationType = VegetationType.GRASSLAND

    def __post_init__(self):
        """Validate values are in [0, 1] range."""
        if not (0.0 <= self.fire_risk <= 1.0):
            raise ValueError(f"Fire risk must be between 0 and 1, got {self.fire_risk}")
        if not (0.0 <= self.terrain_complexity <= 1.0):
            raise ValueError(
                f"Terrain complexity must be between 0 and 1, got {self.terrain_complexity}"
            )

    def get_fire_risk_factor(self) -> float:
        """Get fire risk contribution factor."""
        return self.fire_risk

    def get_terrain_risk_factor(self) -> float:
        """Get terrain complexity contribution factor."""
        return self.terrain_complexity


@dataclass
class TimeContext:
    """
    Time and season context for risk calculation.

    Attributes:
        hour_of_day: Hour of the day [0, 23]
        season: Current season (DRY or RAINY)
    """
    hour_of_day: int
    season: Season

    def __post_init__(self):
        """Validate hour is in [0, 23] range."""
        if not (0 <= self.hour_of_day <= 23):
            raise ValueError(f"Hour must be between 0 and 23, got {self.hour_of_day}")

    @property
    def is_daytime(self) -> bool:
        """Check if it's daytime (6:00 - 18:00)."""
        return 6 <= self.hour_of_day < 18

    @property
    def is_nighttime(self) -> bool:
        """Check if it's nighttime (18:00 - 6:00)."""
        return not self.is_daytime
