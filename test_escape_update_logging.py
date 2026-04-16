"""
测试警戒更新日志功能

这个脚本演示了DSSA优化器的警戒更新日志功能
"""

import sys
sys.path.insert(0, 'hexdynamic')

from dssa_optimizer import DSSAOptimizer, DSSAConfig
from coverage_model import CoverageModel, DeploymentSolution
from grid_model import HexGridModel
from data_loader import CoverageParameters, GridData
import random

# 设置随机种子以获得可重复的结果
random.seed(42)

# 创建简单的测试数据
grids = [
    GridData(grid_id=i, q=i % 5, r=i // 5, terrain_type='Grass', risk=0.5 + random.random() * 0.3)
    for i in range(20)
]

grid_model = HexGridModel(grids)

coverage_params = CoverageParameters(
    patrol_radius=5.0,
    drone_radius=8.0,
    camera_radius=3.0,
    fence_protection=0.5,
    wp=0.3, wd=0.3, wc=0.2, wf=0.2
)

deployment_matrix = {
    'patrol': {i: 1 for i in range(20)},
    'camp': {i: 1 for i in range(20)},
    'drone': {i: 1 for i in range(20)},
    'camera': {i: 1 for i in range(20)},
    'fence': {i: 1 for i in range(20)}
}

visibility_params = {
    i: {'drone': 1.0, 'camera': 1.0}
    for i in range(20)
}

coverage_model = CoverageModel(grid_model, coverage_params, deployment_matrix, visibility_params)

constraints = {
    'total_patrol': 10,
    'total_camps': 3,
    'max_rangers_per_camp': 5,
    'total_cameras': 8,
    'total_drones': 2,
    'total_fence_length': 20,
    'max_cameras_per_grid': 3,
    'max_drones_per_grid': 1,
    'max_camps_per_grid': 1,
}

# 创建DSSA配置（使用较少的迭代以加快测试）
dssa_config = DSSAConfig(
    population_size=20,
    max_iterations=10,  # 只运行10次迭代用于演示
    producer_ratio=0.2,
    scout_ratio=0.2,
    ST=0.8,
    R2=0.5
)

# 创建优化器
optimizer = DSSAOptimizer(coverage_model, constraints, dssa_config)

# 运行优化
print("=" * 70)
print("DSSA优化器 - 警戒更新日志演示")
print("=" * 70)
print()

best_solution, best_fitness, fitness_history = optimizer.optimize()

print()
print("=" * 70)
print("优化完成")
print("=" * 70)
print(f"最佳适应度: {best_fitness:.6f}")
print(f"部署的资源:")
print(f"  摄像头: {sum(best_solution.cameras.values())}")
print(f"  无人机: {sum(best_solution.drones.values())}")
print(f"  营地: {sum(best_solution.camps.values())}")
print(f"  巡逻人员: {sum(best_solution.rangers.values())}")
print(f"  围栏: {sum(1 for v in best_solution.fences.values() if v == 1)}")
