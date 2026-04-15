"""
Tests for core data structures.
"""

import pytest

from risk_model.core import (
    Grid,
    Species,
    SpeciesDensity,
    Season,
    Environment,
    VegetationType,
    TimeContext,
)


class TestGrid:
    """Tests for Grid class."""

    def test_create_grid(self):
        """Test creating a grid with valid values."""
        grid = Grid(
            grid_id="A01",
            x=10.0,
            y=20.0,
            distance_to_boundary=0.5,
            distance_to_road=0.3,
            distance_to_water=0.7
        )

        assert grid.grid_id == "A01"
        assert grid.x == 10.0
        assert grid.y == 20.0

    def test_invalid_distance(self):
        """Test invalid distance raises error."""
        with pytest.raises(ValueError):
            Grid("A01", 0, 0, 1.5, 0.5, 0.5)  # boundary > 1

        with pytest.raises(ValueError):
            Grid("A01", 0, 0, 0.5, -0.1, 0.5)  # road < 0

    def test_proximity_score(self):
        """Test proximity score calculation."""
        grid = Grid("A01", 0, 0, 0.2, 0.3, 0.4)
        boundary, road, water = grid.proximity_score

        assert boundary == pytest.approx(0.8)
        assert road == pytest.approx(0.7)
        assert water == pytest.approx(0.6)

    def test_get_position(self):
        """Test getting grid position."""
        grid = Grid("A01", 12.3, 45.6, 0.5, 0.5, 0.5)
        x, y = grid.get_position()
        assert x == 12.3
        assert y == 45.6


class TestSpecies:
    """Tests for Species class."""

    def test_create_species(self):
        """Test creating a species."""
        species = Species(
            name="rhino",
            weight=0.5,
            rainy_season_multiplier=1.2,
            dry_season_multiplier=1.0
        )

        assert species.name == "rhino"
        assert species.weight == 0.5

    def test_invalid_weight(self):
        """Test invalid weight raises error."""
        with pytest.raises(ValueError):
            Species("test", weight=0.0)

        with pytest.raises(ValueError):
            Species("test", weight=-0.5)

    def test_seasonal_multiplier(self):
        """Test seasonal multiplier."""
        species = Species(
            name="elephant",
            weight=0.3,
            rainy_season_multiplier=1.3,
            dry_season_multiplier=0.9
        )

        assert species.get_seasonal_multiplier(Season.RAINY) == 1.3
        assert species.get_seasonal_multiplier(Season.DRY) == 0.9


class TestEnvironment:
    """Tests for Environment class."""

    def test_create_environment(self):
        """Test creating environment."""
        env = Environment(
            fire_risk=0.5,
            terrain_complexity=0.7,
            vegetation_type=VegetationType.FOREST
        )

        assert env.fire_risk == 0.5
        assert env.terrain_complexity == 0.7
        assert env.vegetation_type == VegetationType.FOREST

    def test_invalid_fire_risk(self):
        """Test invalid fire risk raises error."""
        with pytest.raises(ValueError):
            Environment(1.5, 0.5, VegetationType.GRASSLAND)

        with pytest.raises(ValueError):
            Environment(-0.1, 0.5, VegetationType.GRASSLAND)

    def test_invalid_terrain_complexity(self):
        """Test invalid terrain complexity raises error."""
        with pytest.raises(ValueError):
            Environment(0.5, 1.5, VegetationType.GRASSLAND)

        with pytest.raises(ValueError):
            Environment(0.5, -0.1, VegetationType.GRASSLAND)


class TestTimeContext:
    """Tests for TimeContext class."""

    def test_create_time_context(self):
        """Test creating time context."""
        ctx = TimeContext(hour_of_day=14, season=Season.RAINY)
        assert ctx.hour_of_day == 14
        assert ctx.season == Season.RAINY

    def test_invalid_hour(self):
        """Test invalid hour raises error."""
        with pytest.raises(ValueError):
            TimeContext(hour_of_day=24, season=Season.DRY)

        with pytest.raises(ValueError):
            TimeContext(hour_of_day=-1, season=Season.DRY)

    def test_is_daytime(self):
        """Test daytime detection."""
        assert TimeContext(6, Season.DRY).is_daytime is True
        assert TimeContext(12, Season.DRY).is_daytime is True
        assert TimeContext(17, Season.DRY).is_daytime is True
        assert TimeContext(18, Season.DRY).is_daytime is False
        assert TimeContext(0, Season.DRY).is_daytime is False
        assert TimeContext(5, Season.DRY).is_daytime is False

    def test_is_nighttime(self):
        """Test nighttime detection."""
        assert TimeContext(6, Season.DRY).is_nighttime is False
        assert TimeContext(18, Season.DRY).is_nighttime is True
        assert TimeContext(0, Season.DRY).is_nighttime is True
