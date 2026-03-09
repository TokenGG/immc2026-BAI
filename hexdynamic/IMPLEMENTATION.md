# Wildlife Reserve Protection Optimization - Implementation Guide

## 1. 系统架构概述

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Main Program                             │
│                    (main.py)                                    │
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌───▼────────┐ ┌─▼──────────────┐
│ Data Loader  │ │ Grid Model │ │ Coverage Model │
│(data_loader) │ │(grid_model)│ │(coverage_model)│
└───────┬──────┘ └───┬────────┘ └─┬──────────────┘
        │            │            │
        └────────────┼────────────┘
                     │
            ┌────────▼────────┐
            │  DSSA Optimizer │
            │ (dssa_optimizer)│
            └────────┬────────┘
                     │
            ┌────────▼────────┐
            │  Visualizer     │
            │ (visualization) │
            └─────────────────┘
```

### 1.2 模块职责

| 模块 | 文件名 | 职责 |
|------|--------|------|
| 数据加载器 | `data_loader.py` | 管理输入数据、地形、风险、约束条件 |
| 网格模型 | `grid_model.py` | 六边形网格几何计算、距离计算 |
| 覆盖模型 | `coverage_model.py` | 保护覆盖计算、效益评估、约束验证 |
| DSSA优化器 | `dssa_optimizer.py` | 麻雀搜索算法实现、优化求解 |
| 可视化 | `visualization.py` | 结果可视化、图表生成 |
| 主程序 | `main.py` | 流程控制、用户接口 |

---

## 2. 输入数据结构

### 2.1 网格数据 (GridData)

```python
@dataclass
class GridData:
    grid_id: int          # 网格唯一标识符
    q: int                # 六边形轴坐标q
    r: int                # 六边形轴坐标r
    terrain_type: str     # 地形类型
    risk: float           # 风险值 [0,1]
```

**示例数据：**
```json
{
  "grid_id": 0,
  "q": -5,
  "r": 0,
  "terrain_type": "SparseGrass",
  "risk": 0.75
}
```

### 2.2 资源约束 (ResourceConstraints)

```python
@dataclass
class ResourceConstraints:
    total_patrol: int           # 巡逻人员总数
    total_camps: int            # 营地数量
    max_rangers_per_camp: int   # 每营地最大人数
    total_cameras: int          # 摄像头数量
    total_drones: int           # 无人机数量
    total_fence_length: float   # 围栏总长度
```

**示例数据：**
```json
{
  "total_patrol": 20,
  "total_camps": 5,
  "max_rangers_per_camp": 5,
  "total_cameras": 10,
  "total_drones": 3,
  "total_fence_length": 50.0
}
```

### 2.3 覆盖参数 (CoverageParameters)

```python
@dataclass
class CoverageParameters:
    patrol_radius: float = 5.0      # 巡逻覆盖半径
    drone_radius: float = 8.0       # 无人机覆盖半径
    camera_radius: float = 3.0      # 摄像头覆盖半径
    fence_protection: float = 0.5   # 围栏保护系数
    wp: float = 0.3                 # 巡逻权重
    wd: float = 0.3                 # 无人机权重
    wc: float = 0.2                 # 摄像头权重
    wf: float = 0.2                 # 围栏权重
```

**示例数据：**
```json
{
  "patrol_radius": 5.0,
  "drone_radius": 8.0,
  "camera_radius": 3.0,
  "fence_protection": 0.5,
  "wp": 0.3,
  "wd": 0.3,
  "wc": 0.2,
  "wf": 0.2
}
```

### 2.4 部署可行性矩阵

**数据结构：** `Dict[str, Dict[int, int]]`

**说明：** 每个资源类型对每个网格的可部署性 (0=不可部署, 1=可部署)

**示例数据：**
```json
{
  "patrol": {
    "0": 1, "1": 0, "2": 1, ...
  },
  "camp": {
    "0": 1, "1": 0, "2": 1, ...
  },
  "drone": {
    "0": 1, "1": 1, "2": 1, ...
  },
  "camera": {
    "0": 1, "1": 0, "2": 0, ...
  },
  "fence": {
    "0": 1, "1": 0, "2": 1, ...
  }
}
```

**地形-资源部署规则表：**

| 地形 | Patrol | Camp | Drone | Camera | Fence |
|------|--------|------|-------|--------|-------|
| SaltMarsh | 0 | 0 | 1 | 0 | 0 |
| SparseGrass | 1 | 1 | 1 | 1 | 1 |
| DenseGrass | 1 | 1 | 1 | 0 | 1 |
| WaterHole | 0 | 0 | 1 | 0 | 0 |
| Road | 1 | 1 | 1 | 1 | 1 |

### 2.5 可见性参数

**数据结构：** `Dict[int, Dict[str, float]]`

**说明：** 每个网格的传感器可见性系数

**示例数据：**
```json
{
  "0": {"drone": 1.0, "camera": 1.0},
  "1": {"drone": 0.7, "camera": 0.5},
  "2": {"drone": 0.9, "camera": 0.6}
}
```

**地形-可见性系数表：**

| 地形 | Drone Visibility | Camera Visibility |
|------|------------------|-------------------|
| SparseGrass | 1.0 | 1.0 |
| DenseGrass | 0.7 | 0.5 |
| SaltMarsh | 0.9 | 0.6 |
| WaterHole | 1.0 | 0.8 |
| Road | 1.0 | 1.0 |

### 2.6 DSSA算法配置 (DSSAConfig)

```python
@dataclass
class DSSAConfig:
    population_size: int = 50       # 种群大小
    max_iterations: int = 100       # 最大迭代次数
    producer_ratio: float = 0.2     # 生产者比例
    scout_ratio: float = 0.2        # 侦察者比例
    ST: float = 0.8                 # 安全阈值
    R2: float = 0.5                 # 警告值
```

**示例数据：**
```json
{
  "population_size": 50,
  "max_iterations": 100,
  "producer_ratio": 0.2,
  "scout_ratio": 0.2,
  "ST": 0.8,
  "R2": 0.5
}
```

---

## 3. 核心数据结构

### 3.1 决策方案 (DeploymentSolution)

```python
@dataclass
class DeploymentSolution:
    cameras: Dict[int, int]              # 网格ID -> 是否部署摄像头 (0/1)
    camps: Dict[int, int]                # 网格ID -> 是否部署营地 (0/1)
    drones: Dict[int, int]               # 网格ID -> 是否部署无人机 (0/1)
    rangers: Dict[int, int]              # 营地ID -> 巡逻人数
    fences: Dict[Tuple[int, int], int]   # (网格1, 网格2) -> 是否建围栏 (0/1)
```

**示例数据：**
```json
{
  "cameras": {
    "0": 1, "13": 1, "18": 1, "26": 1, 
    "34": 1, "57": 1, "63": 1, "89": 1
  },
  "camps": {
    "9": 1, "38": 1, "49": 1, "84": 1
  },
  "drones": {
    "22": 1, "43": 1, "86": 1
  },
  "rangers": {
    "9": 3, "38": 4, "49": 5, "84": 7
  },
  "fences": {
    "(0, 1)": 1, "(1, 2)": 1, "(2, 3)": 1, ...
  }
}
```

### 3.2 覆盖结果

**巡逻覆盖：** `Dict[int, float]`
```json
{
  "0": 0.95, "1": 0.87, "2": 0.92, ...
}
```

**无人机覆盖：** `Dict[int, float]`
```json
{
  "0": 0.99, "1": 0.95, "2": 1.00, ...
}
```

**摄像头覆盖：** `Dict[int, float]`
```json
{
  "0": 0.75, "1": 0.00, "2": 0.00, ...
}
```

**围栏保护：** `Dict[int, float]`
```json
{
  "0": 0.50, "1": 0.00, "2": 0.50, ...
}
```

### 3.3 保护效益

**数据结构：** `Dict[int, float]`

**说明：** 每个网格的保护效益值

**计算公式：**
```
B_i = R_i × (1 - exp(-E_i))
```

**示例数据：**
```json
{
  "0": 0.45, "1": 0.32, "2": 0.28, ...
}
```

---

## 4. 输出数据结构

### 4.1 优化结果 (OptimizationResult)

```python
{
  "best_fitness": 21.6465,                    # 最优适应度值
  "fitness_history": [21.5478, 21.5640, ...], # 每次迭代的适应度
  "solution": DeploymentSolution,              # 最优解
  "convergence_stats": {
    "initial_fitness": 21.5478,
    "final_fitness": 21.6465,
    "improvement_count": 8,
    "total_improvement": 0.0987,
    "improvement_rate": 0.46
  }
}
```

### 4.2 解决方案统计 (SolutionStatistics)

```python
{
  "total_cameras": 8,
  "total_drones": 3,
  "total_camps": 4,
  "total_rangers": 19,
  "total_fence_length": 50,
  "camera_locations": [0, 13, 18, 26, 34, 57, 63, 89],
  "drone_locations": [22, 43, 86],
  "camp_locations": [9, 38, 49, 84],
  "fence_edges": [[0, 1], [1, 2], ...]
}
```

### 4.3 覆盖统计 (CoverageStatistics)

```python
{
  "patrol": {
    "mean": 0.6614,
    "max": 1.00,
    "min": 0.00,
    "full_coverage_count": 61,
    "zero_coverage_count": 30
  },
  "drone": {
    "mean": 0.9999,
    "max": 1.00,
    "min": 0.95,
    "full_coverage_count": 91,
    "zero_coverage_count": 0
  },
  "camera": {
    "mean": 0.4283,
    "max": 1.00,
    "min": 0.00,
    "full_coverage_count": 36,
    "zero_coverage_count": 50
  },
  "fence": {
    "mean": 0.4890,
    "max": 1.00,
    "min": 0.00,
    "protected_count": 55
  }
}
```

### 4.4 保护效益统计 (BenefitStatistics)

```python
{
  "total_benefit": 21.6465,
  "mean_benefit": 0.2369,
  "max_benefit": 0.5931,
  "min_benefit": 0.0164,
  "std_benefit": 0.1561,
  "benefit_by_grid": {
    "0": 0.45, "1": 0.32, "2": 0.28, ...
  }
}
```

---

## 5. 文件格式规范

### 5.1 配置文件 (config.json)

```json
{
  "grid_radius": 5,
  "terrain_map": {
    "0": "SparseGrass",
    "1": "DenseGrass",
    ...
  },
  "risk_map": {
    "0": 0.75,
    "1": 0.45,
    ...
  },
  "constraints": {
    "total_patrol": 20,
    "total_camps": 5,
    "max_rangers_per_camp": 5,
    "total_cameras": 10,
    "total_drones": 3,
    "total_fence_length": 50.0
  },
  "coverage_params": {
    "patrol_radius": 5.0,
    "drone_radius": 8.0,
    "camera_radius": 3.0,
    "fence_protection": 0.5,
    "wp": 0.3,
    "wd": 0.3,
    "wc": 0.2,
    "wf": 0.2
  }
}
```

### 5.2 结果文件 (results.json)

```json
{
  "best_fitness": 21.64649279388448,
  "fitness_history": [21.5478, 21.5640, ...],
  "solution_stats": {
    "total_cameras": 8,
    "total_drones": 3,
    "total_camps": 4,
    "total_rangers": 19,
    "total_fence_length": 50,
    "camera_locations": [0, 13, 18, 26, 34, 57, 63, 89],
    "drone_locations": [22, 43, 86],
    "camp_locations": [9, 38, 49, 84],
    "fence_edges": [[7, 15], [7, 8], ...]
  },
  "grid_count": 91,
  "terrain_distribution": {
    "SparseGrass": 32,
    "DenseGrass": 23,
    "SaltMarsh": 14,
    "WaterHole": 13,
    "Road": 9
  }
}
```

### 5.3 收敛历史 (convergence_history.json)

```json
{
  "initial_fitness": 21.5477932908442,
  "final_fitness": 21.64649279388448,
  "total_iterations": 50,
  "improvement_count": 8,
  "total_improvement": 0.09869950304028064,
  "fitness_history": [21.5478, 21.5478, ...],
  "improvements": [
    {
      "iteration": 12,
      "prev_fitness": 21.5477932908442,
      "curr_fitness": 21.563971892865755,
      "improvement": 0.01617860202155502,
      "rate": 0.07508239255199485
    },
    ...
  ]
}
```

### 5.4 收敛详细数据 (convergence_detailed.csv)

```csv
iteration,fitness,cameras,drones,camps,rangers,fence_length,camera_locations,drone_locations,camp_locations
0,21.5477932908442,6,3,4,19,50,"[63, 34, 26, 18, 0, 57]","[22, 86, 43]","[38, 49, 84, 9]"
1,21.5477932908442,6,3,4,19,50,"[63, 34, 26, 18, 0, 57]","[22, 86, 43]","[38, 49, 84, 9]"
...
50,21.64649279388448,8,3,4,19,50,"[0, 13, 18, 26, 34, 57, 63, 89]","[22, 43, 86]","[9, 38, 49, 84]"
```

---

## 6. 核心算法实现

### 6.1 六边形距离计算

```python
def hex_distance(grid1: GridData, grid2: GridData) -> int:
    """
    计算两个六边形网格之间的距离
    使用轴坐标距离公式
    """
    return (abs(grid1.q - grid2.q) + 
            abs(grid1.q + grid1.r - grid2.q - grid2.r) + 
            abs(grid1.r - grid2.r)) // 2
```

### 6.2 巡逻覆盖计算

```python
def calculate_patrol_coverage(self, solution: DeploymentSolution) -> Dict[int, float]:
    """
    计算每个网格的巡逻覆盖度
    公式: Patrol_i = 1 - exp(-Σ(s_j * p_j * exp(-d_ij / r_p)))
    """
    patrol_coverage = {}
    for grid_id in self.grid_ids:
        if self.deployment_matrix['patrol'][grid_id] == 0:
            patrol_coverage[grid_id] = 0.0
            continue
        
        patrol_intensity = 0.0
        for camp_id, camp_value in solution.camps.items():
            if camp_value == 1:
                rangers = solution.rangers.get(camp_id, 0)
                distance = self.grid_model.get_distance(grid_id, camp_id)
                patrol_intensity += rangers * np.exp(-distance / self.params.patrol_radius)
        
        patrol_coverage[grid_id] = 1 - np.exp(-patrol_intensity)
    return patrol_coverage
```

### 6.3 保护效益计算

```python
def calculate_protection_benefit(self, solution: DeploymentSolution) -> Dict[int, float]:
    """
    计算每个网格的保护效益
    公式: B_i = R_i * (1 - exp(-E_i))
    其中 E_i = w_p*Patrol_i + w_d*Drone_i + w_c*Camera_i + w_f*Fence_i
    """
    protection_effect = self.calculate_protection_effect(solution)
    protection_benefit = {}
    
    for grid_id in self.grid_ids:
        risk = self.grid_model.get_grid_risk(grid_id)
        E_i = protection_effect[grid_id]
        B_i = risk * (1 - np.exp(-E_i))
        protection_benefit[grid_id] = B_i
    
    return protection_benefit
```

### 6.4 DSSA生产者更新

```python
def _update_producers(self, iteration: int):
    """
    更新生产者位置
    生产者向最优解方向移动
    """
    num_producers = int(self.config.population_size * self.config.producer_ratio)
    producers = self.population[:num_producers]
    
    for i, solution in enumerate(producers):
        if i == 0:
            # 最优生产者向全局最优移动
            current_vector = self._solution_to_vector(solution)
            best_vector = self._solution_to_vector(self.best_solution)
            new_vector = current_vector + np.random.uniform(0, 1) * (best_vector - current_vector)
        else:
            # 其他生产者随机探索
            current_vector = self._solution_to_vector(solution)
            new_vector = current_vector + np.random.uniform(-1, 1, current_vector.shape)
        
        new_solution = self._vector_to_solution(new_vector)
        new_solution = self.coverage_model.repair_solution(new_solution, self.constraints)
        
        # 选择更优解
        current_fitness = self.evaluate_fitness(solution)
        new_fitness = self.evaluate_fitness(new_solution)
        if new_fitness > current_fitness:
            self.population[i] = new_solution
```

---

## 7. 可视化输出

### 7.1 风险热力图 (risk_heatmap.png)

- **类型**: 六边形网格热力图
- **颜色映射**: YlOrRd (黄色到红色)
- **显示内容**: 每个网格的风险值 R_i
- **用途**: 识别高风险区域

### 7.2 资源部署图 (deployment_map.png)

- **类型**: 六边形网格+标记图
- **标记说明**:
  - 🔴 红色圆圈: 摄像头 (C)
  - 🔵 蓝色圆圈: 无人机 (D)
  - 🟢 绿色圆圈: 营地 (S+人数)
  - 🟠 橙色线段: 围栏
- **背景**: 地形类型颜色编码
- **用途**: 展示最优资源配置方案

### 7.3 收敛曲线图 (convergence_curve.png)

- **类型**: 折线图
- **X轴**: 迭代次数
- **Y轴**: 适应度值
- **曲线**: 最优适应度随迭代变化
- **用途**: 评估算法收敛性

### 7.4 地形分布图 (terrain_map.png)

- **类型**: 六边形网格图
- **颜色编码**:
  - 盐沼: 米色 (#E8DCC4)
  - 稀疏草原: 浅绿 (#90EE90)
  - 密集草原: 深绿 (#228B22)
  - 水坑: 浅蓝 (#87CEEB)
  - 主路: 灰色 (#808080)
- **用途**: 展示保护区地形分布

---

## 8. 使用示例

### 8.1 基本使用

```python
from main import WildlifeProtectionOptimizer
from dssa_optimizer import DSSAConfig

# 创建优化器
optimizer = WildlifeProtectionOptimizer()

# 设置默认场景
optimizer.setup_default_scenario()

# 配置DSSA
dssa_config = DSSAConfig(
    population_size=50,
    max_iterations=100
)

# 运行优化
solution, fitness, history = optimizer.run_optimization(dssa_config)

# 生成可视化
optimizer.generate_all_visualizations()

# 保存结果
optimizer.save_results()
```

### 8.2 自定义配置

```python
import json

# 加载自定义配置
with open('custom_config.json', 'r') as f:
    config = json.load(f)

# 使用配置创建优化器
optimizer = WildlifeProtectionOptimizer(config)

# 运行优化
optimizer.run_optimization()
```

### 8.3 收敛追踪

```python
from demo_convergence import demo_with_convergence_tracking

# 运行带收敛追踪的demo
result = demo_with_convergence_tracking()

# 访问收敛历史
fitness_history = result['fitness_history']
improvements = result['improvements']
```

---

## 9. 性能指标

### 9.1 时间复杂度

| 操作 | 复杂度 | 说明 |
|------|--------|------|
| 网格生成 | O(n) | n = 网格数量 |
| 距离计算 | O(n²) | 计算所有网格对距离 |
| 覆盖计算 | O(n × m) | m = 资源数量 |
| DSSA迭代 | O(pop_size × iter × n) | 种群大小 × 迭代次数 × 网格数 |

### 9.2 空间复杂度

| 数据结构 | 空间复杂度 | 说明 |
|----------|-----------|------|
| 网格数据 | O(n) | 存储网格信息 |
| 距离矩阵 | O(n²) | 存储网格间距离 |
| 部署矩阵 | O(n × r) | r = 资源类型数 |
| 种群 | O(pop_size × n) | 存储多个解 |

### 9.3 典型性能

- **网格规模**: 91个六边形网格 (半径=5)
- **优化时间**: 30-60秒 (50-100迭代)
- **内存占用**: 50-100 MB
- **收敛速度**: 8-15次改进/100迭代

---

## 10. 扩展指南

### 10.1 添加新资源类型

1. 在 `data_loader.py` 中更新 `initialize_deployment_matrix()`
2. 在 `coverage_model.py` 中添加新的覆盖计算方法
3. 在 `DeploymentSolution` 中添加新资源的决策变量
4. 在 `dssa_optimizer.py` 中更新解的编码/解码方法

### 10.2 修改覆盖模型

1. 编辑 `coverage_model.py` 中的覆盖计算方法
2. 调整覆盖半径或衰减函数
3. 更新权重参数

### 10.3 自定义可视化

1. 在 `visualization.py` 中添加新的绘图方法
2. 使用 `matplotlib` 创建自定义图表
3. 在 `main.py` 中调用新的可视化方法

---

## 11. 注意事项

1. **随机种子**: 使用 `np.random.seed()` 确保结果可重复
2. **约束修复**: 所有解都经过 `repair_solution()` 确保可行性
3. **数值稳定性**: 使用 `np.exp()` 时注意溢出处理
4. **内存管理**: 大规模网格时注意距离矩阵的内存占用
5. **收敛判断**: 建议运行多次取平均结果

---

**文档版本**: 1.0  
**最后更新**: 2024年  
**作者**: AI Assistant
