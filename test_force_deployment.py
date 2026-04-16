"""
测试强制资源部署功能

验证强制部署模式和部分部署模式的行为
"""

import json
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hexdynamic'))

from dssa_optimizer import DSSAOptimizer, DSSAConfig
from coverage_model import CoverageModel
from grid_model import HexGridModel
from data_loader import GridData, CoverageParameters


def create_test_data():
    """创建测试数据"""
    # 创建一个简单的5x5网格
    grids = []
    grid_id = 0
    for r in range(5):
        for q in range(5):
            grids.append(GridData(
                grid_id=grid_id,
                q=q,
                r=r,
                terrain_type='SparseGrass',
                risk=0.5 + (grid_id % 10) * 0.05  # 变化的风险值
            ))
            grid_id += 1
    
    return grids


def test_force_deployment():
    """测试强制部署模式"""
    
    print("=" * 70)
    print("测试强制资源部署功能")
    print("=" * 70)
    
    # 创建测试数据
    grids = create_test_data()
    grid_model = HexGridModel(grids)
    
    # 覆盖参数
    coverage_params = CoverageParameters(
        patrol_radius=3.0,
        drone_radius=6.0,
        camera_radius=2.0,
        fence_protection=0.5,
        wp=0.3,
        wd=0.3,
        wc=0.2,  # 摄像头权重较低
        wf=0.2
    )
    
    # 部署矩阵（所有网格都可以部署）
    deployment_matrix = {
        'camera': {gid: 1 for gid in range(25)},
        'drone': {gid: 1 for gid in range(25)},
        'camp': {gid: 1 for gid in range(25)},
        'patrol': {gid: 1 for gid in range(25)},
        'fence': {gid: 1 for gid in range(25)}
    }
    
    # 可见性参数
    visibility_params = {
        gid: {'camera': 1.0, 'drone': 1.0} for gid in range(25)
    }
    
    # 创建覆盖模型
    coverage_model = CoverageModel(grid_model, coverage_params, deployment_matrix, visibility_params)
    
    # 约束
    constraints = {
        'total_cameras': 10,
        'total_drones': 5,
        'total_camps': 3,
        'total_patrol': 15,
        'total_fence_length': 10,
        'max_cameras_per_grid': 3,
        'max_drones_per_grid': 1,
        'max_camps_per_grid': 1
    }
    
    # DSSA配置（少量迭代用于测试）
    dssa_config = DSSAConfig(
        population_size=20,
        max_iterations=10,
        producer_ratio=0.2,
        scout_ratio=0.2,
        ST=0.8
    )
    
    # 测试1：强制部署模式（默认）
    print("\n" + "=" * 70)
    print("测试1：强制部署模式 (force_full_deployment=True)")
    print("=" * 70)
    
    optimizer1 = DSSAOptimizer(
        coverage_model, 
        constraints, 
        dssa_config,
        force_full_deployment=True
    )
    
    best_solution1, best_fitness1, _ = optimizer1.optimize()
    
    cam_deployed1 = sum(best_solution1.cameras.values())
    drone_deployed1 = sum(best_solution1.drones.values())
    camp_deployed1 = sum(best_solution1.camps.values())
    ranger_deployed1 = sum(best_solution1.rangers.values())
    
    print(f"\n部署结果:")
    print(f"  摄像头: {cam_deployed1} / {constraints['total_cameras']}")
    print(f"  无人机: {drone_deployed1} / {constraints['total_drones']}")
    print(f"  营地: {camp_deployed1} / {constraints['total_camps']}")
    print(f"  巡逻人员: {ranger_deployed1} / {constraints['total_patrol']}")
    
    # 验证
    assert cam_deployed1 == constraints['total_cameras'], f"摄像头未全部部署: {cam_deployed1} != {constraints['total_cameras']}"
    assert drone_deployed1 == constraints['total_drones'], f"无人机未全部部署: {drone_deployed1} != {constraints['total_drones']}"
    assert camp_deployed1 == constraints['total_camps'], f"营地未全部部署: {camp_deployed1} != {constraints['total_camps']}"
    assert ranger_deployed1 == constraints['total_patrol'], f"巡逻人员未全部部署: {ranger_deployed1} != {constraints['total_patrol']}"
    
    print(f"\n✅ 强制部署模式测试通过：所有资源都已部署到上限")
    
    # 测试2：部分部署模式
    print("\n" + "=" * 70)
    print("测试2：部分部署模式 (force_full_deployment=False)")
    print("=" * 70)
    
    optimizer2 = DSSAOptimizer(
        coverage_model, 
        constraints, 
        dssa_config,
        force_full_deployment=False
    )
    
    best_solution2, best_fitness2, _ = optimizer2.optimize()
    
    cam_deployed2 = sum(best_solution2.cameras.values())
    drone_deployed2 = sum(best_solution2.drones.values())
    camp_deployed2 = sum(best_solution2.camps.values())
    ranger_deployed2 = sum(best_solution2.rangers.values())
    
    print(f"\n部署结果:")
    print(f"  摄像头: {cam_deployed2} / {constraints['total_cameras']}")
    print(f"  无人机: {drone_deployed2} / {constraints['total_drones']}")
    print(f"  营地: {camp_deployed2} / {constraints['total_camps']}")
    print(f"  巡逻人员: {ranger_deployed2} / {constraints['total_patrol']}")
    
    print(f"\n💡 部分部署模式：优化器可以根据边际收益选择资源")
    
    # 对比
    print("\n" + "=" * 70)
    print("对比分析")
    print("=" * 70)
    
    print(f"\n资源利用率对比:")
    print(f"  资源类型    | 强制部署 | 部分部署 | 差异")
    print(f"  " + "-" * 50)
    print(f"  摄像头      | {cam_deployed1:8d} | {cam_deployed2:8d} | {cam_deployed1 - cam_deployed2:+4d}")
    print(f"  无人机      | {drone_deployed1:8d} | {drone_deployed2:8d} | {drone_deployed1 - drone_deployed2:+4d}")
    print(f"  营地        | {camp_deployed1:8d} | {camp_deployed2:8d} | {camp_deployed1 - camp_deployed2:+4d}")
    print(f"  巡逻人员    | {ranger_deployed1:8d} | {ranger_deployed2:8d} | {ranger_deployed1 - ranger_deployed2:+4d}")
    
    print(f"\n适应度对比:")
    print(f"  强制部署模式: {best_fitness1:.6f}")
    print(f"  部分部署模式: {best_fitness2:.6f}")
    print(f"  差异: {best_fitness2 - best_fitness1:+.6f}")
    
    # 总结
    print("\n" + "=" * 70)
    print("总结")
    print("=" * 70)
    
    print("\n强制部署模式 (默认):")
    print("  ✅ 确保所有资源都被部署")
    print("  ✅ 不受权重配置影响")
    print("  ✅ 不受边际收益递减影响")
    print("  ✅ 适合资源已购买必须使用的场景")
    
    print("\n部分部署模式 (--allow-partial-deployment):")
    print("  ✅ 优化器根据边际收益选择资源")
    print("  ✅ 可能获得更高的适应度")
    print("  ✅ 适合资源配置是预算上限的场景")
    print("  ⚠️  某些资源可能不被部署")
    
    print("\n使用建议:")
    print("  • 默认使用强制部署模式")
    print("  • 如果需要优化器自动选择资源，使用 --allow-partial-deployment")
    print("  • 通过命令行参数控制：")
    print("    python hexdynamic/protection_pipeline.py input.json output.json")
    print("    python hexdynamic/protection_pipeline.py input.json output.json --allow-partial-deployment")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    test_force_deployment()
