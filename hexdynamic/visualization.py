import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon, Circle
from typing import Dict, List, Tuple
from grid_model import HexGridModel
from coverage_model import DeploymentSolution


class Visualizer:
    def __init__(self, grid_model: HexGridModel, hex_size: float = 1.0):
        self.grid_model = grid_model
        self.hex_size = hex_size
        self.grid_ids = grid_model.get_all_grid_ids()

    def _get_hex_corners(self, grid_id: int) -> List[Tuple[float, float]]:
        return self.grid_model.get_grid_corners(grid_id, self.hex_size)

    def _get_hex_center(self, grid_id: int) -> Tuple[float, float]:
        return self.grid_model.get_grid_center_coords(grid_id, self.hex_size)

    def plot_risk_heatmap(self, save_path: str = None, show: bool = True):
        fig, ax = plt.subplots(figsize=(12, 10))

        risk_values = {}
        for grid_id in self.grid_ids:
            risk_values[grid_id] = self.grid_model.get_grid_risk(grid_id)

        cmap = matplotlib.colormaps.get_cmap('YlOrRd')

        # 使用统一的 [0, 1] 范围便于跨场景对比
        for grid_id in self.grid_ids:
            corners = self._get_hex_corners(grid_id)
            risk = risk_values[grid_id]
            # 直接使用风险值作为颜色映射（已经是 [0, 1] 范围）
            color = cmap(risk)

            polygon = Polygon(corners, facecolor=color, edgecolor='black', linewidth=0.5, alpha=0.8)
            ax.add_patch(polygon)

        # 使用统一的 [0, 1] 范围的颜色条
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=1))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, shrink=0.8)
        cbar.set_label('Normalized Risk [0, 1]', fontsize=12)

        ax.set_aspect('equal')
        ax.set_title('Risk Heatmap (Normalized)', fontsize=16, fontweight='bold')
        ax.set_xlabel('X Coordinate', fontsize=12)
        ax.set_ylabel('Y Coordinate', fontsize=12)
        ax.grid(True, alpha=0.3)

        bounds = self.grid_model.get_grid_bounds(self.hex_size)
        ax.set_xlim(bounds[0] - 1, bounds[1] + 1)
        ax.set_ylim(bounds[2] - 1, bounds[3] + 1)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Risk heatmap saved to {save_path}")

        if show:
            plt.show()
        else:
            plt.close()

    def plot_deployment_map(self, solution: DeploymentSolution, save_path: str = None, show: bool = True):
        fig, ax = plt.subplots(figsize=(14, 12))

        terrain_colors = {
            'SaltMarsh': '#E8DCC4',
            'SparseGrass': '#90EE90',
            'DenseGrass': '#228B22',
            'WaterHole': '#87CEEB',
            'Road': '#808080'
        }

        for grid_id in self.grid_ids:
            corners = self._get_hex_corners(grid_id)
            terrain = self.grid_model.get_grid_terrain(grid_id)
            color = terrain_colors.get(terrain, '#FFFFFF')

            polygon = Polygon(corners, facecolor=color, edgecolor='black', linewidth=0.5, alpha=0.7)
            ax.add_patch(polygon)

        for grid_id in solution.cameras.keys():
            center = self._get_hex_center(grid_id)
            circle = Circle(center, radius=self.hex_size * 0.4, color='red', alpha=0.8, zorder=10)
            ax.add_patch(circle)
            ax.text(center[0], center[1], 'C', ha='center', va='center', 
                   fontsize=10, fontweight='bold', color='white', zorder=11)

        for grid_id in solution.drones.keys():
            center = self._get_hex_center(grid_id)
            circle = Circle(center, radius=self.hex_size * 0.4, color='blue', alpha=0.8, zorder=10)
            ax.add_patch(circle)
            ax.text(center[0], center[1], 'D', ha='center', va='center', 
                   fontsize=10, fontweight='bold', color='white', zorder=11)

        for grid_id in solution.camps.keys():
            center = self._get_hex_center(grid_id)
            circle = Circle(center, radius=self.hex_size * 0.5, color='green', alpha=0.8, zorder=10)
            ax.add_patch(circle)
            rangers = solution.rangers.get(grid_id, 0)
            ax.text(center[0], center[1], f'S\n{rangers}', ha='center', va='center', 
                   fontsize=8, fontweight='bold', color='white', zorder=11)

        for edge_key in solution.fences.keys():
            grid_id1, grid_id2 = edge_key
            center1 = self._get_hex_center(grid_id1)
            center2 = self._get_hex_center(grid_id2)

            mid_x = (center1[0] + center2[0]) / 2
            mid_y = (center1[1] + center2[1]) / 2

            ax.plot([center1[0], center2[0]], [center1[1], center2[1]], 
                   color='orange', linewidth=3, alpha=0.8, zorder=5)

        legend_elements = [
            patches.Patch(color='red', label='Camera (C)'),
            patches.Patch(color='blue', label='Drone (D)'),
            patches.Patch(color='green', label='Camp (S)'),
            patches.Patch(color='orange', label='Fence'),
            patches.Patch(color='#E8DCC4', label='Salt Marsh'),
            patches.Patch(color='#90EE90', label='Sparse Grass'),
            patches.Patch(color='#228B22', label='Dense Grass'),
            patches.Patch(color='#87CEEB', label='Water Hole'),
            patches.Patch(color='#808080', label='Road')
        ]

        ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=10)

        ax.set_aspect('equal')
        ax.set_title('Resource Deployment Map', fontsize=16, fontweight='bold')
        ax.set_xlabel('X Coordinate', fontsize=12)
        ax.set_ylabel('Y Coordinate', fontsize=12)
        ax.grid(True, alpha=0.3)

        bounds = self.grid_model.get_grid_bounds(self.hex_size)
        ax.set_xlim(bounds[0] - 1, bounds[1] + 1)
        ax.set_ylim(bounds[2] - 1, bounds[3] + 1)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Deployment map saved to {save_path}")

        if show:
            plt.show()
        else:
            plt.close()

    def plot_convergence_curve(self, fitness_history: List[float], save_path: str = None, show: bool = True):
        fig, ax = plt.subplots(figsize=(10, 6))

        iterations = range(len(fitness_history))
        ax.plot(iterations, fitness_history, 'b-', linewidth=2, label='Best Fitness')

        ax.set_xlabel('Iteration', fontsize=12)
        ax.set_ylabel('Fitness Value', fontsize=12)
        ax.set_title('DSSA Convergence Curve', fontsize=16, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Convergence curve saved to {save_path}")

        if show:
            plt.show()
        else:
            plt.close()

    def plot_protection_coverage(self, solution: DeploymentSolution, coverage_model, 
                                 save_path: str = None, show: bool = True):
        fig, axes = plt.subplots(2, 2, figsize=(16, 14))

        patrol_cov = coverage_model.calculate_patrol_coverage(solution)
        drone_cov = coverage_model.calculate_drone_coverage(solution)
        camera_cov = coverage_model.calculate_camera_coverage(solution)
        fence_prot = coverage_model.calculate_fencing_edges()

        coverage_types = [
            ('Patrol Coverage', patrol_cov, 'Greens'),
            ('Drone Coverage', drone_cov, 'Blues'),
            ('Camera Coverage', camera_cov, 'Reds'),
            ('Fence Protection', fence_prot, 'Oranges')
        ]

        for idx, (title, coverage_dict, cmap_name) in enumerate(coverage_types):
            ax = axes[idx // 2, idx % 2]

            cmap = matplotlib.colormaps.get_cmap(cmap_name)

            for grid_id in self.grid_ids:
                corners = self._get_hex_corners(grid_id)
                value = coverage_dict.get(grid_id, 0.0)
                color = cmap(value)

                polygon = Polygon(corners, facecolor=color, edgecolor='black', linewidth=0.5, alpha=0.8)
                ax.add_patch(polygon)

            sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=1))
            sm.set_array([])
            cbar = plt.colorbar(sm, ax=ax, shrink=0.8)
            cbar.set_label('Coverage Level', fontsize=10)

            ax.set_aspect('equal')
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xlabel('X Coordinate', fontsize=10)
            ax.set_ylabel('Y Coordinate', fontsize=10)
            ax.grid(True, alpha=0.3)

            bounds = self.grid_model.get_grid_bounds(self.hex_size)
            ax.set_xlim(bounds[0] - 1, bounds[1] + 1)
            ax.set_ylim(bounds[2] - 1, bounds[3] + 1)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Protection coverage plot saved to {save_path}")

        if show:
            plt.show()
        else:
            plt.close()

    def plot_terrain_map(self, save_path: str = None, show: bool = True):
        fig, ax = plt.subplots(figsize=(12, 10))

        terrain_colors = {
            'SaltMarsh': '#E8DCC4',
            'SparseGrass': '#90EE90',
            'DenseGrass': '#228B22',
            'WaterHole': '#87CEEB',
            'Road': '#808080'
        }

        for grid_id in self.grid_ids:
            corners = self._get_hex_corners(grid_id)
            terrain = self.grid_model.get_grid_terrain(grid_id)
            color = terrain_colors.get(terrain, '#FFFFFF')

            polygon = Polygon(corners, facecolor=color, edgecolor='black', linewidth=0.5, alpha=0.8)
            ax.add_patch(polygon)

        legend_elements = [
            patches.Patch(color='#E8DCC4', label='Salt Marsh'),
            patches.Patch(color='#90EE90', label='Sparse Grass'),
            patches.Patch(color='#228B22', label='Dense Grass'),
            patches.Patch(color='#87CEEB', label='Water Hole'),
            patches.Patch(color='#808080', label='Road')
        ]

        ax.legend(handles=legend_elements, loc='upper right', fontsize=10)

        ax.set_aspect('equal')
        ax.set_title('Terrain Map', fontsize=16, fontweight='bold')
        ax.set_xlabel('X Coordinate', fontsize=12)
        ax.set_ylabel('Y Coordinate', fontsize=12)
        ax.grid(True, alpha=0.3)

        bounds = self.grid_model.get_grid_bounds(self.hex_size)
        ax.set_xlim(bounds[0] - 1, bounds[1] + 1)
        ax.set_ylim(bounds[2] - 1, bounds[3] + 1)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Terrain map saved to {save_path}")

        if show:
            plt.show()
        else:
            plt.close()
