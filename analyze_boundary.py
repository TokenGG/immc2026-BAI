import json

with open("marker/pipeline_input (5).json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 1. 从 map_config.boundary_locations 提取 original_grid_id
boundary_locations = data["map_config"]["boundary_locations"]
boundary_ids = [b["original_grid_id"] for b in boundary_locations]

# 2. 从 grids 数组提取所有 original_grid_id
grids = data["grids"]
grid_ids = set(g["original_grid_id"] for g in grids)

# 3. 找出 boundary 里不在 grids 里的
missing = [bid for bid in boundary_ids if bid not in grid_ids]

# 4. 统计
total_boundary = len(boundary_ids)
total_missing = len(missing)
ratio = total_missing / total_boundary * 100 if total_boundary > 0 else 0

print(f"boundary_locations 总数:          {total_boundary}")
print(f"不在 grids 里的数量 (colorTag=0): {total_missing}")
print(f"占比:                              {ratio:.2f}%")
print()

# 5. 前 10 个示例
print("前 10 个不在 grids 里的 boundary original_grid_id：")
for i, bid in enumerate(missing[:10], 1):
    print(f"  {i:2d}. {bid}")
