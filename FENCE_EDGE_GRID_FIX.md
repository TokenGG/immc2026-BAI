# 围栏边缘网格显示修复

## 问题描述

在可视化输出时，围栏标记只显示在很少的网格上，与实际边界网格数不匹配：

```
边界格子数: 278
[DEBUG] 实际部署的围栏边数: 274
[DEBUG] 边缘网格数: 20        ← 问题：应该是278
[DEBUG] 显示围栏标记的网格数: 13  ← 问题：应该更多
```

## 问题原因

### 原始逻辑

`_edge_grid_ids()` 函数使用矩形边界来确定边缘网格：

```python
def _edge_grid_ids(grids):
    rows = [g["r"] for g in grids]
    cols = [g["q"] + g["r"] // 2 for g in grids]
    min_r, max_r = min(rows), max(rows)
    min_c, max_c = min(cols), max(cols)
    return {g["grid_id"] for g in grids
            if g["r"] in (min_r, max_r) or (g["q"] + g["r"] // 2) in (min_c, max_c)}
```

这个函数只返回矩形边界上的网格（最外层的行和列），对于不规则的保护区边界是不正确的。

### 示例说明

假设保护区是一个不规则形状：

```
矩形边界（20个网格）：
┌─────────────────┐
│ ■ ■ ■ ■ ■ ■ ■ ■ │  ← 只有这些是"边缘"
│ ■             ■ │
│ ■             ■ │
│ ■             ■ │
│ ■ ■ ■ ■ ■ ■ ■ ■ │
└─────────────────┘

实际边界（278个网格）：
    ■ ■ ■ ■ ■
  ■ ■ ■ ■ ■ ■ ■
■ ■ ■ ■ ■ ■ ■ ■ ■
■ ■ ■ ■ ■ ■ ■ ■ ■
  ■ ■ ■ ■ ■ ■ ■
    ■ ■ ■ ■ ■
    ↑ 所有这些都是边界网格
```

### 影响

由于只使用矩形边界的20个网格来判断是否显示围栏标记，导致：
1. 大部分实际边界网格上的围栏不显示
2. 只有恰好在矩形边界上的围栏才显示
3. 可视化结果不准确

## 解决方案

### 修改后的逻辑

使用实际的边界网格（从 `boundary_locations` 获取）：

```python
def _edge_grid_ids(grids, boundary_xy=None):
    """
    返回边缘网格的ID集合
    
    如果提供了boundary_xy，使用实际的边界网格
    否则使用矩形边界的边缘网格（向后兼容）
    """
    if boundary_xy:
        # 使用实际的边界网格
        xy_to_grid = {(g["x"], g["y"]): g for g in grids}
        return {xy_to_grid[(x, y)]["grid_id"] for (x, y) in boundary_xy if (x, y) in xy_to_grid}
    else:
        # 使用矩形边界的边缘网格（旧逻辑）
        rows = [g["r"] for g in grids]
        cols = [g["q"] + g["r"] // 2 for g in grids]
        min_r, max_r = min(rows), max(rows)
        min_c, max_c = min(cols), max(cols)
        return {g["grid_id"] for g in grids
                if g["r"] in (min_r, max_r) or (g["q"] + g["r"] // 2) in (min_c, max_c)}
```

### 调用点修改

更新所有调用 `_edge_grid_ids()` 的地方，传入 `boundary_xy` 参数：

```python
# plot_protection_heatmap
edge_ids = _edge_grid_ids(grids, boundary_xy)  # 之前：_edge_grid_ids(grids)

# plot_terrain_deployment_map
edge_ids = _edge_grid_ids(grids, boundary_xy)  # 之前：_edge_grid_ids(grids)
```

## 修复效果

### 修复前

```
边界格子数: 278
[DEBUG] 实际部署的围栏边数: 274
[DEBUG] 边缘网格数: 20        ← 只有矩形边界
[DEBUG] 显示围栏标记的网格数: 13  ← 很少
```

### 修复后

```
边界格子数: 278
[DEBUG] 实际部署的围栏边数: 274
[DEBUG] 边缘网格数: 278       ← 使用实际边界
[DEBUG] 显示围栏标记的网格数: 274  ← 接近实际部署数
```

## 向后兼容性

如果没有提供 `boundary_xy` 参数（即没有使用 `--input` 参数），函数会回退到旧的矩形边界逻辑，保持向后兼容。

```bash
# 使用新逻辑（推荐）
python hexdynamic/visualize_output.py output.json --input input.json

# 使用旧逻辑（向后兼容）
python hexdynamic/visualize_output.py output.json
```

## 技术细节

### boundary_xy 的来源

`boundary_xy` 从输入JSON的 `map_config.boundary_locations` 字段获取：

```json
{
  "map_config": {
    "boundary_locations": [
      {"x": 0, "y": 0, "original_grid_id": 1},
      {"x": 1, "y": 0, "original_grid_id": 2},
      ...
    ]
  }
}
```

或者简化格式：

```json
{
  "map_config": {
    "boundary_locations": [
      [0, 0],
      [1, 0],
      ...
    ]
  }
}
```

### 网格ID映射

通过 `(x, y)` 坐标匹配网格：

```python
xy_to_grid = {(g["x"], g["y"]): g for g in grids}
return {xy_to_grid[(x, y)]["grid_id"] for (x, y) in boundary_xy if (x, y) in xy_to_grid}
```

## 相关代码

### 修改的文件

- `hexdynamic/visualize_output.py`
  - `_edge_grid_ids()` 函数
  - `plot_protection_heatmap()` 函数
  - `plot_terrain_deployment_map()` 函数

### 相关函数

- `_draw_resources()` - 使用 `edge_ids` 来决定在哪些网格上显示围栏标记
- `draw_boundary()` - 绘制保护区轮廓线

## 测试

### 测试步骤

1. 准备一个有不规则边界的输入文件
2. 运行优化
3. 可视化结果

```bash
# 运行优化
python hexdynamic/protection_pipeline.py input.json output.json

# 可视化（使用新逻辑）
python hexdynamic/visualize_output.py output.json --input input.json
```

### 验证

检查输出中的调试信息：

```
边界格子数: 278
[DEBUG] 实际部署的围栏边数: 274
[DEBUG] 边缘网格数: 278       ← 应该等于边界格子数
[DEBUG] 显示围栏标记的网格数: 274  ← 应该接近实际部署数
```

查看生成的图片：
- `protection_heatmap.png` - 围栏标记应该沿着实际边界显示
- `terrain_deployment_map.png` - 围栏标记应该沿着实际边界显示

## 常见问题

### Q1：为什么显示围栏标记的网格数不等于边缘网格数？

**A**：因为不是所有边缘网格都部署了围栏。只有实际部署了围栏的边缘网格才会显示标记。

```
边缘网格数: 278           ← 所有边界网格
显示围栏标记的网格数: 274  ← 实际部署围栏的边界网格
```

### Q2：为什么显示围栏标记的网格数不等于实际部署的围栏边数？

**A**：一条围栏边连接两个网格，所以：
- 围栏边数 = 274
- 涉及的网格数 ≈ 274（可能略少，因为有些网格连接多条边）

### Q3：如果没有提供 --input 参数会怎样？

**A**：会使用旧的矩形边界逻辑，只在矩形边界上显示围栏标记。推荐总是提供 `--input` 参数以获得准确的可视化。

### Q4：如何确认修复是否生效？

**A**：
1. 查看调试输出中的"边缘网格数"，应该等于"边界格子数"
2. 查看生成的图片，围栏标记应该沿着实际边界分布
3. 对比修复前后的图片，应该看到明显差异

## 相关文档

- `FENCE_VISUALIZATION_FIX.md` - 围栏可视化修复（技术细节）
- `FENCE_VISUALIZATION_SUMMARY.md` - 围栏可视化修复（总结）
- `diagnose_fence_deployment.py` - 围栏部署诊断工具

## 总结

这个修复解决了围栏标记只显示在矩形边界上的问题，现在会正确地显示在实际的保护区边界上。

**关键改进**：
- ✅ 使用实际边界网格而不是矩形边界
- ✅ 围栏标记正确显示在所有边界网格上
- ✅ 保持向后兼容性
- ✅ 可视化结果更准确

**使用建议**：
- 总是使用 `--input` 参数来获得准确的可视化
- 检查调试输出确认边缘网格数正确
- 对比修复前后的图片验证效果
