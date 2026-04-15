# IMM C 2026 - 野生动物保护区资源优化系统

## 目录结构

```
immc2026/
├── hexdynamic/      # 六边形网格动态资源优化系统
├── marker/          # 图片查看和网格标记工具
└── riskIndex/       # 保护区网格风险指数模型
```

---

## hexdynamic/ - 六边形网格动态资源优化系统

### 主要功能

基于六边形蜂窝网格的野生动物保护区资源部署优化系统，使用 DSSA（动态麻雀搜索算法）优化巡逻人员、无人机、监控摄像头、基地营地和围栏的部署。

### 核心模块

| 文件 | 功能 |
|------|------|
| `main.py` | 主程序入口，完整工作流控制 |
| `demo.py` | 基于JSON配置的演示程序 |
| `batch_run.py` | 批量运行脚本，测试多个资源配置 |
| `data_loader.py` | 数据加载、网格生成、约束管理 |
| `grid_model.py` | 六边形网格模型、距离计算、邻接关系 |
| `coverage_model.py` | 保护覆盖计算、效益评估 |
| `dssa_optimizer.py` | DSSA优化算法实现 |
| `dynamic_coverage_model.py` | 时间动态保护分析 |
| `visualization.py` | 可视化和绘图 |

### 关键模型与公式

#### 1. 六边形网格距离计算
```
六边形距离 = max(|q1-q2|, |r1-r2|, |s1-s2|)
其中 s = -q - r
```

#### 2. 巡逻覆盖模型（指数衰减）
```
巡逻强度 = Σ [rangers × exp(-distance / patrol_radius)]
巡逻覆盖 = 1 - exp(-巡逻强度)
```

#### 3. 综合保护效益
```
E_i = wp × 巡逻覆盖 + wd × 无人机覆盖 + wc × 摄像头覆盖 + wf × 围栏保护

保护效益 B_i = 风险值 R_i × (1 - exp(-E_i))

总保护效益 = ΣB_i / ΣR_i（归一化）
```

### 关键参数（默认值）

#### 覆盖参数 (`CoverageParameters`)
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `patrol_radius` | 5.0 | 巡逻人员有效半径 |
| `drone_radius` | 8.0 | 无人机有效半径 |
| `camera_radius` | 3.0 | 摄像头有效半径 |
| `fence_protection` | 0.5 | 围栏保护系数 |
| `wp` | 0.3 | 巡逻权重 |
| `wd` | 0.3 | 无人机权重 |
| `wc` | 0.2 | 摄像头权重 |
| `wf` | 0.2 | 围栏权重 |

#### DSSA 算法参数 (`DSSAConfig`)
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `population_size` | 50 | 种群大小 |
| `max_iterations` | 100 | 最大迭代次数 |
| `producer_ratio` | 0.2 | 生产者比例 |
| `scout_ratio` | 0.2 | 侦察者比例 |
| `ST` | 0.8 | 稳定阈值 |
| `R2` | 0.5 | 探索参数 |

#### 资源约束
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `total_patrol` | 20 | 巡逻人员总数 |
| `total_camps` | 5 | 基地营地数量 |
| `max_rangers_per_camp` | 5 | 每个营地最大人员数 |
| `total_cameras` | 10 | 摄像头数量 |
| `total_drones` | 3 | 无人机数量 |
| `total_fence_length` | 50.0 | 围栏总长度 |

### 输入输出

#### 输入
- `demo_config.json` - 配置文件，包含网格尺寸、风险配置、资源库存、覆盖参数等

#### 输出（demo.py）
- `1_risk_heatmap.png` - 网格风险值热力图
- `2_resource_distribution.png` - 资源分布图
- `3_protection_heatmap.png` - 保护水平热力图
- `4_convergence_curve.png` - DSSA收敛曲线
- `5_terrain_map.png` - 地形分布图
- `6_time_dynamic_analysis.png` - 时间动态分析图
- `demo_results.json` - 完整结果数据
- `summary_report.txt` - 摘要报告

#### 批量运行输出（batch_run.py）
- `batch_output/{resource_type}/run_XXX/` - 每个资源类型的运行目录
- `batch_output/batch_summary.json` - JSON汇总报告
- `batch_output/batch_summary.txt` - 文本汇总报告

---

## marker/ - 图片查看和网格标记工具

### 主要功能

独立的本地图片查看和六边形网格标记工具，用于手动标记保护区网格。

### 核心文件

| 文件 | 功能 |
|------|------|
| `image-viewer.html` | 完整的HTML5图片查看和网格标记工具 |
| `grid-coordinates.json` | 预生成的网格坐标数据示例 |

### 功能特性

- 本地图片上传和预览
- 六边形网格生成和可视化
- 7种预设颜色标记系统
- 缩放和平移功能
- 网格选择（单选、多选、框选）
- JSON/SVG数据导出

### 输入输出

#### 输入
- 本地图片文件
- JSON网格坐标文件（可选）

#### 输出
- JSON格式的网格坐标和标记数据
- SVG格式的网格图层

---

## riskIndex/ - 保护区网格风险指数模型

### 主要功能

计算野生动物保护区网格单元的风险系数，用于指导巡逻和监测资源的最优分配。

### 核心模块

| 文件 | 功能 |
|------|------|
| `risk_model_wrapper.py` | JSON配置驱动的主API入口 |
| `generate_hex_map.py` | 六边形网格地图生成器 |
| `generate_square_map.py` | 方形网格地图生成器 |
| `visualize_risk_from_json.py` | 风险热力图可视化工具 |
| `convert_map_for_wrapper.py` | 地图数据格式转换 |
| `src/risk_model/` | 核心风险模型库 |

### 核心模块结构

```
src/risk_model/
├── core/          # 核心数据结构（Grid, Species, Environment, TimeContext）
├── risk/          # 风险计算器
│   ├── human.py           # 人为风险计算器
│   ├── environmental.py   # 环境风险计算器
│   ├── density.py         # 物种密度风险计算器
│   ├── temporal.py        # 时间因素计算器
│   └── composite.py       # 综合风险计算器
├── config/        # 配置管理（权重、默认值）
├── data/          # 数据生成和I/O
├── visualization/ # 绘图和可视化
└── advanced/      # IMMC高级功能（DSSA、时空风险场）
```

### 关键模型与公式

#### 1. 人为风险（距离加权）
```
人为风险 = boundary_weight × 距离边界归一化
         + road_weight × 距离道路归一化
         + water_weight × 距离水源归一化
```

#### 2. 环境风险
```
环境风险 = fire_weight × 火灾风险
         + terrain_weight × 地形复杂度
```

#### 3. 综合风险（归一化）
```
原始风险 = human_risk × human_weight
         + environmental_risk × environmental_weight
         + density_value × density_weight

归一化风险 = (原始风险 - min) / (max - min)
```

#### 4. 时间因素
```
日周期因子 = sin(π × (hour - 6) / 12)  # 白天高，夜晚低

季节因子 = 干季/雨季调整系数

时间因子 = 日周期 × 季节因子
```

### 关键参数（默认值）

#### 风险权重 (`RiskWeights`)
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `human_weight` | 0.4 | 人为风险权重 |
| `environmental_weight` | 0.3 | 环境风险权重 |
| `density_weight` | 0.3 | 物种密度权重 |

#### 人为风险权重 (`HumanRiskWeights`)
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `boundary_weight` | 0.4 | 距离边界权重 |
| `road_weight` | 0.35 | 距离道路权重 |
| `water_weight` | 0.25 | 距离水源权重 |

#### 环境风险权重 (`EnvironmentalRiskWeights`)
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `fire_weight` | 0.6 | 火灾风险权重 |
| `terrain_weight` | 0.4 | 地形复杂度权重 |

### 输入输出

#### 输入（risk_model_wrapper.py）
- `data.json` - 包含地图配置、网格数据、时间上下文
- `config.json` - 可选的权重配置文件

#### 输出
- `results.json` - 包含每个网格的原始风险和归一化风险

#### 地图生成器输出
- `hex_map_for_risk.json` / `square_map_for_risk.json` - 生成的地图数据

---

## 快速开始

### hexdynamic - 运行单次优化
```bash
cd hexdynamic
python demo.py
# 或使用自定义配置
python demo.py my_config.json
```

### hexdynamic - 批量运行
```bash
cd hexdynamic
python batch_run.py --runs 10 --min 2 --range 4
```

### riskIndex - 运行风险计算
```bash
cd riskIndex
python risk_model_wrapper.py --data example_data.json --config example_config.json --output results.json
```

### riskIndex - 生成地图
```bash
cd riskIndex
python generate_hex_map.py
python generate_square_map.py
```

---

## 依赖要求

所有项目都需要：
- Python 3.7+
- numpy
- matplotlib

安装依赖：
```bash
pip install -r requirements.txt
```
