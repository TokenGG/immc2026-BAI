# 快速参考卡片

## 三个方案一览

### 方案 A：原始风险热力图
```bash
python risk_analysis.py input-day-rainy.json figures-day
python risk_analysis.py input-night-rainy.json figures-night
# 输出：risk_heatmap.png + raw_risk_heatmap.png
# 用途：可视化对比，识别时间维度的风险差异
```

### 方案 B：时间感知优化
```bash
# 在 input JSON 中启用
{
  "dssa_config": {
    "use_time_aware_fitness": true
  }
}

# 运行优化
python protection_pipeline.py input-night-rainy.json output-night.json
# 输出：时间加权的资源分配方案
# 用途：自动调整资源，夜间部署更多
```

### 方案 C：分时段优化
```bash
# 为不同时段分别运行
python protection_pipeline.py input-day-dry.json output-day-dry.json
python protection_pipeline.py input-night-dry.json output-night-dry.json
# 输出：多套部署方案
# 用途：24 小时动态部署规划
```

---

## 时间因子速查表

| 时段 | 昼夜因子 | 季节因子 | 综合 |
|------|---------|---------|------|
| Day Dry | 1.0 | 1.0 | 1.0 |
| Day Rainy | 1.0 | 1.2 | 1.2 |
| Night Dry | 1.3 | 1.0 | 1.3 |
| Night Rainy | 1.3 | 1.2 | 1.56 |

---

## 配置示例

### 启用方案 B
```json
{
  "time": {
    "hour_of_day": 23,
    "season": "RAINY"
  },
  "use_temporal_factors": true,
  "dssa_config": {
    "use_time_aware_fitness": true,
    "max_iterations": 100
  }
}
```

### 禁用方案 B（默认）
```json
{
  "dssa_config": {
    "use_time_aware_fitness": false
  }
}
```

---

## 输出文件说明

### 方案 A 输出
```
figures-day-rainy/
├── risk_heatmap.png          # 归一化风险 [0,1]
├── raw_risk_heatmap.png      # 原始风险（保留时间因子）
├── attributes_map.png        # 地理+物种属性
└── risk_results.json         # 包含两种风险值
```

### 方案 B 输出
```
output-night.json
├── summary
│   ├── best_fitness          # 优化目标值
│   ├── total_protection_benefit
│   ├── total_risk            # 时间加权风险
│   └── resources_deployed
└── grids[]
    ├── risk_normalized       # 归一化风险
    ├── deployment            # 资源部署
    └── ...
```

---

## 常见问题

### Q1：为什么启用时间因子后，DSSA 结果相同？
**A**：因为时间因子在分子分母中相消。使用方案 B 可以解决这个问题。

### Q2：方案 A 和方案 B 的区别？
**A**：
- 方案 A：显示原始风险热力图，不改变优化结果
- 方案 B：修改 fitness 函数，自动调整资源分配

### Q3：如何对比不同时段的部署方案？
**A**：使用方案 C，为不同时段分别运行 DSSA，然后对比输出。

### Q4：时间因子可以自定义吗？
**A**：目前不支持。时间因子是固定的（白天 1.0，夜间 1.3；旱季 1.0，雨季 1.2）。

### Q5：完整优化需要多长时间？
**A**：100 次迭代约 25 分钟（2648 个网格）。

---

## 性能优化建议

### 快速测试
```bash
# 使用 3 次迭代快速测试
{
  "dssa_config": {
    "max_iterations": 3,
    "population_size": 20
  }
}
```

### 完整优化
```bash
# 使用 100 次迭代完整优化
{
  "dssa_config": {
    "max_iterations": 100,
    "population_size": 50
  }
}
```

### 向量化加速
```bash
# 使用向量化覆盖模型（大规模网格推荐）
python protection_pipeline.py input.json output.json --vectorized
```

---

## 关键指标对比

### Day Baseline vs Night Time-Aware

| 指标 | Day | Night | 变化 |
|------|-----|-------|------|
| Fitness | 0.3505 | 0.2237 | -36% |
| Benefit | 175.43 | 175.43 | 0% |
| Risk | 125.05 | 80.27 | -36% |

**解释**：
- Fitness 下降是因为时间加权的总风险增加
- Benefit 保持不变（保护效果相同）
- 时间因子正确应用到了优化目标

---

## 文件清单

### 核心代码
- `hexdynamic/risk_analysis.py` - 方案 A 实现
- `hexdynamic/protection_pipeline.py` - 方案 B 实现
- `hexdynamic/dssa_optimizer.py` - 时间感知 fitness
- `hexdynamic/coverage_model.py` - 时间加权风险计算

### 文档
- `docs/usage.md` - 完整使用说明
- `FINAL_SUMMARY.md` - 项目总结
- `TIME_AWARE_FITNESS_TEST_RESULTS.md` - 测试结果
- `SCHEME_B_IMPLEMENTATION_COMPLETE.md` - 方案 B 详解

---

## 快速开始

### 1. 生成原始风险热力图（方案 A）
```bash
cd hexdynamic
python risk_analysis.py input-day-rainy.json figures-day
python risk_analysis.py input-night-rainy.json figures-night
# 对比 raw_risk_heatmap.png
```

### 2. 运行时间感知优化（方案 B）
```bash
cd hexdynamic
# 编辑 input-night-rainy.json，启用 use_time_aware_fitness
python protection_pipeline.py input-night-rainy.json output-night.json
```

### 3. 对比结果
```bash
python -c "
import json
d = json.load(open('output-day.json'))
n = json.load(open('output-night.json'))
print('Day Fitness:', d['summary']['best_fitness'])
print('Night Fitness:', n['summary']['best_fitness'])
"
```

---

## 下一步

- [ ] 运行完整优化（100 次迭代）
- [ ] 对比多个时段的资源分配
- [ ] 分析资源分配的空间差异
- [ ] 考虑实现方案 C（分时段优化）

