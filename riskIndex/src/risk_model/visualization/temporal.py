"""
Temporal visualization for risk comparison.
"""

from typing import List, Dict, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt

from ..core import Grid, TimeContext, Season
from ..risk import RiskModel


class TemporalVisualizer:
    """Visualizes temporal variations in risk."""

    def __init__(self):
        """Initialize the temporal visualizer."""
        self.colors = {
            'night_rainy': '#c41e3a',
            'night_dry': '#ff6b6b',
            'day_rainy': '#4ecdc4',
            'day_dry': '#45b7d1',
        }

    def compare_day_night(
        self,
        grids: List[Grid],
        environments: List,
        densities: List,
        model: RiskModel,
        season: Season = Season.RAINY,
        selected_grids: Optional[List[str]] = None,
        title: str = "Day vs Night Risk Comparison",
        figsize: Tuple[int, int] = (12, 6),
        output_path: Optional[str] = None
    ) -> None:
        """
        Compare risk between day and night.

        Args:
            grids: List of Grid objects
            environments: List of Environment objects
            densities: List of SpeciesDensity objects
            model: RiskModel instance
            season: Season to use for comparison
            selected_grids: Optional list of grid IDs to highlight
            title: Plot title
            figsize: Figure size
            output_path: Optional path to save the figure
        """
        # Calculate risks for day and night
        grid_data = list(zip(grids, environments, densities))

        day_ctx = TimeContext(hour_of_day=10, season=season)
        night_ctx = TimeContext(hour_of_day=22, season=season)

        day_results = model.calculate_batch(grid_data, day_ctx)
        night_results = model.calculate_batch(grid_data, night_ctx)

        day_risks = [r.normalized_risk for r in day_results]
        night_risks = [r.normalized_risk for r in night_results]
        grid_ids = [r.grid_id for r in day_results]

        # Create plot
        fig, ax = plt.subplots(figsize=figsize)

        x = np.arange(len(grid_ids))
        width = 0.35

        ax.bar(x - width/2, day_risks, width, label='Day (10:00)', color=self.colors['day_dry'], alpha=0.8)
        ax.bar(x + width/2, night_risks, width, label='Night (22:00)', color=self.colors['night_dry'], alpha=0.8)

        # Highlight selected grids
        if selected_grids:
            for i, grid_id in enumerate(grid_ids):
                if grid_id in selected_grids:
                    ax.plot([i - width/2, i - width/2], [0, day_risks[i]],
                            color='gold', linewidth=3, zorder=5)
                    ax.plot([i + width/2, i + width/2], [0, night_risks[i]],
                            color='gold', linewidth=3, zorder=5)

        ax.set_xlabel('Grid Cell', fontsize=11)
        ax.set_ylabel('Normalized Risk', fontsize=11)
        ax.set_title(title, fontsize=14, pad=20)
        ax.set_xticks(x[::max(1, len(grid_ids) // 10)])
        ax.set_xticklabels(grid_ids[::max(1, len(grid_ids) // 10)], rotation=45)
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=10)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        # Add average lines
        ax.axhline(y=np.mean(day_risks), color=self.colors['day_dry'],
                   linestyle='--', alpha=0.7, label=f'Day Avg: {np.mean(day_risks):.3f}')
        ax.axhline(y=np.mean(night_risks), color=self.colors['night_dry'],
                   linestyle='--', alpha=0.7, label=f'Night Avg: {np.mean(night_risks):.3f}')
        ax.legend(fontsize=10, loc='upper right')

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Day/night comparison plot saved to: {output_path}")
        else:
            plt.show()

        plt.close(fig)

    def compare_seasons(
        self,
        grids: List[Grid],
        environments: List,
        densities: List,
        model: RiskModel,
        hour: int = 22,
        title: str = "Dry vs Rainy Season Risk Comparison",
        figsize: Tuple[int, int] = (12, 6),
        output_path: Optional[str] = None
    ) -> None:
        """
        Compare risk between dry and rainy seasons.

        Args:
            grids: List of Grid objects
            environments: List of Environment objects
            densities: List of SpeciesDensity objects
            model: RiskModel instance
            hour: Hour of day to use for comparison
            title: Plot title
            figsize: Figure size
            output_path: Optional path to save the figure
        """
        grid_data = list(zip(grids, environments, densities))

        dry_ctx = TimeContext(hour_of_day=hour, season=Season.DRY)
        rainy_ctx = TimeContext(hour_of_day=hour, season=Season.RAINY)

        dry_results = model.calculate_batch(grid_data, dry_ctx)
        rainy_results = model.calculate_batch(grid_data, rainy_ctx)

        dry_risks = [r.normalized_risk for r in dry_results]
        rainy_risks = [r.normalized_risk for r in rainy_results]
        grid_ids = [r.grid_id for r in dry_results]

        # Create plot
        fig, ax = plt.subplots(figsize=figsize)

        x = np.arange(len(grid_ids))
        width = 0.35

        ax.bar(x - width/2, dry_risks, width, label='Dry Season', color='#f4a460', alpha=0.8)
        ax.bar(x + width/2, rainy_risks, width, label='Rainy Season', color='#4682b4', alpha=0.8)

        ax.set_xlabel('Grid Cell', fontsize=11)
        ax.set_ylabel('Normalized Risk', fontsize=11)
        ax.set_title(title, fontsize=14, pad=20)
        ax.set_xticks(x[::max(1, len(grid_ids) // 10)])
        ax.set_xticklabels(grid_ids[::max(1, len(grid_ids) // 10)], rotation=45)
        ax.set_ylim(0, 1.05)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        ax.axhline(y=np.mean(dry_risks), color='#f4a460',
                   linestyle='--', alpha=0.7, label=f'Dry Avg: {np.mean(dry_risks):.3f}')
        ax.axhline(y=np.mean(rainy_risks), color='#4682b4',
                   linestyle='--', alpha=0.7, label=f'Rainy Avg: {np.mean(rainy_risks):.3f}')
        ax.legend(fontsize=10, loc='upper right')

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Season comparison plot saved to: {output_path}")
        else:
            plt.show()

        plt.close(fig)
