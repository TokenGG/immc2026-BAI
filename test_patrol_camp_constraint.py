"""
测试patrol和camp不能部署在同一个grid的约束
"""
import sys
sys.path.insert(0, 'hexdynamic')

from coverage_model import CoverageModel, DeploymentSolution
from grid_model import HexGridModel
from data_loader import CoverageParameters, GridData

# 创建简单的测试数据
grids = [
    GridData(grid_id=1, q=0, r=0, terrain_type='Grass', risk=0.5),
    GridData(grid_id=2, q=1, r=0, terrain_type='Grass', risk=0.6),
    GridData(grid_id=3, q=0, r=1, terrain_type='Grass', risk=0.7),
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
    'patrol': {1: 1, 2: 1, 3: 1},
    'camp': {1: 1, 2: 1, 3: 1},
    'drone': {1: 1, 2: 1, 3: 1},
    'camera': {1: 1, 2: 1, 3: 1},
    'fence': {1: 1, 2: 1, 3: 1}
}

visibility_params = {
    1: {'drone': 1.0, 'camera': 1.0},
    2: {'drone': 1.0, 'camera': 1.0},
    3: {'drone': 1.0, 'camera': 1.0}
}

model = CoverageModel(grid_model, coverage_params, deployment_matrix, visibility_params)

# 测试1: patrol和camp在同一个grid (应该失败)
print("测试1: patrol和camp在同一个grid")
solution1 = DeploymentSolution(
    cameras={},
    camps={1: 1},      # camp在grid 1
    drones={},
    rangers={1: 2},    # patrol也在grid 1
    fences={}
)

is_valid, violations = model.validate_solution(solution1, {
    'total_patrol': 2,
    'total_camps': 1,
    'total_cameras': 0,
    'total_drones': 0,
    'total_fence_length': 0,
    'max_cameras_per_grid': 3,
    'max_drones_per_grid': 1,
    'max_camps_per_grid': 1,
    'max_rangers_per_camp': 5
})

print(f"  有效: {is_valid}")
print(f"  违规: {violations}")
print()

# 测试2: patrol和camp在不同grid (应该成功)
print("测试2: patrol和camp在不同grid")
solution2 = DeploymentSolution(
    cameras={},
    camps={1: 1},      # camp在grid 1
    drones={},
    rangers={2: 2},    # patrol在grid 2
    fences={}
)

is_valid, violations = model.validate_solution(solution2, {
    'total_patrol': 2,
    'total_camps': 1,
    'total_cameras': 0,
    'total_drones': 0,
    'total_fence_length': 0,
    'max_cameras_per_grid': 3,
    'max_drones_per_grid': 1,
    'max_camps_per_grid': 1,
    'max_rangers_per_camp': 5
})

print(f"  有效: {is_valid}")
print(f"  违规: {violations}")
print()

# 测试3: repair_solution应该移除冲突的patrol
print("测试3: repair_solution修复冲突")
solution3 = DeploymentSolution(
    cameras={},
    camps={1: 1, 2: 1},    # camps在grid 1和2
    drones={},
    rangers={1: 1, 2: 1, 3: 1},  # patrol在grid 1, 2, 3 (1和2冲突)
    fences={}
)

print(f"  修复前 - camps: {solution3.camps}, rangers: {solution3.rangers}")

repaired = model.repair_solution(solution3, {
    'total_patrol': 3,
    'total_camps': 2,
    'total_cameras': 0,
    'total_drones': 0,
    'total_fence_length': 0,
    'max_cameras_per_grid': 3,
    'max_drones_per_grid': 1,
    'max_camps_per_grid': 1,
    'max_rangers_per_camp': 5
})

print(f"  修复后 - camps: {repaired.camps}, rangers: {repaired.rangers}")

is_valid, violations = model.validate_solution(repaired, {
    'total_patrol': 3,
    'total_camps': 2,
    'total_cameras': 0,
    'total_drones': 0,
    'total_fence_length': 0,
    'max_cameras_per_grid': 3,
    'max_drones_per_grid': 1,
    'max_camps_per_grid': 1,
    'max_rangers_per_camp': 5
})

print(f"  修复后有效: {is_valid}")
print(f"  修复后违规: {violations}")
