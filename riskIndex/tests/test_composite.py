"""
Tests for composite risk calculator and normalization.
"""

import pytest

from risk_model.core import (
    Grid,
    SpeciesDensity,
    Environment,
    VegetationType,
    TimeContext,
    Season,
)
from risk_model.risk import (
    CompositeRiskCalculator,
    NormalizationEngine,
    RiskModel,
)


class TestNormalizationEngine:
    """Tests for NormalizationEngine."""

    def test_fit(self):
        """Test fitting the normalizer."""
        normalizer = NormalizationEngine()
        normalizer.fit([0.2, 0.5, 0.8])

        assert normalizer.min_risk == 0.2
        assert normalizer.max_risk == 0.8
        assert normalizer._is_fitted is True

    def test_fit_empty_list(self):
        """Test fitting with empty list raises error."""
        normalizer = NormalizationEngine()
        with pytest.raises(ValueError):
            normalizer.fit([])

    def test_normalize(self):
        """Test normalization."""
        normalizer = NormalizationEngine()
        normalizer.fit([0.1, 0.5, 0.9])

        assert normalizer.normalize(0.1) == pytest.approx(0.0)
        assert normalizer.normalize(0.5) == pytest.approx(0.5)
        assert normalizer.normalize(0.9) == pytest.approx(1.0)

    def test_normalize_before_fit(self):
        """Test normalize before fit raises error."""
        normalizer = NormalizationEngine()
        with pytest.raises(ValueError):
            normalizer.normalize(0.5)

    def test_normalize_all_same_values(self):
        """Test normalization when all values are the same."""
        normalizer = NormalizationEngine()
        normalizer.fit([0.5, 0.5, 0.5])

        assert normalizer.normalize(0.5) == pytest.approx(0.5)

    def test_normalize_batch(self):
        """Test batch normalization."""
        normalizer = NormalizationEngine()
        values = [0.1, 0.3, 0.5, 0.7, 0.9]
        normalized = normalizer.normalize_batch(values)

        assert len(normalized) == 5
        assert normalized[0] == pytest.approx(0.0)
        assert normalized[-1] == pytest.approx(1.0)

    def test_reset(self):
        """Test resetting the normalizer."""
        normalizer = NormalizationEngine()
        normalizer.fit([0.1, 0.9])
        normalizer.reset()

        assert normalizer._is_fitted is False
        assert normalizer.min_risk is None
        assert normalizer.max_risk is None


class TestRiskModel:
    """Tests for RiskModel."""

    def test_calculate_batch(self):
        """Test batch risk calculation."""
        model = RiskModel()

        # Create test data
        grid1 = Grid("A01", 0, 0, 0.1, 0.1, 0.1)
        env1 = Environment(0.8, 0.7, VegetationType.FOREST)
        density1 = SpeciesDensity({"rhino": 0.9, "elephant": 0.5, "bird": 0.3})

        grid2 = Grid("B02", 1, 1, 0.9, 0.9, 0.9)
        env2 = Environment(0.1, 0.1, VegetationType.GRASSLAND)
        density2 = SpeciesDensity({"rhino": 0.1, "elephant": 0.2, "bird": 0.3})

        grid_data = [(grid1, env1, density1), (grid2, env2, density2)]
        time_context = TimeContext(hour_of_day=22, season=Season.RAINY)

        results = model.calculate_batch(grid_data, time_context)

        assert len(results) == 2
        assert results[0].grid_id == "A01"
        assert results[1].grid_id == "B02"

        # First grid should have higher risk
        assert results[0].normalized_risk > results[1].normalized_risk

        # Normalized values should be in [0, 1]
        assert 0.0 <= results[0].normalized_risk <= 1.0
        assert 0.0 <= results[1].normalized_risk <= 1.0

    def test_normalization_range(self):
        """Test that normalization produces values in [0, 1]."""
        model = RiskModel()

        # Create multiple grid cells
        grid_data = []
        for i in range(10):
            grid = Grid(f"G{i:02d}", i, i, 0.1 * i, 0.1 * i, 0.1 * i)
            env = Environment(0.1 * i, 0.1 * i, VegetationType.GRASSLAND)
            density = SpeciesDensity({"rhino": 0.1 * i, "elephant": 0.5, "bird": 0.5})
            grid_data.append((grid, env, density))

        time_context = TimeContext(hour_of_day=12, season=Season.DRY)
        results = model.calculate_batch(grid_data, time_context)

        normalized_risks = [r.normalized_risk for r in results]
        assert min(normalized_risks) == pytest.approx(0.0, abs=1e-9)
        assert max(normalized_risks) == pytest.approx(1.0, abs=1e-9)
