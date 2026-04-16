# 敏感性分析方案设计

## 目标

分析每种保护资源对总保护收益的影响，通过逐个改变单一资源数量，保持其他资源不变，观察保护效果的变化趋势。

## 核心思路

### 1. 分析流程

```
输入：base_input.json（基础配置）
      resource_type: 'patrol' | 'camera' | 'drone' | 'camp' | 'fence'
      resource_range: [min, max, step]  例如 [0, 50, 5]

对于每个资源数量值：
  1. 复制 base_input.json
  2. 修改目标资源的数量
  3. 冻结其他资源的数量（保持不变）
  4. 运行 protection_pipeline.py
  5. 记录输出指标：
     - total_protection_benefit
     - best_fitness
     - resources_deployed
     - 各资源的利用率

输出：sensitivity_analysis_results.json
      包含每个资源数量对应的指标数据
```

### 2. 关键设计点

#### 2.1 资源冻结机制

在 `protection_pipeline.py` 中添加新参数：

```python
--freeze-resources <resource_list>
```

例如：
```bash
# 只优化 patrol，冻结其他资源
python protection_pipeline.py input.json output.json --freeze-resources camera,drone,camp,fence

# 只优化 camera，冻结其他资源
python protection_pipeline.py input.json output.json --freeze-resources patrol,drone,camp,fence
```

#### 2.2 冻结实现方式

在 `DSSAOptimizer` 中添加冻结逻辑：

```python
class DSSAOptimizer:
    def __init__(self, ..., frozen_resources: List[str] = None):
        self.frozen_resources = frozen_resources or []
    
    def _initialize_solution(self):
        # 正常初始化所有资源
        solution = ...
        
        # 如果某资源被冻结，使用初始解决方案的值
        if 'patrol' in self.frozen_resources:
            solution.rangers = self.initial_solution.rangers
        if 'camera' in self.frozen_resources:
            solution.cameras = self.initial_solution.cameras
        # ... 其他资源
        
        return solution
    
    def _update_producers(self):
        # 更新时，冻结的资源不参与优化
        # 只修改非冻结资源的部分
        ...
```

#### 2.3 初始解决方案保存

需要保存初始的部署方案，作为冻结资源的参考：

```python
# 在 optimize() 开始时保存初始方案
self.initial_solution = self._initialize_solution()

# 后续迭代中，冻结的资源始终使用 initial_solution 的值
```

### 3. 敏感性分析脚本

创建 `sensitivity_analysis.py`：

```python
def run_sensitivity_analysis(
    base_input_path: str,
    resource_type: str,  # 'patrol', 'camera', 'drone', 'camp', 'fence'
    resource_range: Tuple[int, int, int],  # (min, max, step)
    output_dir: str = './sensitivity_results'
):
    """
    运行敏感性分析
    
    Args:
        base_input_path: 基础输入 JSON 路径
        resource_type: 要分析的资源类型
        resource_range: (最小值, 最大值, 步长)
        output_dir: 输出目录
    
    Returns:
        sensitivity_results: {
            'resource_type': 'patrol',
            'resource_values': [0, 5, 10, 15, 20],
            'results': [
                {
                    'resource_value': 0,
                    'total_protection_benefit': 0.123,
                    'best_fitness': 0.456,
                    'resources_deployed': {...},
                    'output_json': 'output_0.json'
                },
                ...
            ]
        }
    """
    
    # 1. 加载基础输入
    base_input = load_json(base_input_path)
    
    # 2. 获取其他资源的初始值
    other_resources = {
        'patrol': base_input['constraints']['total_patrol'],
        'camera': base_input['constraints']['total_cameras'],
        'drone': base_input['constraints']['total_drones'],
        'camp': base_input['constraints']['total_camps'],
        'fence': base_input['constraints']['total_fence_length'],
    }
    
    # 3. 生成资源值范围
    min_val, max_val, step = resource_range
    resource_values = list(range(min_val, max_val + 1, step))
    
    results = []
    
    # 4. 对每个资源值运行优化
    for resource_value in resource_values:
        # 创建临时输入文件
        temp_input = copy.deepcopy(base_input)
        temp_input['constraints'][f'total_{resource_type}s'] = resource_value
        
        # 冻结其他资源
        frozen_list = [r for r in other_resources.keys() if r != resource_type]
        
        # 运行 protection_pipeline
        temp_output_path = f'{output_dir}/temp_output_{resource_value}.json'
        run_pipeline(
            temp_input,
            temp_output_path,
            frozen_resources=frozen_list
        )
        
        # 提取结果
        output = load_json(temp_output_path)
        result = {
            'resource_value': resource_value,
            'total_protection_benefit': output['summary']['total_protection_benefit'],
            'best_fitness': output['summary']['best_fitness'],
            'resources_deployed': output['summary']['resources_deployed'],
            'output_json': temp_output_path
        }
        results.append(result)
    
    # 5. 保存敏感性分析结果
    sensitivity_results = {
        'resource_type': resource_type,
        'resource_values': resource_values,
        'results': results
    }
    
    save_json(
        f'{output_dir}/sensitivity_{resource_type}.json',
        sensitivity_results
    )
    
    return sensitivity_results
```

### 4. 使用示例

#### 4.1 分析 Patrol 敏感性

```bash
python sensitivity_analysis.py \
    --input base_input.json \
    --resource patrol \
    --range 0 50 5 \
    --output ./sensitivity_results
```

输出：
```
sensitivity_results/
├── sensitivity_patrol.json
├── temp_output_0.json
├── temp_output_5.json
├── temp_output_10.json
├── ...
└── sensitivity_patrol_plot.png
```

#### 4.2 分析 Camera 敏感性

```bash
python sensitivity_analysis.py \
    --input base_input.json \
    --resource camera \
    --range 0 20 2 \
    --output ./sensitivity_results
```

#### 4.3 分析所有资源

```bash
python sensitivity_analysis.py \
    --input base_input.json \
    --resource all \
    --output ./sensitivity_results
```

### 5. 结果可视化

创建 `plot_sensitivity.py`：

```python
def plot_sensitivity_results(sensitivity_json_path: str, output_path: str):
    """
    绘制敏感性分析曲线
    
    X轴：资源数量
    Y轴：总保护收益 / 最佳适应度
    """
    
    results = load_json(sensitivity_json_path)
    resource_type = results['resource_type']
    resource_values = results['resource_values']
    
    # 提取指标
    total_benefits = [r['total_protection_benefit'] for r in results['results']]
    best_fitnesses = [r['best_fitness'] for r in results['results']]
    
    # 绘制
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # 曲线1：总保护收益
    ax1.plot(resource_values, total_benefits, 'o-', linewidth=2, markersize=8, color='#2ca02c')
    ax1.set_xlabel(f'{resource_type.capitalize()} Count', fontsize=12)
    ax1.set_ylabel('Total Protection Benefit', fontsize=12)
    ax1.set_title(f'Sensitivity: {resource_type.capitalize()} Impact on Protection Benefit', fontsize=13)
    ax1.grid(True, alpha=0.3)
    
    # 曲线2：最佳适应度
    ax2.plot(resource_values, best_fitnesses, 's-', linewidth=2, markersize=8, color='#1f77b4')
    ax2.set_xlabel(f'{resource_type.capitalize()} Count', fontsize=12)
    ax2.set_ylabel('Best Fitness', fontsize=12)
    ax2.set_title(f'Sensitivity: {resource_type.capitalize()} Impact on Fitness', fontsize=13)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
```

### 6. 输出格式

#### 6.1 敏感性分析结果 JSON

```json
{
  "resource_type": "patrol",
  "resource_values": [0, 5, 10, 15, 20, 25, 30],
  "results": [
    {
      "resource_value": 0,
      "total_protection_benefit": 0.0,
      "best_fitness": 0.0,
      "resources_deployed": {
        "total_cameras": 10,
        "total_drones": 5,
        "total_camps": 3,
        "total_rangers": 0,
        "fence_segments": 5
      },
      "output_json": "temp_output_0.json"
    },
    {
      "resource_value": 5,
      "total_protection_benefit": 12.345,
      "best_fitness": 0.234,
      "resources_deployed": {
        "total_cameras": 10,
        "total_drones": 5,
        "total_camps": 3,
        "total_rangers": 5,
        "fence_segments": 5
      },
      "output_json": "temp_output_5.json"
    },
    ...
  ]
}
```

#### 6.2 敏感性分析曲线图

显示：
- X轴：资源数量
- Y轴：总保护收益 / 最佳适应度
- 曲线：显示边际收益递减趋势

### 7. 实现步骤

#### 第一阶段：修改核心模块

1. **修改 `DSSAOptimizer`**
   - 添加 `frozen_resources` 参数
   - 添加 `initial_solution` 保存
   - 修改 `_initialize_solution()` 支持冻结
   - 修改 `_update_producers()` 和 `_update_followers()` 支持冻结

2. **修改 `protection_pipeline.py`**
   - 添加 `--freeze-resources` 参数
   - 传递冻结列表给 `DSSAOptimizer`

#### 第二阶段：创建敏感性分析脚本

1. **创建 `sensitivity_analysis.py`**
   - 实现主分析流程
   - 支持单个资源和全部资源分析

2. **创建 `plot_sensitivity.py`**
   - 绘制敏感性曲线
   - 生成对比图表

#### 第三阶段：测试和文档

1. **创建测试脚本** `test_sensitivity_analysis.py`
2. **创建文档** `SENSITIVITY_ANALYSIS_GUIDE.md`

### 8. 优势

- ✅ 清晰的资源影响分析
- ✅ 边际收益递减可视化
- ✅ 支持多资源对比
- ✅ 可重复运行，结果可追溯
- ✅ 为资源配置优化提供数据支持

### 9. 预期输出

对于 Patrol 敏感性分析：

```
Patrol 敏感性分析结果
===================

资源数量 | 总保护收益 | 最佳适应度 | 边际收益
--------|-----------|----------|--------
0       | 0.000     | 0.000    | -
5       | 12.345    | 0.234    | 2.469
10      | 21.456    | 0.389    | 1.822
15      | 28.901    | 0.512    | 1.489
20      | 34.567    | 0.601    | 1.133
25      | 38.234    | 0.654    | 0.733
30      | 40.123    | 0.678    | 0.378

趋势：边际收益递减，在 20-25 个 patrol 时达到最优平衡点
```

## 总结

这个方案通过：
1. **冻结机制** - 保持其他资源不变
2. **参数化分析** - 逐步改变单一资源
3. **结果可视化** - 清晰展示敏感性趋势
4. **数据驱动** - 为资源配置提供科学依据

能够全面分析每种资源对保护效果的影响，帮助优化资源配置策略。
