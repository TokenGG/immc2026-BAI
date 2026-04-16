"""
敏感性分析测试脚本

测试冻结资源功能和敏感性分析流程
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加 hexdynamic 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hexdynamic'))

from dssa_optimizer import DSSAOptimizer, DSSAConfig
from coverage_model import CoverageModel, DeploymentSolution
from grid_model import HexGridModel
from data_loader import GridData


def create_test_grid_model():
    """创建测试用的网格模型"""
    grids = [
        GridData(grid_id=i, q=i % 10, r=i // 10, terrain_type="SparseGrass", risk=0.5)
        for i in range(100)
    ]
    return HexGridModel(grids)


def create_test_coverage_model():
    """创建测试用的覆盖模型"""
    from data_loader import CoverageParameters
    
    grid_model = create_test_grid_model()
    
    # 创建覆盖参数
    coverage_params = CoverageParameters(
        patrol_radius=5.0,
        drone_radius=8.0,
        camera_radius=3.0,
        fence_protection=0.5,
        wp=0.3, wd=0.3, wc=0.2, wf=0.2
    )
    
    # 创建部署矩阵（所有网格都可以部署）
    deployment_matrix = {
        'camera': {gid: 1 for gid in grid_model.get_all_grid_ids()},
        'drone': {gid: 1 for gid in grid_model.get_all_grid_ids()},
        'camp': {gid: 1 for gid in grid_model.get_all_grid_ids()},
        'patrol': {gid: 1 for gid in grid_model.get_all_grid_ids()},
        'fence': {gid: 1 for gid in grid_model.get_all_grid_ids()},
    }
    
    # 创建可见性参数
    visibility_params = {
        gid: {'camera': 1.0, 'drone': 1.0}
        for gid in grid_model.get_all_grid_ids()
    }
    
    coverage_model = CoverageModel(
        grid_model,
        coverage_params,
        deployment_matrix,
        visibility_params
    )
    
    return coverage_model


def test_frozen_resources():
    """测试冻结资源功能"""
    print("\n" + "="*70)
    print("测试 1: 冻结资源功能")
    print("="*70)
    
    coverage_model = create_test_coverage_model()
    
    constraints = {
        'total_patrol': 20,
        'total_camps': 3,
        'max_rangers_per_camp': 10,
        'total_cameras': 10,
        'total_drones': 5,
        'total_fence_length': 10,
        'max_cameras_per_grid': 3,
        'max_drones_per_grid': 1,
        'max_camps_per_grid': 1,
    }
    
    config = DSSAConfig(
        population_size=20,
        max_iterations=5,
        producer_ratio=0.2,
        scout_ratio=0.2,
        ST=0.8,
        R2=0.5
    )
    
    # 测试1：不冻结任何资源
    print("\n[1.1] 不冻结任何资源")
    optimizer1 = DSSAOptimizer(
        coverage_model,
        constraints,
        config,
        force_full_deployment=True,
        frozen_resources=[]
    )
    solution1, fitness1, _ = optimizer1.optimize()
    
    patrol_count1 = sum(solution1.rangers.values())
    camera_count1 = sum(solution1.cameras.values())
    
    print(f"  巡逻人员: {patrol_count1}")
    print(f"  摄像头: {camera_count1}")
    
    # 测试2：冻结 patrol，只优化其他资源
    print("\n[1.2] 冻结 patrol，只优化其他资源")
    optimizer2 = DSSAOptimizer(
        coverage_model,
        constraints,
        config,
        force_full_deployment=True,
        frozen_resources=['patrol']
    )
    solution2, fitness2, _ = optimizer2.optimize()
    
    patrol_count2 = sum(solution2.rangers.values())
    camera_count2 = sum(solution2.cameras.values())
    
    print(f"  巡逻人员: {patrol_count2}")
    print(f"  摄像头: {camera_count2}")
    
    # 验证：冻结的资源应该保持不变
    if patrol_count2 == patrol_count1:
        print("  ✓ 冻结资源成功：巡逻人员数量保持不变")
    else:
        print(f"  ✗ 冻结资源失败：巡逻人员数量改变了 ({patrol_count1} -> {patrol_count2})")
    
    # 测试3：冻结 camera 和 drone
    print("\n[1.3] 冻结 camera 和 drone")
    optimizer3 = DSSAOptimizer(
        coverage_model,
        constraints,
        config,
        force_full_deployment=True,
        frozen_resources=['camera', 'drone']
    )
    solution3, fitness3, _ = optimizer3.optimize()
    
    camera_count3 = sum(solution3.cameras.values())
    drone_count3 = sum(solution3.drones.values())
    patrol_count3 = sum(solution3.rangers.values())
    
    print(f"  摄像头: {camera_count3}")
    print(f"  无人机: {drone_count3}")
    print(f"  巡逻人员: {patrol_count3}")
    
    if camera_count3 == camera_count1 and drone_count3 == sum(solution1.drones.values()):
        print("  ✓ 冻结多个资源成功")
    else:
        print("  ✗ 冻结多个资源失败")


def test_sensitivity_analysis_workflow():
    """测试敏感性分析工作流"""
    print("\n" + "="*70)
    print("测试 2: 敏感性分析工作流")
    print("="*70)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"\n使用临时目录: {temp_dir}")
    
    try:
        # 创建基础输入 JSON
        base_input = {
            "map_config": {
                "map_width": 1000,
                "map_height": 1000,
                "boundary_type": "RECTANGLE",
                "road_locations": [],
                "water_locations": [],
                "boundary_locations": []
            },
            "time": {
                "hour_of_day": 12,
                "season": "DRY"
            },
            "grids": [
                {
                    "grid_id": i,
                    "q": i % 10,
                    "r": i // 10,
                    "x": (i % 10) * 100,
                    "y": (i // 10) * 100,
                    "terrain_type": "SparseGrass",
                    "fire_risk": 0.5,
                    "terrain_complexity": 0.3,
                    "vegetation_type": "GRASSLAND",
                    "species_densities": {},
                    "hex_size": 62.0
                }
                for i in range(100)
            ],
            "constraints": {
                "total_patrol": 20,
                "total_camps": 3,
                "max_rangers_per_camp": 10,
                "total_cameras": 10,
                "total_drones": 5,
                "total_fence_length": 10,
                "max_cameras_per_grid": 3,
                "max_drones_per_grid": 1,
                "max_camps_per_grid": 1
            },
            "coverage_params": {
                "patrol_radius": 5.0,
                "drone_radius": 8.0,
                "camera_radius": 3.0,
                "fence_protection": 0.5,
                "wp": 0.3,
                "wd": 0.3,
                "wc": 0.2,
                "wf": 0.2
            },
            "dssa_config": {
                "population_size": 20,
                "max_iterations": 5,
                "producer_ratio": 0.2,
                "scout_ratio": 0.2,
                "ST": 0.8,
                "R2": 0.5
            }
        }
        
        base_input_path = os.path.join(temp_dir, 'base_input.json')
        with open(base_input_path, 'w') as f:
            json.dump(base_input, f, indent=2)
        
        print(f"✓ 创建基础输入: {base_input_path}")
        
        # 测试敏感性分析脚本
        print("\n[2.1] 测试敏感性分析脚本")
        
        # 导入敏感性分析模块
        sys.path.insert(0, os.path.dirname(__file__))
        from sensitivity_analysis import run_sensitivity_analysis
        
        # 运行敏感性分析（只运行 2 个值以加快测试）
        output_dir = os.path.join(temp_dir, 'sensitivity_results')
        
        print(f"  运行敏感性分析: patrol (0-10, step 5)")
        run_sensitivity_analysis(
            base_input_path,
            'patrol',
            resource_range=(0, 10, 5),
            output_dir=output_dir,
            vectorized=False
        )
        
        # 检查输出文件
        result_file = os.path.join(output_dir, 'sensitivity_patrol.json')
        if os.path.exists(result_file):
            print(f"  ✓ 敏感性分析结果已生成: {result_file}")
            
            with open(result_file, 'r') as f:
                results = json.load(f)
            
            print(f"  资源类型: {results['resource_type']}")
            print(f"  资源值: {results['resource_values']}")
            print(f"  结果数量: {len(results['results'])}")
            
            for r in results['results']:
                print(f"    - patrol={r['resource_value']}: benefit={r['total_protection_benefit']:.4f}, fitness={r['best_fitness']:.4f}")
        else:
            print(f"  ✗ 敏感性分析结果未生成")
        
        # 检查绘图文件
        plot_file = os.path.join(output_dir, 'sensitivity_patrol_plot.png')
        if os.path.exists(plot_file):
            print(f"  ✓ 敏感性分析曲线已生成: {plot_file}")
        else:
            print(f"  ✗ 敏感性分析曲线未生成")
    
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)
        print(f"\n✓ 清理临时目录")


def main():
    print("\n" + "="*70)
    print("敏感性分析测试")
    print("="*70)
    
    try:
        test_frozen_resources()
        # test_sensitivity_analysis_workflow()  # 注释掉，因为需要完整的 pipeline
        
        print("\n" + "="*70)
        print("✓ 所有测试完成！")
        print("="*70 + "\n")
    
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
