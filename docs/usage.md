# 使用说明

本文档说明如何使用以下四个工具完成从地图标注到保护资源部署优化的完整流程。

---

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
  ▼
[protection_pipeline.py] 计算风险指数 → DSSA 优化部署方案
  │  输出 pipeline_output.json
  ▼
[visualize_output.py] 生成可视化图片
```

---

## 一、Marker 标注工具

文件：`marker/image-viewer.html`，直接用浏览器打开，无需安装依赖。

### 基本操作

**加载图片**：将地图图片拖入页面，或点击上传区域选择文件。

**网格化**：点击 `⬡ 网格化` 按钮叠加六边形网格，拖动 `半径` 滑块调整网格大小。

**标注地形**：调色板中每种颜色对应一种地形类型：

| 颜色 | 地形类型 | terrain_type |
|------|----------|--------------|
| 🟢 绿色 | 森林密集区 | DenseGrass |
| 🔴 红色 | 森林稀疏区 | SparseGrass |
| 🔵 蓝色 | 水坑 | WaterHole |
| 🟡 黄色 | 干坑 | SaltMarsh |
| 🟣 紫色 | 主路 | Road |
| 🟠 橙色 | 小路 | Road |
| 🩵 青色 | 盐沼 | SaltMarsh |

- 单击色块选色，再单击格子填色；框选可批量填色
- 再次单击已填色格子取消填色
- `Ctrl/Cmd + 点击` 多选后点色块统一填色
- `📥 导入JSON` / `📤 导出JSON`：导入或导出网格标注数据
- `📥 导出SVG`：导出带图例的矢量网格图

### 导出 Pipeline 输入 JSON

完成标注后点击 `🚀 导出Pipeline JSON`，在弹出的配置面板中填写参数后点击 `📥 生成并下载`，下载 `pipeline_input.json`。

配置面板参数说明见第三节（与 `generate_map.py` 参数一致）。

> 未标注颜色的格子默认视为 SparseGrass。主路/小路格子坐标自动提取为 `road_locations`，水坑格子自动提取为 `water_locations`。

---

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

- 道路随机选南北或东西方向贯穿，每隔 2~3 格随机横向偏移 ±1，不是直线
- 犀牛/大象密度只在 SparseGrass 格子生成，其他地形为 0
- 鸟类密度在 SaltMarsh 为 0.6~1.0，其他地形为 0~0.1

### 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `-m` | 10 | 地图行数 |
| `-n` | 12 | 地图列数 |
| `-o` | pipeline_input.json | 输出文件路径 |
| `--seed` | None | 随机种子 |
| `--hour_of_day` | 12 | 时间（0-23） |
| `--season` | DRY | 季节：DRY / RAINY |
| `--use_temporal_factors` | False | 启用昼夜/季节时间因子 |
| `--total_patrol` | 20 | 巡逻人员总数 |
| `--total_camps` | 5 | 营地总数 |
| `--max_rangers_per_camp` | 5 | 每营地最大人员 |
| `--total_cameras` | 10 | 摄像头总数 |
| `--total_drones` | 3 | 无人机总数 |
| `--total_fence_length` | 50 | 围栏总段数上限 |
| `--patrol_radius` | 5.0 | 巡逻覆盖衰减半径 |
| `--drone_radius` | 8.0 | 无人机覆盖半径 |
| `--camera_radius` | 3.0 | 摄像头覆盖半径 |
| `--fence_protection` | 0.5 | 每段围栏保护系数 |
| `--wp/wd/wc/wf` | 0.3/0.3/0.2/0.2 | 巡逻/无人机/摄像头/围栏权重 |
| `--population_size` | 50 | DSSA 种群大小 |
| `--max_iterations` | 100 | DSSA 最大迭代次数 |

---

## 三、Protection Pipeline 脚本

文件：`hexdynamic/protection_pipeline.py`

### 依赖安装

```bash
pip install -r hexdynamic/requirements.txt
pip install -r riskIndex/requirements.txt
```

### 用法

```bash
cd hexdynamic
python protection_pipeline.py <input.json> <output.json>
```

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
    "total_cameras": 10, "total_drones": 3, "total_fence_length": 50
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

| terrain_type | 巡逻 | 营地 | 无人机 | 摄像头 | 围栏 |
|---|:---:|:---:|:---:|:---:|:---:|
| SparseGrass | ✗ | ✗ | ✓ | ✓ | ✓（仅边缘） |
| DenseGrass  | ✗ | ✗ | ✓ | ✗ | ✓（仅边缘） |
| WaterHole   | ✗ | ✗ | ✓ | ✗ | ✗ |
| SaltMarsh   | ✗ | ✗ | ✓ | ✗ | ✗ |
| Road        | ✓ | ✓ | ✓ | ✓ | ✓（仅边缘） |

围栏只能部署在地图边缘格子，且该格子地形必须允许（非 WaterHole/SaltMarsh）。

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
      "deployment": {
        "patrol_rangers": 0, "camp": 0, "drone": 1, "camera": 1
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

| 指标 | 公式 | 含义 |
|------|------|------|
| `risk_normalized` | riskIndex min-max 归一化 | 综合威胁程度，越高越需要保护 |
| `protection_benefit_raw` | `R_i × (1 - e^(-E_i))` | 该格实际获得的保护收益 |
| `protection_benefit_normalized` | min-max 归一化 | 相对保护收益，便于可视化 |
| `Total Protection Benefit` | `Σ protection_benefit_raw` | 全局保护收益总量 |
| `Average Protection Benefit` | `Total / N` | 每格平均保护收益 |
| `Best Fitness` | `Total / Σ R_i` | 风险加权归一化保护效率，优化目标 |

综合保护效果 `E_i = wp × patrol_cov + wd × drone_cov + wc × camera_cov + wf × fence_prot`，各覆盖度基于指数衰减函数计算。

---

## 四、可视化脚本

文件：`hexdynamic/visualize_output.py`

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

| 文件 | 内容 | 颜色条 |
|------|------|--------|
| `risk_heatmap.png` | 风险热力图，右侧显示 Total PB / Average PB / Best Fitness | YlOrRd |
| `protection_heatmap.png` | 保护收益热力图，叠加摄像头/无人机/营地/巡逻员/围栏图标 | RdYlGn |
| `terrain_map.png` | 地形颜色地图 | — |
| `terrain_deployment_map.png` | 地形底图 + 部署资源图标叠加 | — |
| `species_map.png` | 地形底图 + 物种密度图标（大小正比于密度，形状区分物种） | — |

有颜色条的图采用三列布局：地图 | 颜色条 | 图例+指标，三者互不遮挡。

### 资源图标说明

| 图标 | 颜色 | 资源 |
|------|------|------|
| ■ 方形 | 蓝色 | Camera（摄像头） |
| ▲ 三角 | 橙色 | Drone（无人机） |
| ◆ 菱形 | 紫色 | Camp（营地） |
| ● 圆形 | 绿色 | Patrol（巡逻员） |
| ⬠ 五边形 | 红色 | Fence（围栏，仅显示在边缘格） |
