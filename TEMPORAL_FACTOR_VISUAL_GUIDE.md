# 时间因子可视化指南

## 快速对比

### 数据对比表

| 指标 | Day (hour=12) | Night (hour=23) | 比率 |
|------|---------------|-----------------|------|
| **归一化风险 min** | 0.0000 | 0.0000 | 1.0 |
| **归一化风险 max** | 1.0000 | 1.0000 | 1.0 |
| **归一化风险 mean** | 0.189335 | 0.189335 | 1.0 |
| **原始风险 min** | 0.053739 | 0.069860 | 1.30 |
| **原始风险 max** | 0.430381 | 0.559495 | 1.30 |
| **原始风险 mean** | 0.125050 | 0.162565 | 1.30 |

### 关键发现

1. **归一化风险完全相同** → DSSA 优化结果相同
2. **原始风险相差 1.3 倍** → 时间因子的绝对影响
3. **比率恒定为 1.3** → 所有格子都乘以相同的时间因子

---

## 热力图对比

### 归一化风险热力图 (risk_heatmap.png)

```
Day 场景                          Night 场景
┌─────────────────────┐          ┌─────────────────────┐
│                     │          │                     │
│   [视觉效果相同]     │          │   [视觉效果相同]     │
│                     │          │                     │
│  黄色 → 橙色 → 红色  │          │  黄色 → 橙色 → 红色  │
│  [0.0]    [0.5]   [1.0]        │  [0.0]    [0.5]   [1.0]
│                     │          │                     │
└─────────────────────┘          └─────────────────────┘
```

**特点**：
- 两张图完全相同
- 用于 DSSA 优化
- 便于跨时段对比

### 原始风险热力图 (raw_risk_heatmap.png)

```
Day 场景                          Night 场景
┌─────────────────────┐          ┌─────────────────────┐
│                     │          │                     │
│   [偏黄色调]        │          │   [偏红色调]        │
│                     │          │                     │
│  黄色 → 浅橙 → 橙色 │          │  橙色 → 深红 → 暗红 │
│  [0.05]  [0.24]  [0.43]        │  [0.07]  [0.31]  [0.56]
│                     │          │                     │
└─────────────────────┘          └─────────────────────┘
```

**特点**：
- 两张图颜色分布不同
- Night 更红（风险更高）
- 保留时间因子的绝对差异
- 用于绝对风险评估

---

## 使用场景

### 场景 1：DSSA 优化

**使用**：归一化风险热力图 + risk_heatmap.png

```
输入：input-day-rainy.json
↓
运行：python protection_pipeline.py input-day-rainy.json output.json
↓
输出：部署方案（与 night 场景相同）
```

**原因**：DSSA 优化基于相对风险排序，时间因子不影响优化结果

---

### 场景 2：时间维度风险分析

**使用**：原始风险热力图 + raw_risk_heatmap.png

```
对比 Day 和 Night 的 raw_risk_heatmap.png
↓
识别高风险时段和区域
↓
制定时间感知的巡逻计划
```

**示例**：
- 某区域在 Night 的风险是 Day 的 1.3 倍
- 应在 Night 增加巡逻频率或部署更多摄像头
- 但 DSSA 优化不会自动调整（因为相对排序不变）

---

### 场景 3：决策支持

**使用**：两种风险值结合

```
Step 1: 运行 DSSA 优化
        python protection_pipeline.py input-day-rainy.json output.json
        → 获得基准部署方案

Step 2: 分析原始风险
        python risk_analysis.py input-day-rainy.json figures-day
        python risk_analysis.py input-night-rainy.json figures-night
        → 对比 raw_risk_heatmap.png

Step 3: 制定时间感知策略
        - 白天：按 DSSA 方案部署
        - 夜间：增加巡逻频率（×1.3）或摄像头覆盖
```

---

## JSON 数据解读

### 查看原始风险值

```bash
# 提取 Day 场景的原始风险统计
python -c "
import json
with open('figures-day-rainy/risk_results.json') as f:
    data = json.load(f)
    s = data['summary']
    print(f'Day raw risk:   min={s[\"raw_risk_min\"]:.6f}  max={s[\"raw_risk_max\"]:.6f}  mean={s[\"raw_risk_mean\"]:.6f}')
"

# 提取 Night 场景的原始风险统计
python -c "
import json
with open('figures-night-rainy/risk_results.json') as f:
    data = json.load(f)
    s = data['summary']
    print(f'Night raw risk: min={s[\"raw_risk_min\"]:.6f}  max={s[\"raw_risk_max\"]:.6f}  mean={s[\"raw_risk_mean\"]:.6f}')
"
```

### 查看单个格子的两种风险值

```bash
python -c "
import json
with open('figures-day-rainy/risk_results.json') as f:
    day_data = json.load(f)
with open('figures-night-rainy/risk_results.json') as f:
    night_data = json.load(f)

# 查看格子 0 的风险值
day_grid = day_data['grids'][0]
night_grid = night_data['grids'][0]

print(f'Grid 0:')
print(f'  Day   - normalized: {day_grid[\"normalized_risk\"]:.6f}  raw: {day_grid[\"raw_risk\"]:.6f}')
print(f'  Night - normalized: {night_grid[\"normalized_risk\"]:.6f}  raw: {night_grid[\"raw_risk\"]:.6f}')
print(f'  Ratio (night/day) raw: {night_grid[\"raw_risk\"] / day_grid[\"raw_risk\"]:.4f}')
"
```

---

## 常见问题

### Q1: 为什么 DSSA 优化结果相同？

**A**: 因为 DSSA 的目标函数中，分子分母都乘以相同的时间因子，相消了。

```
fitness = Σ [R_i × (1 - e^(-E_i))] / Σ R_i

fitness_night = Σ [1.3×R_i × (1 - e^(-E_i))] / Σ [1.3×R_i]
              = 1.3 × Σ [R_i × (1 - e^(-E_i))] / (1.3 × Σ R_i)
              = fitness_day
```

### Q2: 如何让 DSSA 优化考虑时间因子？

**A**: 有两种方法：

1. **修改 DSSA 目标函数**（方案 B）
   - 使用时间加权的总风险
   - 结果：夜间部署更多资源
   - 需要重新验证算法

2. **分时段优化**（方案 C）
   - 为 day 和 night 分别运行 DSSA
   - 输出两套部署方案
   - 用户选择或融合

### Q3: 原始风险和归一化风险哪个更重要？

**A**: 取决于用途：

| 用途 | 使用 | 原因 |
|------|------|------|
| DSSA 优化 | 归一化 | 已内置在算法中 |
| 跨时段对比 | 归一化 | 相对排序一致 |
| 绝对风险评估 | 原始 | 反映真实威胁 |
| 时间感知决策 | 两者 | 完整信息 |

### Q4: 如何在实际部署中应用时间因子？

**A**: 建议的时间感知策略：

```
基准部署（DSSA 优化）
├─ 白天（6:00-18:00）
│  └─ 按 DSSA 方案部署
│
└─ 夜间（18:00-6:00）
   ├─ 保持 DSSA 部署
   ├─ 增加巡逻频率 ×1.3
   ├─ 增加摄像头覆盖
   └─ 加强无人机巡查
```

---

## 文件清单

### 输出文件

```
figures-day-rainy/
├── risk_heatmap.png          # 归一化风险（[0,1]）
├── raw_risk_heatmap.png      # 原始风险（保留时间因子）
├── attributes_map.png        # 地理+物种属性
└── risk_results.json         # 包含两种风险值

figures-night-rainy/
├── risk_heatmap.png          # 归一化风险（[0,1]）
├── raw_risk_heatmap.png      # 原始风险（×1.3 倍）
├── attributes_map.png        # 地理+物种属性
└── risk_results.json         # 包含两种风险值
```

### 文档文件

```
docs/usage.md                                    # 更新了第四、六、七节
TEMPORAL_FACTOR_SOLUTION_SUMMARY.md              # 完整的实现总结
TEMPORAL_FACTOR_VISUAL_GUIDE.md                  # 本文件
TEMPORAL_NORMALIZATION_IMPACT_ANALYSIS.md        # 详细的影响分析
```

---

## 总结

**已解决的问题**：
1. ✓ 如何显示时间因子的影响？→ 原始风险热力图
2. ✓ 为什么 DSSA 优化结果相同？→ 数学推导和解释
3. ✓ 如何在实际部署中应用？→ 时间感知的策略建议

**用户可以**：
- 对比两张热力图，直观看到时间维度的风险差异
- 在 JSON 中查看原始风险值
- 根据实际需求制定时间感知的巡逻计划
- 理解 DSSA 优化的数学原理

**后续可选**：
- 方案 B：修改 DSSA 目标函数，自动调整资源分配
- 方案 C：分时段优化，输出多套部署方案

