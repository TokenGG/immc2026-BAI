import json
from collections import Counter

# ── 1. 读取 grid-coordinates.json ──────────────────────────────────────────
with open("marker/grid-coordinates.json", encoding="utf-8") as f:
    grid_coords = json.load(f)

# 建立 gridId -> 记录 的索引（grid-coordinates.json 用 gridId 字段）
grid_index = {item["gridId"]: item for item in grid_coords}

# 统计 colorTag 分布
color_tag_counter = Counter(item.get("colorTag") for item in grid_coords)
print("=" * 50)
print("1. colorTag 分布（grid-coordinates.json）")
print("=" * 50)
for tag, count in sorted(color_tag_counter.items(), key=lambda x: (x[0] is None, x[0])):
    print(f"  colorTag={tag}: {count} 个")
print(f"  总计: {len(grid_coords)} 个格子\n")

# ── 2. 读取 pipeline_input (5).json，取前 5 个格子的 original_grid_id ──────
with open("marker/pipeline_input (5).json", encoding="utf-8") as f:
    pipeline = json.load(f)

grids = pipeline.get("grids", [])
top5_grids = grids[:5]
top5_ids = [g["original_grid_id"] for g in top5_grids]

print("=" * 50)
print("2. pipeline_input (5).json grids 前 5 个格子的 original_grid_id")
print("=" * 50)
for i, gid in enumerate(top5_ids, 1):
    print(f"  [{i}] {gid}")
print()

# ── 3. 用这些 id 查 colorTag ───────────────────────────────────────────────
print("=" * 50)
print("3. 前 5 个格子在 grid-coordinates.json 中的 colorTag")
print("=" * 50)
for gid in top5_ids:
    rec = grid_index.get(gid)
    if rec:
        print(f"  {gid} -> colorTag={rec.get('colorTag')}, color={rec.get('color')}")
    else:
        print(f"  {gid} -> 未找到")
print()

# ── 4. boundary_locations 里的格子，查 grid-coordinates 中 colorTag=0 的 ──
# boundary_locations 在 map_config 下，格子本身无 colorTag，需去 grid_index 查
boundary = pipeline["map_config"].get("boundary_locations", [])
print(f"  boundary_locations 总数: {len(boundary)}")

# 找出在 grid-coordinates 中 colorTag=0 的 boundary 格子
bl_ct0 = []
for g in boundary:
    gid = g["original_grid_id"]
    rec = grid_index.get(gid)
    if rec and rec.get("colorTag") == 0:
        bl_ct0.append((gid, rec))

print("=" * 50)
print(f"4. boundary_locations 中对应 colorTag=0 的格子共 {len(bl_ct0)} 个，取前 5 个查 color 字段")
print("=" * 50)
for gid, rec in bl_ct0[:5]:
    print(f"  {gid} -> color={rec.get('color')}, colorTag={rec.get('colorTag')}")
print()
