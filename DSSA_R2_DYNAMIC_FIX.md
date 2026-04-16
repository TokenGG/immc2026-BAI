# DSSA优化器R2参数动态化改进

## 问题描述

在原始的DSSA优化器实现中，R2参数被设置为固定值（默认0.5），这与标准的麻雀搜索算法（Sparrow Search Algorithm, SSA）不符。

根据SSA算法原理，R2应该在每次迭代中为每个个体随机生成，用于控制探索（exploration）和开发（exploitation）的平衡。

## 算法原理

在SSA算法中，R2参数的作用：

```
for t in range(max_iter):
    for i in range(population_size):
        R2 = random.uniform(0, 1)  # 每次随机生成
        if R2 < ST:
            # 正常更新（开发 / exploitation）
            update_normal(i)
        else:
            # 警戒更新（探索 / exploration）
            update_escape(i)
```

- **R2 < ST**: 进行正常更新，利用当前已知的好解进行局部搜索（开发）
- **R2 >= ST**: 进行警戒更新，使用更大的随机扰动进行全局搜索（探索）

## 修复内容

### 1. dssa_optimizer.py - _update_producers方法

#### 修复前
```python
def _update_producers(self, iteration: int):
    num_producers = int(self.config.population_size * self.config.producer_ratio)
    producers = self.population[:num_producers]

    for i, solution in enumerate(producers):
        if i == 0:
            # 总是使用相同的更新策略
            current_vector = self._solution_to_vector(solution)
            best_vector = self._solution_to_vector(self.best_solution)
            new_vector = current_vector + np.random.uniform(0, 1, current_vector.shape) * (best_vector - current_vector)
        else:
            current_vector = self._solution_to_vector(solution)
            new_vector = current_vector + np.random.uniform(-1, 1, current_vector.shape)
```

#### 修复后
```python
def _update_producers(self, iteration: int):
    num_producers = int(self.config.population_size * self.config.producer_ratio)
    producers = self.population[:num_producers]

    for i, solution in enumerate(producers):
        # R2 在每次迭代中随机生成 [0, 1]
        R2 = random.uniform(0, 1)
        
        if R2 < self.config.ST:
            # 正常更新（开发 / exploitation）
            if i == 0:
                current_vector = self._solution_to_vector(solution)
                best_vector = self._solution_to_vector(self.best_solution)
                new_vector = current_vector + np.random.uniform(0, 1, current_vector.shape) * (best_vector - current_vector)
            else:
                current_vector = self._solution_to_vector(solution)
                new_vector = current_vector + np.random.uniform(-1, 1, current_vector.shape)
        else:
            # 警戒更新（探索 / exploration）
            current_vector = self._solution_to_vector(solution)
            # 使用更大的随机扰动进行探索
            new_vector = current_vector + np.random.uniform(-2, 2, current_vector.shape)
```

### 2. dssa_optimizer.py - _update_followers方法

#### 修复前
```python
def _update_followers(self):
    # ...
    for i, solution in enumerate(followers):
        if i > self.config.population_size / 2:
            # 总是使用相同的更新策略
            current_vector = self._solution_to_vector(solution)
            best_vector = self._solution_to_vector(self.best_solution)
            new_vector = np.abs(best_vector - current_vector) * np.random.uniform(0, 1, current_vector.shape)
        else:
            # ...
```

#### 修复后
```python
def _update_followers(self):
    # ...
    for i, solution in enumerate(followers):
        # R2 在每次迭代中随机生成 [0, 1]
        R2 = random.uniform(0, 1)
        
        if R2 < self.config.ST:
            # 正常更新（开发 / exploitation）
            if i > self.config.population_size / 2:
                current_vector = self._solution_to_vector(solution)
                best_vector = self._solution_to_vector(self.best_solution)
                new_vector = np.abs(best_vector - current_vector) * np.random.uniform(0, 1, current_vector.shape)
            else:
                # ...
        else:
            # 警戒更新（探索 / exploration）
            current_vector = self._solution_to_vector(solution)
            # 使用更大的随机扰动进行探索
            new_vector = current_vector + np.random.uniform(-2, 2, current_vector.shape)
```

### 3. DSSAConfig类更新

```python
@dataclass
class DSSAConfig:
    population_size: int = 50
    max_iterations: int = 100
    producer_ratio: float = 0.2
    scout_ratio: float = 0.2
    ST: float = 0.8
    R2: float = 0.5  # 已弃用：R2现在在每次迭代中随机生成，此参数保留用于向后兼容
```

## 改进效果

### 1. 更好的探索-开发平衡

- **动态切换**：每次迭代随机决定是进行局部搜索还是全局搜索
- **避免早熟收敛**：增加了跳出局部最优的机会
- **提高多样性**：种群保持更好的多样性

### 2. 符合标准算法

- 实现与标准SSA算法一致
- 理论基础更加扎实
- 便于与其他实现对比

### 3. 参数控制

- **ST参数**：控制探索和开发的比例
  - ST = 0.8：80%的时间进行开发，20%进行探索
  - ST越大，开发比例越高
  - ST越小，探索比例越高

## 使用说明

修改后的代码无需改变使用方式，只需正常运行：

```bash
python hexdynamic/protection_pipeline.py input.json output.json
```

如果需要调整探索-开发平衡，可以在输入JSON中修改ST参数：

```json
{
  "dssa_config": {
    "population_size": 50,
    "max_iterations": 100,
    "ST": 0.8,
    "R2": 0.5
  }
}
```

注意：R2参数现在会被忽略，保留只是为了向后兼容。

## 警戒更新策略

在警戒更新（R2 >= ST）时，使用更大的随机扰动：

```python
# 正常更新：扰动范围 [-1, 1]
new_vector = current_vector + np.random.uniform(-1, 1, current_vector.shape)

# 警戒更新：扰动范围 [-2, 2]（更大的探索范围）
new_vector = current_vector + np.random.uniform(-2, 2, current_vector.shape)
```

这样可以在需要探索时跳得更远，增加发现更好解的可能性。

## 向后兼容性

- 配置文件中的R2参数仍然可以设置，但不会影响算法行为
- 所有现有的输入JSON文件无需修改即可使用
- API接口保持不变

## 测试验证

可以通过观察优化过程中的fitness变化来验证改进效果：

```python
python hexdynamic/protection_pipeline.py input.json output.json
```

预期效果：
- 优化过程中会有更多的fitness波动（探索）
- 最终收敛到更好的解
- 避免过早陷入局部最优
