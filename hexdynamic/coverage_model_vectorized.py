"""
coverage_model_vectorized.py

CoverageModel 的向量化实现，用 NumPy 矩阵运算替代 Python 循环。
适合网格数量较大（千级以上）的场景，可显著降低 evaluate_fitness 的耗时。

与原始 CoverageModel 接口完全兼容，通过 protection_pipeline.py 的
--vectorized 参数启用。
"""

import numpy as np
from typing import Dict, List, Tuple

from grid_model import HexGridModel
from data_loader import CoverageParameters
from coverage_model import CoverageModel, DeploymentSolution


class VectorizedCoverageModel(CoverageModel):
    """
    向量化覆盖模型。

    初始化时预计算以下 NumPy 数组，避免在每次 evaluate_fitness 时重复构建：
      - dist_matrix : (N, N) 网格间距离矩阵（已在 HexGridModel 中预计算）
      - risk_vec    : (N,)   各网格风险值
      - deploy_*    : (N,)   各资源的部署可行性掩码
      - visibility_drone/camera : (N,) 可见度向量
    """

    def __init__(self, grid_model: HexGridModel, coverage_params: CoverageParameters,
                 deployment_matrix: Dict[str, Dict[int, int]],
                 visibility_params: Dict[int, Dict[str, float]]):
        super().__init__(grid_model, coverage_params, deployment_matrix, visibility_params)

        # grid_ids 顺序固定，建立 id → index 映射
        self._id_to_idx: Dict[int, int] = {gid: i for i, gid in enumerate(self.grid_ids)}
        N = len(self.grid_ids)

        # 距离矩阵（已在 HexGridModel 预计算，直接引用）
        self._dist: np.ndarray = grid_model.distance_matrix  # (N, N)

        # 风险向量
        self._risk_vec = np.array(
            [grid_model.get_grid_risk(gid) for gid in self.grid_ids], dtype=np.float64
        )
        self._total_risk = float(self._risk_vec.sum())

        # 部署可行性掩码
        self._deploy_patrol = np.array(
            [deployment_matrix['patrol'][gid] for gid in self.grid_ids], dtype=np.float64
        )
        self._deploy_drone = np.array(
            [deployment_matrix['drone'][gid] for gid in self.grid_ids], dtype=np.float64
        )
        self._deploy_camera = np.array(
            [deployment_matrix['camera'][gid] for gid in self.grid_ids], dtype=np.float64
        )
        self._deploy_fence = np.array(
            [deployment_matrix['fence'][gid] for gid in self.grid_ids], dtype=np.float64
        )

        # 可见度向量
        self._vis_drone = np.array(
            [visibility_params[gid]['drone'] for gid in self.grid_ids], dtype=np.float64
        )
        self._vis_camera = np.array(
            [visibility_params[gid]['camera'] for gid in self.grid_ids], dtype=np.float64
        )

        # 邻接矩阵（稀疏，用于围栏计算）
        # adj[i, j] = 1 表示 grid_ids[i] 和 grid_ids[j] 相邻
        self._adj = np.zeros((N, N), dtype=np.float64)
        for i, gid in enumerate(self.grid_ids):
            for nb in grid_model.get_neighbors(gid):
                j = self._id_to_idx[nb]
                self._adj[i, j] = 1.0

    # ------------------------------------------------------------------
    # 内部辅助：把解转换为 NumPy 索引数组
    # ------------------------------------------------------------------

    def _ranger_vec(self, solution: DeploymentSolution) -> np.ndarray:
        """返回 (N,) 巡逻强度向量（含营地人员 + 直接部署人员）"""
        vec = np.zeros(len(self.grid_ids), dtype=np.float64)
        for gid, cnt in solution.rangers.items():
            if cnt > 0:
                idx = self._id_to_idx.get(gid)
                if idx is not None:
                    vec[idx] += cnt
        return vec

    def _resource_indices(self, resource_dict: Dict[int, int]) -> np.ndarray:
        """返回部署了该资源的格子在 grid_ids 中的索引数组"""
        return np.array(
            [self._id_to_idx[gid] for gid, v in resource_dict.items()
             if v > 0 and gid in self._id_to_idx],
            dtype=np.int64
        )

    def _fence_vec(self, solution: DeploymentSolution) -> np.ndarray:
        """返回 (N,) 围栏段数向量：fence_vec[i] = 格子 i 相邻的围栏段数"""
        N = len(self.grid_ids)
        fence_mat = np.zeros((N, N), dtype=np.float64)
        for (gid1, gid2), v in solution.fences.items():
            if v > 0:
                i = self._id_to_idx.get(gid1)
                j = self._id_to_idx.get(gid2)
                if i is not None and j is not None:
                    fence_mat[i, j] = 1.0
                    fence_mat[j, i] = 1.0
        # 每个格子相邻的围栏段数 = 该行之和
        return fence_mat.sum(axis=1)

    # ------------------------------------------------------------------
    # 向量化覆盖计算
    # ------------------------------------------------------------------

    def calculate_patrol_coverage(self, solution: DeploymentSolution) -> Dict[int, float]:
        ranger_vec = self._ranger_vec(solution)   # (N,) 各格巡逻强度
        active = np.where(ranger_vec > 0)[0]      # 有巡逻员的格子索引

        if len(active) == 0:
            return {gid: 0.0 for gid in self.grid_ids}

        # dist[:, active] shape (N, K)，K = 有巡逻员的格子数
        dists = self._dist[:, active]             # (N, K)
        weights = ranger_vec[active]              # (K,)
        # intensity[i] = Σ_k weights[k] * exp(-dist[i,k] / patrol_radius)
        intensity = (np.exp(-dists / self.params.patrol_radius) * weights).sum(axis=1)  # (N,)
        intensity *= self._deploy_patrol          # 不可巡逻的格子强制为 0
        coverage = 1.0 - np.exp(-intensity)

        return {gid: float(coverage[i]) for i, gid in enumerate(self.grid_ids)}

    def calculate_drone_coverage(self, solution: DeploymentSolution) -> Dict[int, float]:
        drone_idx = self._resource_indices(solution.drones)

        if len(drone_idx) == 0:
            return {gid: 0.0 for gid in self.grid_ids}

        # 每个格子有自己的 effective_radius（受可见度影响）
        eff_radius = self.params.drone_radius * self._vis_drone  # (N,)

        dists = self._dist[:, drone_idx]          # (N, K)
        # 对每个格子 i，用其自身的 eff_radius[i] 计算衰减
        # exp(-dists / eff_radius[:, None])，shape (N, K)
        eff_r = eff_radius[:, None]               # (N, 1) broadcast
        within = dists <= eff_r * 2               # 距离截断掩码
        coverage = (np.exp(-dists / np.where(eff_r > 0, eff_r, 1.0)) * within).sum(axis=1)
        coverage = np.minimum(1.0, coverage) * self._deploy_drone

        return {gid: float(coverage[i]) for i, gid in enumerate(self.grid_ids)}

    def calculate_camera_coverage(self, solution: DeploymentSolution) -> Dict[int, float]:
        # 建立摄像头数量向量 (N,)
        cam_vec = np.zeros(len(self.grid_ids), dtype=np.float64)
        for gid, cnt in solution.cameras.items():
            if cnt > 0:
                idx = self._id_to_idx.get(gid)
                if idx is not None:
                    cam_vec[idx] = cnt
        active = np.where(cam_vec > 0)[0]

        if len(active) == 0:
            return {gid: 0.0 for gid in self.grid_ids}

        eff_radius = self.params.camera_radius * self._vis_camera  # (N,)
        dists = self._dist[:, active]            # (N, K)
        weights = cam_vec[active]                # (K,) 数量权重
        eff_r = eff_radius[:, None]
        within = dists <= eff_r * 2
        coverage = (np.exp(-dists / np.where(eff_r > 0, eff_r, 1.0)) * within * weights).sum(axis=1)
        coverage = np.minimum(1.0, coverage) * self._deploy_camera

        return {gid: float(coverage[i]) for i, gid in enumerate(self.grid_ids)}

    def calculate_fence_protection(self, solution: DeploymentSolution) -> Dict[int, float]:
        fence_counts = self._fence_vec(solution)  # (N,) 每格相邻围栏段数
        protection = np.minimum(1.0, fence_counts * self.params.fence_protection)
        protection *= self._deploy_fence

        return {gid: float(protection[i]) for i, gid in enumerate(self.grid_ids)}

    def calculate_total_benefit(self, solution: DeploymentSolution) -> float:
        """完全向量化的总收益计算，避免中间字典开销"""
        patrol_cov = self.calculate_patrol_coverage(solution)
        drone_cov  = self.calculate_drone_coverage(solution)
        camera_cov = self.calculate_camera_coverage(solution)
        fence_prot = self.calculate_fence_protection(solution)

        pc = np.array([patrol_cov[gid] for gid in self.grid_ids])
        dc = np.array([drone_cov[gid]  for gid in self.grid_ids])
        cc = np.array([camera_cov[gid] for gid in self.grid_ids])
        fp = np.array([fence_prot[gid] for gid in self.grid_ids])

        E = (self.params.wp * pc + self.params.wd * dc +
             self.params.wc * cc + self.params.wf * fp)

        benefit = self._risk_vec * (1.0 - np.exp(-E))
        total = float(benefit.sum())

        if self._total_risk > 0:
            total /= self._total_risk

        return total
