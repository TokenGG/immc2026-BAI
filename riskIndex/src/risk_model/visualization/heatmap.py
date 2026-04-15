"""
Risk heatmap visualization.
"""

from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from ..core import Grid


class RiskHeatmap:
    """Generates risk heatmap visualizations."""

    def __init__(self):
        """Initialize the heatmap generator."""
        # Create a custom colormap: green -> yellow -> red
        colors = [
            (0.0, '#00aa00'),   # Green - low risk
            (0.5, '#ffff00'),   # Yellow - medium risk
            (1.0, '#ff0000')    # Red - high risk
        ]
        self.cmap = LinearSegmentedColormap.from_list('risk_gradient', colors)

    def plot_heatmap(
        self,
        grids: List[Grid],
        risk_values: List[float],
        grid_width: int,
        grid_height: int,
        title: str = "Risk Heatmap",
        show_grid_labels: bool = True,
        figsize: Tuple[int, int] = (10, 8),
        output_path: Optional[str] = None
    ) -> None:
        """
        Plot a risk heatmap.

        Args:
            grids: List of Grid objects
            risk_values: List of normalized risk values [0, 1]
            grid_width: Number of grid columns
            grid_height: Number of grid rows
            title: Plot title
            show_grid_labels: Whether to show grid IDs
            figsize: Figure size
            output_path: Optional path to save the figure
        """
        # Create 2D array for heatmap
        risk_grid = np.zeros((grid_height, grid_width))
        grid_labels = [['' for _ in range(grid_width)] for _ in range(grid_height)]

        for grid, risk in zip(grids, risk_values):
            # Parse grid ID (format: "A01")
            row = ord(grid.grid_id[0]) - ord('A')
            col = int(grid.grid_id[1:])

            if 0 <= row < grid_height and 0 <= col < grid_width:
                risk_grid[row, col] = risk
                grid_labels[row][col] = grid.grid_id

        # Create plot
        fig, ax = plt.subplots(figsize=figsize)

        # Plot heatmap
        im = ax.imshow(risk_grid, cmap=self.cmap, vmin=0, vmax=1, aspect='equal')

        # Add grid labels
        if show_grid_labels:
            for i in range(grid_height):
                for j in range(grid_width):
                    if grid_labels[i][j]:
                        text_color = 'white' if risk_grid[i, j] > 0.5 else 'black'
                        ax.text(j, i, grid_labels[i][j],
                                ha='center', va='center',
                                color=text_color, fontsize=8)

        # Customize ticks
        ax.set_xticks(range(grid_width))
        ax.set_yticks(range(grid_height))
        ax.set_xticklabels([f"{i:02d}" for i in range(grid_width)])
        ax.set_yticklabels([chr(ord('A') + i) for i in range(grid_height)])

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Normalized Risk', rotation=270, labelpad=15)

        ax.set_title(title, fontsize=14, pad=20)
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Heatmap saved to: {output_path}")
        else:
            plt.show()

        plt.close(fig)

    def plot_risk_distribution(
        self,
        risk_values: List[float],
        title: str = "Risk Distribution",
        figsize: Tuple[int, int] = (10, 5),
        output_path: Optional[str] = None
    ) -> None:
        """
        Plot histogram of risk distribution.

        Args:
            risk_values: List of normalized risk values
            title: Plot title
            figsize: Figure size
            output_path: Optional path to save the figure
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

        # Histogram
        ax1.hist(risk_values, bins=20, range=(0, 1), color='steelblue', edgecolor='black', alpha=0.7)
        ax1.set_xlabel('Normalized Risk', fontsize=11)
        ax1.set_ylabel('Number of Grids', fontsize=11)
        ax1.set_title('Risk Distribution Histogram', fontsize=12)
        ax1.grid(alpha=0.3, linestyle='--')

        # Box plot
        ax2.boxplot(risk_values, vert=True)
        ax2.set_ylabel('Normalized Risk', fontsize=11)
        ax2.set_title('Risk Box Plot', fontsize=12)
        ax2.set_ylim(-0.05, 1.05)
        ax2.grid(alpha=0.3, linestyle='--')

        # Statistics text
        stats_text = f"Statistics:\n"
        stats_text += f"  Mean: {np.mean(risk_values):.3f}\n"
        stats_text += f"  Median: {np.median(risk_values):.3f}\n"
        stats_text += f"  Std: {np.std(risk_values):.3f}\n"
        stats_text += f"  Min: {np.min(risk_values):.3f}\n"
        stats_text += f"  Max: {np.max(risk_values):.3f}"

        ax2.text(1.3, 0.5, stats_text, transform=ax2.transAxes,
                 verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.suptitle(title, fontsize=14, y=1.02)
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Risk distribution plot saved to: {output_path}")
        else:
            plt.show()

        plt.close(fig)
