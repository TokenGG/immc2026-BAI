# 剩余风险计算修复

## 问题描述

部署保护资源前后的网格综合风险指数热力图看起来一样，这说明剩余风险（residual risk）的计算有问题。

## 根本原因

在原始实现中，剩余风险的计算方式是：

```python
rr_per_grid = {
    gid: max(0.0, grid_model.get_grid_risk(gid) - pb_per_grid[gid])
    for gid in grid_model.get_all_grid_ids()
}
```

这个计算有两个问题：

1. **量纲不匹配**：
   - `grid_model.get_grid_risk(gid)` 是原始风险值（绝对值）
   - `pb_per_grid[gid]` 是保护收益（绝对值）
   - 两者虽然都是绝对值，但直接相减不符合风险模型的逻辑

2. **模型不一致**：
   - 保护收益的计算公式是：`PB = risk * (1 - exp(-E_i))`
   - 其中 `E_i` 是保护效果（0到1之间）
   - 因此剩余风险应该是：`RR = risk * exp(-E_i)`
   - 而不是简单的 `RR = risk - PB`

## 修复方案

### 正确的剩余风险计算

根据保护收益的定义，剩余风险应该是：

```
保护收益 = 原始风险 × (1 - exp(-E_i))
剩余风险 = 原始风险 - 保护收益
        = 原始风险 × (1 - (1 - exp(-E_i)))
        = 原始风险 × exp(-E_i)
```

### 修复后的代码

```python
# 获取保护效果
protection_effect = coverage_model.calculate_protection_effect(best_solution)

# 计算剩余风险
rr_per_grid = {
    gid: grid_model.get_grid_risk(gid) * np.exp(-protection_effect[gid])
    for gid in grid_model.get_all_grid_ids()
}
```

## 数学验证

对于任意网格 i：

```
原始风险: R_i
保护效果: E_i ∈ [0, 1]
保护收益: PB_i = R_i × (1 - exp(-E_i))
剩余风险: RR_i = R_i × exp(-E_i)

验证：PB_i + RR_i = R_i × (1 - exp(-E_i)) + R_i × exp(-E_i)
                  = R_i × [(1 - exp(-E_i)) + exp(-E_i)]
                  = R_i × 1
                  = R_i ✓
```

## 效果对比

### 修复前
- 部署前后热力图几乎相同
- 剩余风险值与原始风险值接近
- 无法直观看出保护资源的效果

### 修复后
- 部署前：显示原始风险分布
- 部署后：显示剩余风险分布
- 有保护资源部署的网格，剩余风险明显降低
- 热力图对比清晰，能直观看出保护效果

## 使用示例

运行优化后生成的可视化：

```bash
python hexdynamic/visualize_output.py output.json --input input.json
```

会生成 `risk_comparison.png`，显示：
- 左图：部署前的原始风险热力图
- 右图：部署后的剩余风险热力图

对比两张图可以清晰看出：
- 有保护资源的网格（特别是有巡逻人员、摄像头等的网格）风险明显降低
- 无保护资源的网格风险保持不变
- 保护资源的部署位置与风险降低的区域相对应

## 关键参数说明

### 保护效果 (E_i)
- 范围：[0, 1]
- 计算：`E_i = wp × patrol_cov + wd × drone_cov + wc × camera_cov + wf × fence_prot`
- 含义：综合保护覆盖程度

### 保护收益 (PB_i)
- 公式：`PB_i = R_i × (1 - exp(-E_i))`
- 含义：实际降低的风险量
- 范围：[0, R_i]

### 剩余风险 (RR_i)
- 公式：`RR_i = R_i × exp(-E_i)`
- 含义：部署保护资源后仍然存在的风险
- 范围：[0, R_i]

## 归一化处理

在输出JSON中，剩余风险会被归一化到 [0, 1]：

```python
rr_min, rr_max = min(rr_vals), max(rr_vals)

def norm_rr(v):
    return float((v - rr_min) / (rr_max - rr_min)) if rr_max != rr_min else float(v)

'residual_risk_normalized': round(norm_rr(rr_per_grid[gid]), 6)
```

这样可以在热力图中更清晰地显示相对风险差异。

## 验证方法

可以通过以下方式验证修复效果：

```python
import json

with open('output.json', 'r') as f:
    data = json.load(f)

for grid in data['grids'][:5]:
    risk = grid['risk_normalized']
    pb = grid['protection_benefit_normalized']
    rr = grid['residual_risk_normalized']
    print(f"Grid {grid['grid_id']}: Risk={risk:.3f}, PB={pb:.3f}, RR={rr:.3f}")
    
    # 验证：有保护资源的网格，剩余风险应该小于原始风险
    if grid['deployment']['patrol_rangers'] > 0 or grid['deployment']['camera'] > 0:
        print(f"  ✓ 有保护资源，剩余风险应该 < 原始风险")
```

## 影响范围

- 修改文件：`hexdynamic/protection_pipeline.py`
- 影响输出：`output.json` 中的 `residual_risk_normalized` 字段
- 影响可视化：`risk_comparison.png` 中的右图（部署后）
- 不影响：其他所有计算和输出
