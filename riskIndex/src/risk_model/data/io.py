"""
Input/output handlers for the risk model.
"""

import csv
import json
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

from ..core import (
    Grid,
    SpeciesDensity,
    Environment,
    VegetationType,
    Season,
)


class GridDataWriter:
    """Writes grid and risk data to various formats."""

    @staticmethod
    def write_grids_to_csv(
        grids: List[Grid],
        filepath: str,
        environments: Optional[List[Environment]] = None,
        densities: Optional[List[SpeciesDensity]] = None,
        risk_results: Optional[List[Any]] = None
    ) -> None:
        """
        Write grid data to CSV file.

        Args:
            grids: List of Grid objects
            filepath: Output file path
            environments: Optional list of Environment objects
            densities: Optional list of SpeciesDensity objects
            risk_results: Optional list of risk result objects
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        # Build header
        header = [
            "grid_id", "x", "y",
            "distance_to_boundary", "distance_to_road", "distance_to_water"
        ]

        if environments:
            header.extend(["fire_risk", "terrain_complexity", "vegetation_type"])

        if densities:
            # Get all species names from first density
            if densities:
                species_names = list(densities[0].densities.keys())
                header.extend([f"density_{name}" for name in species_names])

        if risk_results:
            header.extend(["raw_risk", "normalized_risk"])

        rows = []
        for i, grid in enumerate(grids):
            row = [
                grid.grid_id,
                grid.x,
                grid.y,
                grid.distance_to_boundary,
                grid.distance_to_road,
                grid.distance_to_water
            ]

            if environments and i < len(environments):
                env = environments[i]
                row.extend([
                    env.fire_risk,
                    env.terrain_complexity,
                    env.vegetation_type.value
                ])

            if densities and i < len(densities):
                dens = densities[i]
                for species_name in species_names:
                    row.append(dens.densities.get(species_name, 0.0))

            if risk_results and i < len(risk_results):
                result = risk_results[i]
                row.extend([
                    result.raw_risk,
                    result.normalized_risk if result.normalized_risk is not None else ""
                ])

            rows.append(row)

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

    @staticmethod
    def write_risk_summary_to_json(
        risk_results: List[Any],
        filepath: str
    ) -> None:
        """
        Write risk summary to JSON file.

        Args:
            risk_results: List of risk result objects
            filepath: Output file path
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        results_dict = {
            "summary": {
                "total_grids": len(risk_results),
                "high_risk_count": sum(1 for r in risk_results if r.normalized_risk and r.normalized_risk > 0.7),
                "medium_risk_count": sum(1 for r in risk_results if r.normalized_risk and 0.3 <= r.normalized_risk <= 0.7),
                "low_risk_count": sum(1 for r in risk_results if r.normalized_risk and r.normalized_risk < 0.3),
            },
            "grids": [
                {
                    "grid_id": r.grid_id,
                    "raw_risk": r.raw_risk,
                    "normalized_risk": r.normalized_risk,
                    "components": {
                        "human_risk": r.components.human_risk,
                        "environmental_risk": r.components.environmental_risk,
                        "density_value": r.components.density_value,
                        "temporal_factor": r.components.temporal_factor,
                    } if r.components else None
                }
                for r in risk_results
            ]
        }

        with open(filepath, 'w') as f:
            json.dump(results_dict, f, indent=2)


class GridDataReader:
    """Reads grid data from various formats."""

    @staticmethod
    def read_grids_from_csv(filepath: str) -> Tuple[List[Grid], List[Environment], List[SpeciesDensity]]:
        """
        Read grid data from CSV file.

        Args:
            filepath: Input CSV file path

        Returns:
            Tuple of (grids, environments, species_densities)
        """
        grids = []
        environments = []
        densities = []

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Read grid
                grid = Grid(
                    grid_id=row["grid_id"],
                    x=float(row["x"]),
                    y=float(row["y"]),
                    distance_to_boundary=float(row["distance_to_boundary"]),
                    distance_to_road=float(row["distance_to_road"]),
                    distance_to_water=float(row["distance_to_water"])
                )
                grids.append(grid)

                # Read environment if available
                if "fire_risk" in row:
                    env = Environment(
                        fire_risk=float(row["fire_risk"]),
                        terrain_complexity=float(row["terrain_complexity"]),
                        vegetation_type=VegetationType(row["vegetation_type"])
                    )
                    environments.append(env)

                # Read densities if available
                density_dict = {}
                for key, value in row.items():
                    if key.startswith("density_"):
                        species_name = key[len("density_"):]
                        density_dict[species_name] = float(value)
                if density_dict:
                    densities.append(SpeciesDensity(densities=density_dict))

        return grids, environments, densities
