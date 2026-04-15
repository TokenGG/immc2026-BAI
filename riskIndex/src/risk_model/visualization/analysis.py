"""
Analysis and component breakdown visualizations.
"""

from typing import List, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt

from ..risk import GridRiskResult


class AnalysisVisualizer:
    """Visualizes risk component analysis."""

    def __init__(self):
        """Initialize the analysis visualizer."""
        self.component_colors = {
            'human': '#e74c3c',
            'environmental': '#9b59b6',
            'density': '#27ae60',
        }

    def plot_component_breakdown(
        self,
        results: List[GridRiskResult],
        top_n: int = 10,
        title: str = "Risk Component Breakdown (Top High-Risk Grids)",
        figsize: Tuple[int, int] = (12, 6),
        output_path: Optional[str] = None
    ) -> None:
        """
        Plot stacked bar chart of risk components.

        Args:
            results: List of GridRiskResult objects
            top_n: Number of top-risk grids to show
            title: Plot title
            figsize: Figure size
            output_path: Optional path to save the figure
        """
        # Sort by normalized risk
        sorted_results = sorted(results, key=lambda r: r.normalized_risk, reverse=True)[:top_n]

        grid_ids = [r.grid_id for r in sorted_results]
        human_risks = [r.components.human_risk if r.components else 0 for r in sorted_results]
        env_risks = [r.components.environmental_risk if r.components else 0 for r in sorted_results]
        density_risks = [r.components.density_value if r.components else 0 for r in sorted_results]

        x = np.arange(len(grid_ids))
        width = 0.6

        fig, ax = plt.subplots(figsize=figsize)

        ax.bar(x, human_risks, width, label='Human Risk',
               color=self.component_colors['human'], alpha=0.8)
        ax.bar(x, env_risks, width, bottom=human_risks, label='Environmental Risk',
               color=self.component_colors['environmental'], alpha=0.8)
        ax.bar(x, density_risks, width,
               bottom=np.array(human_risks) + np.array(env_risks),
               label='Species Density',
               color=self.component_colors['density'], alpha=0.8)

        ax.set_xlabel('Grid Cell', fontsize=11)
        ax.set_ylabel('Raw Risk Value', fontsize=11)
        ax.set_title(title, fontsize=14, pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(grid_ids, rotation=45)
        ax.legend(fontsize=10, loc='upper right')
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Component breakdown plot saved to: {output_path}")
        else:
            plt.show()

        plt.close(fig)

    def plot_risk_scatter(
        self,
        results: List[GridRiskResult],
        title: str = "Risk Components Scatter Plot",
        figsize: Tuple[int, int] = (14, 5),
        output_path: Optional[str] = None
    ) -> None:
        """
        Create scatter plots comparing risk components.

        Args:
            results: List of GridRiskResult objects
            title: Plot title
            figsize: Figure size
            output_path: Optional path to save the figure
        """
        human_risks = [r.components.human_risk if r.components else 0 for r in results]
        env_risks = [r.components.environmental_risk if r.components else 0 for r in results]
        density_risks = [r.components.density_value if r.components else 0 for r in results]
        total_risks = [r.normalized_risk for r in results]

        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=figsize)

        # Human vs Environmental
        scatter1 = ax1.scatter(human_risks, env_risks, c=total_risks,
                                cmap='RdYlGn_r', s=80, alpha=0.7, edgecolors='black', linewidth=0.5)
        ax1.set_xlabel('Human Risk', fontsize=10)
        ax1.set_ylabel('Environmental Risk', fontsize=10)
        ax1.set_title('Human vs Environmental', fontsize=11)
        ax1.grid(alpha=0.3, linestyle='--')
        plt.colorbar(scatter1, ax=ax1, label='Total Risk')

        # Human vs Density
        scatter2 = ax2.scatter(human_risks, density_risks, c=total_risks,
                                cmap='RdYlGn_r', s=80, alpha=0.7, edgecolors='black', linewidth=0.5)
        ax2.set_xlabel('Human Risk', fontsize=10)
        ax2.set_ylabel('Species Density', fontsize=10)
        ax2.set_title('Human vs Species Density', fontsize=11)
        ax2.grid(alpha=0.3, linestyle='--')
        plt.colorbar(scatter2, ax=ax2, label='Total Risk')

        # Environmental vs Density
        scatter3 = ax3.scatter(env_risks, density_risks, c=total_risks,
                                cmap='RdYlGn_r', s=80, alpha=0.7, edgecolors='black', linewidth=0.5)
        ax3.set_xlabel('Environmental Risk', fontsize=10)
        ax3.set_ylabel('Species Density', fontsize=10)
        ax3.set_title('Environmental vs Species Density', fontsize=11)
        ax3.grid(alpha=0.3, linestyle='--')
        plt.colorbar(scatter3, ax=ax3, label='Total Risk')

        plt.suptitle(title, fontsize=14, y=1.02)
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Scatter plot saved to: {output_path}")
        else:
            plt.show()

        plt.close(fig)
