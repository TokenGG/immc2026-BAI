"""
Tests for human risk calculator.
"""

import pytest

from risk_model.core import Grid
from risk_model.risk import HumanRiskCalculator, HumanRiskWeights


class TestHumanRiskWeights:
    """Tests for HumanRiskWeights."""

    def test_default_weights(self):
        """Test default weight values."""
        weights = HumanRiskWeights()
        assert weights.boundary_weight == 0.4
        assert weights.road_weight == 0.35
        assert weights.water_weight == 0.25

    def test_weights_sum_to_one(self):
        """Test that weights must sum to 1."""
        with pytest.raises(ValueError):
            HumanRiskWeights(boundary_weight=0.5, road_weight=0.5, water_weight=0.5)

    def test_custom_weights(self):
        """Test custom weight configuration."""
        weights = HumanRiskWeights(
            boundary_weight=0.5,
            road_weight=0.3,
            water_weight=0.2
        )
        assert weights.boundary_weight == 0.5
        assert weights.road_weight == 0.3
        assert weights.water_weight == 0.2


class TestHumanRiskCalculator:
    """Tests for HumanRiskCalculator."""

    def test_calculate_high_risk(self):
        """Test high risk calculation (near boundary and road)."""
        grid = Grid(
            grid_id="TEST",
            x=0,
            y=0,
            distance_to_boundary=0.05,
            distance_to_road=0.05,
            distance_to_water=0.1
        )
        calculator = HumanRiskCalculator()
        risk = calculator.calculate(grid, poaching_probability=1.0)
        assert risk > 0.8
        assert risk <= 1.0

    def test_calculate_low_risk(self):
        """Test low risk calculation (far from everything)."""
        grid = Grid(
            grid_id="TEST",
            x=0,
            y=0,
            distance_to_boundary=0.95,
            distance_to_road=0.95,
            distance_to_water=0.9
        )
        calculator = HumanRiskCalculator()
        risk = calculator.calculate(grid, poaching_probability=1.0)
        assert risk < 0.2

    def test_poaching_probability(self):
        """Test that poaching probability affects risk."""
        grid = Grid(
            grid_id="TEST",
            x=0,
            y=0,
            distance_to_boundary=0.1,
            distance_to_road=0.1,
            distance_to_water=0.1
        )
        calculator = HumanRiskCalculator()

        risk_full = calculator.calculate(grid, poaching_probability=1.0)
        risk_half = calculator.calculate(grid, poaching_probability=0.5)

        assert risk_half == pytest.approx(risk_full * 0.5)

    def test_invalid_poaching_probability(self):
        """Test invalid poaching probability raises error."""
        grid = Grid(
            grid_id="TEST",
            x=0,
            y=0,
            distance_to_boundary=0.5,
            distance_to_road=0.5,
            distance_to_water=0.5
        )
        calculator = HumanRiskCalculator()

        with pytest.raises(ValueError):
            calculator.calculate(grid, poaching_probability=1.5)

        with pytest.raises(ValueError):
            calculator.calculate(grid, poaching_probability=-0.1)

    def test_component_breakdown(self):
        """Test component breakdown calculation."""
        grid = Grid(
            grid_id="TEST",
            x=0,
            y=0,
            distance_to_boundary=0.1,
            distance_to_road=0.2,
            distance_to_water=0.3
        )
        calculator = HumanRiskCalculator()

        boundary, road, water = calculator.calculate_component_breakdown(grid)

        assert boundary > 0
        assert road > 0
        assert water > 0
        assert boundary + road + water < 1.0
