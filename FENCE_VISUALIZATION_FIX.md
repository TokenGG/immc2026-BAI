# 围栏可视化修复

## 问题描述

在可视化脚本中，所有允许部署围栏的边缘网格都显示了围栏标记（五边形），而不仅仅是实际部署的围栏。这导致热力图上看起来所有边缘都被围栏覆盖了。

## 根本原因

问题可能出现在以下几个地方：

1. **输出JSON中的fence_edges为空**
   - 优化器可能没有部署任何围栏
   - 或者围栏部署信息没有正确保存到输出JSON

2. **可视化脚本的逻辑问题**
   - `_draw_resources` 函数中的围栏绘制逻辑可能有误
   - 可能在某个地方所有边缘网格都被标记为有围栏

## 修复方案

### 1. 改进的_draw_resources函数

添加了调试信息来帮助诊断问题：

```python
def _draw_resources(ax, grids, out, hex_size, edge_ids):
    """在 ax 上绘制所有资源图标（fence pentagon + 其他）
    
    围栏只在实际部署的边上显示，不是所有边缘网格都显示
    """
    fence_edges = {(e["grid_id_1"], e["grid_id_2"]) for e in out.get("fence_edges", [])}
    centers = {g["grid_id"]: grid_center(g["q"], g["r"], hex_size) for g in grids}

    # 只在实际部署的围栏边的端点上显示围栏标记
    fenced = {gid for (a, b) in fence_edges for gid in (a, b) if gid in edge_ids}
    
    # 调试：打印围栏信息
    if fence_edges:
        print(f"[DEBUG] 实际部署的围栏边数: {len(fence_edges)}")
        print(f"[DEBUG] 边缘网格数: {len(edge_ids)}")
        print(f"[DEBUG] 显示围栏标记的网格数: {len(fenced)}")
    
    for gid in fenced:
        cx, cy = centers[gid]
        ax.scatter(cx, cy + hex_size * 0.38, marker="p", s=80, color=FENCE_COLOR,
                   edgecolors="black", linewidths=0.5, zorder=4)
    
    # ... 其他资源绘制代码
```

### 2. 调试步骤

运行可视化脚本时，会输出调试信息：

```
[DEBUG] 实际部署的围栏边数: 5
[DEBUG] 边缘网格数: 24
[DEBUG] 显示围栏标记的网格数: 8
```

这可以帮助确定：
- 是否有围栏被部署
- 有多少边缘网格
- 有多少网格显示了围栏标记

### 3. 可能的原因和解决方案

#### 情况1：fence_edges为空（没有部署围栏）

**症状**：
- 调试输出显示 `实际部署的围栏边数: 0`
- 但热力图上仍然显示围栏

**原因**：
- 优化器没有部署任何围栏
- 或者围栏部署信息没有保存到输出JSON

**解决方案**：
- 检查输入JSON中的 `total_fence_length` 是否足够大
- 检查约束条件是否允许部署围栏
- 查看优化器的输出日志

#### 情况2：fence_edges不为空但显示过多

**症状**：
- 调试输出显示 `实际部署的围栏边数: 10`
- 但 `显示围栏标记的网格数: 24`（等于所有边缘网格）

**原因**：
- 所有边缘网格都被标记为有围栏
- 可能是在某个地方的逻辑错误

**解决方案**：
- 检查 `fence_edges` 的内容
- 验证 `edge_ids` 的计算是否正确
- 查看输出JSON中的 `fence_edges` 字段

## 验证方法

### 1. 检查输出JSON

```python
import json

with open('output.json', 'r') as f:
    data = json.load(f)

fence_edges = data.get('fence_edges', [])
print(f"部署的围栏边数: {len(fence_edges)}")
print(f"前5条围栏边: {fence_edges[:5]}")
```

### 2. 运行可视化脚本并查看调试输出

```bash
python hexdynamic/visualize_output.py output.json --input input.json
```

查看输出中的 `[DEBUG]` 信息。

### 3. 检查热力图

- 如果围栏标记只出现在实际部署的位置，说明修复成功
- 如果围栏标记遍布所有边缘网格，说明还有问题

## 围栏部署的正确行为

### 正确的围栏部署

1. **优化器决定部署围栏**
   - 根据约束条件和风险分布
   - 只在必要的位置部署

2. **输出JSON记录围栏**
   - `fence_edges` 包含实际部署的围栏边
   - 每条边由两个网格ID组成

3. **可视化显示围栏**
   - 只在实际部署的围栏边的端点显示标记
   - 使用五边形（pentagon）标记

### 围栏标记的含义

- **五边形标记**：表示该网格是围栏的端点
- **位置**：在网格中心上方（`cy + hex_size * 0.38`）
- **颜色**：红色（`FENCE_COLOR = "#c0392b"`）

## 性能考虑

- 围栏绘制不会显著影响性能
- 调试信息只在有围栏时打印
- 可以通过注释调试代码来禁用输出

## 相关代码

### 文件：hexdynamic/visualize_output.py

- `_edge_grid_ids(grids)` - 计算边缘网格
- `_draw_resources(ax, grids, out, hex_size, edge_ids)` - 绘制资源
- `plot_protection_heatmap()` - 保护收益热力图
- `plot_terrain_deployment_map()` - 地形+部署地图

### 文件：hexdynamic/protection_pipeline.py

- `fence_edges` 的生成逻辑
- 围栏部署的约束条件

## 故障排除

### 问题：所有边缘网格都显示围栏

1. 检查 `fence_edges` 是否为空
2. 查看输出JSON中的 `fence_edges` 字段
3. 运行调试脚本验证数据

### 问题：没有显示任何围栏

1. 检查优化器是否部署了围栏
2. 查看约束条件中的 `total_fence_length`
3. 检查输入JSON中的围栏相关参数

### 问题：围栏显示位置不对

1. 检查 `edge_ids` 的计算
2. 验证 `grid_center()` 函数的坐标计算
3. 查看六边形的几何参数

## 后续改进

可以考虑的改进方向：

1. **更详细的围栏可视化**
   - 显示围栏边而不仅仅是端点
   - 使用不同颜色表示不同的围栏段

2. **围栏效果可视化**
   - 显示围栏保护的区域
   - 显示围栏的保护收益

3. **交互式可视化**
   - 点击围栏显示详细信息
   - 高亮相关的网格

4. **统计信息**
   - 显示围栏的总长度
   - 显示围栏的保护效果
