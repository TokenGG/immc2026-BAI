# 敏感性分析实现文档

## 概述

实现了敏感性分析功能，用于分析每种保护资源对总保护收益的影响。通过逐个改变单一资源数量，保持其他资源不变，观察保护效果的变化趋势。

## 核心实现

### 1. 冻结资源机制

#### 1.1 DSSAOptimizer 修改

**新增参数**：
```python
def __init__(self, ..., frozen_resources: List[str] = None):
    self.frozen_resources = frozen_resources or []
    self.initial_solution = None  # 保存初始解决方案
```

**新增方法**：
```python
def _apply_frozen_resources(self, solution: DeploymentSolution) -> DeploymentSolution:
    """应用冻结资源：将冻结的资源替换为初始解决方案中的值"""
    if not self.frozen_resources or not self.initial_solution:
        return solution
    
    if 'patrol' in self.frozen_resources:
        solution.rangers = dict(self.initial_solution.rangers)
    if 'camera' in self.frozen_resources:
        solution.cameras = dict(self.initial_solution.cameras)
    # ... 其他资源
    
    return solution
```

**修改 optimize() 方法**：
```python
def optimize(self):
    # 保存初始解决方案（用于冻结资源）
    self.initial_solution = self._initialize_solution()
    
    # ... 优化过程
```

**修改更新方法**：
```python
def _update_producers(self, iteration: int):
    # ... 生成新解决方案
    new_solution = self.coverage_model.repair_solution(...)
    
    # 应用冻结资源
    new_solution = self._apply_frozen_resources(new_solution)
    
    # ... 继续优化
```

#### 1.2 protection_pipeline.py 修改

**新增参数**：
```python
parser.add_argument(
    "--freeze-resources",
    type=str,
    default=None,
    help="Comma-separated list of resources to freeze (e.g., 'patrol,camera,drone')"
)
```

**传递参数**：
```python
frozen_resources_list = []
if freeze_resources:
    frozen_resources_list = [r.strip() for r in freeze_resources.split(',')]

optimizer = DSSAOptimizer(
    coverage_model, 
    constraints, 
    dssa_config,
    frozen_resources=frozen_resources_list
)
```

### 2. 敏感性分析脚本

#### 2.1 sensitivity_analysis.py

**主要功能**：
- 加载基础输入 JSON
- 对每个资源值运行优化
- 冻结其他资源
- 收集结果数据
- 生成敏感性曲线

**核心流程**：
```python
def run_sensitivity_analysis(
    base_input_path: str,
    resource_type: str,
    resource_range: Tuple[int, int, int],
    output_dir: str
):
    # 1. 加载基础输入
    base_input = load_json(base_input_path)
    
    # 2. 生成资源值范围
    resource_values = list(range(min_val, max_val + 1, step))
    
    # 3. 对每个资源值运行优化
    for resource_value in resource_values:
        # 修改目标资源
        temp_input['constraints'][resource_key] = resource_value
        
        # 冻结其他资源
        frozen_list = [r for r in all_resources if r != resource_type]
        
        # 运行 protection_pipeline
        run_protection_pipeline(
            temp_input_path,
            temp_output_path,
            freeze_resources=','.join(frozen_list)
        )
        
        # 提取结果
        results.append({
            'resource_value': resource_value,
            'total_protection_benefit': ...,
            'best_fitness': ...,
            'resources_deployed': ...
        })
    
    # 4. 保存结果
    save_json(f'sensitivity_{resource_type}.json', results)
    
    # 5. 绘制曲线
    plot_sensitivity_results(...)
```

#### 2.2 可视化

**绘制内容**：
1. **总保护收益曲线** - 显示资源数量与保护效果的关系
2. **最佳适应度曲线** - 显示优化质量
3. **边际收益曲线** - 显示边际收益递减趋势
4. **数据表格** - 汇总所有数据

## 使用方法

### 基本用法

#### 分析单个资源

```bash
# 分析 Patrol 敏感性（0-50，步长5）
python sensitivity_analysis.py --input base_input.json --resource patrol --range 0 50 5

# 分析 Camera 敏感性（0-20，步长2）
python sensitivity_analysis.py --input base_input.json --resource camera --range 0 20 2

# 分析 Drone 敏感性（使用默认范围）
python sensitivity_analysis.py --input base_input.json --resource drone
```

#### 分析所有资源

```bash
# 分析所有资源（使用默认范围）
python sensitivity_analysis.py --input base_input.json --resource all
```

#### 使用向量化模式

```bash
# 大规模地图推荐使用向量化模式
python sensitivity_analysis.py --input base_input.json --resource patrol --vectorized
```

### 默认资源范围

| 资源 | 默认范围 | 步长 |
|------|---------|------|
| patrol | 0-50 | 5 |
| camera | 0-20 | 2 |
| drone | 0-10 | 1 |
| camp | 0-5 | 1 |
| fence | 0-100 | 10 |

### 直接调用 protection_pipeline 进行冻结

```bash
# 只优化 patrol，冻结其他资源
python hexdynamic/protection_pipeline.py input.json output.json \
    --freeze-resources camera,drone,camp,fence

# 只优化 camera，冻结其他资源
python hexdynamic/protection_pipeline.py input.json output.json \
    --freeze-resources patrol,drone,camp,fence
```

## 输出格式

### 敏感性分析结果 JSON

```json
{
  "resource_type": "patrol",
  "resource_values": [0, 5, 10, 15, 20],
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
      "output_json": "temp_output_patrol_0.json"
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
      "output_json": "temp_output_patrol_5.json"
    }
  ]
}
```

### 输出文件结构

```
sensitivity_results/
├── sensitivity_patrol.json           # Patrol 敏感性分析结果
├── sensitivity_patrol_plot.png       # Patrol 敏感性曲线图
├── sensitivity_camera.json           # Camera 敏感性分析结果
├── sensitivity_camera_plot.png       # Camera 敏感性曲线图
├── temp_input_patrol_0.json          # 临时输入文件
├── temp_output_patrol_0.json         # 临时输出文件
├── temp_input_patrol_5.json
├── temp_output_patrol_5.json
└── ...
```

## 敏感性曲线图

### 图表内容

1. **左上：总保护收益 vs 资源数量**
   - X轴：资源数量
   - Y轴：总保护收益
   - 显示保护效果随资源增加的变化

2. **右上：最佳适应度 vs 资源数量**
   - X轴：资源数量
   - Y轴：最佳适应度
   - 显示优化质量

3. **左下：边际收益 vs 资源数量**
   - X轴：资源数量
   - Y轴：边际收益
   - 显示边际收益递减趋势

4. **右下：数据表格**
   - 汇总所有数据
   - 便于查看具体数值

## 实现细节

### 冻结机制工作原理

1. **初始化阶段**
   - 保存初始解决方案 `self.initial_solution`
   - 记录冻结资源列表 `self.frozen_resources`

2. **优化迭代**
   - 生成新解决方案
   - 调用 `_apply_frozen_resources()` 应用冻结
   - 冻结的资源被替换为初始值

3. **结果**
   - 冻结的资源保持不变
   - 其他资源被优化

### 敏感性分析流程

1. **准备阶段**
   - 加载基础输入 JSON
   - 确定资源范围和步长

2. **迭代阶段**
   - 对每个资源值：
     - 创建临时输入文件
     - 修改目标资源数量
     - 冻结其他资源
     - 运行 protection_pipeline
     - 提取结果

3. **分析阶段**
   - 收集所有结果
   - 计算边际收益
   - 生成敏感性曲线

4. **输出阶段**
   - 保存结果 JSON
   - 生成可视化图表

## 性能考虑

### 运行时间

- 单个资源分析：取决于资源范围和步长
- 例如：patrol (0-50, step 5) = 11 次优化
- 每次优化时间：取决于地图大小和迭代次数

### 优化建议

1. **使用向量化模式**
   ```bash
   python sensitivity_analysis.py --input base_input.json --resource patrol --vectorized
   ```

2. **减少步长**
   ```bash
   # 快速分析
   python sensitivity_analysis.py --input base_input.json --resource patrol --range 0 50 10
   ```

3. **并行运行**
   - 可以同时运行多个资源的敏感性分析
   - 每个分析使用独立的输出目录

## 测试

运行测试脚本：

```bash
python test_sensitivity_analysis.py
```

测试内容：
1. 冻结资源功能
2. 敏感性分析工作流

## 应用场景

### 1. 资源配置优化

分析每种资源的贡献度，确定最优的资源配置：

```bash
python sensitivity_analysis.py --input base_input.json --resource all
```

### 2. 预算规划

了解增加资源投入的边际效益：

```bash
python sensitivity_analysis.py --input base_input.json --resource patrol --range 0 100 10
```

### 3. 资源优先级

比较不同资源的敏感性，确定优先级：

```bash
# 分别分析每种资源
python sensitivity_analysis.py --input base_input.json --resource patrol
python sensitivity_analysis.py --input base_input.json --resource camera
python sensitivity_analysis.py --input base_input.json --resource drone
```

### 4. 性能基准测试

建立保护效果与资源投入的关系曲线

## 示例输出

### 敏感性分析结果示例

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

趋势分析：
- 保护收益随 patrol 数量增加而增加
- 边际收益呈递减趋势
- 在 20-25 个 patrol 时达到最优平衡点
- 超过 25 个后，边际收益快速下降
```

## 总结

敏感性分析功能通过：

1. **冻结机制** - 保持其他资源不变
2. **参数化分析** - 逐步改变单一资源
3. **结果可视化** - 清晰展示敏感性趋势
4. **数据驱动** - 为资源配置提供科学依据

能够全面分析每种资源对保护效果的影响，帮助优化资源配置策略。

## 相关文件

- `sensitivity_analysis.py` - 敏感性分析脚本
- `test_sensitivity_analysis.py` - 测试脚本
- `hexdynamic/dssa_optimizer.py` - 优化器（包含冻结机制）
- `hexdynamic/protection_pipeline.py` - 管道脚本（包含冻结参数）
