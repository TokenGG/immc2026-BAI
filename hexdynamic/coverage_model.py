import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from grid_model import HexGridModel
from data_loader import CoverageParameters


@dataclass
class DeploymentSolution:
    cameras: Dict[int, int]
    camps: Dict[int, int]
    drones: Dict[int, int]
    rangers: Dict[int, int]
    fences: Dict[Tuple[int, int], int]


class CoverageModel:
    def __init__(self, grid_model: HexGridModel, coverage_params: CoverageParameters,
                 deployment_matrix: Dict[str, Dict[int, int]],
                 visibility_params: Dict[int, Dict[str, float]]):
        self.grid_model = grid_model
        self.params = coverage_params
        self.deployment_matrix = deployment_matrix
        self.visibility_params = visibility_params
        self.grid_ids = grid_model.get_all_grid_ids()

    def calculate_patrol_coverage(self, solution: DeploymentSolution) -> Dict[int, float]:
        patrol_coverage = {}

        for grid_id in self.grid_ids:
            if self.deployment_matrix['patrol'][grid_id] == 0:
                patrol_coverage[grid_id] = 0.0
                continue

            patrol_intensity = 0.0
            
            # 1. 计算来自营地的巡逻覆盖
            for camp_id, camp_value in solution.camps.items():
                if camp_value == 1:
                    rangers = solution.rangers.get(camp_id, 0)
                    distance = self.grid_model.get_distance(grid_id, camp_id)
                    patrol_intensity += rangers * np.exp(-distance / self.params.patrol_radius)
            
            # 2. 计算来自直接部署巡逻人员的覆盖
            for ranger_id, ranger_count in solution.rangers.items():
                # 只考虑直接部署的巡逻人员（不在营地中的）
                if ranger_count > 0 and ranger_id not in solution.camps:
                    distance = self.grid_model.get_distance(grid_id, ranger_id)
                    patrol_intensity += ranger_count * np.exp(-distance / self.params.patrol_radius)

            patrol_coverage[grid_id] = 1 - np.exp(-patrol_intensity)

        return patrol_coverage

    def calculate_drone_coverage(self, solution: DeploymentSolution) -> Dict[int, float]:
        drone_coverage = {}

        for grid_id in self.grid_ids:
            visibility = self.visibility_params[grid_id]['drone']
            effective_radius = self.params.drone_radius * visibility

            coverage = 0.0
            for drone_id, drone_value in solution.drones.items():
                if drone_value == 1 and self.deployment_matrix['drone'][grid_id] == 1:
                    distance = self.grid_model.get_distance(grid_id, drone_id)
                    if distance <= effective_radius * 2:
                        coverage += np.exp(-distance / effective_radius)

            drone_coverage[grid_id] = min(1.0, coverage)

        return drone_coverage

    def calculate_camera_coverage(self, solution: DeploymentSolution) -> Dict[int, float]:
        camera_coverage = {}

        for grid_id in self.grid_ids:
            visibility = self.visibility_params[grid_id]['camera']
            effective_radius = self.params.camera_radius * visibility

            coverage = 0.0
            for cam_id, cam_value in solution.cameras.items():
                if cam_value == 1 and self.deployment_matrix['camera'][grid_id] == 1:
                    distance = self.grid_model.get_distance(grid_id, cam_id)
                    if distance <= effective_radius * 2:
                        coverage += np.exp(-distance / effective_radius)

            camera_coverage[grid_id] = min(1.0, coverage)

        return camera_coverage

    def calculate_fence_protection(self, solution: DeploymentSolution) -> Dict[int, float]:
        fence_protection = {}

        for grid_id in self.grid_ids:
            protection = 0.0
            neighbors = self.grid_model.get_neighbors(grid_id)

            for neighbor_id in neighbors:
                edge_key = tuple(sorted((grid_id, neighbor_id)))
                if edge_key in solution.fences and solution.fences[edge_key] == 1:
                    if self.deployment_matrix['fence'][grid_id] == 1:
                        protection += self.params.fence_protection

            fence_protection[grid_id] = min(1.0, protection)

        return fence_protection

    def calculate_protection_effect(self, solution: DeploymentSolution) -> Dict[int, float]:
        patrol_cov = self.calculate_patrol_coverage(solution)
        drone_cov = self.calculate_drone_coverage(solution)
        camera_cov = self.calculate_camera_coverage(solution)
        fence_prot = self.calculate_fence_protection(solution)

        protection_effect = {}

        for grid_id in self.grid_ids:
            E_i = (self.params.wp * patrol_cov[grid_id] +
                   self.params.wd * drone_cov[grid_id] +
                   self.params.wc * camera_cov[grid_id] +
                   self.params.wf * fence_prot[grid_id])

            protection_effect[grid_id] = E_i

        return protection_effect

    def calculate_protection_benefit(self, solution: DeploymentSolution) -> Dict[int, float]:
        protection_effect = self.calculate_protection_effect(solution)
        protection_benefit = {}

        for grid_id in self.grid_ids:
            risk = self.grid_model.get_grid_risk(grid_id)
            E_i = protection_effect[grid_id]
            # 计算每个网格的保护效益：R_i * (1 - e^(-E_i))
            B_i = risk * (1 - np.exp(-E_i))
            protection_benefit[grid_id] = B_i

        return protection_benefit

    def calculate_total_benefit(self, solution: DeploymentSolution) -> float:
        protection_benefit = self.calculate_protection_benefit(solution)
        
        # 计算风险权重总和 W = Σ R_i
        total_risk = 0.0
        for grid_id in self.grid_ids:
            total_risk += self.grid_model.get_grid_risk(grid_id)
        
        # 计算总保护效益：(1/W) * Σ [R_i * (1 - e^(-E_i))]
        total_benefit = sum(protection_benefit.values())
        
        # 归一化：如果总风险大于0，则除以总风险
        if total_risk > 0:
            total_benefit = total_benefit / total_risk
        
        return total_benefit

    def validate_solution(self, solution: DeploymentSolution, 
                          constraints: Dict[str, any]) -> Tuple[bool, List[str]]:
        violations = []

        total_cameras = sum(solution.cameras.values())
        if total_cameras > constraints['total_cameras']:
            violations.append(f"Camera limit exceeded: {total_cameras} > {constraints['total_cameras']}")

        total_drones = sum(solution.drones.values())
        if total_drones > constraints['total_drones']:
            violations.append(f"Drone limit exceeded: {total_drones} > {constraints['total_drones']}")

        total_camps = sum(solution.camps.values())
        if total_camps > constraints['total_camps']:
            violations.append(f"Camp limit exceeded: {total_camps} > {constraints['total_camps']}")

        total_rangers = sum(solution.rangers.values())
        if total_rangers > constraints['total_patrol']:
            violations.append(f"Patrol limit exceeded: {total_rangers} > {constraints['total_patrol']}")

        for camp_id, rangers in solution.rangers.items():
            if rangers > constraints['max_rangers_per_camp']:
                violations.append(f"Rangers per camp exceeded at camp {camp_id}: {rangers} > {constraints['max_rangers_per_camp']}")

        total_fence_length = sum(solution.fences.values())
        if total_fence_length > constraints['total_fence_length']:
            violations.append(f"Fence length exceeded: {total_fence_length} > {constraints['total_fence_length']}")

        for grid_id in self.grid_ids:
            if solution.cameras.get(grid_id, 0) > self.deployment_matrix['camera'][grid_id]:
                violations.append(f"Camera deployment infeasible at grid {grid_id}")

            if solution.camps.get(grid_id, 0) > self.deployment_matrix['camp'][grid_id]:
                violations.append(f"Camp deployment infeasible at grid {grid_id}")

            if solution.drones.get(grid_id, 0) > self.deployment_matrix['drone'][grid_id]:
                violations.append(f"Drone deployment infeasible at grid {grid_id}")

        return (len(violations) == 0, violations)

    def repair_solution(self, solution: DeploymentSolution, 
                       constraints: Dict[str, any]) -> DeploymentSolution:
        # 清理输入解决方案，只保留值大于0的条目
        cleaned_cameras = {k: v for k, v in solution.cameras.items() if v > 0}
        cleaned_camps = {k: v for k, v in solution.camps.items() if v > 0}
        cleaned_drones = {k: v for k, v in solution.drones.items() if v > 0}
        cleaned_rangers = {k: v for k, v in solution.rangers.items() if v > 0}
        cleaned_fences = {k: v for k, v in solution.fences.items() if v > 0}
        
        repaired = DeploymentSolution(
            cameras=cleaned_cameras,
            camps=cleaned_camps,
            drones=cleaned_drones,
            rangers=cleaned_rangers,
            fences=cleaned_fences
        )

        for grid_id in self.grid_ids:
            if repaired.cameras.get(grid_id, 0) > self.deployment_matrix['camera'][grid_id]:
                if grid_id in repaired.cameras:
                    del repaired.cameras[grid_id]

            if repaired.camps.get(grid_id, 0) > self.deployment_matrix['camp'][grid_id]:
                if grid_id in repaired.camps:
                    del repaired.camps[grid_id]
                if grid_id in repaired.rangers:
                    del repaired.rangers[grid_id]

            if repaired.drones.get(grid_id, 0) > self.deployment_matrix['drone'][grid_id]:
                if grid_id in repaired.drones:
                    del repaired.drones[grid_id]

        total_cameras = sum(repaired.cameras.values())
        while total_cameras > constraints['total_cameras']:
            for grid_id in list(repaired.cameras.keys()):
                if repaired.cameras[grid_id] == 1:
                    del repaired.cameras[grid_id]
                    total_cameras -= 1
                    if total_cameras <= constraints['total_cameras']:
                        break

        total_drones = sum(repaired.drones.values())
        while total_drones > constraints['total_drones']:
            for grid_id in list(repaired.drones.keys()):
                if repaired.drones[grid_id] == 1:
                    del repaired.drones[grid_id]
                    total_drones -= 1
                    if total_drones <= constraints['total_drones']:
                        break

        total_camps = sum(repaired.camps.values())
        while total_camps > constraints['total_camps']:
            for grid_id in list(repaired.camps.keys()):
                if repaired.camps[grid_id] == 1:
                    del repaired.camps[grid_id]
                    if grid_id in repaired.rangers:
                        del repaired.rangers[grid_id]
                    total_camps -= 1
                    if total_camps <= constraints['total_camps']:
                        break

        total_rangers = sum(repaired.rangers.values())
        
        # 确保巡逻人员数量不超过约束
        while total_rangers > constraints['total_patrol']:
            for camp_id in list(repaired.rangers.keys()):
                if repaired.rangers[camp_id] > 0:
                    new_value = min(repaired.rangers[camp_id] - 1, 
                                   constraints['max_rangers_per_camp'])
                    if new_value == 0:
                        del repaired.rangers[camp_id]
                    else:
                        repaired.rangers[camp_id] = new_value
                    total_rangers -= 1
                    if total_rangers <= constraints['total_patrol']:
                        break
        
        # 确保巡逻人员数量达到约束（如果需要）
        if constraints['total_patrol'] > 0 and total_rangers < constraints['total_patrol']:
            remaining_rangers = constraints['total_patrol'] - total_rangers
            # 找到可以部署巡逻人员的网格
            for grid_id in self.grid_ids:
                if remaining_rangers <= 0:
                    break
                if (grid_id not in repaired.cameras and 
                    grid_id not in repaired.drones and 
                    grid_id not in repaired.camps and
                    grid_id not in repaired.rangers and
                    self.deployment_matrix['patrol'][grid_id] == 1):
                    repaired.rangers[grid_id] = 1
                    remaining_rangers -= 1

        total_fence_length = sum(repaired.fences.values())
        while total_fence_length > constraints['total_fence_length']:
            for edge_key in list(repaired.fences.keys()):
                if repaired.fences[edge_key] == 1:
                    del repaired.fences[edge_key]
                    total_fence_length -= 1
                    if total_fence_length <= constraints['total_fence_length']:
                        break

        return repaired
