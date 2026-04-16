# 热力图颜色条标准化

## 目标

统一所有热力图的颜色条范围为 [0, 1]，便于跨场景横向对比。

## 修改内容

### 1. risk_analysis.py

#### plot_risk_heatmap 函数
**修改前**：
```python
norm = Normalize(vmin=0, vmax=1)  # 已经是 [0, 1]
```

**修改后**：
```python
# 使用统一的 [0, 1] 范围便于跨场景对比
norm = Normalize(vmin=0, vmax=1)
```

**改进**：
- 添加了清晰的注释说明使用 [0, 1] 范围的原因
- 更新了标题为 "Composite Risk Index Heatmap (Normalized)"
- 更新了颜色条标签为 "Normalized Risk [0, 1]"

#### plot_raw_risk_heatmap 函数
**修改前**：
```python
vmin, vmax = min(raw_vals), max(raw_vals)
norm = Normalize(vmin=vmin, vmax=vmax)  # 使用数据的实际范围
```

**修改后**：
```python
# 使用统一的 [0, 1] 范围便于跨场景对比
# 注意：原始风险值可能超过 1.0，会被截断到 [0, 1]
norm = Normalize(vmin=0, vmax=1)
```

**改进**：
- 改为使用统一的 [0, 1] 范围
- 添加了说明超过 1.0 的值会被截断的注释
- 在图例中添加了 "Note: Values > 1.0 shown as max color" 提示
- 更新了颜色条标签为 "Raw Risk [0, 1]"

### 2. visualization.py

#### plot_risk_heatmap 函数
**修改前**：
```python
max_risk = max(risk_values.values()) if risk_values else 1.0
min_risk = min(risk_values.values()) if risk_values else 0.0

for grid_id in self.grid_ids:
    normalized_risk = (risk - min_risk) / (max_risk - min_risk) if max_risk > min_risk else 0.5
    color = cmap(normalized_risk)

sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=min_risk, vmax=max_risk))
```

**修改后**：
```python
# 使用统一的 [0, 1] 范围便于跨场景对比
for grid_id in self.grid_ids:
    risk = risk_values[grid_id]
    # 直接使用风险值作为颜色映射（已经是 [0, 1] 范围）
    color = cmap(risk)

# 使用统一的 [0, 1] 范围的颜色条
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=1))
```

**改进**：
- 移除了本地归一化逻辑（因为风险值已经是 [0, 1]）
- 直接使用风险值作为颜色映射
- 使用统一的 [0, 1] 范围的颜色条
- 更新了标题为 "Risk Heatmap (Normalized)"
- 更新了颜色条标签为 "Normalized Risk [0, 1]"

#### plot_protection_coverage 函数
**状态**：已经使用 [0, 1] 范围，无需修改
```python
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=1))
```

### 3. visualize_output.py

#### plot_risk_heatmap 函数
**状态**：已经使用 [0, 1] 范围，无需修改
```python
norm = Normalize(vmin=0, vmax=1)
```

#### plot_protection_heatmap 函数
**状态**：已经使用 [0, 1] 范围，无需修改
```python
norm = Normalize(vmin=0, vmax=1)
```

---

## 颜色条范围对比

### 修改前

| 脚本 | 函数 | 范围 | 说明 |
|------|------|------|------|
| risk_analysis.py | plot_risk_heatmap | [0, 1] | 已正确 |
| risk_analysis.py | plot_raw_risk_heatmap | [min, max] | **需要修改** |
| visualization.py | plot_risk_heatmap | [min, max] | **需要修改** |
| visualization.py | plot_protection_coverage | [0, 1] | 已正确 |
| visualize_output.py | plot_risk_heatmap | [0, 1] | 已正确 |
| visualize_output.py | plot_protection_heatmap | [0, 1] | 已正确 |

### 修改后

| 脚本 | 函数 | 范围 | 说明 |
|------|------|------|------|
| risk_analysis.py | plot_risk_heatmap | [0, 1] | ✓ 统一 |
| risk_analysis.py | plot_raw_risk_heatmap | [0, 1] | ✓ 统一 |
| visualization.py | plot_risk_heatmap | [0, 1] | ✓ 统一 |
| visualization.py | plot_protection_coverage | [0, 1] | ✓ 统一 |
| visualize_output.py | plot_risk_heatmap | [0, 1] | ✓ 统一 |
| visualize_output.py | plot_protection_heatmap | [0, 1] | ✓ 统一 |

---

## 使用示例

### 对比不同场景的风险热力图

```bash
# 生成 Day 场景的热力图
python risk_analysis.py input-day-rainy.json figures-day

# 生成 Night 场景的热力图
python risk_analysis.py input-night-rainy.json figures-night

# 现在可以直接对比两张热力图
# - figures-day/risk_heatmap.png
# - figures-night/risk_heatmap.png
# - figures-day/raw_risk_heatmap.png
# - figures-night/raw_risk_heatmap.png
# 
# 所有热力图都使用相同的 [0, 1] 颜色条范围，便于直观对比
```

### 对比部署前后的风险

```bash
# 运行优化
python protection_pipeline.py input-night-rainy.json output-night.json

# 生成可视化
python visualize_output.py output-night.json --input input-night-rainy.json --out_dir figures-night

# 对比热力图
# - figures-night/risk_heatmap.png (部署前风险)
# - figures-night/risk_comparison.png (部署前后对比)
# 
# 两张图都使用相同的 [0, 1] 颜色条范围
```

---

## 优势

### 1. 跨场景对比
- 不同时段（Day/Night）的热力图可以直接对比
- 不同季节（Dry/Rainy）的热力图可以直接对比
- 相同的颜色表示相同的风险水平

### 2. 直观理解
- 红色总是表示高风险（接近 1.0）
- 黄色总是表示中等风险（接近 0.5）
- 浅黄色总是表示低风险（接近 0.0）

### 3. 一致性
- 所有热力图使用相同的颜色条范围
- 用户不需要重新调整视觉参考
- 便于报告和演示

---

## 特殊情况处理

### 原始风险值超过 1.0

在 `plot_raw_risk_heatmap` 中，原始风险值可能超过 1.0（特别是启用时间因子时）。

**处理方式**：
- 颜色条范围仍然是 [0, 1]
- 超过 1.0 的值会被映射到最深的红色
- 在图例中添加了提示："Note: Values > 1.0 shown as max color"

**示例**：
```
Night Rainy 场景：
  raw_risk_mean = 0.162565
  raw_risk_max = 0.559495
  
  所有值都在 [0, 1] 范围内，正常显示

Day Rainy 场景（如果启用时间因子）：
  raw_risk_mean = 0.162565 × 1.2 = 0.195078
  raw_risk_max = 0.559495 × 1.2 = 0.671394
  
  所有值都在 [0, 1] 范围内，正常显示

Night Rainy 场景（如果启用时间因子）：
  raw_risk_mean = 0.162565 × 1.56 = 0.253599
  raw_risk_max = 0.559495 × 1.56 = 0.872812
  
  所有值都在 [0, 1] 范围内，正常显示
```

---

## 验证清单

- [x] risk_analysis.py - plot_risk_heatmap 使用 [0, 1]
- [x] risk_analysis.py - plot_raw_risk_heatmap 使用 [0, 1]
- [x] visualization.py - plot_risk_heatmap 使用 [0, 1]
- [x] visualization.py - plot_protection_coverage 已使用 [0, 1]
- [x] visualize_output.py - plot_risk_heatmap 已使用 [0, 1]
- [x] visualize_output.py - plot_protection_heatmap 已使用 [0, 1]
- [x] 所有颜色条标签已更新为 "[0, 1]"
- [x] 所有标题已更新为 "(Normalized)"

---

## 总结

✓ **所有热力图颜色条已标准化为 [0, 1]**

- 便于跨场景横向对比
- 提高了可视化的一致性
- 用户可以直观理解风险水平

