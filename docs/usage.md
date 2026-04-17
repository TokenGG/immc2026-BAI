# 使用说明

本文档说明如何使用以下工具完成从地图标注到保护资源部署优化的完整流程。

***

## 整体流程

```
地图图片
  │
  ▼
[Marker] 在图片上绘制六边形网格，标注地形与物种信息
  │  导出 pipeline_input.json
  │
  │  或者
  │
[generate_map.py] 随机生成 m×n 地图数据
  │  输出 pipeline_input.json
  ├─────────────────────────────────────┐
  │                                     │
  ▼                                     ▼
[risk_analysis.py]                   [run.py]  ← 推荐入口
计算风险指数                      计算风险指数 → DSSA 优化 → 可视化
生成热力图+属性图                  （整合 protection_pipeline + visualize_output）
                                         │
                                    也可分步运行：
                                    [protection_pipeline.py] → output.json
                                    [visualize_output.py]    → 图片
```

***

## 一、Marker 标注工具

文件：`marker/image-viewer.html`，直接用浏览器打开，无需安装依赖。

### 基本操作

**加载图片**：将地图图片拖入页面，或点击上传区域选择文件。

**网格化**：点击 `⬡ 网格化` 按钮叠加六边形网格，拖动 `半径` 滑块调整网格大小。

**标注地形**：调色板中每种颜色对应一种地形类型：

| 颜色    | 地形类型  | terrain\_type |
| ----- | ----- | ------------- |
| 🟢 绿色 | 森林密集区 | DenseGrass    |
| 🔴 红色 | 森林稀疏区 | SparseGrass   |
| 🔵 蓝色 | 水坑    | WaterHole     |
| 🟡 黄色 | 干坑    | SaltMarsh     |
| 🟣 紫色 | 主路    | Road          |
| 🟠 橙色 | 小路    | Road          |
| 🩵 青色 | 盐沼    | SaltMarsh     |

- 单击色块选色，再单击格子填色；框选可批量填色
- 再次单击已填色格子取消填色
- `Ctrl/Cmd + 点击` 多选后点色块统一填色
- `📥 导入JSON` / `📤 导出JSON`：导入或导出网格标注数据
- `📥 导出SVG`：导出带图例的矢量网格图

### 导出 Pipeline 输入 JSON

完成标注后点击 `🚀 导出Pipeline JSON`，在弹出的配置面板中填写参数后点击 `📥 生成并下载`，下载 `pipeline_input.json`。

配置面板参数说明见第三节（与 `generate_map.py` 参数一致）。

> 未标注颜色的格子默认视为 SparseGrass。主路/小路格子坐标自动提取为 `road_locations`，水坑格子自动提取为 `water_locations`。

***

## 二、地图生成脚本

文件：`hexdynamic/generate_map.py`

随机生成 m×n 规模的地图，直接输出 pipeline 输入 JSON，无需手动标注。

### 用法

```bash
# 基本用法（10×12，默认参数）
python generate_map.py -m 10 -n 12 -o pipeline_input.json

# 指定资源约束和时间
python generate_map.py -m 20 -n 25 --total_patrol 40 --total_cameras 20 --season RAINY -o map.json

# 固定随机种子（可复现）
python generate_map.py -m 15 -n 15 --seed 42 -o map.json
```

### 生成规则

- 道路随机选南北或东西方向贯穿，每隔 2\~3 格随机横向偏移 ±1，不是直线
- 犀牛/大象密度只在 SparseGrass 格子生成，其他地形为 0
- 鸟类密度在 SaltMarsh 为 0.6~~1.0，其他地形为 0~~0.1

### 命令行参数

| 参数                       | 默认值                  | 说明                        |
| ------------------------ | -------------------- | ------------------------- |
| `-m`                     | 10                   | 地图行数                      |
| `-n`                     | 12                   | 地图列数                      |
| `-o`                     | pipeline\_input.json | 输出文件路径                    |
| `--seed`                 | None                 | 随机种子                      |
| `--hour_of_day`          | 12                   | 时间（0-23）                  |
| `--season`               | DRY                  | 季节：DRY / RAINY            |
| `--use_temporal_factors` | False                | 启用昼夜/季节时间因子               |
| `--total_patrol`         | 20                   | 巡逻人员总数                    |
| `--total_camps`          | 5                    | 营地总数                      |
| `--max_rangers_per_camp` | 5                    | 每营地最大人员                   |
| `--total_cameras`        | 10                   | 摄像头总数                     |
| `--total_drones`         | 3                    | 无人机总数                     |
| `--total_fence_length`   | 50                   | 围栏参数（已不影响结果，围栏固定部署在所有边缘格） |
| `--patrol_radius`        | 5.0                  | 巡逻覆盖衰减半径                  |
| `--drone_radius`         | 8.0                  | 无人机覆盖半径                   |
| `--camera_radius`        | 3.0                  | 摄像头覆盖半径                   |
| `--fence_protection`     | 0.5                  | 每段围栏保护系数                  |
| `--wp/wd/wc/wf`          | 0.3/0.3/0.2/0.2      | 巡逻/无人机/摄像头/围栏权重           |
| `--population_size`      | 50                   | DSSA 种群大小                 |
| `--max_iterations`       | 100                  | DSSA 最大迭代次数               |

***

## 三、Protection Pipeline 脚本

文件：`hexdynamic/protection_pipeline.py`

> 推荐使用 `run.py`（见第三节）一键完成优化+可视化。`protection_pipeline.py` 适合只需要输出 JSON、不需要图片的场景。

### 依赖安装

```bash
pip install -r hexdynamic/requirements.txt
pip install -r riskIndex/requirements.txt
```

### 用法

```bash
cd hexdynamic

# 默认模式
python protection_pipeline.py <input.json> <output.json>

# 向量化模式（大规模网格推荐，千级以上网格约 4x+ 加速）
python protection_pipeline.py <input.json> <output.json> --vectorized

# 冻结部分资源（不参与优化）
python protection_pipeline.py <input.json> <output.json> --freeze-resources patrol,camera
```

`--vectorized` 启用 `VectorizedCoverageModel`，用 NumPy 矩阵运算替代 Python 循环计算覆盖度，初始化时预构建距离矩阵切片和部署掩码，每次 `evaluate_fitness` 只做矩阵广播运算。网格数越大加速比越显著，120 格约 4x，上千格预计 10x+。

运行时每轮迭代输出格式：

```
Iter    1/100  fitness=0.351623  iter=84.5ms  avg=84.5ms
...
Optimization completed.  Best Fitness = 0.498100  Total = 8.45s  Avg/iter = 84.5ms
```

- `fitness`：当前最优适应度
- `iter`：本轮耗时
- `avg`：累计平均每轮耗时

### 输入 JSON 格式

```jsonc
{
  // * 地图配置（用于计算各格到边界/道路/水源的距离）
  "map_config": {
    "map_width": 12,
    "map_height": 10,
    "boundary_type": "RECTANGLE",
    "road_locations": [[1,0], [2,1]],   // 道路格子的 [x, y] 坐标
    "water_locations": [[0,3], [4,0]]   // 水源格子的 [x, y] 坐标
  },

  // 时间上下文（可选，默认 hour=12, season=DRY）
  "time": { "hour_of_day": 14, "season": "DRY" },

  // 是否启用昼夜/季节时间因子（可选，默认 false）
  "use_temporal_factors": false,

  // 风险模型权重（可选）
  "risk_model_config": {
    "risk_weights": { "human_weight": 0.4, "environmental_weight": 0.3, "density_weight": 0.3 },
    "human_risk_weights": { "boundary_weight": 0.4, "road_weight": 0.35, "water_weight": 0.25 },
    "environmental_risk_weights": { "fire_weight": 0.6, "terrain_weight": 0.4 }
  },

  // * 物种配置
  "species_config": {
    "rhino":    { "weight": 0.5, "rainy_season_multiplier": 1.2, "dry_season_multiplier": 1.0 },
    "elephant": { "weight": 0.3, "rainy_season_multiplier": 1.3, "dry_season_multiplier": 0.9 },
    "bird":     { "weight": 0.2, "rainy_season_multiplier": 1.5, "dry_season_multiplier": 0.8 }
  },

  // * 网格列表
  "grids": [
    {
      "grid_id": 0,
      "q": 0, "r": 0,             // * 六边形轴坐标
      "x": 0, "y": 0,             // * 笛卡尔坐标（原点左下，y 轴向上）
      "hex_size": 62,             // 格子像素半径（来自 marker）
      "terrain_type": "SparseGrass",  // * 见地形类型表
      "fire_risk": 0.3,           // * 火灾风险 [0,1]
      "terrain_complexity": 0.2,  // * 地形复杂度 [0,1]
      "vegetation_type": "GRASSLAND", // * GRASSLAND / FOREST / SHRUB
      "species_densities": { "rhino": 0.4, "elephant": 0.3, "bird": 0.5 }
    }
  ],

  // * 资源约束
  "constraints": {
    "total_patrol": 20, "total_camps": 5, "max_rangers_per_camp": 5,
    "total_cameras": 10, "total_drones": 3, "total_fence_length": 50,
    "max_cameras_per_grid": 3,   // 单格最大摄像头数（默认 3）
    "max_drones_per_grid": 1,    // 单格最大无人机数（默认 1）
    "max_camps_per_grid": 1,     // 单格最大营地数（默认 1）
    "max_rangers_per_grid": 1    // 单格最大巡逻人员数（默认 1）
  },

  // 覆盖参数（可选）
  "coverage_params": {
    "patrol_radius": 5.0, "drone_radius": 8.0, "camera_radius": 3.0,
    "fence_protection": 0.5, "wp": 0.3, "wd": 0.3, "wc": 0.2, "wf": 0.2
  },

  // DSSA 优化参数（可选）
  "dssa_config": {
    "population_size": 50, "max_iterations": 100,
    "producer_ratio": 0.2, "scout_ratio": 0.2, "ST": 0.8, "R2": 0.5
  }
}
```

### 地形类型与部署约束

| terrain\_type |    巡逻   |  营地 | 无人机 | 摄像头 |   围栏   |
| ------------- | :-----: | :-: | :-: | :-: | :----: |
| SparseGrass   | ✓（无物种时） |  ✗  |  ✓  |  ✓  | ✓（仅边缘） |
| DenseGrass    |    ✗    |  ✗  |  ✓  |  ✗  | ✓（仅边缘） |
| WaterHole     |    ✗    |  ✗  |  ✓  |  ✗  |    ✗   |
| SaltMarsh     |    ✗    |  ✗  |  ✓  |  ✗  |    ✗   |
| Road          |    ✓    |  ✓  |  ✓  |  ✓  | ✓（仅边缘） |

巡逻员部署规则：

- 只能部署在 Road 或无物种的 SparseGrass 格子
- 有任意物种密度（`species_densities` 中任一值 > 0）的格子禁止部署巡逻员
- 不能部署在 WaterHole、DenseGrass（树林）、SaltMarsh

围栏固定部署在所有地图边缘格子（地形允许的边），不参与 DSSA 优化，`total_fence_length` 参数不再影响结果。

### 输出 JSON 格式

```jsonc
{
  "summary": {
    "total_grids": 120,
    "total_risk": 45.23,
    "best_fitness": 0.498,          // 风险加权归一化保护效率（优化目标）
    "total_protection_benefit": 33.2, // Σ [R_i × (1 - e^(-E_i))]
    "average_protection_benefit": 0.277, // Total / 格子数
    "fitness_history": [...],
    "resources_deployed": { "total_cameras": 10, "total_drones": 3, ... }
  },
  "grids": [
    {
      "grid_id": 0, "q": 0, "r": 0, "x": 0, "y": 0,
      "terrain_type": "SparseGrass",
      "risk_normalized": 0.35,              // riskIndex 归一化风险 [0,1]
      "protection_benefit_raw": 0.22,       // R_i × (1 - e^(-E_i))
      "protection_benefit_normalized": 0.43, // min-max 归一化 [0,1]
      "residual_risk_normalized": 0.18,     // 部署后剩余风险 R_i × e^(-E_i)，min-max 归一化
      "deployment": {
        "patrol_rangers": 0, "camp": 0, "drone": 1, "camera": 2
      },
      "hex_size": 62
    }
  ],
  "fence_edges": [
    { "grid_id_1": 0, "grid_id_2": 1 }  // 部署围栏的相邻格子对
  ]
}
```

### 关键指标说明

| 指标                              | 公式                           | 含义                |
| ------------------------------- | ---------------------------- | ----------------- |
| `risk_normalized`               | riskIndex min-max 归一化        | 综合威胁程度，越高越需要保护    |
| `protection_benefit_raw`        | `R_i × (1 - e^(-E_i))`       | 该格实际获得的保护收益       |
| `protection_benefit_normalized` | min-max 归一化                  | 相对保护收益，便于可视化      |
| `residual_risk_normalized`      | `R_i × e^(-E_i)`，min-max 归一化 | 部署后剩余风险，越低说明保护越充分 |
| `Total Protection Benefit`      | `Σ protection_benefit_raw`   | 全局保护收益总量          |
| `Average Protection Benefit`    | `Total / N`                  | 每格平均保护收益          |
| `Best Fitness`                  | `Total / Σ R_i`              | 风险加权归一化保护效率，优化目标  |

综合保护效果 `E_i = wp × patrol_cov + wd × drone_cov + wc × camera_cov + wf × fence_prot`，各覆盖度基于指数衰减函数计算。

***

## 六、风险模型说明（riskIndex）

pipeline 脚本调用 `riskIndex` 模块计算每个网格的归一化综合风险值 `R_i ∈ [0, 1]`，作为 DSSA 优化的输入。

### 综合风险公式

```
R'_i = (ω₁·H_i + ω₂·E_i + ω₃·D_i) × T_t × S_t

R_i = (R'_i - R_min) / (R_max - R_min)
```

| 符号   | 含义             | 默认权重     |
| ---- | -------------- | -------- |
| H\_i | 人为风险（盗猎/人兽冲突）  | ω₁ = 0.4 |
| E\_i | 环境风险（火灾 + 地形）  | ω₂ = 0.3 |
| D\_i | 物种密度风险（珍稀物种分布） | ω₃ = 0.3 |
| T\_t | 昼夜因子（可选）       | —        |
| S\_t | 季节因子（可选）       | —        |

### 人为风险 H\_i（盗猎风险 + 人兽冲突）

反映人类活动对保护区的威胁，综合考虑三个距离因素：

```
H_i = (α₁·prox_boundary + α₂·prox_road + α₃·prox_water) × P_t
```

| 因素              | 含义                  | 默认权重      |
| --------------- | ------------------- | --------- |
| `prox_boundary` | 到保护区边界的接近度（越近越高）    | α₁ = 0.40 |
| `prox_road`     | 到道路的接近度（道路是盗猎者进入通道） | α₂ = 0.35 |
| `prox_water`    | 到水源的接近度（水源是人兽冲突热点）  | α₃ = 0.25 |
| `P_t`           | 盗猎时间概率（由昼夜因子决定）     | —         |

接近度 = `1 - 归一化距离`，即距离越近，接近度越高，风险越大。

在输入 JSON 中，`road_locations` 和 `water_locations` 用于自动计算各格到道路/水源的距离。

### 环境风险 E\_i（火灾风险 + 地形复杂度）

```
E_i = β₁·fire_risk + β₂·terrain_complexity
```

| 字段                   | 含义                       | 默认权重     |
| -------------------- | ------------------------ | -------- |
| `fire_risk`          | 火灾风险 \[0,1]，由植被类型和干燥程度决定 | β₁ = 0.6 |
| `terrain_complexity` | 地形复杂度 \[0,1]，复杂地形增加巡逻难度  | β₂ = 0.4 |

这两个值在每个网格的输入数据中直接提供（`generate_map.py` 按地形类型随机生成，marker 工具按颜色给出默认值）。

### 物种密度风险 D\_i（珍稀物种分布）

反映该格子的保护价值，物种越密集、保护权重越高，风险值越高：

```
D_i = Σ_s (w_s × density_{s,i} × seasonal_multiplier_s)
```

| 参数                      | 含义                                        |
| ----------------------- | ----------------------------------------- |
| `w_s`                   | 物种保护权重（rhino=0.5, elephant=0.3, bird=0.2） |
| `density_{s,i}`         | 物种 s 在格子 i 的密度 \[0,1]                     |
| `seasonal_multiplier_s` | 季节密度系数（雨季/旱季不同）                           |

### 时间因子（可选，`use_temporal_factors: true` 时启用）

| 因子        | 计算方式                         | 默认值  |
| --------- | ---------------------------- | ---- |
| 昼夜因子 T\_t | 白天（6:00-18:00）= 1.0，夜间 = 1.3 | 离散模式 |
| 季节因子 S\_t | 旱季 = 1.0，雨季 = 1.2            | —    |

时间因子作为乘数叠加在基础风险上，夜间雨季的综合风险最高（×1.56）。默认关闭，适合需要分析特定时段风险的场景。

#### 时间因子与归一化的交互

启用时间因子后，原始风险值会按时间因子放大（例如夜间约 1.3 倍），但**归一化后的风险统计指标（min/max/mean）会相同**。这是因为：

1. 原始风险计算：`R'_i = (ω₁·H_i + ω₂·E_i + ω₃·D_i) × T_t × S_t`
2. 归一化处理：`R_i = (R'_i - R_min) / (R_max - R_min)`

所有原始风险都乘以相同的时间因子，因此 min/max 也同时放大，归一化后仍映射到 [0, 1] 范围。结果是：

- **原始风险**：夜间 ≈ 1.3 × 白天
- **归一化风险**：夜间与白天的 min/max/mean 统计值相同（都是 [0, 1] 范围）

这是**预期行为**，用于确保不同时段的风险分布形状一致，便于跨时段对比。若需要保留时间因子的绝对差异，应在输出后对原始风险值进行分析。

***

## 三点五、一键运行脚本（推荐）

文件：`hexdynamic/run.py`

整合 `protection_pipeline.py` 和 `visualize_output.py`，一条命令完成优化和出图。

### 用法

```bash
cd hexdynamic

# 完整流程：优化 + 出图
python run.py input.json output.json

# 指定图片目录和文件名前缀
python run.py input.json output.json --out_dir ./figures --prefix night_rainy

# 向量化模式 + 出图
python run.py input.json output.json --vectorized --out_dir ./figures

# 只优化，不出图
python run.py input.json output.json --no-visualize

# 只出图（已有 output JSON）
python run.py output.json --visualize-only --input input.json --out_dir ./figures
```

### 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `input` | 必填 | 输入 JSON（pipeline 模式）或 output JSON（`--visualize-only` 模式） |
| `output` | 必填（pipeline 模式） | 输出 JSON 路径 |
| `--vectorized` | false | 使用向量化覆盖模型（网格数 >1000 推荐） |
| `--allow-partial-deployment` | false | 允许按边际收益决定是否部署资源 |
| `--freeze-resources` | None | 冻结资源列表，逗号分隔，如 `patrol,camera` |
| `--no-visualize` | false | 只运行优化，不生成图片 |
| `--visualize-only` | false | 只生成图片，跳过优化 |
| `--input, -i` | None | `--visualize-only` 时的原始 input JSON（用于物种数据） |
| `--out_dir, -d` | `./figures` | 图片输出目录 |
| `--prefix` | `""` | 输出文件名前缀 |

### 输出

优化结果写入 `output.json`，图片写入 `--out_dir` 目录，文件名同 `visualize_output.py`（见第八节）。

***

文件：`hexdynamic/risk_analysis.py`

仅计算综合风险指数，生成风险热力图和地理属性+物种属性地图，不涉及 DSSA 优化。

### 用法

```bash
cd hexdynamic

# 基本用法（hex_size 自动从 input JSON 中提取）
python risk_analysis.py <input.json> <output_dir>

# 指定六边形大小（覆盖 input JSON 中的值）
python risk_analysis.py <input.json> <output_dir> --hex-size 1.0
```

hex\_size 优先级：命令行参数 > input JSON 中的 `grids[0].hex_size` > 默认值 1.0

### 输入

同 `protection_pipeline.py` 的输入 JSON 格式（见第三节）。

### 输出

输出到指定目录的四个文件：

| 文件                   | 内容            | 说明                      |
| -------------------- | ------------- | ----------------------- |
| `risk_heatmap.png`   | 归一化风险指数热力图 | YlOrRd 色阶，[0,1] 范围，便于跨时段对比 |
| `raw_risk_heatmap.png` | 原始风险指数热力图 | YlOrRd 色阶，保留时间因子的绝对差异 |
| `attributes_map.png` | 2×2 地理+物种属性图  | 包含植被类型、地形复杂度、火灾风险、物种总密度 |
| `risk_results.json`  | 每个网格的风险值及属性数据 | 包含 normalized_risk 和 raw_risk 两个字段 |

#### 两种风险值的区别

**归一化风险** (`normalized_risk`)：
- 范围：[0, 1]
- 用途：DSSA 优化、跨时段对比
- 特点：不同时段的 min/max/mean 相同，相对排序一致

**原始风险** (`raw_risk`)：
- 范围：取决于输入数据和时间因子
- 用途：绝对风险评估、时间感知决策
- 特点：保留时间因子的绝对差异（夜间 ≈ 1.3 × 白天）

#### risk\_heatmap.png

单图热力图，显示每个网格的**归一化**综合风险值（0～1），便于快速识别高风险区域。所有时段的热力图视觉效果相同。

#### raw\_risk\_heatmap.png

单图热力图，显示每个网格的**原始**综合风险值，保留时间因子的影响。不同时段的热力图颜色分布不同：
- 白天：风险值较低，热力图偏黄
- 夜间：风险值较高（×1.3），热力图偏红

#### attributes\_map.png

2×2 子图布局：

| 位置     | 内容    | 类型                                    |
| ------ | ----- | ------------------------------------- |
| \[0,0] | 植被类型  | 分类色（GRASSLAND/SHRUB/FOREST/WETLAND 等） |
| \[0,1] | 地形复杂度 | 连续热力图（Blues 色阶）                       |
| \[1,0] | 火灾风险  | 连续热力图（Reds 色阶）                        |
| \[1,1] | 物种总密度 | 连续热力图（Greens 色阶）                      |

#### risk\_results.json

```jsonc
{
  "summary": {
    "total_grids": 120,
    "normalized_risk_min": 0.05,
    "normalized_risk_max": 0.95,
    "normalized_risk_mean": 0.45,
    "raw_risk_min": 0.053739,
    "raw_risk_max": 0.430381,
    "raw_risk_mean": 0.125050,
    "temporal_factor": 1.3  // 仅当启用时间因子时出现
  },
  "grids": [
    {
      "grid_id": 0,
      "q": 0, "r": 0,
      "normalized_risk": 0.35,
      "raw_risk": 0.053739,
      "vegetation_type": "GRASSLAND",
      "terrain_complexity": 0.2,
      "fire_risk": 0.3,
      "species_densities": { "rhino": 0.4, "elephant": 0.3, "bird": 0.5 }
    }
  ]
}
```

### 何时使用哪种风险值

| 场景 | 使用 | 原因 |
|------|------|------|
| DSSA 优化 | 归一化风险 | 已内置在算法中，不受时间因子影响 |
| 跨时段对比 | 归一化风险 | 相对排序一致，便于对比 |
| 绝对风险评估 | 原始风险 | 反映真实威胁程度 |
| 时间感知决策 | 两者结合 | 完整的决策信息 |

***

## 五、风险分析批量处理脚本

文件：`hexdynamic/risk_analysis_batch.py`

批量处理多个输入 JSON 文件，生成每个场景的独立可视化，并生成所有场景的对比图。

### 用法

```bash
cd hexdynamic

# 基本用法
python risk_analysis_batch.py --input-dir ./data --output-dir ./results

# 指定文件模式
python risk_analysis_batch.py --input-dir ./data --output-dir ./results --pattern "scenario_*.json"

# 指定 hex_size
python risk_analysis_batch.py --input-dir ./data --output-dir ./results --hex-size 62.0
```

### 输入

输入目录中的多个 JSON 文件，格式同 `protection_pipeline.py` 的输入 JSON。

### 输出结构

```
output_dir/
├── scenario_1/
│   ├── risk_heatmap.png
│   ├── raw_risk_heatmap.png
│   ├── attributes_map.png
│   └── risk_results.json
├── scenario_2/
│   ├── risk_heatmap.png
│   ├── raw_risk_heatmap.png
│   ├── attributes_map.png
│   └── risk_results.json
├── scenario_3/
│   └── ...
├── risk_heatmap_comparison.png      # 所有场景归一化风险对比
├── raw_risk_heatmap_comparison.png  # 所有场景原始风险对比
└── summary_report.json              # 统计汇总报告
```

### 输出文件说明

| 文件 | 说明 |
|------|------|
| `scenario_x/risk_heatmap.png` | 单个场景的归一化风险热力图 |
| `scenario_x/raw_risk_heatmap.png` | 单个场景的原始风险热力图 |
| `scenario_x/attributes_map.png` | 单个场景的地理属性图 |
| `scenario_x/risk_results.json` | 单个场景的风险数据 |
| `risk_heatmap_comparison.png` | 所有场景的归一化风险对比图（统一颜色条） |
| `raw_risk_heatmap_comparison.png` | 所有场景的原始风险对比图（统一颜色条） |
| `summary_report.json` | 所有场景的统计汇总 |

### 对比图特点

- **统一颜色条**：使用所有场景的最大风险值作为颜色条上限，确保不同场景之间可以直观对比
- **固定 2×2 布局**：每个热力图保持原始尺寸，不压缩
- **清晰标注**：每个子图标注场景名称
- **最多 4 个场景**：一次对比最多显示 4 个场景，超过 4 个会生成多张对比图

### 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--input-dir, -i` | 必需 | 输入目录路径 |
| `--output-dir, -o` | `./risk_analysis_results` | 输出目录路径 |
| `--pattern, -p` | `*.json` | 文件匹配模式 |
| `--hex-size` | 自动检测 | 六边形大小 |

### 使用场景

1. **多时段对比**：分析不同时段（白天/夜间、旱季/雨季）的风险分布差异
2. **多场景分析**：对比不同配置或假设下的风险分布
3. **批量报告生成**：自动生成所有场景的可视化和统计报告

### 示例

```bash
# 分析 data 目录下所有 JSON 文件
python risk_analysis_batch.py --input-dir ./data --output-dir ./results

# 只分析 scenario_ 开头的文件
python risk_analysis_batch.py --input-dir ./data --output-dir ./results --pattern "scenario_*.json"
```

### 输出示例

```
Scanning input directory: ./data
  Pattern: *.json
  Found 3 file(s)
    - scenario_1.json
    - scenario_2.json
    - scenario_3.json

Processing 3 file(s)...

[1/3] Processing: scenario_1.json
  Normalized: min=0.1234  max=0.8765  mean=0.4567
  Raw       : min=0.1234  max=1.2345  mean=0.6789
  Saved to: ./results/scenario_1/

[2/3] Processing: scenario_2.json
  ...

Generating comparison plots...
  Normalized risk max: 0.9876
  Raw risk max: 1.4567
  Saved: risk_heatmap_comparison.png
  Saved: raw_risk_heatmap_comparison.png
  Saved: summary_report.json

======================================================================
Batch processing complete!
  Processed: 3/3 file(s)
  Output directory: ./results
======================================================================
```

***

## 七、时间因子与资源部署策略

### 7.1 问题：为什么启用时间因子后，DSSA 优化结果相同？

当 `use_temporal_factors: true` 时，原始风险会按时间因子放大（夜间 ×1.3），但**DSSA 优化的资源分配结果不变**。这是因为：

**DSSA 优化目标**：
```
fitness = total_protection_benefit / total_risk
```

**时间因子的影响**：
```
fitness_night = Σ [1.3×R_i × (1 - e^(-E_i))] / Σ [1.3×R_i]
              = 1.3 × Σ [R_i × (1 - e^(-E_i))] / (1.3 × Σ R_i)
              = Σ [R_i × (1 - e^(-E_i))] / Σ R_i
              = fitness_day
```

由于分子分母同时乘以相同的时间因子，fitness 值不变，导致：
- 资源分配优先级相同
- 部署位置相同
- 部署数量相同

### 7.2 两种风险值的用途

| 风险值 | 范围 | 用途 | 特点 |
|--------|------|------|------|
| **归一化风险** | [0, 1] | DSSA 优化、跨时段对比 | 不同时段的相对排序一致 |
| **原始风险** | 取决于输入 | 绝对风险评估、时间感知决策 | 保留时间因子的绝对差异 |

### 7.3 如何利用时间因子信息

**方案 A：可视化对比（推荐用于决策支持）**
- 生成 `risk_heatmap.png`（归一化）和 `raw_risk_heatmap.png`（原始）
- 对比两张热力图，识别时间维度的风险差异
- 用于决策支持，但不改变 DSSA 优化结果
- 实现：`risk_analysis.py` 脚本

**方案 B：时间感知的资源分配（推荐用于自动优化）**
- 启用 `use_time_aware_fitness: true` 配置选项
- DSSA 优化器使用时间加权的总风险：`total_risk_weighted = Σ [R_i × T_t × S_t]`
- 结果：夜间部署更多资源，雨季增加覆盖
- 实现：`protection_pipeline.py` 脚本

**方案 C：分时段优化（最灵活）**
- 为不同时段分别运行 DSSA
- 输出多套部署方案
- 用户根据实际需求选择或融合

### 7.4 方案 B：时间感知的资源分配

#### 启用时间感知模式

在输入 JSON 中添加配置：

```json
{
  "time": {
    "hour_of_day": 23,
    "season": "RAINY"
  },
  "use_temporal_factors": true,
  "dssa_config": {
    "population_size": 50,
    "max_iterations": 100,
    "use_time_aware_fitness": true
  }
}
```

#### 运行优化

```bash
python protection_pipeline.py input-night-rainy.json output-night.json
```

输出中会显示：
```
[TIME-AWARE] 时间感知模式：资源分配将反映时间因子的影响
```

#### 算法对比

| 方面 | 标准模式 | 时间感知模式 |
|------|---------|-----------|
| **Fitness 公式** | `total_benefit / total_risk` | `total_benefit / (total_risk × T_t × S_t)` |
| **时间因子** | 不考虑 | 考虑（夜间 ×1.3，雨季 ×1.2） |
| **资源分配** | 相对风险排序 | 时间加权风险排序 |
| **应用场景** | 基准部署 | 时间感知部署 |

#### 测试结果

使用 input-night-rainy-quick.json（hour=23, season=RAINY）：

| 指标 | 标准模式 | 时间感知模式 | 变化 |
|------|---------|-----------|------|
| Best Fitness | 0.350513 | 0.223743 | -36.17% |
| Total Benefit | 175.427024 | 175.427024 | 0% |
| Total Risk | 125.050000 | 80.273000 | -35.77% |

**解释**：
- Fitness 下降是因为时间加权的总风险增加（×1.56）
- Total Benefit 保持不变（保护效果相同）
- 时间因子正确应用到了优化目标中

### 7.5 实际应用建议

1. **日常监测**：使用方案 A（可视化对比）
   - 生成两种风险热力图
   - 识别时间维度的风险差异
   - 用于决策支持

2. **自动部署**：使用方案 B（时间感知优化）
   - 启用 `use_time_aware_fitness: true`
   - DSSA 自动调整资源分配
   - 夜间部署更多资源

3. **多时段规划**：使用方案 C（分时段优化）
   - 为 day 和 night 分别运行 DSSA
   - 输出两套部署方案
   - 根据实际需求选择或融合

4. **资源调度**：根据季节和昼夜周期动态调整部署方案
   - 白天：按标准模式部署
   - 夜间：启用时间感知模式，增加资源
   - 雨季：增加时间因子权重

***

## 八、可视化脚本

文件：`hexdynamic/visualize_output.py`

> 推荐通过 `run.py` 调用（自动在优化后出图）。直接使用 `visualize_output.py` 适合已有 output JSON、只需重新生成图片的场景。

### 用法

```bash
# 基本用法（无物种图）
python visualize_output.py output.json --out_dir ./figures

# 完整用法（同时提供 input，生成物种密度图）
python visualize_output.py output.json --input pipeline_input.json --out_dir ./figures

# 加前缀区分多次运行
python visualize_output.py output.json --input pipeline_input.json --out_dir ./figures --prefix run1
```

### 输出图片

| 文件                           | 内容                                                 | 颜色条    |
| ---------------------------- | -------------------------------------------------- | ------ |
| `risk_heatmap.png`           | 部署前风险热力图，右侧显示 Total PB / Average PB / Best Fitness | YlOrRd |
| `risk_comparison.png`        | 部署前后风险对比（左：原始风险，右：剩余风险），同色阶便于直接对比                  | YlOrRd |
| `protection_heatmap.png`     | 保护收益热力图，叠加摄像头/无人机/营地/巡逻员/围栏图标                      | RdYlGn |
| `terrain_map.png`            | 地形颜色地图                                             | —      |
| `terrain_deployment_map.png` | 地形底图 + 部署资源图标叠加                                    | —      |
| `species_map.png`            | 地形底图 + 物种密度图标（大小正比于密度，形状区分物种）                      | —      |

有颜色条的图采用三列布局：地图 | 颜色条 | 图例+指标，三者互不遮挡。`risk_comparison.png` 采用双图并排布局，左右共用同一颜色条，颜色越深（红色）表示风险越高，对比左右可直观看出哪些高风险区域被有效覆盖。

### 资源图标说明

| 图标    | 颜色 | 资源                |
| ----- | -- | ----------------- |
| ■ 方形  | 蓝色 | Camera（摄像头）       |
| ▲ 三角  | 橙色 | Drone（无人机）        |
| ◆ 菱形  | 紫色 | Camp（营地）          |
| ● 圆形  | 绿色 | Patrol（巡逻员）       |
| ⬠ 五边形 | 红色 | Fence（围栏，仅显示在边缘格） |

