# Risk Analysis 批量处理优化方案

## 需求理解

### 当前功能
- `risk_analysis.py` 处理单个输入 JSON 文件
- 生成 3 个输出文件：
  1. `risk_heatmap.png` - 归一化风险热力图
  2. `raw_risk_heatmap.png` - 原始风险热力图
  3. `attributes_map.png` - 地理属性图
  4. `risk_results.json` - 风险结果数据

### 新需求

1. **批量处理**
   - 从输入目录读取多个 input JSON 文件
   - 对每个文件生成独立的可视化图片和 JSON 结果

2. **对比图生成**
   - 将所有 `risk_heatmap` 合成一张对比图片
   - 将所有 `raw_risk_heatmap` 合成一张对比图片

3. **统一颜色条**
   - 对比图的颜色条最大值使用所有场景的最大值
   - 确保不同场景之间可以直观对比

## 方案设计

### 1. 新增批量处理脚本

创建 `risk_analysis_batch.py`：

```python
"""
Risk Analysis Batch Processing Script

批量处理多个输入 JSON 文件，生成：
1. 每个场景的独立可视化
2. 所有场景的对比图（risk_heatmap + raw_risk_heatmap）

用法：
    python risk_analysis_batch.py --input-dir ./data --output-dir ./results
"""

import os
import glob
import json
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple

# 复用 risk_analysis.py 的核心功能
from risk_analysis import compute_risk, load_input


def process_single_file(input_path: str, output_dir: str):
    """处理单个文件，返回风险数据用于对比"""
    # 生成独立输出
    # 返回 (normalized_risks, raw_risks, grids, hex_size)
    ...

def generate_comparison_plots(results: List[dict], output_dir: str):
    """生成对比图"""
    # 1. 计算所有场景的最大风险值
    # 2. 使用统一颜色条绘制所有场景
    # 3. 生成 risk_heatmap_comparison.png
    # 4. 生成 raw_risk_heatmap_comparison.png
    ...

def main():
    # 1. 扫描输入目录
    # 2. 对每个文件调用 process_single_file
    # 3. 收集所有结果
    # 4. 生成对比图
    ...
```

### 2. 核心功能

#### 2.1 批量处理流程

```
输入目录 (input_dir)
├── scenario_1.json
├── scenario_2.json
└── scenario_3.json

↓ 批量处理

输出目录 (output_dir)
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
│   ├── risk_heatmap.png
│   ├── raw_risk_heatmap.png
│   ├── attributes_map.png
│   └── risk_results.json
├── risk_heatmap_comparison.png      # 所有场景对比
└── raw_risk_heatmap_comparison.png  # 所有场景对比
```

#### 2.2 对比图设计

**布局**：
- 使用 `matplotlib` 的 `subplots` 创建网格布局
- 每个场景占一个子图
- 右侧统一颜色条

**颜色条统一**：
```python
# 计算所有场景的最大值
all_normalized_max = max([max(r['normalized_risks'].values()) for r in results])
all_raw_max = max([max(r['raw_risks'].values()) for r in results])

# 使用统一的最大值
norm = Normalize(vmin=0, vmax=all_normalized_max)  # 或 all_raw_max
```

**示例布局**（3 个场景）：
```
┌─────────────────────────────────────────────┐
│  [Scenario 1]  [Scenario 2]  [Scenario 3]  │
│                                              │
│  risk_heatmap   risk_heatmap   risk_heatmap │
│                                              │
│                    [Colorbar]                │
│                    0.0 - Max                │
└─────────────────────────────────────────────┘
```

### 3. 实现细节

#### 3.1 文件扫描

```python
def scan_input_files(input_dir: str) -> List[str]:
    """扫描输入目录，返回所有 JSON 文件路径"""
    patterns = ['*.json', '*.JSON']
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(input_dir, pattern)))
    return sorted(files)
```

#### 3.2 单文件处理

```python
def process_single_file(input_path: str, output_dir: str) -> dict:
    """
    处理单个文件
    
    Returns:
        {
            'name': 'scenario_1',
            'normalized_risks': {grid_id: risk, ...},
            'raw_risks': {grid_id: risk, ...},
            'grids': [...],
            'hex_size': 62.0
        }
    """
    # 1. 加载数据
    data = load_input(input_path)
    
    # 2. 计算风险
    normalized_risks, raw_risks = compute_risk(data)
    
    # 3. 生成独立可视化
    scenario_name = os.path.splitext(os.path.basename(input_path))[0]
    scenario_dir = os.path.join(output_dir, scenario_name)
    os.makedirs(scenario_dir, exist_ok=True)
    
    # 调用原有的绘图函数
    plot_risk_heatmap(data['grids'], normalized_risks, hex_size,
                      save_path=os.path.join(scenario_dir, 'risk_heatmap.png'))
    plot_raw_risk_heatmap(data['grids'], raw_risks, hex_size,
                          save_path=os.path.join(scenario_dir, 'raw_risk_heatmap.png'))
    plot_attributes_map(data['grids'], hex_size,
                        save_path=os.path.join(scenario_dir, 'attributes_map.png'))
    
    # 4. 保存 JSON
    save_risk_results(...)
    
    # 5. 返回数据用于对比
    return {
        'name': scenario_name,
        'normalized_risks': normalized_risks,
        'raw_risks': raw_risks,
        'grids': data['grids'],
        'hex_size': hex_size
    }
```

#### 3.3 对比图生成

```python
def generate_comparison_plots(results: List[dict], output_dir: str):
    """生成对比图"""
    
    # 1. 计算统一颜色条范围
    all_normalized_max = max([max(r['normalized_risks'].values()) for r in results])
    all_raw_max = max([max(r['raw_risks'].values()) for r in results])
    
    # 2. 生成 normalized risk 对比图
    generate_single_comparison(
        results, 
        'normalized_risks',
        all_normalized_max,
        os.path.join(output_dir, 'risk_heatmap_comparison.png'),
        'Normalized Risk Comparison'
    )
    
    # 3. 生成 raw risk 对比图
    generate_single_comparison(
        results,
        'raw_risks',
        all_raw_max,
        os.path.join(output_dir, 'raw_risk_heatmap_comparison.png'),
        'Raw Risk Comparison'
    )


def generate_single_comparison(results: List[dict], risk_key: str, 
                                max_val: float, save_path: str, title: str):
    """生成单个对比图"""
    
    n_scenarios = len(results)
    
    # 计算布局
    if n_scenarios <= 3:
        n_cols = n_scenarios
        n_rows = 1
    else:
        n_cols = 3
        n_rows = (n_scenarios + 2) // 3
    
    # 创建图形
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(6 * n_cols, 6 * n_rows))
    if n_scenarios == 1:
        axes = [axes]
    else:
        axes = axes.flatten()
    
    # 统一颜色条
    cmap = matplotlib.colormaps.get_cmap("YlOrRd")
    norm = Normalize(vmin=0, vmax=max_val)
    
    # 绘制每个场景
    for i, result in enumerate(results):
        ax = axes[i]
        grids = result['grids']
        risks = result[risk_key]
        hex_size = result['hex_size']
        
        # 绘制六边形
        for g in grids:
            gid = g['grid_id']
            risk = risks.get(gid, 0.0)
            cx, cy = grid_center(g["q"], g["r"], hex_size)
            draw_hex(ax, cx, cy, hex_size * 0.97, facecolor=cmap(norm(risk)))
        
        # 设置
        setup_map_ax(ax, grids, hex_size)
        ax.set_title(result['name'], fontsize=11, fontweight='bold')
        ax.axis('off')
    
    # 隐藏多余的子图
    for i in range(n_scenarios, len(axes)):
        axes[i].axis('off')
    
    # 添加统一颜色条
    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=axes[:n_scenarios], shrink=0.8, aspect=30)
    cbar.set_label('Risk Value', fontsize=10)
    
    # 标题
    fig.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    # 保存
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
```

### 4. 使用方法

#### 基本用法

```bash
# 批量处理
python risk_analysis_batch.py --input-dir ./data --output-dir ./results

# 指定文件模式
python risk_analysis_batch.py --input-dir ./data --output-dir ./results --pattern "scenario_*.json"

# 指定 hex_size
python risk_analysis_batch.py --input-dir ./data --output-dir ./results --hex-size 62.0
```

#### 输出示例

```
处理进度：
[1/3] Processing: scenario_1.json
  ✓ Normalized: min=0.1234  max=0.8765  mean=0.4567
  ✓ Raw       : min=0.1234  max=1.2345  mean=0.6789
  ✓ Saved to: ./results/scenario_1/

[2/3] Processing: scenario_2.json
  ✓ Normalized: min=0.2345  max=0.9876  mean=0.5678
  ✓ Raw       : min=0.2345  max=1.3456  mean=0.7890
  ✓ Saved to: ./results/scenario_2/

[3/3] Processing: scenario_3.json
  ✓ Normalized: min=0.3456  max=0.8765  mean=0.6789
  ✓ Raw       : min=0.3456  max=1.4567  mean=0.8901
  ✓ Saved to: ./results/scenario_3/

生成对比图：
  ✓ Normalized risk max: 0.9876
  ✓ Raw risk max: 1.4567
  ✓ Saved: risk_heatmap_comparison.png
  ✓ Saved: raw_risk_heatmap_comparison.png

完成！
```

### 5. 优势

- ✅ **批量处理**：自动处理多个文件
- ✅ **独立输出**：每个场景有独立的可视化
- ✅ **统一对比**：颜色条统一，便于对比
- ✅ **灵活布局**：自动适应不同数量的场景
- ✅ **进度显示**：清晰的处理进度

### 6. 扩展功能（可选）

#### 6.1 并行处理

```python
from multiprocessing import Pool

def process_parallel(files: List[str], output_dir: str, n_workers: int = 4):
    """并行处理多个文件"""
    with Pool(n_workers) as pool:
        results = pool.starmap(process_single_file, 
                              [(f, output_dir) for f in files])
    return results
```

#### 6.2 统计汇总

```python
def generate_summary_report(results: List[dict], output_dir: str):
    """生成统计汇总报告"""
    summary = {
        'scenarios': [
            {
                'name': r['name'],
                'normalized_risk_mean': np.mean(list(r['normalized_risks'].values())),
                'raw_risk_mean': np.mean(list(r['raw_risks'].values())),
                ...
            }
            for r in results
        ]
    }
    
    with open(os.path.join(output_dir, 'summary_report.json'), 'w') as f:
        json.dump(summary, f, indent=2)
```

## 实现步骤

1. **创建 `risk_analysis_batch.py`**
   - 实现批量处理逻辑
   - 实现对比图生成

2. **修改 `risk_analysis.py`**
   - 提取核心函数，便于复用
   - 添加返回值支持

3. **测试**
   - 创建测试数据
   - 验证批量处理
   - 验证对比图生成

4. **文档**
   - 使用说明
   - 示例输出

## 总结

这个方案通过：
1. **批量处理** - 自动处理多个输入文件
2. **独立输出** - 每个场景有独立的可视化
3. **统一对比** - 颜色条统一，便于对比
4. **灵活布局** - 自动适应不同数量的场景

能够高效地处理多个风险分析场景，并生成直观的对比图。
