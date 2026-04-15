"""
Composite risk calculator and normalization engine.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import math

from ..core import Grid, SpeciesDensity, Environment, TimeContext
from ..config import RiskWeights, WeightManager, DEFAULT_RISK_WEIGHTS
from .human import HumanRiskCalculator
from .environmental import EnvironmentalRiskCalculator
from .density import DensityRiskCalculator
from .temporal import TemporalFactorCalculator


@dataclass
class RiskComponents:
    """
    Container for individual risk components.
    """
    human_risk: float
    environmental_risk: float
    density_value: float
    diurnal_factor: float
    seasonal_factor: float

    @property
    def temporal_factor(self) -> float:
        """Get combined temporal factor."""
        return self.diurnal_factor * self.seasonal_factor


@dataclass
class GridRiskResult:
    """
    Result of risk calculation for a single grid cell.
    """
    grid_id: str
    raw_risk: float
    normalized_risk: Optional[float] = None
    components: Optional[RiskComponents] = None


class CompositeRiskCalculator:
    """
    Calculates composite risk by combining all risk components.
    """

    def __init__(
        self,
        weight_manager: Optional[WeightManager] = None,
        human_calculator: Optional[HumanRiskCalculator] = None,
        environmental_calculator: Optional[EnvironmentalRiskCalculator] = None,
        density_calculator: Optional[DensityRiskCalculator] = None,
        temporal_calculator: Optional[TemporalFactorCalculator] = None
    ):
        """
        Initialize the composite risk calculator.

        Args:
            weight_manager: Weight configuration manager
            human_calculator: Human risk calculator
            environmental_calculator: Environmental risk calculator
            density_calculator: Density risk calculator
            temporal_calculator: Temporal factor calculator
        """
        self.weight_manager = weight_manager or WeightManager()
        self.human_calculator = human_calculator or HumanRiskCalculator(
            weights=self.weight_manager.get_human_risk_weights()
        )
        self.environmental_calculator = environmental_calculator or EnvironmentalRiskCalculator(
            weights=self.weight_manager.get_environmental_risk_weights()
        )
        self.density_calculator = density_calculator or DensityRiskCalculator()
        self.temporal_calculator = temporal_calculator or TemporalFactorCalculator()

    def calculate_components(
        self,
        grid: Grid,
        environment: Environment,
        density: SpeciesDensity,
        time_context: TimeContext,
        poaching_probability: float = 1.0
    ) -> RiskComponents:
        """
        Calculate individual risk components.

        Args:
            grid: Grid cell data
            environment: Environmental data
            density: Species density data
            time_context: Time and season context
            poaching_probability: Time-based poaching probability

        Returns:
            RiskComponents object with individual components
        """
        human_risk = self.human_calculator.calculate(grid, poaching_probability)
        environmental_risk = self.environmental_calculator.calculate(environment)
        density_value = self.density_calculator.calculate(density, time_context.season)
        diurnal_factor, seasonal_factor = self.temporal_calculator.calculate_components(
            time_context
        )

        return RiskComponents(
            human_risk=human_risk,
            environmental_risk=environmental_risk,
            density_value=density_value,
            diurnal_factor=diurnal_factor,
            seasonal_factor=seasonal_factor
        )

    def calculate_raw(
        self,
        grid: Grid,
        environment: Environment,
        density: SpeciesDensity,
        time_context: TimeContext,
        poaching_probability: float = 1.0,
        return_components: bool = False,
        use_temporal_factors: bool = False
    ) -> Tuple[float, Optional[RiskComponents]]:
        """
        Calculate raw (non-normalized) risk for a single grid cell.

        Args:
            grid: Grid cell data
            environment: Environmental data
            density: Species density data
            time_context: Time and season context
            poaching_probability: Time-based poaching probability
            return_components: Whether to return individual components
            use_temporal_factors: Whether to apply diurnal/seasonal/temporal factors (default: False)

        Returns:
            Tuple of (raw_risk_value, risk_components if requested)
        """
        weights = self.weight_manager.get_risk_weights()
        components = self.calculate_components(
            grid, environment, density, time_context, poaching_probability
        )

        base_risk = (
            weights.human_weight * components.human_risk +
            weights.environmental_weight * components.environmental_risk +
            weights.density_weight * components.density_value
        )

        if use_temporal_factors:
            raw_risk = base_risk * components.temporal_factor
        else:
            raw_risk = base_risk

        if return_components:
            return raw_risk, components
        return raw_risk, None


class NormalizationEngine:
    """
    Normalizes risk values across all grid cells to [0, 1] range.
    """

    def __init__(self):
        """Initialize the normalization engine."""
        self._min_risk: Optional[float] = None
        self._max_risk: Optional[float] = None
        self._is_fitted = False

    def fit(self, raw_risks: List[float]) -> None:
        """
        Fit the normalizer to a set of raw risk values.

        Args:
            raw_risks: List of raw risk values
        """
        if not raw_risks:
            raise ValueError("Cannot fit with empty risk list")

        self._min_risk = min(raw_risks)
        self._max_risk = max(raw_risks)
        self._is_fitted = True

    def normalize(self, raw_risk: float) -> float:
        """
        Normalize a single raw risk value.

        Args:
            raw_risk: Raw risk value to normalize

        Returns:
            Normalized risk value in [0, 1]
        """
        if not self._is_fitted:
            raise ValueError("Normalizer has not been fitted. Call fit() first.")

        if self._max_risk == self._min_risk:
            return 0.5  # All values are the same

        normalized = (raw_risk - self._min_risk) / (self._max_risk - self._min_risk)

        # Clamp to [0, 1] to handle floating point errors
        return max(0.0, min(1.0, normalized))

    def normalize_batch(self, raw_risks: List[float]) -> List[float]:
        """
        Normalize a batch of raw risk values.

        Args:
            raw_risks: List of raw risk values

        Returns:
            List of normalized risk values in [0, 1]
        """
        if not self._is_fitted:
            self.fit(raw_risks)

        return [self.normalize(r) for r in raw_risks]

    @property
    def min_risk(self) -> Optional[float]:
        """Get the minimum risk value used for normalization."""
        return self._min_risk

    @property
    def max_risk(self) -> Optional[float]:
        """Get the maximum risk value used for normalization."""
        return self._max_risk

    def reset(self) -> None:
        """Reset the normalizer state."""
        self._min_risk = None
        self._max_risk = None
        self._is_fitted = False


class RiskModel:
    """
    Complete risk model combining calculation and normalization.
    """

    def __init__(
        self,
        composite_calculator: Optional[CompositeRiskCalculator] = None,
        normalization_engine: Optional[NormalizationEngine] = None
    ):
        """
        Initialize the complete risk model.

        Args:
            composite_calculator: Composite risk calculator
            normalization_engine: Normalization engine
        """
        self.calculator = composite_calculator or CompositeRiskCalculator()
        self.normalizer = normalization_engine or NormalizationEngine()

    def calculate_grid(
        self,
        grid: Grid,
        environment: Environment,
        density: SpeciesDensity,
        time_context: TimeContext,
        poaching_probability: float = 1.0,
        fit_normalizer: bool = False
    ) -> GridRiskResult:
        """
        Calculate risk for a single grid cell.

        Note: For proper normalization, use calculate_batch() instead.

        Args:
            grid: Grid cell data
            environment: Environmental data
            density: Species density data
            time_context: Time and season context
            poaching_probability: Time-based poaching probability
            fit_normalizer: Whether to fit normalizer to this single value (not recommended)

        Returns:
            GridRiskResult with raw and normalized risk
        """
        raw_risk, components = self.calculator.calculate_raw(
            grid, environment, density, time_context, poaching_probability,
            return_components=True
        )

        normalized_risk = None
        if fit_normalizer:
            self.normalizer.fit([raw_risk])
            normalized_risk = self.normalizer.normalize(raw_risk)

        return GridRiskResult(
            grid_id=grid.grid_id,
            raw_risk=raw_risk,
            normalized_risk=normalized_risk,
            components=components
        )

    def calculate_batch(
        self,
        grid_data: List[Tuple[Grid, Environment, SpeciesDensity]],
        time_context: TimeContext,
        poaching_probability: float = 1.0,
        use_temporal_factors: bool = False
    ) -> List[GridRiskResult]:
        """
        Calculate risk for a batch of grid cells with proper normalization.

        Args:
            grid_data: List of (Grid, Environment, SpeciesDensity) tuples
            time_context: Time and season context
            poaching_probability: Time-based poaching probability
            use_temporal_factors: Whether to apply diurnal/seasonal/temporal factors (default: False)

        Returns:
            List of GridRiskResult with normalized risk values
        """
        # Calculate raw risks first
        raw_results: List[Tuple[Grid, float, RiskComponents]] = []
        for grid, env, density in grid_data:
            raw_risk, components = self.calculator.calculate_raw(
                grid, env, density, time_context, poaching_probability,
                return_components=True,
                use_temporal_factors=use_temporal_factors
            )
            raw_results.append((grid, raw_risk, components))

        # Fit normalizer
        raw_risks = [r[1] for r in raw_results]
        self.normalizer.fit(raw_risks)

        # Normalize and create results
        results = []
        for grid, raw_risk, components in raw_results:
            normalized_risk = self.normalizer.normalize(raw_risk)
            results.append(GridRiskResult(
                grid_id=grid.grid_id,
                raw_risk=raw_risk,
                normalized_risk=normalized_risk,
                components=components
            ))

        return results
