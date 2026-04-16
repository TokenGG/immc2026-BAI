# Patrol和Camp部署约束修复

## 问题描述
在原始实现中，patrol（巡逻人员）可能会被部署在与camp（营地）相同的grid中，这在实际场景中是不合理的。

## 修复内容

### 1. coverage_model.py

#### validate_solution方法
修复了约束检查逻辑，确保正确检测patrol和camp在同一grid的情况：

```python
# 修复前（有bug）
for camp_id, rangers in solution.rangers.items():
    if camp_id in solution.camps:
        violations.append(f"Patrol and camp cannot share the same grid: {camp_id}")

# 修复后（正确）
for grid_id in self.grid_ids:
    has_camp = solution.camps.get(grid_id, 0) > 0
    has_ranger = solution.rangers.get(grid_id, 0) > 0
    if has_camp and has_ranger:
        violations.append(f"Patrol and camp cannot share the same grid: {grid_id}")
```

#### repair_solution方法
改进了解决方案修复逻辑，确保在修复过程中移除冲突的patrol部署：

```python
# 修复后：确保patrol和camp不能在同一grid
for grid_id in list(repaired.rangers.keys()):
    if grid_id in repaired.camps:
        repaired.rangers.pop(grid_id, None)
```

### 2. dssa_optimizer.py

#### _initialize_solution方法
修复了初始化逻辑，确保在生成初始解时不会将patrol部署在已有camp的grid：

```python
# 修复后：检查grid_id不在rangers字典中
if (grid_id not in cameras and
        grid_id not in drones and
        grid_id not in camps and
        grid_id not in rangers and  # 新增检查
        self.coverage_model.deployment_matrix['patrol'][grid_id] == 1):
    rangers[grid_id] = rangers.get(grid_id, 0) + 1
    remaining_rangers -= 1
```

### 3. coverage_model_vectorized.py

由于`VectorizedCoverageModel`继承自`CoverageModel`，它会自动继承修复后的`validate_solution`和`repair_solution`方法，无需额外修改。

## 测试验证

创建了测试脚本`test_patrol_camp_constraint.py`来验证修复：

1. **测试1**: patrol和camp在同一grid → 验证失败（预期）
2. **测试2**: patrol和camp在不同grid → 验证成功（预期）
3. **测试3**: repair_solution正确移除冲突的patrol部署

所有测试均通过。

## 影响范围

- 优化器在生成初始解时会避免patrol和camp的冲突
- 解决方案验证会正确检测这种冲突
- 解决方案修复会自动移除冲突的patrol部署（优先保留camp）
- 不影响其他资源（camera、drone、fence）的部署逻辑

## 使用说明

修复后的代码会自动确保patrol和camp不会部署在同一个grid中。在运行优化时：

```bash
python hexdynamic/protection_pipeline.py input.json output.json
```

或使用向量化版本：

```bash
python hexdynamic/protection_pipeline.py input.json output.json --vectorized
```

优化器会自动遵守这个约束，无需额外配置。
