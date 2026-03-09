import numpy as np
from typing import List, Tuple, Dict
from dataclasses import dataclass
from data_loader import GridData


@dataclass
class HexCoordinates:
    q: int
    r: int
    s: int

    def __post_init__(self):
        self.s = -self.q - self.r


class HexGridModel:
    def __init__(self, grids: List[GridData]):
        self.grids = grids
        self.grid_dict = {grid.grid_id: grid for grid in grids}
        self.adjacency_matrix = self._build_adjacency_matrix()
        self.distance_matrix = self._build_distance_matrix()

    def _build_adjacency_matrix(self) -> Dict[int, List[int]]:
        adjacency = {}
        directions = [
            (1, 0), (1, -1), (0, -1),
            (-1, 0), (-1, 1), (0, 1)
        ]

        for grid in self.grids:
            neighbors = []
            for dq, dr in directions:
                neighbor_q = grid.q + dq
                neighbor_r = grid.r + dr
                neighbor_grid = self._find_grid_by_coords(neighbor_q, neighbor_r)
                if neighbor_grid:
                    neighbors.append(neighbor_grid.grid_id)
            adjacency[grid.grid_id] = neighbors

        return adjacency

    def _build_distance_matrix(self) -> np.ndarray:
        n = len(self.grids)
        distance_matrix = np.zeros((n, n))

        for i, grid_i in enumerate(self.grids):
            for j, grid_j in enumerate(self.grids):
                distance_matrix[i][j] = self.hex_distance(grid_i, grid_j)

        return distance_matrix

    def _find_grid_by_coords(self, q: int, r: int) -> GridData:
        for grid in self.grids:
            if grid.q == q and grid.r == r:
                return grid
        return None

    @staticmethod
    def hex_distance(grid1: GridData, grid2: GridData) -> int:
        return (abs(grid1.q - grid2.q) + 
                abs(grid1.q + grid1.r - grid2.q - grid2.r) + 
                abs(grid1.r - grid2.r)) // 2

    def get_distance(self, grid_id1: int, grid_id2: int) -> int:
        if grid_id1 not in self.grid_dict or grid_id2 not in self.grid_dict:
            return float('inf')
        grid1 = self.grid_dict[grid_id1]
        grid2 = self.grid_dict[grid_id2]
        return self.hex_distance(grid1, grid2)

    def get_neighbors(self, grid_id: int) -> List[int]:
        return self.adjacency_matrix.get(grid_id, [])

    def get_all_grid_ids(self) -> List[int]:
        return list(self.grid_dict.keys())

    def get_grid_by_id(self, grid_id: int) -> GridData:
        return self.grid_dict.get(grid_id, None)

    def get_grid_center_coords(self, grid_id: int, hex_size: float = 1.0) -> Tuple[float, float]:
        """获取六边形网格中心坐标，确保网格紧密嵌合"""
        grid = self.get_grid_by_id(grid_id)
        if not grid:
            return (0.0, 0.0)

        # 使用even-r offset坐标系统计算笛卡尔坐标
        # 对于pointy-topped六边形
        # col = q + floor(r/2)
        # row = r
        # x = hex_size * sqrt(3) * (col + 0.5 * (row & 1))
        # y = hex_size * 3/2 * row
        
        col = grid.q + (grid.r // 2)
        row = grid.r
        
        x = hex_size * np.sqrt(3) * (col + 0.5 * (row & 1))
        y = hex_size * 3/2 * row
        return (x, y)

    def get_grid_corners(self, grid_id: int, hex_size: float = 1.0) -> List[Tuple[float, float]]:
        """获取六边形网格的六个角点坐标"""
        center_x, center_y = self.get_grid_center_coords(grid_id, hex_size)
        corners = []
        for i in range(6):
            # 对于pointy-topped六边形，从30度开始
            angle_deg = 60 * i + 30
            angle_rad = np.pi / 180 * angle_deg
            corner_x = center_x + hex_size * np.cos(angle_rad)
            corner_y = center_y + hex_size * np.sin(angle_rad)
            corners.append((corner_x, corner_y))
        return corners

    def get_boundary_edges(self) -> List[Tuple[int, int, float]]:
        boundary_edges = []
        grid_ids = self.get_all_grid_ids()

        for grid_id in grid_ids:
            neighbors = self.get_neighbors(grid_id)
            for neighbor_id in neighbors:
                if grid_id < neighbor_id:
                    boundary_edges.append((grid_id, neighbor_id, 1.0))

        return boundary_edges

    def get_fencing_edges(self) -> List[Tuple[int, int, float]]:
        return self.get_boundary_edges()

    def get_grid_risk(self, grid_id: int) -> float:
        grid = self.get_grid_by_id(grid_id)
        return grid.risk if grid else 0.0

    def get_grid_terrain(self, grid_id: int) -> str:
        grid = self.get_grid_by_id(grid_id)
        return grid.terrain_type if grid else 'Unknown'

    def get_grids_by_terrain(self, terrain_type: str) -> List[int]:
        return [grid.grid_id for grid in self.grids if grid.terrain_type == terrain_type]

    def get_high_risk_grids(self, threshold: float = 0.7) -> List[int]:
        return [grid.grid_id for grid in self.grids if grid.risk >= threshold]

    def get_edge_grids(self) -> List[int]:
        """获取地图边缘的网格ID列表
        
        边缘网格定义为：
        1. 邻居数量少于6的网格（边界网格）
        2. 位于矩形地图边界的网格
        """
        edge_grids = []
        
        # 获取网格的行列范围
        rows = set()
        cols = set()
        grid_info = {}  # grid_id -> (row, col)
        
        for grid in self.grids:
            row = grid.r
            col = grid.q + (row // 2)  # 从轴坐标转换回行列坐标
            rows.add(row)
            cols.add(col)
            grid_info[grid.grid_id] = (row, col)
        
        min_row, max_row = min(rows), max(rows)
        min_col, max_col = min(cols), max(cols)
        
        for grid_id, (row, col) in grid_info.items():
            # 检查是否为边缘网格
            is_edge = False
            
            # 1. 邻居数量少于6（边界网格）
            neighbors = self.get_neighbors(grid_id)
            if len(neighbors) < 6:
                is_edge = True
            
            # 2. 位于矩形地图边界
            if row == min_row or row == max_row or col == min_col or col == max_col:
                is_edge = True
            
            if is_edge:
                edge_grids.append(grid_id)
        
        return sorted(edge_grids)

    def get_grid_bounds(self, hex_size: float = 1.0) -> Tuple[float, float, float, float]:
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')

        for grid_id in self.get_all_grid_ids():
            corners = self.get_grid_corners(grid_id, hex_size)
            for x, y in corners:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

        return (min_x, max_x, min_y, max_y)

    def get_grid_count(self) -> int:
        return len(self.grids)

    def get_distance_matrix(self) -> np.ndarray:
        return self.distance_matrix

    def get_adjacency_matrix(self) -> Dict[int, List[int]]:
        return self.adjacency_matrix
