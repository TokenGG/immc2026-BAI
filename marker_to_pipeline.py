"""
marker_to_pipeline.py
从 marker 导出的 grid-coordinates.json 生成 protection_pipeline.py 的输入 JSON。

关键规则：
1. 根据 colorTag 映射地形类型
2. 犀牛(rhino)和大象(elephant)不能分布在水坑(WaterHole)和盐沼(SaltMarsh)网格
3. 鸟类(bird)集中在盐沼，其他地形密度较低

用法：
    python marker_to_pipeline.py marker/grid-coordinates.json -o marker/pipeline_input.json
"""

import argparse
import json
import random
from typing import Dict, List


# colorTag 到地形类型的映射
COLOR_TAG_TO_TERRAIN = {
    1: "DenseGrass",    # 森林密集区 (绿色)
    2: "SparseGrass",   # 森林稀疏区 (红色)
    3: "WaterHole",     # 水坑 (蓝色)
    4: "SparseGrass",   # 干坑 (黄色) -> 视为稀疏草地
    5: "Road",          # 主路 (紫色)
    6: "Road",          # 小路 (橙色) -> 视为道路
    7: "SaltMarsh",     # 盐沼 (青色)
    0: "SparseGrass",   # 未知/其他 -> 默认稀疏草地
}

# 地形 → riskIndex vegetation_type
TERRAIN_TO_VEG = {
    "SparseGrass": "GRASSLAND",
    "DenseGrass":  "FOREST",
    "WaterHole":   "SHRUB",
    "SaltMarsh":   "SHRUB",
    "Road":        "GRASSLAND",
}

# 地形 → 环境风险默认范围 (fire_risk_range, terrain_complexity_range)
TERRAIN_ENV = {
    "SparseGrass": ((0.2, 0.5), (0.1, 0.4)),
    "DenseGrass":  ((0.4, 0.8), (0.4, 0.7)),
    "WaterHole":   ((0.05, 0.2), (0.1, 0.3)),
    "SaltMarsh":   ((0.05, 0.2), (0.3, 0.5)),
    "Road":        ((0.1, 0.3), (0.05, 0.2)),
}

# 默认参数
DEFAULTS = {
    "total_patrol": 20,
    "total_camps": 5,
    "max_rangers_per_camp": 5,
    "total_cameras": 10,
    "total_drones": 3,
    "total_fence_length": 50,
    "patrol_radius": 5.0,
    "drone_radius": 8.0,
    "camera_radius": 3.0,
    "fence_protection": 0.5,
    "wp": 0.3,
    "wd": 0.3,
    "wc": 0.2,
    "wf": 0.2,
    "population_size": 50,
    "max_iterations": 100,
    "producer_ratio": 0.2,
    "scout_ratio": 0.2,
    "ST": 0.8,
    "R2": 0.5,
    "hour_of_day": 12,
    "season": "DRY",
    "use_temporal_factors": False,
    "human_weight": 0.4,
    "environmental_weight": 0.3,
    "density_weight": 0.3,
}


def generate_species_densities(terrain: str) -> Dict[str, float]:
    """
    按规则生成物种密度：
    - rhino / elephant 只在 SparseGrass 和 DenseGrass 有密度
    - rhino / elephant 在 WaterHole 和 SaltMarsh 密度为 0（关键约束）
    - bird 集中在 SaltMarsh，其他地形密度较低
    """
    if terrain == "SparseGrass":
        return {
            "rhino":    round(random.uniform(0.4, 0.9), 2),
            "elephant": round(random.uniform(0.3, 0.8), 2),
            "bird":     round(random.uniform(0.0, 0.15), 2),
        }
    elif terrain == "DenseGrass":
        return {
            "rhino":    round(random.uniform(0.3, 0.7), 2),
            "elephant": round(random.uniform(0.2, 0.6), 2),
            "bird":     round(random.uniform(0.0, 0.1), 2),
        }
    elif terrain == "SaltMarsh":
        # 盐沼：犀牛和大象密度为0
        return {
            "rhino":    0.0,
            "elephant": 0.0,
            "bird":     round(random.uniform(0.6, 1.0), 2),
        }
    elif terrain == "WaterHole":
        # 水坑：犀牛和大象密度为0
        return {
            "rhino":    0.0,
            "elephant": 0.0,
            "bird":     round(random.uniform(0.1, 0.3), 2),
        }
    else:  # Road
        return {
            "rhino":    0.0,
            "elephant": 0.0,
            "bird":     round(random.uniform(0.0, 0.1), 2),
        }


def convert_marker_to_pipeline(grid_coords: List[dict], args) -> dict:
    """
    将 marker 导出的 grid-coordinates.json 转换为 pipeline 输入格式
    """
    random.seed(args.seed)
    
    # 解析网格ID，提取row和col的范围
    rows = set()
    cols = set()
    for grid in grid_coords:
        grid_id = grid["gridId"]
        row, col = map(int, grid_id.split("_"))
        rows.add(row)
        cols.add(col)
    
    min_row, max_row = min(rows), max(rows)
    min_col, max_col = min(cols), max(cols)
    
    # 计算地图尺寸（marker使用的坐标系）
    map_height = max_row - min_row + 1
    map_width = max_col - min_col + 1
    
    # 收集道路和水源位置
    road_locations = []
    water_locations = []
    
    # 转换网格数据
    grids = []
    grid_id_counter = 0
    
    # 创建gridId到原始数据的映射
    grid_map = {g["gridId"]: g for g in grid_coords}
    
    for grid in grid_coords:
        marker_grid_id = grid["gridId"]
        row, col = map(int, marker_grid_id.split("_"))
        
        # 获取地形类型
        color_tag = grid.get("colorTag", 0)
        terrain = COLOR_TAG_TO_TERRAIN.get(color_tag, "SparseGrass")
        
        # 坐标转换：marker的x,y已经是正确的坐标
        x = grid["x"]
        y = grid["y"]
        
        # 六边形轴坐标（从marker的row, col转换）
        # marker使用odd-r offset坐标系
        q_hex = col - (row // 2)
        r_hex = row
        
        # 生成环境风险参数
        env_fire_range, env_terrain_range = TERRAIN_ENV[terrain]
        fire_risk = round(random.uniform(*env_fire_range), 2)
        terrain_complexity = round(random.uniform(*env_terrain_range), 2)
        
        # 生成物种密度（应用约束规则）
        species_densities = generate_species_densities(terrain)
        
        # 收集道路和水源位置
        if terrain == "Road":
            road_locations.append([x, y])
        elif terrain == "WaterHole":
            water_locations.append([x, y])
        
        grids.append({
            "grid_id": grid_id_counter,
            "original_grid_id": marker_grid_id,  # 保留原始ID用于追溯
            "q": q_hex,
            "r": r_hex,
            "x": x,
            "y": y,
            "hex_size": int(grid.get("hexSizeNatural", 62)),
            "terrain_type": terrain,
            "fire_risk": fire_risk,
            "terrain_complexity": terrain_complexity,
            "vegetation_type": TERRAIN_TO_VEG[terrain],
            "species_densities": species_densities,
        })
        grid_id_counter += 1
    
    # 构建输出JSON
    output = {
        "map_config": {
            "map_width": map_width,
            "map_height": map_height,
            "boundary_type": "RECTANGLE",
            "road_locations": road_locations,
            "water_locations": water_locations,
        },
        "time": {
            "hour_of_day": args.hour_of_day,
            "season": args.season,
        },
        "use_temporal_factors": args.use_temporal_factors,
        "risk_model_config": {
            "risk_weights": {
                "human_weight": args.human_weight,
                "environmental_weight": args.environmental_weight,
                "density_weight": args.density_weight,
            }
        },
        "species_config": {
            "rhino": {
                "weight": 0.5,
                "rainy_season_multiplier": 1.2,
                "dry_season_multiplier": 1.0,
            },
            "elephant": {
                "weight": 0.3,
                "rainy_season_multiplier": 1.3,
                "dry_season_multiplier": 0.9,
            },
            "bird": {
                "weight": 0.2,
                "rainy_season_multiplier": 1.5,
                "dry_season_multiplier": 0.8,
            },
        },
        "constraints": {
            "total_patrol": args.total_patrol,
            "total_camps": args.total_camps,
            "max_rangers_per_camp": args.max_rangers_per_camp,
            "total_cameras": args.total_cameras,
            "total_drones": args.total_drones,
            "total_fence_length": args.total_fence_length,
        },
        "coverage_params": {
            "patrol_radius": args.patrol_radius,
            "drone_radius": args.drone_radius,
            "camera_radius": args.camera_radius,
            "fence_protection": args.fence_protection,
            "wp": args.wp,
            "wd": args.wd,
            "wc": args.wc,
            "wf": args.wf,
        },
        "dssa_config": {
            "population_size": args.population_size,
            "max_iterations": args.max_iterations,
            "producer_ratio": args.producer_ratio,
            "scout_ratio": args.scout_ratio,
            "ST": args.ST,
            "R2": args.R2,
        },
        "grids": grids,
    }
    
    return output


def parse_args():
    D = DEFAULTS
    p = argparse.ArgumentParser(
        description="从 marker 导出的 grid-coordinates.json 生成 pipeline 输入 JSON",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    p.add_argument("input", help="输入的 grid-coordinates.json 文件路径")
    p.add_argument("-o", "--output", type=str, default="pipeline_input.json", help="输出文件路径")
    p.add_argument("--seed", type=int, default=None, help="随机种子（可复现）")
    
    # 时间配置
    p.add_argument("--hour_of_day", type=int, default=D["hour_of_day"], help="时间（0-23）")
    p.add_argument("--season", type=str, default=D["season"], choices=["DRY", "RAINY"], help="季节")
    p.add_argument("--use_temporal_factors", action="store_true", default=D["use_temporal_factors"],
                   help="启用昼夜/季节时间因子")
    
    # 资源约束
    p.add_argument("--total_patrol",        type=int,   default=D["total_patrol"])
    p.add_argument("--total_camps",         type=int,   default=D["total_camps"])
    p.add_argument("--max_rangers_per_camp",type=int,   default=D["max_rangers_per_camp"])
    p.add_argument("--total_cameras",       type=int,   default=D["total_cameras"])
    p.add_argument("--total_drones",        type=int,   default=D["total_drones"])
    p.add_argument("--total_fence_length",  type=float, default=D["total_fence_length"])
    
    # 覆盖参数
    p.add_argument("--patrol_radius",   type=float, default=D["patrol_radius"])
    p.add_argument("--drone_radius",    type=float, default=D["drone_radius"])
    p.add_argument("--camera_radius",   type=float, default=D["camera_radius"])
    p.add_argument("--fence_protection",type=float, default=D["fence_protection"])
    p.add_argument("--wp", type=float, default=D["wp"], help="巡逻权重")
    p.add_argument("--wd", type=float, default=D["wd"], help="无人机权重")
    p.add_argument("--wc", type=float, default=D["wc"], help="摄像头权重")
    p.add_argument("--wf", type=float, default=D["wf"], help="围栏权重")
    
    # DSSA
    p.add_argument("--population_size", type=int,   default=D["population_size"])
    p.add_argument("--max_iterations",  type=int,   default=D["max_iterations"])
    p.add_argument("--producer_ratio",  type=float, default=D["producer_ratio"])
    p.add_argument("--scout_ratio",     type=float, default=D["scout_ratio"])
    p.add_argument("--ST",              type=float, default=D["ST"])
    p.add_argument("--R2",              type=float, default=D["R2"])
    
    # 风险模型权重
    p.add_argument("--human_weight",        type=float, default=D["human_weight"])
    p.add_argument("--environmental_weight",type=float, default=D["environmental_weight"])
    p.add_argument("--density_weight",      type=float, default=D["density_weight"])
    
    return p.parse_args()


def main():
    args = parse_args()
    
    # 读取 marker 导出的 JSON
    with open(args.input, "r", encoding="utf-8") as f:
        grid_coords = json.load(f)
    
    if not grid_coords:
        print("错误：输入文件为空或格式不正确")
        return
    
    # 转换为 pipeline 输入格式
    output = convert_marker_to_pipeline(grid_coords, args)
    
    # 写入输出文件
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # 统计信息
    terrain_count = {}
    rhino_grids = 0
    elephant_grids = 0
    waterhole_saltmarsh_count = 0
    
    for g in output["grids"]:
        t = g["terrain_type"]
        terrain_count[t] = terrain_count.get(t, 0) + 1
        
        if g["species_densities"]["rhino"] > 0:
            rhino_grids += 1
        if g["species_densities"]["elephant"] > 0:
            elephant_grids += 1
        if t in ["WaterHole", "SaltMarsh"]:
            waterhole_saltmarsh_count += 1
            # 验证约束
            if g["species_densities"]["rhino"] > 0 or g["species_densities"]["elephant"] > 0:
                print(f"警告：网格 {g['original_grid_id']} ({t}) 有犀牛或大象分布！")
    
    print(f"\n转换完成：{len(output['grids'])} 个网格")
    print(f"地形分布：{terrain_count}")
    print(f"道路格子：{len(output['map_config']['road_locations'])} 个")
    print(f"水源格子：{len(output['map_config']['water_locations'])} 个")
    print(f"犀牛分布网格：{rhino_grids} 个")
    print(f"大象分布网格：{elephant_grids} 个")
    print(f"水坑+盐沼网格：{waterhole_saltmarsh_count} 个（犀牛和大象密度应为0）")
    print(f"输出文件：{args.output}")


if __name__ == "__main__":
    main()
