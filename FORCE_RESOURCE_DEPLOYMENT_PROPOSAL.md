# 强制资源部署方案

## 需求

DSSA优化只需要根据资源上限进行约束，不需要考虑资源收益的边际递减问题，以确保所有类型资源都可以部署。

## 当前问题

### 当前行为
- 优化器基于适应度函数 `fitness = total_benefit / total_risk` 来优化
- 由于边际收益递减，某些资源可能不被部署
- 权重低的资源（如摄像头 wc=0.2）更容易被忽略

### 示例
```
配置：摄像头4个，无人机2个
结果：摄像头0个，无人机2个
原因：无人机权重更高，边际收益更大
```

## 解决方案

### 方案1：修改初始化策略（推荐）

**核心思想**：在初始化时强制部署所有资源，然后在优化过程中只调整位置，不减少数量。

#### 实现步骤

1. **修改 `_initialize_solution()`**
   - 强制部署所有配置的资源
   - 确保每种资源都达到上限

2. **修改 `repair_solution()`**
   - 如果某种资源数量低于上限，补充到上限
   - 只允许调整位置，不允许减少数量

3. **修改约束验证**
   - 添加最小资源数量约束
   - 确保每种资源都被使用

#### 代码实现

```python
def _initialize_solution(self) -> DeploymentSolution:
    """初始化解，强制部署所有资源到上限"""
    cameras = {}
    camps = {}
    drones = {}
    rangers = {}

    grid_ids_shuffled = self.grid_ids.copy()
    random.shuffle(grid_ids_shuffled)

    # 1. 强制部署所有摄像头
    max_cam = self.constraints.get('max_cameras_per_grid', 3)
    cam_deployed = 0
    cam_target = self.constraints['total_cameras']
    
    for grid_id in grid_ids_shuffled:
        if cam_deployed >= cam_target:
            break
        if self.coverage_model.deployment_matrix['camera'][grid_id] == 1:
            count = min(max_cam, cam_target - cam_deployed)
            cameras[grid_id] = count
            cam_deployed += count
    
    # 如果还没部署完，继续尝试
    if cam_deployed < cam_target:
        for grid_id in grid_ids_shuffled:
            if cam_deployed >= cam_target:
                break
            if grid_id not in cameras and self.coverage_model.deployment_matrix['camera'][grid_id] == 1:
                count = min(max_cam, cam_target - cam_deployed)
                cameras[grid_id] = count
                cam_deployed += count

    # 2. 强制部署所有无人机
    max_drone = self.constraints.get('max_drones_per_grid', 1)
    drone_deployed = 0
    drone_target = self.constraints['total_drones']
    
    for grid_id in grid_ids_shuffled:
        if drone_deployed >= drone_target:
            break
        if self.coverage_model.deployment_matrix['drone'][grid_id] == 1:
            count = min(max_drone, drone_target - drone_deployed)
            drones[grid_id] = count
            drone_deployed += count

    # 3. 强制部署所有营地
    max_camp = self.constraints.get('max_camps_per_grid', 1)
    camp_deployed = 0
    camp_target = self.constraints['total_camps']
    
    for grid_id in grid_ids_shuffled:
        if camp_deployed >= camp_target:
            break
        if self.coverage_model.deployment_matrix['camp'][grid_id] == 1:
            count = min(max_camp, camp_target - camp_deployed)
            camps[grid_id] = count
            camp_deployed += count

    # 4. 强制部署所有巡逻人员
    ranger_target = self.constraints['total_patrol']
    ranger_deployed = 0
    
    for grid_id in grid_ids_shuffled:
        if ranger_deployed >= ranger_target:
            break
        # 避免与营地冲突
        if grid_id not in camps and self.coverage_model.deployment_matrix['patrol'][grid_id] == 1:
            rangers[grid_id] = 1
            ranger_deployed += 1

    solution = DeploymentSolution(
        cameras=cameras,
        camps=camps,
        drones=drones,
        rangers=rangers,
        fences=dict(self.fixed_fences)
    )
    
    return solution


def repair_solution(self, solution: DeploymentSolution, constraints: Dict[str, any]) -> DeploymentSolution:
    """修复解，确保所有资源都被部署到上限"""
    
    # 1. 修复超出上限的资源
    # ... 现有逻辑 ...
    
    # 2. 补充未达到上限的资源
    
    # 补充摄像头
    cam_deployed = sum(solution.cameras.values())
    cam_target = constraints['total_cameras']
    if cam_deployed < cam_target:
        available_grids = [gid for gid in self.grid_ids 
                          if self.coverage_model.deployment_matrix['camera'][gid] == 1]
        random.shuffle(available_grids)
        
        for grid_id in available_grids:
            if cam_deployed >= cam_target:
                break
            current = solution.cameras.get(grid_id, 0)
            max_cam = constraints.get('max_cameras_per_grid', 3)
            can_add = min(max_cam - current, cam_target - cam_deployed)
            if can_add > 0:
                solution.cameras[grid_id] = current + can_add
                cam_deployed += can_add
    
    # 补充无人机
    drone_deployed = sum(solution.drones.values())
    drone_target = constraints['total_drones']
    if drone_deployed < drone_target:
        available_grids = [gid for gid in self.grid_ids 
                          if self.coverage_model.deployment_matrix['drone'][gid] == 1
                          and gid not in solution.drones]
        random.shuffle(available_grids)
        
        for grid_id in available_grids:
            if drone_deployed >= drone_target:
                break
            solution.drones[grid_id] = 1
            drone_deployed += 1
    
    # 补充营地
    camp_deployed = sum(solution.camps.values())
    camp_target = constraints['total_camps']
    if camp_deployed < camp_target:
        available_grids = [gid for gid in self.grid_ids 
                          if self.coverage_model.deployment_matrix['camp'][gid] == 1
                          and gid not in solution.camps]
        random.shuffle(available_grids)
        
        for grid_id in available_grids:
            if camp_deployed >= camp_target:
                break
            solution.camps[grid_id] = 1
            camp_deployed += 1
    
    # 补充巡逻人员
    ranger_deployed = sum(solution.rangers.values())
    ranger_target = constraints['total_patrol']
    if ranger_deployed < ranger_target:
        available_grids = [gid for gid in self.grid_ids 
                          if self.coverage_model.deployment_matrix['patrol'][gid] == 1
                          and gid not in solution.camps  # 避免与营地冲突
                          and gid not in solution.rangers]
        random.shuffle(available_grids)
        
        for grid_id in available_grids:
            if ranger_deployed >= ranger_target:
                break
            solution.rangers[grid_id] = 1
            ranger_deployed += 1
    
    return solution
```

### 方案2：添加资源利用率惩罚

**核心思想**：在适应度函数中添加资源利用率惩罚，鼓励使用所有资源。

#### 实现

```python
def evaluate_fitness(self, solution: DeploymentSolution) -> float:
    is_valid, violations = self.coverage_model.validate_solution(solution, self.constraints)
    if not is_valid:
        return -len(violations) * 1000
    
    # 计算保护收益
    total_benefit = self.coverage_model.calculate_total_benefit(solution)
    
    # 计算资源利用率
    cam_util = sum(solution.cameras.values()) / max(1, self.constraints['total_cameras'])
    drone_util = sum(solution.drones.values()) / max(1, self.constraints['total_drones'])
    camp_util = sum(solution.camps.values()) / max(1, self.constraints['total_camps'])
    ranger_util = sum(solution.rangers.values()) / max(1, self.constraints['total_patrol'])
    
    # 平均利用率
    avg_util = (cam_util + drone_util + camp_util + ranger_util) / 4
    
    # 利用率惩罚：如果利用率低于100%，减少适应度
    utilization_penalty = (1 - avg_util) * 0.5  # 惩罚系数可调
    
    # 最终适应度 = 保护收益 - 利用率惩罚
    fitness = total_benefit - utilization_penalty
    
    return fitness
```

### 方案3：修改约束验证（最简单）

**核心思想**：将资源上限约束改为资源等于约束，强制使用所有资源。

#### 实现

```python
def validate_solution(self, solution: DeploymentSolution, constraints: Dict[str, any]) -> Tuple[bool, List[str]]:
    violations = []

    # 摄像头必须等于上限
    total_cameras = sum(solution.cameras.values())
    if total_cameras != constraints['total_cameras']:
        violations.append(f"Camera count must equal {constraints['total_cameras']}, got {total_cameras}")

    # 无人机必须等于上限
    total_drones = sum(solution.drones.values())
    if total_drones != constraints['total_drones']:
        violations.append(f"Drone count must equal {constraints['total_drones']}, got {total_drones}")

    # 营地必须等于上限
    total_camps = sum(solution.camps.values())
    if total_camps != constraints['total_camps']:
        violations.append(f"Camp count must equal {constraints['total_camps']}, got {total_camps}")

    # 巡逻人员必须等于上限
    total_rangers = sum(solution.rangers.values())
    if total_rangers != constraints['total_patrol']:
        violations.append(f"Ranger count must equal {constraints['total_patrol']}, got {total_rangers}")

    # ... 其他约束 ...

    return len(violations) == 0, violations
```

## 推荐方案

**推荐使用方案1（修改初始化和修复策略）**，原因：

1. ✅ 最直接有效
2. ✅ 不改变适应度函数的数学意义
3. ✅ 保持优化器的灵活性
4. ✅ 只调整资源位置，不改变数量

## 实现细节

### 关键点

1. **初始化阶段**
   - 强制部署所有资源到上限
   - 随机分配位置

2. **优化阶段**
   - 只调整资源位置
   - 不减少资源数量
   - 通过 `repair_solution` 确保数量不变

3. **修复阶段**
   - 如果数量不足，补充到上限
   - 如果数量超出，削减到上限
   - 保持数量等于上限

### 配置选项

可以添加一个配置选项来控制行为：

```json
{
  "dssa_config": {
    "force_full_deployment": true,  // 新增：强制部署所有资源
    "population_size": 50,
    "max_iterations": 100
  }
}
```

如果 `force_full_deployment = true`，使用新的初始化和修复逻辑。
如果 `force_full_deployment = false`，使用原来的逻辑（允许部分部署）。

## 优缺点对比

### 优点
- ✅ 确保所有资源都被使用
- ✅ 不受权重配置影响
- ✅ 不受边际收益递减影响
- ✅ 简单直接

### 缺点
- ❌ 可能不是最优解（如果某些资源确实不需要）
- ❌ 失去了优化器自动选择资源的能力
- ❌ 可能导致资源浪费

## 使用场景

### 适合使用强制部署
- 资源已经购买，必须全部使用
- 需要展示所有资源的效果
- 资源配置是固定的，不能调整

### 不适合使用强制部署
- 资源配置是预算上限，可以少用
- 需要找到最优的资源组合
- 希望优化器自动选择资源

## 测试验证

```python
# 测试脚本
def test_force_deployment():
    # 配置
    constraints = {
        'total_cameras': 10,
        'total_drones': 5,
        'total_camps': 3,
        'total_patrol': 20
    }
    
    # 运行优化
    optimizer = DSSAOptimizer(coverage_model, constraints, config)
    best_solution, best_fitness, fitness_history = optimizer.optimize()
    
    # 验证
    assert sum(best_solution.cameras.values()) == 10, "摄像头未全部部署"
    assert sum(best_solution.drones.values()) == 5, "无人机未全部部署"
    assert sum(best_solution.camps.values()) == 3, "营地未全部部署"
    assert sum(best_solution.rangers.values()) == 20, "巡逻人员未全部部署"
    
    print("✅ 所有资源都已部署到上限")
```

## 相关文档

- `WHY_ZERO_UTILIZATION.md` - 解释了为什么会出现利用率为0%
- `RESOURCE_UTILIZATION_GUIDE.md` - 资源利用率诊断指南
- 本方案提供了强制部署的解决方案

## 总结

推荐使用**方案1：修改初始化和修复策略**，通过以下步骤实现：

1. 修改 `_initialize_solution()` - 强制部署所有资源
2. 修改 `repair_solution()` - 补充未达到上限的资源
3. 添加配置选项 `force_full_deployment` - 控制行为
4. 创建测试脚本验证

这样可以确保所有类型的资源都被部署，同时保持代码的灵活性和向后兼容性。
