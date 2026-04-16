# 快速开始指南

## 基本命令

### 1. 运行优化
```bash
# 标准模式
python hexdynamic/protection_pipeline.py input.json output.json

# 向量化模式（推荐用于大规模地图）
python hexdynamic/protection_pipeline.py input.json output.json --vectorized
```

### 2. 可视化结果
```bash
python hexdynamic/visualize_output.py output.json --input input.json
```

### 3. 诊断围栏部署
```bash
python diagnose_fence_deployment.py output.json --input input.json
```

### 4. 诊断资源利用率
```bash
python diagnose_resource_utilization.py input.json output.json
```

## 输出解读

### 优化过程
```
Iter    5/100  fitness=0.856234  benefit=45.123456  [ESCAPE=8]  iter=456.7ms  avg=500.1ms
```

| 字段 | 含义 |
|------|------|
| `Iter 5/100` | 第5次迭代，共100次 |
| `fitness=0.856234` | 适应度（保护收益/总风险） |
| `benefit=45.123456` | 总保护收益（实际降低的风险） |
| `[ESCAPE=8]` | 警戒更新次数（探索） |
| `iter=456.7ms` | 本次迭代耗时 |
| `avg=500.1ms` | 平均迭代耗时 |

### 资源部署总结
```
📷 摄像头: 10 / 10 (100.0%)
🚁 无人机: 3 / 3 (100.0%)
⛺ 营地: 5 / 5 (100.0%)
👮 巡逻人员: 20 / 20 (100.0%)
🚧 围栏: 5 段
```

## 常见问题

### Q1：如何加快优化？
```bash
# 使用向量化模式
python hexdynamic/protection_pipeline.py input.json output.json --vectorized

# 或减少迭代次数（在input.json中修改）
"dssa_config": {
    "max_iterations": 50  # 从100改为50
}
```

### Q2：如何找到更好的解？
```bash
# 增加迭代次数
"dssa_config": {
    "max_iterations": 200  # 增加迭代
}

# 或增加种群大小
"dssa_config": {
    "population_size": 100  # 增加种群
}

# 或减少ST值（增加探索）
"dssa_config": {
    "ST": 0.6  # 从0.8改为0.6
}
```

### Q3：为什么热力图没有变化？
```bash
# 运行诊断脚本
python diagnose_fence_deployment.py output.json --input input.json

# 检查输出JSON中的residual_risk_normalized字段
# 应该与risk_normalized不同
```

### Q4：为什么某些资源利用率为0%？
```bash
# 运行资源利用率诊断工具
python diagnose_resource_utilization.py input.json output.json

# 可能的原因：
# 1. 资源未配置（约束为0）- 现在会显示"N/A"
# 2. 权重太低（调整wp, wd, wc, wf）
# 3. 覆盖半径太小（调整radius参数）
# 4. 其他资源已提供足够保护

# 解决方案：增加该资源的权重或覆盖半径
```

### Q5：警戒更新频率太高/太低？
```bash
# 调整ST参数
"dssa_config": {
    "ST": 0.7  # 减少ST增加探索
    # 或
    "ST": 0.9  # 增加ST减少探索
}
```

## 参数调优

### 小规模地图（< 500网格）
```json
{
    "dssa_config": {
        "population_size": 30,
        "max_iterations": 50,
        "ST": 0.8
    }
}
```

### 中规模地图（500-2000网格）
```json
{
    "dssa_config": {
        "population_size": 50,
        "max_iterations": 100,
        "ST": 0.8
    }
}
```

### 大规模地图（> 2000网格）
```json
{
    "dssa_config": {
        "population_size": 50,
        "max_iterations": 100,
        "ST": 0.8
    }
}
```
使用 `--vectorized` 模式运行。

## 工作流程

### 1. 准备输入数据
```bash
# 使用marker工具标记网格
# 或使用generate_map.py生成随机地图
python hexdynamic/generate_map.py -m 10 -n 12 -o input.json
```

### 2. 运行优化
```bash
python hexdynamic/protection_pipeline.py input.json output.json --vectorized
```

### 3. 查看结果
```bash
python hexdynamic/visualize_output.py output.json --input input.json
```

### 4. 诊断问题（如需要）
```bash
python diagnose_fence_deployment.py output.json --input input.json
```

## 性能指标

### 优化质量
- **Fitness**: 越高越好（0-1）
- **Benefit**: 越高越好（0-总风险）
- **Escape频率**: 20%左右最佳

### 运行时间
- 小规模地图：< 1秒
- 中规模地图：1-10秒
- 大规模地图：10-60秒（使用向量化模式）

## 文件说明

### 输入文件
- `input.json` - 地图和约束配置

### 输出文件
- `output.json` - 优化结果
- `risk_heatmap.png` - 风险热力图
- `risk_comparison.png` - 部署前后对比
- `protection_heatmap.png` - 保护收益热力图
- `terrain_map.png` - 地形地图
- `terrain_deployment_map.png` - 地形+部署地图
- `species_map.png` - 物种分布地图

## 约束说明

### Patrol和Camp
- ✅ Patrol和Camp不能在同一网格
- ✅ 每个Camp最多有max_rangers_per_camp个Patrol

### 物种分布
- ✅ 犀牛和大象不分布在水坑和盐沼
- ✅ 鸟类集中在盐沼

### 资源部署
- ✅ 摄像头：最多max_cameras_per_grid个/网格
- ✅ 无人机：最多max_drones_per_grid个/网格
- ✅ 营地：最多max_camps_per_grid个/网格
- ✅ 围栏：总长度不超过total_fence_length

## 调试技巧

### 1. 检查约束是否满足
```bash
# 查看输出JSON中的deployment字段
# 确保patrol和camp不在同一网格
```

### 2. 检查优化过程
```bash
# 查看迭代输出中的fitness和benefit
# 应该逐渐增加
```

### 3. 检查可视化
```bash
# 查看热力图
# 部署前后应该有明显差异
```

## 常用命令速查

```bash
# 生成随机地图
python hexdynamic/generate_map.py -m 10 -n 12 -o input.json

# 运行优化（标准模式）
python hexdynamic/protection_pipeline.py input.json output.json

# 运行优化（向量化模式）
python hexdynamic/protection_pipeline.py input.json output.json --vectorized

# 可视化结果
python hexdynamic/visualize_output.py output.json --input input.json

# 诊断围栏
python diagnose_fence_deployment.py output.json --input input.json

# 诊断资源利用率
python diagnose_resource_utilization.py input.json output.json

# 测试约束
python test_patrol_camp_constraint.py

# 测试警戒更新
python test_escape_update_logging.py
```

## 获取帮助

```bash
# 查看帮助信息
python hexdynamic/protection_pipeline.py --help
python hexdynamic/visualize_output.py --help
python diagnose_fence_deployment.py --help
```

## 相关文档

- `FINAL_IMPROVEMENTS_CHECKLIST.md` - 完整改进清单
- `DSSA_IMPROVEMENTS_SUMMARY.md` - DSSA改进总结
- `FENCE_VISUALIZATION_SUMMARY.md` - 围栏可视化指南
- `DSSA_ESCAPE_UPDATE_LOGGING.md` - 警戒更新日志详解
- `RESOURCE_UTILIZATION_GUIDE.md` - 资源利用率诊断指南
