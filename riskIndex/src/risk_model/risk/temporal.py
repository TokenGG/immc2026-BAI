"""
Temporal (diurnal and seasonal) factor calculators.
"""

import math
from typing import Optional
from enum import Enum

from ..core.species import Season
from ..core.environment import TimeContext


class DiurnalMode(Enum):
    """Mode for diurnal factor calculation."""
    DISCRETE = "discrete"  # Simple day/night switching
    CONTINUOUS = "continuous"  # Smooth sine wave


class DiurnalFactorCalculator:
    """
    Calculates diurnal (day/night) risk factors.
    """

    def __init__(
        self,
        mode: DiurnalMode = DiurnalMode.DISCRETE,
        daytime_factor: float = 1.0,
        nighttime_factor: float = 1.3,
        gamma: float = 0.3
    ):
        """
        Initialize the diurnal factor calculator.

        Args:
            mode: Calculation mode (DISCRETE or CONTINUOUS)
            daytime_factor: Risk factor for daytime
            nighttime_factor: Risk factor for nighttime
            gamma: Amplitude for continuous mode sine wave
        """
        self.mode = mode
        self.daytime_factor = daytime_factor
        self.nighttime_factor = nighttime_factor
        self.gamma = gamma

    def calculate(self, hour: int) -> float:
        """
        Calculate diurnal factor for a given hour.

        Args:
            hour: Hour of the day [0, 23]

        Returns:
            Diurnal risk factor
        """
        if not (0 <= hour <= 23):
            raise ValueError(f"Hour must be between 0 and 23, got {hour}")

        if self.mode == DiurnalMode.DISCRETE:
            return self._calculate_discrete(hour)
        return self._calculate_continuous(hour)

    def _calculate_discrete(self, hour: int) -> float:
        """Calculate using discrete day/night mode."""
        if 6 <= hour < 18:
            return self.daytime_factor
        return self.nighttime_factor

    def _calculate_continuous(self, hour: int) -> float:
        """Calculate using continuous sine wave mode."""
        # Sinusoidal function with minimum at noon (12:00) and maximum at midnight
        return 1.0 + self.gamma * math.sin(2 * math.pi * (hour - 6) / 24)

    def calculate_from_context(self, context: TimeContext) -> float:
        """Calculate diurnal factor from a TimeContext object."""
        return self.calculate(context.hour_of_day)


class SeasonalFactorCalculator:
    """
    Calculates seasonal risk factors.
    """

    def __init__(
        self,
        dry_season_factor: float = 1.0,
        rainy_season_factor: float = 1.2
    ):
        """
        Initialize the seasonal factor calculator.

        Args:
            dry_season_factor: Risk factor for dry season
            rainy_season_factor: Risk factor for rainy season
        """
        self.dry_season_factor = dry_season_factor
        self.rainy_season_factor = rainy_season_factor

    def calculate(self, season: Season) -> float:
        """
        Calculate seasonal factor for a given season.

        Args:
            season: Current season

        Returns:
            Seasonal risk factor
        """
        if season == Season.RAINY:
            return self.rainy_season_factor
        return self.dry_season_factor

    def calculate_from_context(self, context: TimeContext) -> float:
        """Calculate seasonal factor from a TimeContext object."""
        return self.calculate(context.season)


class TemporalFactorCalculator:
    """
    Combined diurnal and seasonal factor calculator.
    """

    def __init__(
        self,
        diurnal_calculator: Optional[DiurnalFactorCalculator] = None,
        seasonal_calculator: Optional[SeasonalFactorCalculator] = None
    ):
        """
        Initialize the combined temporal factor calculator.

        Args:
            diurnal_calculator: Diurnal factor calculator
            seasonal_calculator: Seasonal factor calculator
        """
        self.diurnal = diurnal_calculator or DiurnalFactorCalculator()
        self.seasonal = seasonal_calculator or SeasonalFactorCalculator()

    def calculate(self, context: TimeContext) -> float:
        """
        Calculate combined temporal factor.

        Args:
            context: Time and season context

        Returns:
            Combined temporal factor (diurnal * seasonal)
        """
        return self.diurnal.calculate_from_context(context) * \
            self.seasonal.calculate_from_context(context)

    def calculate_components(self, context: TimeContext) -> tuple[float, float]:
        """
        Calculate individual temporal components.

        Args:
            context: Time and season context

        Returns:
            Tuple of (diurnal_factor, seasonal_factor)
        """
        return (
            self.diurnal.calculate_from_context(context),
            self.seasonal.calculate_from_context(context)
        )
