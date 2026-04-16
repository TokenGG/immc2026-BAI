# 物种分布约束修复

## 问题描述
在marker导出pipeline JSON时，犀牛(rhino)和大象(elephant)可能会被分配到水坑(WaterHole)和盐沼(SaltMarsh)网格中，这在生态学上是不合理的。

## 修复内容

### marker/image-viewer.html

修改了`assignSpeciesDensities`函数中筛选犀牛和大象候选网格的逻辑。

#### 修复前的问题
```javascript
// 错误：使用 wetMarkerIds（包含水坑和盐沼）作为候选网格
const candidateIndices = grids.map((g, idx) => ({ g, idx }))
    .filter(({ g, idx }) => {
        if (isRoadProhibited(idx)) return false;
        if (!speciesNames.every(sp => g.species_densities[sp] === 0.0)) return false;
        const mid = outputIdxToMarkerId.get(idx);
        return mid && wetMarkerIds.has(mid);  // ❌ 错误：包含了水坑和盐沼
    }).map(({ idx }) => idx);
```

#### 修复后的逻辑
```javascript
// 收集水坑和盐沼的marker IDs（犀牛和大象不能分布在这些网格）
const waterholeSaltmarshIds = new Set();
gridCoordinates.forEach(mg => {
    const color = gridColorMap.get(mg.gridId);
    // #3b82f6 = 水坑(蓝色), #06b6d4 = 盐沼(青色)
    if (color === '#3b82f6' || color === '#06b6d4') {
        waterholeSaltmarshIds.add(mg.gridId);
    }
});

const candidateIndices = grids.map((g, idx) => ({ g, idx }))
    .filter(({ g, idx }) => {
        if (isRoadProhibited(idx)) return false;
        if (!speciesNames.every(sp => g.species_densities[sp] === 0.0)) return false;
        const mid = outputIdxToMarkerId.get(idx);
        // ✅ 正确：排除水坑和盐沼网格
        if (mid && waterholeSaltmarshIds.has(mid)) return false;
        return mid !== undefined;
    }).map(({ idx }) => idx);
```

## 颜色标签映射

| colorTag | 颜色值 | 地形类型 | 犀牛/大象分布 |
|----------|--------|----------|---------------|
| 1 | `#4ade80` | DenseGrass (森林密集区) | ✅ 可以分布 |
| 2 | `#ef4444` | SparseGrass (森林稀疏区) | ✅ 可以分布 |
| 3 | `#3b82f6` | WaterHole (水坑) | ❌ 不能分布 |
| 4 | `#eab308` | SparseGrass (干坑) | ✅ 可以分布 |
| 5 | `#a855f7` | Road (主路) | ❌ 不能分布 |
| 6 | `#f97316` | Road (小路) | ❌ 不能分布 |
| 7 | `#06b6d4` | SaltMarsh (盐沼) | ❌ 不能分布 |

## 物种分布规则

### 犀牛(Rhino)和大象(Elephant)
- ✅ 可以分布在：SparseGrass、DenseGrass
- ❌ 不能分布在：WaterHole、SaltMarsh、Road及其邻居网格
- 分布特点：成片出现，各自有密集区（2个大象区，3个犀牛区）
- 密度范围：0.4 ~ 0.6（随机）

### 鸟类(Bird)
- ✅ 主要分布在：SaltMarsh及其邻居网格
- 密度范围：0.5 ~ 1.0（盐沼区域）
- 其他区域密度极低或为0

## 验证方法

导出pipeline JSON后，可以通过以下方式验证：

```python
import json

with open('pipeline_input.json', 'r') as f:
    data = json.load(f)

# 检查水坑和盐沼网格
for grid in data['grids']:
    terrain = grid['terrain_type']
    rhino = grid['species_densities'].get('rhino', 0)
    elephant = grid['species_densities'].get('elephant', 0)
    
    if terrain in ['WaterHole', 'SaltMarsh']:
        if rhino > 0 or elephant > 0:
            print(f"❌ 错误：网格 {grid['grid_id']} ({terrain}) 有犀牛或大象分布！")
            print(f"   犀牛密度: {rhino}, 大象密度: {elephant}")
        else:
            print(f"✅ 正确：网格 {grid['grid_id']} ({terrain}) 犀牛和大象密度为0")
```

## 使用说明

1. 在marker工具中标记网格颜色
2. 点击"🚀 导出Pipeline JSON"按钮
3. 配置参数并确认导出
4. 导出的JSON会自动应用物种分布约束

修复后，犀牛和大象将不会出现在水坑和盐沼网格中，符合生态学规律。
