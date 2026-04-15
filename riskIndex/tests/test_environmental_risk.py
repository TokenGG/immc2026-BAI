"""
Tests for environmental risk calculator.
"""

import pytest

from risk_model.core import Environment, VegetationType
from risk_model.risk import EnvironmentalRiskCalculator, EnvironmentalRiskWeights


class TestEnvironmentalRiskWeights:
    """Tests for EnvironmentalRiskWeights."""

    def test_default_weights(self):
        """Test default weight values."""
        weights = EnvironmentalRiskWeights()
        assert weights.fire_weight == 0.6
        assert weights.terrain_weight == 0.4

    def test_weights_sum_to_one(self):
        """Test that weights must sum to 1."""
        with pytest.raises(ValueError):
            EnvironmentalRiskWeights(fire_weight=0.8, terrain_weight=0.8)

    def test_custom_weights(self):
        """Test custom weight configuration."""
        weights = EnvironmentalRiskWeights(fire_weight=0.7, terrain_weight=0.3)
        assert weights.fire_weight == 0.7
        assert weights.terrain_weight == 0.3


class TestEnvironmentalRiskCalculator:
    """Tests for EnvironmentalRiskCalculator."""

    def test_calculate_high_risk(self):
        """Test high environmental risk calculation."""
        env = Environment(
            fire_risk=0.9,
            terrain_complexity=0.9,
            vegetation_type=VegetationType.FOREST
        )
        calculator = EnvironmentalRiskCalculator()
        risk = calculator.calculate(env)
        assert risk > 0.8
        assert risk <= 1.0

    def test_calculate_low_risk(self):
        """Test low environmental risk calculation."""
        env = Environment(
            fire_risk=0.1,
            terrain_complexity=0.1,
            vegetation_type=VegetationType.GRASSLAND
        )
        calculator = EnvironmentalRiskCalculator()
        risk = calculator.calculate(env)
        assert risk < 0.2

    def test_only_fire_risk(self):
        """Test only fire risk contributes."""
        env = Environment(
            fire_risk=1.0,
            terrain_complexity=0.0,
            vegetation_type=VegetationType.FOREST
        )
        calculator = EnvironmentalRiskCalculator()
        risk = calculator.calculate(env)
        assert risk == pytest.approx(0.6)  # Default fire weight

    def test_only_terrain_risk(self):
        """Test only terrain risk contributes."""
        env = Environment(
            fire_risk=0.0,
            terrain_complexity=1.0,
            vegetation_type=VegetationType.GRASSLAND
        )
        calculator = EnvironmentalRiskCalculator()
        risk = calculator.calculate(env)
        assert risk == pytest.approx(0.4)  # Default terrain weight

    def test_component_breakdown(self):
        """Test component breakdown calculation."""
        env = Environment(
            fire_risk=0.5,
            terrain_complexity=0.8,
            vegetation_type=VegetationType.FOREST
        )
        calculator = EnvironmentalRiskCalculator()

        fire, terrain = calculator.calculate_component_breakdown(env)

        assert fire == pytest.approx(0.5 * 0.6)
        assert terrain == pytest.approx(0.8 * 0.4)
