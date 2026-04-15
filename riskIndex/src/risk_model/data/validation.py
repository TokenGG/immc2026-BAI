"""
Data validation for the risk model.
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass

from ..core import Grid, SpeciesDensity, Environment


@dataclass
class ValidationError:
    """Represents a data validation error."""
    grid_id: Optional[str]
    field: str
    message: str
    value: Optional[float] = None


class DataValidator:
    """Validates input data for the risk model."""

    def __init__(self):
        """Initialize the data validator."""
        self.errors: List[ValidationError] = []

    def validate_grid(self, grid: Grid) -> bool:
        """
        Validate a single grid.

        Args:
            grid: Grid to validate

        Returns:
            True if valid, False otherwise
        """
        valid = True

        # Check distances
        for attr in ['distance_to_boundary', 'distance_to_road', 'distance_to_water']:
            value = getattr(grid, attr)
            if not (0.0 <= value <= 1.0):
                self.errors.append(ValidationError(
                    grid_id=grid.grid_id,
                    field=attr,
                    message="Must be between 0 and 1",
                    value=value
                ))
                valid = False

        return valid

    def validate_environment(self, environment: Environment, grid_id: Optional[str] = None) -> bool:
        """
        Validate environment data.

        Args:
            environment: Environment to validate
            grid_id: Optional grid ID for error reporting

        Returns:
            True if valid, False otherwise
        """
        valid = True

        if not (0.0 <= environment.fire_risk <= 1.0):
            self.errors.append(ValidationError(
                grid_id=grid_id,
                field="fire_risk",
                message="Must be between 0 and 1",
                value=environment.fire_risk
            ))
            valid = False

        if not (0.0 <= environment.terrain_complexity <= 1.0):
            self.errors.append(ValidationError(
                grid_id=grid_id,
                field="terrain_complexity",
                message="Must be between 0 and 1",
                value=environment.terrain_complexity
            ))
            valid = False

        return valid

    def validate_density(self, density: SpeciesDensity, grid_id: Optional[str] = None) -> bool:
        """
        Validate species density data.

        Args:
            density: Species density to validate
            grid_id: Optional grid ID for error reporting

        Returns:
            True if valid, False otherwise
        """
        valid = True

        for species_name, value in density.densities.items():
            if not (0.0 <= value <= 1.0):
                self.errors.append(ValidationError(
                    grid_id=grid_id,
                    field=f"density_{species_name}",
                    message="Must be between 0 and 1",
                    value=value
                ))
                valid = False

        return valid

    def validate_batch(
        self,
        grids: List[Grid],
        environments: Optional[List[Environment]] = None,
        densities: Optional[List[SpeciesDensity]] = None
    ) -> bool:
        """
        Validate a batch of data.

        Args:
            grids: List of grids
            environments: Optional list of environments
            densities: Optional list of species densities

        Returns:
            True if all valid, False otherwise
        """
        self.errors.clear()
        valid = True

        for i, grid in enumerate(grids):
            if not self.validate_grid(grid):
                valid = False

            if environments and i < len(environments):
                if not self.validate_environment(environments[i], grid.grid_id):
                    valid = False

            if densities and i < len(densities):
                if not self.validate_density(densities[i], grid.grid_id):
                    valid = False

        # Check list lengths match
        if environments and len(grids) != len(environments):
            self.errors.append(ValidationError(
                grid_id=None,
                field="environments",
                message=f"Length mismatch: {len(grids)} grids vs {len(environments)} environments"
            ))
            valid = False

        if densities and len(grids) != len(densities):
            self.errors.append(ValidationError(
                grid_id=None,
                field="densities",
                message=f"Length mismatch: {len(grids)} grids vs {len(densities)} densities"
            ))
            valid = False

        return valid

    def get_errors(self) -> List[ValidationError]:
        """Get all validation errors."""
        return list(self.errors)

    def clear_errors(self) -> None:
        """Clear all validation errors."""
        self.errors.clear()

    def has_errors(self) -> bool:
        """Check if there are any validation errors."""
        return len(self.errors) > 0

    def print_summary(self) -> None:
        """Print a summary of validation errors."""
        if not self.errors:
            print("✓ All data valid!")
            return

        print(f"Found {len(self.errors)} validation error(s):")
        for error in self.errors[:10]:  # Show first 10
            grid_part = f"[{error.grid_id}] " if error.grid_id else ""
            value_part = f" (value: {error.value})" if error.value is not None else ""
            print(f"  {grid_part}{error.field}: {error.message}{value_part}")

        if len(self.errors) > 10:
            print(f"  ... and {len(self.errors) - 10} more")
