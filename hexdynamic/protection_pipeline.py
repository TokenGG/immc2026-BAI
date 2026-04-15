"""
Protection Pipeline
输入：地图网格 JSON（含 riskIndex 所需字段）
流程：riskIndex 计算归一化风险 → DSSA 优化部署方案 → 输出 JSON
输出：每个网格的归一化综合风险指数、保护收益指数，以及全局统计指标和部署资源

用法:
    python protection_pipeline.py <input.json> <output.json>
"""

import json
import sys
import os
import numpy as np
from typing import Dict, List

# ---- 将 riskIndex/src 加入路径 ----
_RISK_SRC = os.path.join(os.path.dirname(__file__), '..', 'riskIndex', 'src')
sys.path.insert(0, os.path.abspath(_RISK_SRC))
_RISK_DIR = os.path.join(os.path.dirname(__file__), '..', 'riskIndex')
sys.path.insert(0, os.path.abspath(_RISK_DIR))

from risk_model_wrapper import (
    MapConfig, GridInputData, TimeInputData, ModelInputData, ModelConfigData,
    DistanceCalculator, convert_grid_input, convert_time_input, create_model_from_config,
)

from data_loader import DataLoader, GridData
from grid_model import HexGridModel
from coverage_model import CoverageModel
from dssa_optimizer import DSSAOptimizer, DSSAConfig


# ---------------------------------------------------------------------------
# 输入 JSON 格式说明
#
# {
#   "map_config": {                          // riskIndex 地图配置
#     "map_width": 5,
#     "map_height": 4,
#     "boundary_type": "RECTANGLE",
#     "road_locations": [[1,0],[2,1]],
#     "water_locations": [[4,3]]
#   },
#   "time": {                                // riskIndex 时间上下文（可选）
#     "hour_of_day": 12,
#     "season": "DRY"
#   },
#   "use_temporal_factors": false,           // 是否启用昼夜/季节因子（可选，默认 false）
#   "risk_model_config": {                   // riskIndex 权重配置（可选）
#     "risk_weights": {"human_weight":0.4,"environmental_weight":0.3,"density_weight":0.3},
#     "human_risk_weights": {"boundary_weight":0.4,"road_weight":0.35,"water_weight":0.25},
#     "environmental_risk_weights": {"fire_weight":0.6,"terrain_weight":0.4}
#   },
#   "grids": [
#     {
#       "grid_id": 0,
#       "q": 0, "r": 0,                      // 六边形轴坐标
#       "x": 0, "y": 0,                      // 笛卡尔坐标（用于 riskIndex 距离计算）
#       "terrain_type": "SparseGrass",       // hexdynamic 地形类型
#       "fire_risk": 0.5,                    // riskIndex 环境字段
#       "terrain_complexity": 0.3,
#       "vegetation_type": "GRASSLAND",      // GRASSLAND / FOREST / SHRUB
#       "species_densities": {"rhino":0.7,"elephant":0.5,"bird":0.3}
#     }, ...
#   ],
#   "constraints": {
#     "total_patrol": 8, "total_camps": 2, "max_rangers_per_camp": 4,
#     "total_cameras": 4, "total_drones": 2, "total_fence_length": 10
#   },
#   "coverage_params": { ... },              // 可选
#   "dssa_config": { ... }                   // 可选
# }
# ---------------------------------------------------------------------------


def load_input(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def compute_risk_with_riskindex(data: dict) -> Dict[int, float]:
    """调用 riskIndex 模块计算每个网格的归一化风险值，返回 {grid_id: normalized_risk}"""

    map_cfg_raw = data['map_config']
    map_config = MapConfig(
        map_width=map_cfg_raw['map_width'],
        map_height=map_cfg_raw['map_height'],
        boundary_type=map_cfg_raw.get('boundary_type', 'RECTANGLE'),
        road_locations=[tuple(p) for p in map_cfg_raw.get('road_locations', [])],
        water_locations=[tuple(p) for p in map_cfg_raw.get('water_locations', [])]
    )

    time_raw = data.get('time', {})
    time_input = TimeInputData(
        hour_of_day=time_raw.get('hour_of_day', 12),
        season=time_raw.get('season', 'DRY')
    )

    distance_calc = DistanceCalculator(map_config)
    time_context = convert_time_input(time_input)

    # 权重配置
    cfg_raw = data.get('risk_model_config', {})
    model_config = ModelConfigData(
        risk_weights=cfg_raw.get('risk_weights'),
        human_risk_weights=cfg_raw.get('human_risk_weights'),
        environmental_risk_weights=cfg_raw.get('environmental_risk_weights')
    )
    model = create_model_from_config(model_config)

    # 构建 riskIndex 输入列表，保持 grid_id 顺序
    grid_data_list = []
    id_order = []
    for g in data['grids']:
        gid = g['grid_id']
        grid_input = GridInputData(
            grid_id=str(gid),
            x=g.get('x', 0),
            y=g.get('y', 0),
            fire_risk=float(g.get('fire_risk', 0.0)),
            terrain_complexity=float(g.get('terrain_complexity', 0.0)),
            vegetation_type=g.get('vegetation_type', 'GRASSLAND'),
            species_densities=g.get('species_densities', {})
        )
        grid_obj, env_obj, density_obj = convert_grid_input(grid_input, distance_calc)
        grid_data_list.append((grid_obj, env_obj, density_obj))
        id_order.append(gid)

    use_temporal = data.get('use_temporal_factors', False)
    results = model.calculate_batch(grid_data_list, time_context,
                                    use_temporal_factors=use_temporal)

    return {id_order[i]: float(r.normalized_risk) for i, r in enumerate(results)}


def build_data_loader(data: dict, risk_map: Dict[int, float]) -> DataLoader:
    loader = DataLoader()

    grids = []
    for g in data['grids']:
        gid = g['grid_id']
        grids.append(GridData(
            grid_id=gid,
            q=g['q'],
            r=g['r'],
            terrain_type=g.get('terrain_type', 'SparseGrass'),
            risk=risk_map.get(gid, 0.0)
        ))
    loader.grids = grids

    cp = data.get('coverage_params', {})
    loader.set_coverage_parameters(
        patrol_radius=cp.get('patrol_radius', 5.0),
        drone_radius=cp.get('drone_radius', 8.0),
        camera_radius=cp.get('camera_radius', 3.0),
        fence_protection=cp.get('fence_protection', 0.5),
        wp=cp.get('wp', 0.3),
        wd=cp.get('wd', 0.3),
        wc=cp.get('wc', 0.2),
        wf=cp.get('wf', 0.2)
    )

    c = data['constraints']
    loader.set_constraints(
        total_patrol=c['total_patrol'],
        total_camps=c['total_camps'],
        max_rangers_per_camp=c['max_rangers_per_camp'],
        total_cameras=c['total_cameras'],
        total_drones=c['total_drones'],
        total_fence_length=float(c['total_fence_length'])
    )

    temp_grid_model = HexGridModel(loader.grids)
    edge_grids = temp_grid_model.get_edge_grids()
    loader.initialize_deployment_matrix(edge_grids=edge_grids)
    loader.initialize_visibility_params()

    return loader


def run_pipeline(input_path: str, output_path: str):
    print(f"[1/4] 读取输入: {input_path}")
    data = load_input(input_path)

    print("[2/4] 调用 riskIndex 计算归一化风险...")
    risk_map = compute_risk_with_riskindex(data)

    print("[3/4] 构建模型并运行 DSSA 优化...")
    loader = build_data_loader(data, risk_map)
    grid_model = HexGridModel(loader.grids)
    coverage_model = CoverageModel(
        grid_model,
        loader.coverage_params,
        loader.deployment_matrix,
        loader.visibility_params
    )

    constraints = {
        'total_patrol': loader.constraints.total_patrol,
        'total_camps': loader.constraints.total_camps,
        'max_rangers_per_camp': loader.constraints.max_rangers_per_camp,
        'total_cameras': loader.constraints.total_cameras,
        'total_drones': loader.constraints.total_drones,
        'total_fence_length': loader.constraints.total_fence_length
    }

    dc = data.get('dssa_config', {})
    dssa_config = DSSAConfig(
        population_size=dc.get('population_size', 50),
        max_iterations=dc.get('max_iterations', 100),
        producer_ratio=dc.get('producer_ratio', 0.2),
        scout_ratio=dc.get('scout_ratio', 0.2),
        ST=dc.get('ST', 0.8),
        R2=dc.get('R2', 0.5)
    )

    optimizer = DSSAOptimizer(coverage_model, constraints, dssa_config)
    best_solution, best_fitness, fitness_history = optimizer.optimize()

    print("[4/4] 计算指标并生成输出...")

    # ---- 全局指标 ----
    pb_per_grid = coverage_model.calculate_protection_benefit(best_solution)
    total_risk = sum(grid_model.get_grid_risk(gid) for gid in grid_model.get_all_grid_ids())
    total_protection_benefit = sum(pb_per_grid.values())
    avg_protection_benefit = float(np.mean(list(pb_per_grid.values())))

    # ---- 保护收益归一化（min-max） ----
    pb_vals = list(pb_per_grid.values())
    pb_min, pb_max = min(pb_vals), max(pb_vals)

    def norm_pb(v):
        return float((v - pb_min) / (pb_max - pb_min)) if pb_max != pb_min else float(v)

    # ---- 每个网格结果 ----
    grid_results = []
    for grid in loader.grids:
        gid = grid.grid_id
        grid_results.append({
            'grid_id': gid,
            'q': grid.q,
            'r': grid.r,
            'x': data['grids'][loader.grids.index(grid)].get('x', 0),
            'y': data['grids'][loader.grids.index(grid)].get('y', 0),
            'terrain_type': grid.terrain_type,
            'risk_normalized': round(float(grid.risk), 6),       # 已由 riskIndex 归一化
            'protection_benefit_raw': round(float(pb_per_grid[gid]), 6),
            'protection_benefit_normalized': round(norm_pb(pb_per_grid[gid]), 6),
            'deployment': {
                'patrol_rangers': int(best_solution.rangers.get(gid, 0)),
                'camp': int(best_solution.camps.get(gid, 0)),
                'drone': int(best_solution.drones.get(gid, 0)),
                'camera': int(best_solution.cameras.get(gid, 0))
            }
        })

    fence_edges = [
        {'grid_id_1': int(e[0]), 'grid_id_2': int(e[1])}
        for e, v in best_solution.fences.items() if v == 1
    ]

    output = {
        'summary': {
            'total_grids': grid_model.get_grid_count(),
            'total_risk': round(float(total_risk), 6),
            'best_fitness': round(float(best_fitness), 6),
            'total_protection_benefit': round(float(total_protection_benefit), 6),
            'average_protection_benefit': round(float(avg_protection_benefit), 6),
            'fitness_history': [round(float(f), 6) for f in fitness_history],
            'resources_deployed': {
                'total_cameras': int(sum(best_solution.cameras.values())),
                'total_drones': int(sum(best_solution.drones.values())),
                'total_camps': int(sum(best_solution.camps.values())),
                'total_rangers': int(sum(best_solution.rangers.values())),
                'fence_segments': len(fence_edges)
            }
        },
        'grids': grid_results,
        'fence_edges': fence_edges
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n结果已保存至: {output_path}")
    print(f"  Best Fitness              : {best_fitness:.4f}")
    print(f"  Total Protection Benefit  : {total_protection_benefit:.4f}")
    print(f"  Average Protection Benefit: {avg_protection_benefit:.4f}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python protection_pipeline.py <input.json> <output.json>")
        sys.exit(1)
    run_pipeline(sys.argv[1], sys.argv[2])
