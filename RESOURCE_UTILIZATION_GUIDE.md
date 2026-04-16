# 资源利用率问题诊断指南

## 问题描述

在运行优化后，可能会看到某些资源的利用率为0.0%，例如：

```
📊 部署统计:
   摄像头利用率: 0.0%
   无人机利用率: 100.0%
   营地利用率: 0.0%
   巡逻人员利用率: 100.0%
```

## 可能的原因

### 1. 资源未配置（约束为0）

如果输入JSON中某个资源的总数设置为0：

```json
"constraints": {
    "total_cameras": 0,  // 未配置摄像头
    "total_camps": 0     // 未配置营地
}
```

**现在的显示**：会显示 `N/A (未配置XX资源)` 而不是 `0.0%`

### 2. 优化器认为部署该资源不划算

DSSA优化器会根据以下因素决定是否部署资源：

- **权重配置** (`wp`, `wd`, `wc`, `wf`)
- **覆盖半径** (`patrol_radius`, `drone_radius`, `camera_radius`)
- **资源成本效益比**

如果某个资源的权重太低或覆盖半径太小，优化器可能选择不部署。

### 3. 其他资源已提供足够保护

如果无人机和巡逻人员已经覆盖了所有高风险区域，优化器可能认为不需要额外部署摄像头。

### 4. 营地的特殊情况

营地本身不直接提供保护收益，它只是巡逻人员的部署点。在当前实现中，巡逻人员可以不依赖营地独立部署，所以营地利用率为0%是正常的。

## 诊断步骤

### 步骤1：检查输入配置

查看输入JSON文件中的约束配置：

```bash
# 查看约束部分
grep -A 10 "constraints" input.json
```

确认资源总数不为0。

### 步骤2：使用诊断工具

运行资源利用率诊断工具：

```bash
python diagnose_resource_utilization.py input.json output.json
```

这个工具会：
- 显示约束配置
- 显示实际部署情况
- 分析每种资源的利用率
- 提供具体的改进建议

### 步骤3：检查权重配置

查看 `coverage_params` 中的权重配置：

```json
"coverage_params": {
    "wp": 0.3,  // 巡逻人员权重
    "wd": 0.3,  // 无人机权重
    "wc": 0.2,  // 摄像头权重
    "wf": 0.2   // 围栏权重
}
```

权重总和应该为1.0，权重越高的资源越容易被部署。

### 步骤4：检查覆盖半径

```json
"coverage_params": {
    "patrol_radius": 3.0,
    "drone_radius": 6.0,
    "camera_radius": 2.0
}
```

覆盖半径越大，资源的保护效果越好，越容易被部署。

## 解决方案

### 方案1：调整权重配置

如果摄像头利用率为0%，可以增加摄像头权重：

```json
"coverage_params": {
    "wp": 0.25,  // 减少
    "wd": 0.25,  // 减少
    "wc": 0.30,  // 增加（从0.2增加到0.3）
    "wf": 0.20
}
```

### 方案2：调整覆盖半径

增加摄像头的覆盖半径：

```json
"coverage_params": {
    "camera_radius": 4.0  // 从2.0增加到4.0
}
```

### 方案3：减少其他资源数量

如果无人机已经提供了足够保护，可以减少无人机数量：

```json
"constraints": {
    "total_drones": 1,  // 从2减少到1
    "total_cameras": 4
}
```

这样优化器会更倾向于使用摄像头。

### 方案4：营地的特殊处理

如果需要强制使用营地，有两个选择：

**选择A：修改约束逻辑**（需要修改代码）

在 `coverage_model.py` 中添加约束：巡逻人员必须部署在有营地的网格附近。

**选择B：接受当前行为**

营地利用率为0%可能是正常的优化结果，因为：
- 巡逻人员可以独立部署
- 不需要营地也能提供保护
- 这样更灵活

## 权重配置建议

### 平衡配置（推荐）

```json
"coverage_params": {
    "wp": 0.3,  // 巡逻人员：中等权重
    "wd": 0.3,  // 无人机：中等权重
    "wc": 0.2,  // 摄像头：较低权重
    "wf": 0.2   // 围栏：较低权重
}
```

### 重视移动资源

```json
"coverage_params": {
    "wp": 0.35,  // 巡逻人员：高权重
    "wd": 0.35,  // 无人机：高权重
    "wc": 0.15,  // 摄像头：低权重
    "wf": 0.15   // 围栏：低权重
}
```

### 重视固定资源

```json
"coverage_params": {
    "wp": 0.25,  // 巡逻人员：较低权重
    "wd": 0.25,  // 无人机：较低权重
    "wc": 0.25,  // 摄像头：中等权重
    "wf": 0.25   // 围栏：中等权重
}
```

### 重视摄像头

```json
"coverage_params": {
    "wp": 0.25,  // 巡逻人员
    "wd": 0.25,  // 无人机
    "wc": 0.35,  // 摄像头：高权重
    "wf": 0.15   // 围栏
}
```

## 覆盖半径建议

### 小规模地图（< 500网格）

```json
"coverage_params": {
    "patrol_radius": 2.0,
    "drone_radius": 4.0,
    "camera_radius": 1.5
}
```

### 中规模地图（500-2000网格）

```json
"coverage_params": {
    "patrol_radius": 3.0,
    "drone_radius": 6.0,
    "camera_radius": 2.0
}
```

### 大规模地图（> 2000网格）

```json
"coverage_params": {
    "patrol_radius": 5.0,
    "drone_radius": 8.0,
    "camera_radius": 3.0
}
```

## 实验和调优

### 步骤1：基准测试

使用默认配置运行一次：

```bash
python hexdynamic/protection_pipeline.py input.json output_baseline.json
```

记录利用率和总保护收益。

### 步骤2：调整权重

修改权重配置，再次运行：

```bash
python hexdynamic/protection_pipeline.py input_modified.json output_test.json
```

### 步骤3：比较结果

```bash
python diagnose_resource_utilization.py input.json output_baseline.json
python diagnose_resource_utilization.py input_modified.json output_test.json
```

比较：
- 资源利用率
- 总保护收益 (total_protection_benefit)
- 最佳适应度 (best_fitness)

### 步骤4：选择最佳配置

选择利用率高且保护收益大的配置。

## 常见问题

### Q1：为什么增加权重后利用率还是0%？

**A**：可能需要同时调整覆盖半径。权重只影响资源的相对重要性，但如果覆盖半径太小，资源的绝对收益仍然很低。

### Q2：如何强制使用所有配置的资源？

**A**：可以设置非常高的权重，但这可能导致次优解。更好的方法是调整资源数量，只配置真正需要的资源。

### Q3：营地利用率为0%是bug吗？

**A**：不是bug。在当前实现中，营地不直接提供保护收益，所以优化器可能选择不使用。这是正常的优化结果。

### Q4：如何平衡不同资源的使用？

**A**：
1. 确保权重总和为1.0
2. 根据资源的实际效果调整权重
3. 多次实验找到最佳配置
4. 使用诊断工具分析结果

## 工具清单

### 1. 资源利用率诊断工具

```bash
python diagnose_resource_utilization.py input.json output.json
```

功能：
- 显示约束和部署情况
- 分析利用率
- 提供改进建议

### 2. 利用率显示测试

```bash
python test_utilization_display.py
```

功能：
- 测试不同场景下的显示
- 验证显示逻辑

### 3. 可视化工具

```bash
python hexdynamic/visualize_output.py output.json --input input.json
```

功能：
- 生成热力图
- 显示资源部署位置

## 改进历史

### v1.0 - 初始实现
- 使用 `max(1, total)` 避免除以零
- 当资源未配置时显示 `0.0%`

### v1.1 - 改进显示（当前版本）
- 当资源未配置时显示 `N/A (未配置XX资源)`
- 更清晰地区分"未配置"和"未使用"
- 添加诊断工具

## 相关文档

- `DEPLOYMENT_SUMMARY_FEATURE.md` - 资源部署总结功能
- `DSSA_IMPROVEMENTS_SUMMARY.md` - DSSA改进总结
- `QUICK_START_GUIDE.md` - 快速开始指南
- `FINAL_IMPROVEMENTS_CHECKLIST.md` - 完整改进清单

## 总结

资源利用率为0%可能是：
1. ✅ 正常的优化结果（资源不划算）
2. ✅ 配置问题（权重或半径设置不当）
3. ✅ 约束问题（资源总数为0）

使用诊断工具可以快速定位问题并获得改进建议。
