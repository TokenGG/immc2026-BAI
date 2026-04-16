# 风险对比图没有差异问题修复

## 问题描述

部署保护资源前后的风险指数热力图看起来没有差异，两张图几乎一模一样。

## 问题根源

### 当前实现

```python
# 在 protection_pipeline.py 中
rr_per_grid = {
    gid: grid_model.get_grid_risk(gid) * np.exp(-coverage_model.calculate_protection_effect(best_solution)[gid])
    for gid in grid_model.get_all_grid_ids()
}
rr_vals = list(rr_per_grid.values())
rr_min, rr_max = min(rr_vals), max(rr_vals)

def norm_rr(v):
    return float((v - rr_min) / (rr_max - rr_min)) if rr_max != rr_min else float(v)

# 输出
'risk_normalized': round(float(grid.risk), 6),  # 已归一化 [0, 1]
'residual_risk_normalized': round(norm_rr(rr_per_grid[gid]), 6),  # 独立归一化 [0, 1]
```

### 问题

1. `risk_normalized` 在 riskIndex 模块中归一化（基于所有网格的风险范围）
2. `residual_risk_normalized` 在 protection_pipeline 中独立归一化（基于剩余风险的范围）
3. 两个字段都映射到 [0, 1]，但使用了**不同的归一化基准**
4. 在可视化时，两者都映射到相同的颜色范围，导致看起来没有差异

### 示例

假设：
- 部署前风险范围：[0.2, 0.8]
- 部署后剩余风险范围：[0.1, 0.4]

当前实现：
```
网格A：
  risk_normalized = (0.8 - 0.2) / (0.8 - 0.2) = 1.0  → 红色
  residual_risk = 0.4
  residual_risk_normalized = (0.4 - 0.1) / (0.4 - 0.1) = 1.0  → 红色（看起来一样！）

网格B：
  risk_normalized = (0.2 - 0.2) / (0.8 - 0.2) = 0.0  → 黄色
  residual_risk = 0.1
  residual_risk_normalized = (0.1 - 0.1) / (0.4 - 0.1) = 0.0  → 黄色（看起来一样！）
```

## 解决方案

### 方案1：使用统一的归一化基准（推荐）

使用部署前的风险范围作为统一基准：

```python
# 计算部署前风险的范围
risk_vals = [grid_model.get_grid_risk(gid) for gid in grid_model.get_all_grid_ids()]
risk_min, risk_max = min(risk_vals), max(risk_vals)

# 使用相同的归一化函数
def norm_unified(v):
    return float((v - risk_min) / (risk_max - risk_min)) if risk_max != risk_min else float(v)

# 归一化部署前风险
risk_normalized = {gid: norm_unified(grid_model.get_grid_risk(gid)) for gid in grid_model.get_all_grid_ids()}

# 归一化部署后剩余风险（使用相同的基准）
rr_per_grid = {
    gid: grid_model.get_grid_risk(gid) * np.exp(-coverage_model.calculate_protection_effect(best_solution)[gid])
    for gid in grid_model.get_all_grid_ids()
}
residual_risk_normalized = {gid: norm_unified(rr_per_grid[gid]) for gid in grid_model.get_all_grid_ids()}
```

### 方案2：保存原始值并在可视化时归一化

保存原始值，在可视化时使用统一的归一化：

```python
# 在 protection_pipeline.py 中保存原始值
'risk_raw': round(float(grid_model.get_grid_risk(gid)), 6),
'residual_risk_raw': round(float(rr_per_grid[gid]), 6),

# 在 visualize_output.py 中统一归一化
all_risks = [g["risk_raw"] for g in grids]
all_residuals = [g["residual_risk_raw"] for g in grids]
risk_min = min(all_risks + all_residuals)
risk_max = max(all_risks + all_residuals)
norm = Normalize(vmin=risk_min, vmax=risk_max)
```

### 方案3：显示绝对差异

直接显示保护收益（风险减少量）：

```python
# 计算风险减少量
risk_reduction = {
    gid: grid_model.get_grid_risk(gid) - rr_per_grid[gid]
    for gid in grid_model.get_all_grid_ids()
}

# 可视化风险减少量
# 这样可以直观看到哪些区域受益最多
```

## 推荐实现

采用方案1，修改 `protection_pipeline.py`：

```python
print("[4/4] Compute metrics and write output...")
pb_per_grid = coverage_model.calculate_protection_benefit(best_solution)
total_risk = sum(grid_model.get_grid_risk(gid) for gid in grid_model.get_all_grid_ids())
total_protection_benefit = sum(pb_per_grid.values())
avg_protection_benefit = float(np.mean(list(pb_per_grid.values())))

# 获取所有网格的原始风险值
risk_vals = [grid_model.get_grid_risk(gid) for gid in grid_model.get_all_grid_ids()]
risk_min, risk_max = min(risk_vals), max(risk_vals)

# 统一的归一化函数（基于部署前风险范围）
def norm_unified_risk(v):
    return float((v - risk_min) / (risk_max - risk_min)) if risk_max != risk_min else float(v)

# 计算剩余风险
rr_per_grid = {
    gid: grid_model.get_grid_risk(gid) * np.exp(-coverage_model.calculate_protection_effect(best_solution)[gid])
    for gid in grid_model.get_all_grid_ids()
}

# 归一化保护收益
pb_vals = list(pb_per_grid.values())
pb_min, pb_max = min(pb_vals), max(pb_vals)

def norm_pb(v):
    return float((v - pb_min) / (pb_max - pb_min)) if pb_max != pb_min else float(v)

# 输出时使用统一的归一化
input_grid_map = {g['grid_id']: g for g in data['grids']}
grid_results = []
for grid in loader.grids:
    gid = grid.grid_id
    src = input_grid_map.get(gid, {})
    entry = {
        'grid_id': gid,
        'q': grid.q,
        'r': grid.r,
        'x': src.get('x', 0),
        'y': src.get('y', 0),
        'terrain_type': grid.terrain_type,
        'risk_normalized': round(norm_unified_risk(grid_model.get_grid_risk(gid)), 6),  # 使用统一归一化
        'residual_risk_normalized': round(norm_unified_risk(rr_per_grid[gid]), 6),  # 使用统一归一化
        'protection_benefit_raw': round(float(pb_per_grid[gid]), 6),
        'protection_benefit_normalized': round(norm_pb(pb_per_grid[gid]), 6),
        'deployment': {
            'patrol_rangers': int(best_solution.rangers.get(gid, 0)),
            'camp': int(best_solution.camps.get(gid, 0)),
            'drone': int(best_solution.drones.get(gid, 0)),
            'camera': int(best_solution.cameras.get(gid, 0))
        }
    }
    if 'hex_size' in src:
        entry['hex_size'] = src['hex_size']
    grid_results.append(entry)
```

## 修复效果

### 修复前
```
网格A：
  risk_normalized = 1.0 → 红色
  residual_risk_normalized = 1.0 → 红色（看起来一样）
```

### 修复后
```
网格A：
  risk_normalized = 1.0 → 红色
  residual_risk_normalized = 0.5 → 橙色（明显不同！）
```

## 注意事项

1. **向后兼容性**：这个修改会改变 `risk_normalized` 的值，可能影响现有的分析脚本
2. **riskIndex 模块**：需要确认 `grid.risk` 是否已经归一化
3. **测试**：需要测试修复后的效果

## 验证方法

```bash
# 运行优化
python hexdynamic/protection_pipeline.py input.json output.json

# 可视化
python hexdynamic/visualize_output.py output.json --input input.json

# 检查 risk_comparison.png
# 应该看到明显的颜色差异
```

## 相关文档

- `RESIDUAL_RISK_FIX.md` - 剩余风险计算修复（之前的修复）
- 本次修复解决的是归一化问题，不是计算公式问题
