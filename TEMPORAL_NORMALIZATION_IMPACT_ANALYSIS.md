# 时间因子归一化对资源部署策略的影响分析

## 问题概述

当启用 `use_temporal_factors: true` 时，昼夜/季节因子会改变原始风险值，但**归一化后的风险统计指标相同**。这对资源部署策略有重要影响。

***

## 1. 数值验证

### 测试数据（input-day-rainy vs input-night-rainy）

```
Day (hour=12):
  Raw risks:        min=0.053739  max=0.430381  mean=0.125050
  Normalized risks: min=0.000000  max=1.000000  mean=0.189335

Night (hour=23):
  Raw risks:        min=0.069860  max=0.559495  mean=0.162565
  Normalized risks: min=0.000000  max=1.000000  mean=0.189335

Ratio (Night raw / Day raw): 1.3000 (exactly the diurnal factor)
```

### 关键观察

1. **原始风险**：夜间 = 1.3 × 白天（所有格子都乘以相同因子）
2. **归一化风险**：min/max/mean 完全相同
3. **原因**：min-max 归一化公式 `(R - R_min) / (R_max - R_min)` 中，分子分母同时乘以 1.3，相消

***

## 2. 对资源部署策略的影响

### 2.1 DSSA 优化目标

```python
# 在 coverage_model.py 中
fitness = total_protection_benefit / total_risk
```

其中：

- `total_protection_benefit = Σ [R_i × (1 - e^(-E_i))]`（保护收益）
- `total_risk = Σ R_i`（总风险）

### 2.2 归一化的影响

**关键发现**：由于所有 R\_i 都乘以相同的时间因子，fitness 不变！

```
fitness_night = Σ [1.3×R_i × (1 - e^(-E_i))] / Σ [1.3×R_i]
              = 1.3 × Σ [R_i × (1 - e^(-E_i))] / (1.3 × Σ R_i)
              = Σ [R_i × (1 - e^(-E_i))] / Σ R_i
              = fitness_day
```

### 2.3 实际后果

| 方面          | 影响              |
| ----------- | --------------- |
| **资源分配优先级** | 相同（高风险格子优先级不变）  |
| **部署数量**    | 相同（总资源约束不变）     |
| **部署位置**    | 相同（相对风险排序不变）    |
| **保护效率**    | 相同（fitness 值相同） |
| **绝对保护收益**  | 不同（夜间 1.3 倍）    |

***

## 3. 问题分析

### 3.1 当前设计的意图

归一化确保**跨时段的相对风险排序一致**：

- 白天最高风险格子 = 夜间最高风险格子
- 便于对比不同时段的部署方案

### 3.2 潜在问题

1. **时间因子被忽视**：虽然启用了 `use_temporal_factors`，但对部署策略无影响
2. **绝对风险差异丢失**：无法反映夜间风险确实更高的事实
3. **决策信息不完整**：管理者看不到时间维度的风险差异

***

## 4. 解决方案

### 方案 A：显示原始风险热力图（推荐）

**优点**：

- 保留时间因子的绝对差异
- 不改变优化算法
- 用户可同时看到两种视角

**实现**：

- 修改 `risk_analysis.py`：输出 `raw_risk_heatmap.png`
- 修改 `visualize_output.py`：输出 `raw_risk_heatmap.png`
- 在 JSON 输出中添加 `raw_risk` 字段

**输出示例**：

```
figures/
├── risk_heatmap.png          # 归一化风险 [0,1]
├── raw_risk_heatmap.png      # 原始风险（保留时间因子）
└── risk_results.json         # 包含 raw_risk 和 normalized_risk
```

### 方案 B：时间感知的资源分配（高级）

**思路**：根据时间因子调整资源分配策略

**实现**：

- 计算时间加权的总风险：`total_risk_weighted = Σ [R_i × T_t × S_t]`
- 修改 fitness 函数：`fitness = total_benefit / total_risk_weighted`
- 结果：夜间部署更多资源

**优点**：

- 资源分配反映时间维度的风险差异
- 更符合实际保护需求

**缺点**：

- 改变优化算法，需要重新验证
- 可能导致夜间部署过度

### 方案 C：分时段优化（最灵活）

**思路**：为不同时段分别优化部署方案

**实现**：

- 运行多次 DSSA：day\_solution, night\_solution
- 输出两套部署方案
- 用户根据实际需求选择或融合

**优点**：

- 完全保留时间维度信息
- 用户有完整的决策支持

**缺点**：

- 计算量翻倍
- 部署方案可能冲突

***

## 5. 建议

### 短期（立即实施）

**采用方案 A**：

1. 修改 `risk_analysis.py` 和 `visualize_output.py` 输出原始风险热力图
2. 在 JSON 中添加 `raw_risk` 字段
3. 更新文档说明两种风险的含义

### 中期（可选）

**采用方案 B**：

- 如果用户反馈需要时间感知的资源分配
- 添加配置选项 `use_time_aware_fitness: true/false`
- 默认保持当前行为（向后兼容）

### 长期（战略）

**采用方案 C**：

- 支持多时段优化
- 提供部署方案融合工具
- 支持 24 小时动态部署规划

***

## 6. 技术实现细节

### 6.1 修改 risk\_analysis.py

```python
# 在 compute_risk 中同时返回原始风险
def compute_risk(data: dict) -> Tuple[Dict[int, float], Dict[int, float]]:
    # ... 现有代码 ...
    results = model.calculate_batch(grid_data_list, time_context, use_temporal_factors=use_temporal)
    
    normalized_risks = {id_order[i]: float(r.normalized_risk) for i, r in enumerate(results)}
    raw_risks = {id_order[i]: float(r.raw_risk) for i, r in enumerate(results)}
    
    return normalized_risks, raw_risks
```

### 6.2 修改 visualize\_output.py

```python
# 添加原始风险热力图
def plot_raw_risk_heatmap(grids, raw_risks, hex_size, save_path):
    # 使用 YlOrRd 色阶，但不进行 [0,1] 归一化
    # 显示原始风险值范围
    pass
```

### 6.3 JSON 输出格式

```json
{
  "summary": {
    "total_grids": 120,
    "risk_min": 0.05,
    "risk_max": 0.95,
    "risk_mean": 0.45,
    "raw_risk_min": 0.053739,
    "raw_risk_max": 0.430381,
    "raw_risk_mean": 0.125050,
    "temporal_factor": 1.3
  },
  "grids": [
    {
      "grid_id": 0,
      "normalized_risk": 0.35,
      "raw_risk": 0.053739
    }
  ]
}
```

***

## 7. 用户指南更新

### 何时使用哪种风险值

| 场景      | 使用    | 原因      |
| ------- | ----- | ------- |
| DSSA 优化 | 归一化风险 | 已内置在算法中 |
| 跨时段对比   | 归一化风险 | 相对排序一致  |
| 绝对风险评估  | 原始风险  | 反映真实威胁  |
| 时间感知决策  | 两者结合  | 完整信息    |

