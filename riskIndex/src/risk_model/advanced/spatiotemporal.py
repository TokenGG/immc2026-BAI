"""
Spatio-Temporal Risk Field Model for IMMC enhancements.
"""

from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass
import math

import numpy as np

from ..core import Grid, TimeContext, Season
from ..risk import RiskModel, GridRiskResult


@dataclass
class RiskPoint:
    """A point in the spatio-temporal risk field."""
    x: float
    y: float
    t: float  # Time in hours [0, 24)
    risk_value: float


class SpatioTemporalRiskField:
    """
    Spatio-Temporal Risk Field Model.

    Provides continuous risk interpolation across space and time.
    """

    def __init__(
        self,
        grids: List[Grid],
        risk_results: List[GridRiskResult],
        spatial_kernel: str = 'gaussian',
        temporal_kernel: str = 'sine'
    ):
        """
        Initialize the spatio-temporal risk field.

        Args:
            grids: List of Grid objects
            risk_results: Corresponding risk results
            spatial_kernel: Type of spatial interpolation kernel
            temporal_kernel: Type of temporal interpolation kernel
        """
        self.grids = grids
        self.risk_results = risk_results
        self.spatial_kernel = spatial_kernel
        self.temporal_kernel = temporal_kernel

        # Extract grid positions and risk values
        self.positions = np.array([(g.x, g.y) for g in grids])
        self.risk_values = np.array([r.normalized_risk for r in risk_results])

    def _spatial_interpolation_gaussian(
        self,
        x: float,
        y: float,
        sigma: float = 20.0
    ) -> float:
        """Gaussian kernel spatial interpolation."""
        distances = np.sqrt((self.positions[:, 0] - x) ** 2 +
                           (self.positions[:, 1] - y) ** 2)
        weights = np.exp(-distances ** 2 / (2 * sigma ** 2))
        weights = weights / np.sum(weights)
        return float(np.sum(weights * self.risk_values))

    def _spatial_interpolation_idw(
        self,
        x: float,
        y: float,
        power: float = 2.0
    ) -> float:
        """Inverse Distance Weighting spatial interpolation."""
        distances = np.sqrt((self.positions[:, 0] - x) ** 2 +
                           (self.positions[:, 1] - y) ** 2)

        # Avoid division by zero
        distances = np.maximum(distances, 1e-6)
        weights = 1.0 / (distances ** power)
        weights = weights / np.sum(weights)
        return float(np.sum(weights * self.risk_values))

    def spatial_interpolate(self, x: float, y: float) -> float:
        """
        Interpolate risk at a given spatial point.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Interpolated risk value
        """
        if self.spatial_kernel == 'gaussian':
            return self._spatial_interpolation_gaussian(x, y)
        elif self.spatial_kernel == 'idw':
            return self._spatial_interpolation_idw(x, y)
        else:
            raise ValueError(f"Unknown spatial kernel: {self.spatial_kernel}")

    def temporal_interpolate(
        self,
        base_risk: float,
        t: float,
        season: Season
    ) -> float:
        """
        Interpolate risk over time.

        Args:
            base_risk: Base risk value at reference time
            t: Time in hours [0, 24)
            season: Current season

        Returns:
            Temporally adjusted risk
        """
        if self.temporal_kernel == 'sine':
            # Diurnal variation with sine wave
            diurnal_factor = 1.0 + 0.3 * math.sin(2 * math.pi * (t - 6) / 24)
        else:
            diurnal_factor = 1.0

        # Seasonal factor
        seasonal_factor = 1.2 if season == Season.RAINY else 1.0

        return base_risk * diurnal_factor * seasonal_factor

    def get_risk_at(self, x: float, y: float, t: float, season: Season) -> float:
        """
        Get risk at a specific point in space and time.

        Args:
            x: X coordinate
            y: Y coordinate
            t: Time in hours [0, 24)
            season: Current season

        Returns:
            Risk value at the specified space-time point
        """
        spatial_risk = self.spatial_interpolate(x, y)
        return self.temporal_interpolate(spatial_risk, t, season)

    def compute_spatial_gradient(
        self,
        x: float,
        y: float,
        epsilon: float = 1.0
    ) -> Tuple[float, float]:
        """
        Compute spatial gradient of risk at a point.

        Args:
            x: X coordinate
            y: Y coordinate
            epsilon: Small step for finite difference

        Returns:
            Tuple of (dx, dy) - risk gradient components
        """
        risk_center = self.spatial_interpolate(x, y)
        risk_x = self.spatial_interpolate(x + epsilon, y)
        risk_y = self.spatial_interpolate(x, y + epsilon)

        dx = (risk_x - risk_center) / epsilon
        dy = (risk_y - risk_center) / epsilon

        return dx, dy

    def compute_temporal_gradient(
        self,
        x: float,
        y: float,
        t: float,
        season: Season,
        epsilon: float = 0.1
    ) -> float:
        """
        Compute temporal gradient of risk at a point.

        Args:
            x: X coordinate
            y: Y coordinate
            t: Time in hours
            season: Current season
            epsilon: Small step for finite difference

        Returns:
            Temporal risk gradient
        """
        risk_now = self.get_risk_at(x, y, t, season)
        risk_next = self.get_risk_at(x, y, (t + epsilon) % 24, season)

        return (risk_next - risk_now) / epsilon

    def predict_future_risk(
        self,
        x: float,
        y: float,
        t: float,
        season: Season,
        time_delta: float
    ) -> float:
        """
        Predict risk at a future time.

        Args:
            x: X coordinate
            y: Y coordinate
            t: Current time in hours
            season: Current season
            time_delta: Time delta in hours (can be negative)

        Returns:
            Predicted risk at future time
        """
        future_t = (t + time_delta) % 24
        return self.get_risk_at(x, y, future_t, season)


def generate_risk_field(
    model: RiskModel,
    grids: List[Grid],
    environments: List,
    densities: List,
    time_context: TimeContext
) -> SpatioTemporalRiskField:
    """
    Generate a spatio-temporal risk field from model results.

    Args:
        model: RiskModel instance
        grids: List of Grid objects
        environments: List of Environment objects
        densities: List of SpeciesDensity objects
        time_context: Time and season context

    Returns:
        SpatioTemporalRiskField instance
    """
    grid_data = list(zip(grids, environments, densities))
    risk_results = model.calculate_batch(grid_data, time_context)

    return SpatioTemporalRiskField(grids, risk_results)
