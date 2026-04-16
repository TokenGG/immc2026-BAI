# 方案 B 修正说明

## 问题发现

在初始测试中，发现 Night Time-Aware 的时间加权风险（80.273）反而低于 Day Baseline 的基础风险（125.050），这是不正确的。

## 根本原因

输出 JSON 中的 `total_risk` 字段没有正确反映时间加权的风险值。应该显示：
- **Day Baseline**：`total_risk_weighted = total_risk × 1.2`（rainy season）
- **Night Time-Aware**：`total_risk_weighted = total_risk × 1.56`（night + rainy）

## 修正内容

### 1. 计算时间加权的总风险

在 `protection_pipeline.py` 中添加：

```python
# 计算时间加权的总风险（如果启用时间感知模式）
total_risk_weighted = 0.0
for gid in grid_model.get_all_grid_ids():
    normalized_risk = grid_model.get_grid_risk(gid)
    temporal_factor = grid_model.get_grid_temporal_factor(gid)
    total_risk_weighted += normalized_risk * temporal_factor
```

### 2. 输出两个风险值

在输出 JSON 中添加 `total_risk_weighted` 字段：

```json
{
  "summary": {
    "total_risk": 501.358502,           // 基础风险（未加权）
    "total_risk_weighted": 782.119263,  // 时间加权的风险
    "best_fitness": 0.224465
  }
}
```

## 修正后的测试结果

### Day Baseline（use_time_aware_fitness=False）

```
total_risk: 501.358502
total_risk_weighted: 601.630202 (×1.2 rainy season)
best_fitness: 0.347466
fitness = benefit / risk = 174.205195 / 501.358502 = 0.347466
```

### Night Time-Aware（use_time_aware_fitness=True）

```
total_risk: 501.358502 (相同的基础风险)
total_risk_weighted: 782.119263 (×1.56 night + rainy)
best_fitness: 0.224465
fitness = benefit / risk_weighted = 175.558478 / 782.119263 = 0.224465
```

### 关键指标对比

| 指标 | Day Baseline | Night Time-Aware | 变化 |
|------|--------------|------------------|------|
| **total_risk** | 501.36 | 501.36 | 0% |
| **total_risk_weighted** | 601.63 | 782.12 | +30.0% |
| **best_fitness** | 0.3475 | 0.2245 | -35.4% |
| **total_benefit** | 174.21 | 175.56 | +0.8% |

### 时间因子验证

```
Day Rainy:
  temporal_factor = 1.0 (day) × 1.2 (rainy) = 1.2
  total_risk_weighted = 501.36 × 1.2 = 601.63 ✓

Night Rainy:
  temporal_factor = 1.3 (night) × 1.2 (rainy) = 1.56
  total_risk_weighted = 501.36 × 1.56 = 782.12 ✓

Ratio: 782.12 / 601.63 = 1.30 (night/day diurnal factor) ✓
```

## 结论

✓ **修正后的结果正确**
- Night 的时间加权风险（782.12）高于 Day（601.63）
- 时间因子正确应用（×1.56 vs ×1.2）
- Fitness 值正确反映了时间维度的风险差异

✓ **方案 B 工作正常**
- 时间感知模式正确计算时间加权的风险
- 资源分配反映了时间维度的差异
- 可用于生产环境

## 使用建议

### 查看时间加权风险

```bash
python -c "
import json
d = json.load(open('output.json'))
print('基础风险:', d['summary']['total_risk'])
print('时间加权风险:', d['summary']['total_risk_weighted'])
print('时间因子:', d['summary']['total_risk_weighted'] / d['summary']['total_risk'])
"
```

### 对比不同时段

```bash
# Day Dry
python protection_pipeline.py input-day-dry.json output-day-dry.json

# Night Dry
python protection_pipeline.py input-night-dry.json output-night-dry.json

# 对比时间加权风险
python -c "
import json
day = json.load(open('output-day-dry.json'))
night = json.load(open('output-night-dry.json'))
print('Day weighted risk:', day['summary']['total_risk_weighted'])
print('Night weighted risk:', night['summary']['total_risk_weighted'])
print('Ratio:', night['summary']['total_risk_weighted'] / day['summary']['total_risk_weighted'])
"
```

## 文件更新

- `hexdynamic/protection_pipeline.py` - 添加时间加权风险计算和输出

