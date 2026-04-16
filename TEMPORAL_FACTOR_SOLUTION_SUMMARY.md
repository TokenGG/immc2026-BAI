# 时间因子显示方案实现总结

## 问题回顾

用户发现启用 `use_temporal_factors: true` 后，day 和 night 场景的**归一化风险统计指标相同**（min/max/mean），尽管原始风险相差 1.3 倍。这引发两个关键问题：

1. **如何显示时间因子的影响？**
2. **这对资源部署策略有什么影响？**

---

## 根本原因分析

### 数值验证

```
Day (hour=12):
  Raw risks:        min=0.053739  max=0.430381  mean=0.125050
  Normalized risks: min=0.000000  max=1.000000  mean=0.189335

Night (hour=23):
  Raw risks:        min=0.069860  max=0.559495  mean=0.162565
  Normalized risks: min=0.000000  max=1.000000  mean=0.189335

Ratio (Night raw / Day raw): 1.3000 (exactly the diurnal factor)
```

### 数学解释

Min-max 归一化公式：
```
R_normalized = (R_raw - R_min) / (R_max - R_min)
```

当所有风险都乘以相同的时间因子 T 时：
```
R_normalized_night = (T×R_raw - T×R_min) / (T×R_max - T×R_min)
                   = T×(R_raw - R_min) / (T×(R_max - R_min))
                   = (R_raw - R_min) / (R_max - R_min)
                   = R_normalized_day
```

**结论**：分子分母同时乘以 T，相消，导致归一化结果相同。

---

## 对资源部署策略的影响

### DSSA 优化目标

```python
fitness = total_protection_benefit / total_risk
        = Σ [R_i × (1 - e^(-E_i))] / Σ R_i
```

### 时间因子的影响

```
fitness_night = Σ [1.3×R_i × (1 - e^(-E_i))] / Σ [1.3×R_i]
              = 1.3 × Σ [R_i × (1 - e^(-E_i))] / (1.3 × Σ R_i)
              = fitness_day
```

### 实际后果

| 方面 | 影响 |
|------|------|
| **资源分配优先级** | 相同（高风险格子优先级不变） |
| **部署数量** | 相同（总资源约束不变） |
| **部署位置** | 相同（相对风险排序不变） |
| **保护效率** | 相同（fitness 值相同） |
| **绝对保护收益** | 不同（夜间 1.3 倍） |

**关键发现**：虽然启用了时间因子，但对 DSSA 优化的资源分配**没有影响**。

---

## 实现方案：方案 A（显示原始风险热力图）

### 修改内容

#### 1. 修改 `hexdynamic/risk_analysis.py`

**改动 1**：修改 `compute_risk()` 函数返回两种风险值

```python
def compute_risk(data: dict) -> Tuple[Dict[int, float], Dict[int, float]]:
    """
    Compute both normalized and raw risk values.
    
    Returns:
        Tuple of (normalized_risks, raw_risks) dictionaries
    """
    # ... 现有代码 ...
    results = model.calculate_batch(grid_data_list, time_context, use_temporal_factors=use_temporal)
    
    normalized_risks = {id_order[i]: float(r.normalized_risk) for i, r in enumerate(results)}
    raw_risks = {id_order[i]: float(r.raw_risk) for i, r in enumerate(results)}
    
    return normalized_risks, raw_risks
```

**改动 2**：添加 `plot_raw_risk_heatmap()` 函数

```python
def plot_raw_risk_heatmap(grids: list, raw_risk_map: Dict[int, float],
                          hex_size: float = 1.0, save_path: str = None):
    """Plot raw risk heatmap (preserves temporal factors)."""
    cmap = matplotlib.colormaps.get_cmap("YlOrRd")
    
    raw_vals = list(raw_risk_map.values())
    vmin, vmax = min(raw_vals), max(raw_vals)
    norm = Normalize(vmin=vmin, vmax=vmax)

    fig, ax, ax_cbar, ax_leg = make_figure(has_colorbar=True)

    for g in grids:
        gid = g['grid_id']
        risk = raw_risk_map.get(gid, 0.0)
        cx, cy = grid_center(g["q"], g["r"], hex_size)
        draw_hex(ax, cx, cy, hex_size * 0.97, facecolor=cmap(norm(risk)))

    setup_map_ax(ax, grids, hex_size)
    ax.set_title("Raw Risk Index Heatmap (with Temporal Factors)", fontsize=13, fontweight="bold", pad=8)
    add_colorbar(fig, ax_cbar, cmap, norm, "Raw Risk")
    
    # ... 添加统计信息 ...
```

**改动 3**：修改 `run()` 函数

```python
def run(input_path: str, output_dir: str, hex_size: float = None):
    # ... 加载和初始化 ...
    
    # 计算两种风险值
    normalized_risks, raw_risks = compute_risk(data)
    
    # 生成两张热力图
    plot_risk_heatmap(grids, normalized_risks, hex_size,
                      save_path=os.path.join(output_dir, 'risk_heatmap.png'))
    plot_raw_risk_heatmap(grids, raw_risks, hex_size,
                          save_path=os.path.join(output_dir, 'raw_risk_heatmap.png'))
    
    # JSON 输出包含两种风险值
    json.dump({
        'summary': {
            'normalized_risk_min': ...,
            'normalized_risk_max': ...,
            'normalized_risk_mean': ...,
            'raw_risk_min': ...,
            'raw_risk_max': ...,
            'raw_risk_mean': ...,
            'temporal_factor': ...  # 仅当启用时间因子时
        },
        'grids': [
            {
                'grid_id': ...,
                'normalized_risk': ...,
                'raw_risk': ...,
                ...
            }
        ]
    }, f)
```

### 2. 输出文件

```
figures-day-rainy/
├── risk_heatmap.png          # 归一化风险 [0,1]
├── raw_risk_heatmap.png      # 原始风险（保留时间因子）
├── attributes_map.png        # 地理+物种属性
└── risk_results.json         # 包含两种风险值

figures-night-rainy/
├── risk_heatmap.png          # 归一化风险 [0,1]（与 day 相同）
├── raw_risk_heatmap.png      # 原始风险（×1.3 倍）
├── attributes_map.png        # 地理+物种属性
└── risk_results.json         # 包含两种风险值
```

### 3. JSON 输出示例

```json
{
  "summary": {
    "total_grids": 2648,
    "normalized_risk_min": 0.0,
    "normalized_risk_max": 1.0,
    "normalized_risk_mean": 0.189335,
    "raw_risk_min": 0.053739,
    "raw_risk_max": 0.430381,
    "raw_risk_mean": 0.12505,
    "temporal_factor": 1.0  // Day 场景
  },
  "grids": [
    {
      "grid_id": 0,
      "q": 0, "r": 0,
      "normalized_risk": 0.35,
      "raw_risk": 0.053739,
      "vegetation_type": "GRASSLAND",
      ...
    }
  ]
}
```

Night 场景的 `raw_risk_mean` 会是 `0.162565`（×1.3 倍）。

---

## 测试结果

### Day 场景

```
[1/3] Loading input: input-day-rainy.json
      Loaded 2648 grids
      Auto-detected hex_size: 62.0
[2/3] Computing composite risk index...
      Computed risk for 2648 grids
      Normalized: min=0.0000  max=1.0000  mean=0.1893
      Raw       : min=0.053739  max=0.430381  mean=0.125050
[3/3] Generating maps...
  Risk heatmap saved -> figures-day-rainy\risk_heatmap.png
  Raw risk heatmap saved -> figures-day-rainy\raw_risk_heatmap.png
  Attributes map saved -> figures-day-rainy\attributes_map.png
  Risk results saved -> figures-day-rainy\risk_results.json
```

### Night 场景

```
[1/3] Loading input: input-night-rainy.json
      Loaded 2648 grids
      Auto-detected hex_size: 62.0
[2/3] Computing composite risk index...
      Computed risk for 2648 grids
      Normalized: min=0.0000  max=1.0000  mean=0.1893
      Raw       : min=0.069860  max=0.559495  mean=0.162565
[3/3] Generating maps...
  Risk heatmap saved -> figures-night-rainy\risk_heatmap.png
  Raw risk heatmap saved -> figures-night-rainy\raw_risk_heatmap.png
  Attributes map saved -> figures-night-rainy\attributes_map.png
  Risk results saved -> figures-night-rainy\risk_results.json
```

**验证**：
- 归一化风险的 mean 相同（0.1893）
- 原始风险的 mean 相差 1.3 倍（0.162565 / 0.125050 = 1.3）

---

## 文档更新

### 更新内容

1. **docs/usage.md - 第四节（风险分析脚本）**
   - 添加 `raw_risk_heatmap.png` 输出说明
   - 解释两种风险值的区别
   - 添加使用场景表格

2. **docs/usage.md - 新增第七节（时间因子与资源部署策略）**
   - 解释为什么 DSSA 优化结果相同
   - 数学推导
   - 实际应用建议

### 关键文档内容

**两种风险值的用途**：

| 风险值 | 范围 | 用途 | 特点 |
|--------|------|------|------|
| **归一化风险** | [0, 1] | DSSA 优化、跨时段对比 | 不同时段的相对排序一致 |
| **原始风险** | 取决于输入 | 绝对风险评估、时间感知决策 | 保留时间因子的绝对差异 |

**实际应用建议**：

1. **日常监测**：使用归一化风险进行 DSSA 优化
2. **时间分析**：对比原始风险热力图，识别高风险时段
3. **决策支持**：结合两种风险值，制定时间感知的巡逻计划
4. **资源调度**：根据季节和昼夜周期动态调整部署方案

---

## 优缺点分析

### 方案 A 的优点

✓ 保留时间因子的绝对差异  
✓ 不改变 DSSA 优化算法  
✓ 用户可同时看到两种视角  
✓ 实现简单，改动最小  
✓ 向后兼容  

### 方案 A 的缺点

✗ DSSA 优化结果仍然相同  
✗ 不能自动调整资源分配  
✗ 需要用户手动解读两张热力图  

---

## 后续可选方案

### 方案 B：时间感知的资源分配

**思路**：修改 DSSA 目标函数，使用时间加权的总风险

```python
# 当前
fitness = total_benefit / total_risk

# 修改后
fitness = total_benefit / total_risk_weighted
total_risk_weighted = Σ [R_i × T_t × S_t]
```

**结果**：夜间部署更多资源

**优点**：资源分配反映时间维度的风险差异  
**缺点**：改变算法，需要重新验证，可能导致部署过度

### 方案 C：分时段优化

**思路**：为不同时段分别运行 DSSA

**结果**：输出多套部署方案（day_solution, night_solution）

**优点**：完全保留时间维度信息  
**缺点**：计算量翻倍，部署方案可能冲突

---

## 总结

**已实现**：方案 A（显示原始风险热力图）
- 修改 `risk_analysis.py` 输出两种风险值
- 生成 `raw_risk_heatmap.png` 和 `risk_heatmap.png`
- 更新文档说明两种风险的含义和用途
- 验证了时间因子的绝对差异（1.3 倍）

**用户可以**：
1. 对比两张热力图，直观看到时间维度的风险差异
2. 在 JSON 中查看原始风险值
3. 根据实际需求制定时间感知的巡逻计划
4. 理解为什么 DSSA 优化结果相同（归一化的数学特性）

**如果需要**：
- 自动调整资源分配：考虑方案 B（修改 DSSA 目标函数）
- 多时段部署方案：考虑方案 C（分时段优化）

