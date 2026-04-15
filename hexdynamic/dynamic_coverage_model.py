import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from grid_model import HexGridModel
from data_loader import CoverageParameters
from coverage_model import DeploymentSolution


@dataclass
class TimeDynamicSolution:
    """时间动态部署解决方案"""
    cameras: Dict[int, int]  # 静态摄像头部署
    camps: Dict[int, int]    # 静态营地部署
    drones: Dict[int, List[Tuple[int, int]]]  # 无人机时间序列: {drone_id: [(time, position)]}
    rangers: Dict[int, List[Tuple[int, int]]]  # 巡逻人员时间序列: {ranger_id: [(time, position)]}
    fences: Dict[Tuple[int, int], int]  # 静态围栏部署


class DynamicCoverageModel:
    """时间动态覆盖模型"""
    def __init__(self, grid_model: HexGridModel, coverage_params: CoverageParameters,
                 deployment_matrix: Dict[str, Dict[int, int]],
                 visibility_params: Dict[int, Dict[str, float]]):
        self.grid_model = grid_model
        self.params = coverage_params
        self.deployment_matrix = deployment_matrix
        self.visibility_params = visibility_params
        self.grid_ids = grid_model.get_all_grid_ids()
    
    def get_patrol_position(self, ranger_id: int, time: int, solution: TimeDynamicSolution) -> Optional[int]:
        """获取巡逻人员在指定时间的位置"""
        if ranger_id not in solution.rangers:
            return None
        
        # 找到最接近指定时间的位置
        positions = solution.rangers[ranger_id]
        if not positions:
            return None
        
        # 简单线性插值或最近时间点
        # 这里使用最近时间点
        closest_pos = min(positions, key=lambda x: abs(x[0] - time))
        return closest_pos[1]
    
    def get_drone_position(self, drone_id: int, time: int, solution: TimeDynamicSolution) -> Optional[int]:
        """获取无人机在指定时间的位置"""
        if drone_id not in solution.drones:
            return None
        
        # 找到最接近指定时间的位置
        positions = solution.drones[drone_id]
        if not positions:
            return None
        
        closest_pos = min(positions, key=lambda x: abs(x[0] - time))
        return closest_pos[1]
    
    def calculate_patrol_coverage(self, solution: TimeDynamicSolution, time: int) -> Dict[int, float]:
        """计算巡逻覆盖（时间动态）"""
        patrol_coverage = {}

        for grid_id in self.grid_ids:
            if self.deployment_matrix['patrol'][grid_id] == 0:
                patrol_coverage[grid_id] = 0.0
                continue

            patrol_intensity = 0.0
            
            # 1. 计算来自营地的巡逻覆盖
            for camp_id, camp_value in solution.camps.items():
                if camp_value == 1:
                    # 营地位置固定，巡逻人员从营地出发
                    distance = self.grid_model.get_distance(grid_id, camp_id)
                    patrol_intensity += 1 * np.exp(-distance / self.params.patrol_radius)
            
            # 2. 计算来自巡逻人员的覆盖
            for ranger_id, positions in solution.rangers.items():
                pos = self.get_patrol_position(ranger_id, time, solution)
                if pos is not None:
                    distance = self.grid_model.get_distance(grid_id, pos)
                    patrol_intensity += 1 * np.exp(-distance / self.params.patrol_radius)

            patrol_coverage[grid_id] = 1 - np.exp(-patrol_intensity)

        return patrol_coverage
    
    def calculate_drone_coverage(self, solution: TimeDynamicSolution, time: int) -> Dict[int, float]:
        """计算无人机覆盖（时间动态）"""
        drone_coverage = {}

        for grid_id in self.grid_ids:
            visibility = self.visibility_params[grid_id]['drone']
            effective_radius = self.params.drone_radius * visibility

            coverage = 0.0
            for drone_id, positions in solution.drones.items():
                pos = self.get_drone_position(drone_id, time, solution)
                if pos is not None and self.deployment_matrix['drone'][grid_id] == 1:
                    distance = self.grid_model.get_distance(grid_id, pos)
                    if distance <= effective_radius * 2:
                        coverage += np.exp(-distance / effective_radius)

            drone_coverage[grid_id] = min(1.0, coverage)

        return drone_coverage
    
    def calculate_camera_coverage(self, solution: TimeDynamicSolution, time: int) -> Dict[int, float]:
        """计算摄像头覆盖（基本静态）"""
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
    
    def calculate_fence_protection(self, solution: TimeDynamicSolution, time: int) -> Dict[int, float]:
        """计算围栏保护（静态）"""
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
    
    def calculate_protection_effect(self, solution: TimeDynamicSolution, time: int) -> Dict[int, float]:
        """计算保护效果（时间动态）"""
        patrol_cov = self.calculate_patrol_coverage(solution, time)
        drone_cov = self.calculate_drone_coverage(solution, time)
        camera_cov = self.calculate_camera_coverage(solution, time)
        fence_prot = self.calculate_fence_protection(solution, time)

        protection_effect = {}

        for grid_id in self.grid_ids:
            E_i = (self.params.wp * patrol_cov[grid_id] +
                   self.params.wd * drone_cov[grid_id] +
                   self.params.wc * camera_cov[grid_id] +
                   self.params.wf * fence_prot[grid_id])

            protection_effect[grid_id] = E_i

        return protection_effect
    
    def calculate_protection_benefit(self, solution: TimeDynamicSolution, time: int) -> Dict[int, float]:
        """计算保护效益（时间动态）"""
        protection_effect = self.calculate_protection_effect(solution, time)
        protection_benefit = {}

        for grid_id in self.grid_ids:
            risk = self.grid_model.get_grid_risk(grid_id)
            E_i = protection_effect[grid_id]
            # 计算每个网格的保护效益：R_i * (1 - e^(-E_i))
            B_i = risk * (1 - np.exp(-E_i))
            protection_benefit[grid_id] = B_i

        return protection_benefit
    
    def calculate_total_benefit(self, solution: TimeDynamicSolution, time: int) -> float:
        """计算总保护效益（时间动态）"""
        protection_benefit = self.calculate_protection_benefit(solution, time)
        
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
    
    def simulate_protection_over_time(self, solution: TimeDynamicSolution, time_steps: int) -> List[float]:
        """模拟保护效益随时间的变化"""
        protection_over_time = []
        
        for t in range(1, time_steps + 1):
            benefit = self.calculate_total_benefit(solution, t)
            protection_over_time.append(benefit)
        
        return protection_over_time
    
    def estimate_minimum_staffing(self, base_solution: DeploymentSolution, time_steps: int, 
                                 target_protection: float, max_patrol: int = 20) -> int:
        """估计维持目标保护水平所需的最小人员数量"""
        # 转换静态解决方案为动态解决方案
        def convert_to_dynamic_solution(patrol_count: int) -> TimeDynamicSolution:
            # 生成巡逻人员的时间序列
            rangers_time_series = {}
            for i in range(patrol_count):
                # 简单的周期性巡逻路线
                positions = []
                for t in range(1, time_steps + 1):
                    # 随机巡逻路线
                    pos = np.random.choice(self.grid_ids)
                    positions.append((t, pos))
                rangers_time_series[i] = positions
            
            # 生成无人机的时间序列
            drones_time_series = {}
            for drone_id in base_solution.drones:
                positions = []
                for t in range(1, time_steps + 1):
                    # 简单的飞行/充电周期
                    if t % 4 < 3:  # 3/4时间飞行
                        pos = np.random.choice(self.grid_ids)
                    else:  # 1/4时间充电（停留在基地）
                        pos = list(base_solution.drones.keys())[0]
                    positions.append((t, pos))
                drones_time_series[drone_id] = positions
            
            return TimeDynamicSolution(
                cameras=base_solution.cameras,
                camps=base_solution.camps,
                drones=drones_time_series,
                rangers=rangers_time_series,
                fences=base_solution.fences
            )
        
        # 从1开始测试不同的巡逻人员数量
        for P in range(1, max_patrol + 1):
            dynamic_solution = convert_to_dynamic_solution(P)
            protection_over_time = self.simulate_protection_over_time(dynamic_solution, time_steps)
            avg_protection = np.mean(protection_over_time)
            
            if avg_protection >= target_protection:
                return P
        
        return max_patrol  # 如果达到最大巡逻人员数仍未满足目标
    
    def generate_patrol_routes(self, patrol_count: int, time_steps: int) -> Dict[int, List[Tuple[int, int]]]:
        """生成巡逻路线"""
        routes = {}
        for i in range(patrol_count):
            # 生成随机巡逻路线
            route = []
            current_pos = np.random.choice(self.grid_ids)
            for t in range(1, time_steps + 1):
                # 随机移动到相邻网格或保持原位
                neighbors = self.grid_model.get_neighbors(current_pos)
                if neighbors:
                    current_pos = np.random.choice(neighbors + [current_pos])
                route.append((t, current_pos))
            routes[i] = route
        return routes
    
    def generate_drone_schedules(self, drone_count: int, time_steps: int) -> Dict[int, List[Tuple[int, int]]]:
        """生成无人机飞行计划"""
        schedules = {}
        for i in range(drone_count):
            # 生成飞行/充电周期
            schedule = []
            base_pos = np.random.choice(self.grid_ids)
            for t in range(1, time_steps + 1):
                if t % 4 < 3:  # 3/4时间飞行
                    # 随机飞行位置
                    flight_pos = np.random.choice(self.grid_ids)
                    schedule.append((t, flight_pos))
                else:  # 1/4时间充电
                    schedule.append((t, base_pos))
            schedules[i] = schedule
        return schedules