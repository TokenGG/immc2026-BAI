# 敏感性分析快速开始指南

## 什么是敏感性分析？

敏感性分析用于分析每种保护资源对总保护收益的影响。通过逐个改变单一资源数量，保持其他资源不变，观察保护效果的变化趋势。

## 快速开始

### 1. 分析 Patrol（巡逻人员）敏感性

```bash
python sensitivity_analysis.py --input pipeline_input.json --resource patrol --range 0 50 5
```

**说明**：
- 分析 patrol 数量从 0 到 50，每次增加 5
- 其他资源（camera, drone, camp, fence）保持不变
- 生成 11 次优化结果

**输出**：
```
sensitivity_results/
├── sensitivity_patrol.json       # 结果数据
└── sensitivity_patrol_plot.png   # 敏感性曲线图
```

### 2. 分析 Camera（摄像头）敏感性

```bash
python sensitivity_analysis.py --input pipeline_input.json --resource camera --range 0 20 2
```

### 3. 分析所有资源

```bash
python sensitivity_analysis.py --input pipeline_input.json --resource all
```

**说明**：
- 依次分析 patrol, camera, drone, camp, fence
- 使用每种资源的默认范围
- 生成 5 个敏感性分析结果

### 4. 使用向量化模式（推荐用于大规模地图）

```bash
python sensitivity_analysis.py --input pipeline_input.json --resource patrol --vectorized
```

## 理解输出

### 敏感性曲线图

图表包含 4 个子图：

1. **左上：保护收益曲线**
   - 显示保护效果随资源增加的变化
   - 通常呈现 S 形或递减趋势

2. **右上：适应度曲线**
   - 显示优化质量
   - 通常随资源增加而提高

3. **左下：边际收益曲线**
   - 显示每增加一个资源的收益
   - 通常呈现递减趋势（边际收益递减）

4. **右下：数据表格**
   - 汇总所有数据
   - 便于查看具体数值

### 结果 JSON 文件

```json
{
  "resource_type": "patrol",
  "resource_values": [0, 5, 10, 15, 20],
  "results": [
    {
      "resource_value": 0,
      "total_protection_benefit": 0.0,
      "best_fitness": 0.0,
      "resources_deployed": {...}
    },
    ...
  ]
}
```

## 常见用法

### 快速分析（步长较大）

```bash
# 快速了解趋势
python sensitivity_analysis.py --input pipeline_input.json --resource patrol --range 0 50 10
```

### 精细分析（步长较小）

```bash
# 详细了解变化
python sensitivity_analysis.py --input pipeline_input.json --resource patrol --range 0 50 2
```

### 对比多个资源

```bash
# 分别分析，然后对比结果
python sensitivity_analysis.py --input pipeline_input.json --resource patrol
python sensitivity_analysis.py --input pipeline_input.json --resource camera
python sensitivity_analysis.py --input pipeline_input.json --resource drone
```

## 直接使用冻结功能

如果只想运行一次优化，冻结某些资源：

```bash
# 只优化 patrol，其他资源保持不变
python hexdynamic/protection_pipeline.py input.json output.json \
    --freeze-resources camera,drone,camp,fence

# 只优化 camera
python hexdynamic/protection_pipeline.py input.json output.json \
    --freeze-resources patrol,drone,camp,fence
```

## 解读结果

### 示例：Patrol 敏感性分析

```
资源数量 | 总保护收益 | 边际收益
--------|-----------|--------
0       | 0.000     | -
5       | 12.345    | 2.469
10      | 21.456    | 1.822
15      | 28.901    | 1.489
20      | 34.567    | 1.133
25      | 38.234    | 0.733
30      | 40.123    | 0.378
```

**解读**：
- **保护收益增长**：从 0 增加到 40.123
- **边际收益递减**：从 2.469 递减到 0.378
- **最优点**：在 20-25 个 patrol 时，边际收益仍然较高
- **建议**：配置 20-25 个 patrol 可以获得较好的收益/成本比

## 性能提示

### 加快分析速度

1. **使用向量化模式**
   ```bash
   python sensitivity_analysis.py --input pipeline_input.json --resource patrol --vectorized
   ```

2. **增大步长**
   ```bash
   # 从 5 改为 10
   python sensitivity_analysis.py --input pipeline_input.json --resource patrol --range 0 50 10
   ```

3. **减少迭代次数**
   - 修改 input JSON 中的 `dssa_config.max_iterations`

### 并行运行

可以同时运行多个资源的分析：

```bash
# 终端 1
python sensitivity_analysis.py --input pipeline_input.json --resource patrol &

# 终端 2
python sensitivity_analysis.py --input pipeline_input.json --resource camera &

# 终端 3
python sensitivity_analysis.py --input pipeline_input.json --resource drone &
```

## 常见问题

### Q: 为什么某个资源的敏感性很低？

**A**: 可能原因：
1. 该资源的权重配置较低（见 `coverage_params` 中的 `wp`, `wd`, `wc`, `wf`）
2. 该资源的覆盖范围已经足够
3. 其他资源已经提供了足够的保护

### Q: 边际收益为负是什么意思？

**A**: 表示增加该资源反而降低了保护效果，可能是因为：
1. 资源已经过度配置
2. 优化器找到了更好的部署方式
3. 资源之间存在冲突

### Q: 如何比较不同资源的重要性？

**A**: 比较各资源的边际收益曲线：
- 曲线下降最慢的资源最重要
- 曲线下降最快的资源最不重要

### Q: 可以修改资源范围吗？

**A**: 可以，使用 `--range` 参数：
```bash
python sensitivity_analysis.py --input pipeline_input.json --resource patrol --range 0 100 10
```

## 下一步

1. **查看详细文档**：`SENSITIVITY_ANALYSIS_IMPLEMENTATION.md`
2. **运行测试**：`python test_sensitivity_analysis.py`
3. **自定义分析**：修改 `sensitivity_analysis.py` 中的参数

## 示例工作流

```bash
# 1. 生成基础输入
python hexdynamic/generate_map.py --output pipeline_input.json

# 2. 分析所有资源
python sensitivity_analysis.py --input pipeline_input.json --resource all

# 3. 查看结果
# 打开 sensitivity_results/ 目录下的 PNG 文件

# 4. 根据结果优化配置
# 修改 pipeline_input.json 中的资源数量

# 5. 运行最终优化
python hexdynamic/protection_pipeline.py pipeline_input.json output.json

# 6. 可视化结果
python hexdynamic/visualize_output.py output.json --input pipeline_input.json
```

## 总结

敏感性分析帮助你：
- ✅ 了解每种资源的贡献度
- ✅ 发现最优的资源配置
- ✅ 优化预算分配
- ✅ 做出数据驱动的决策

开始分析吧！
