# 敏感性分析功能 - 文档索引

## 📖 文档导航

### 🚀 快速开始（5 分钟）

**[SENSITIVITY_ANALYSIS_README.md](SENSITIVITY_ANALYSIS_README.md)**
- 功能概述
- 快速开始
- 常见用法
- 应用场景

**[SENSITIVITY_ANALYSIS_QUICK_START.md](SENSITIVITY_ANALYSIS_QUICK_START.md)**
- 快速开始指南
- 常见用法
- 结果解读
- 常见问题

### 📚 详细了解（15 分钟）

**[SENSITIVITY_ANALYSIS_IMPLEMENTATION.md](SENSITIVITY_ANALYSIS_IMPLEMENTATION.md)**
- 核心实现细节
- 使用方法
- 输出格式
- 性能考虑
- 应用场景

**[SENSITIVITY_ANALYSIS_SUMMARY.md](SENSITIVITY_ANALYSIS_SUMMARY.md)**
- 实现完成情况
- 核心功能
- 使用方法
- 应用场景
- 质量保证

### 🎯 完整了解（30 分钟）

**[SENSITIVITY_ANALYSIS_PROPOSAL.md](SENSITIVITY_ANALYSIS_PROPOSAL.md)**
- 方案设计
- 核心思路
- 关键设计点
- 实现步骤
- 优势和应用场景

**[IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)**
- 实现状态
- 实现内容
- 使用方法
- 输出示例
- 文件清单

**[SENSITIVITY_ANALYSIS_CHECKLIST.md](SENSITIVITY_ANALYSIS_CHECKLIST.md)**
- 实现清单
- 统计数据
- 功能完整性
- 质量保证
- 验收标准

## 🎯 按用途选择文档

### 我想快速了解这个功能

👉 **[SENSITIVITY_ANALYSIS_README.md](SENSITIVITY_ANALYSIS_README.md)**

包含：
- 功能概述
- 快速开始
- 常见用法

### 我想立即开始使用

👉 **[SENSITIVITY_ANALYSIS_QUICK_START.md](SENSITIVITY_ANALYSIS_QUICK_START.md)**

包含：
- 快速开始
- 常见用法
- 结果解读
- 常见问题

### 我想了解实现细节

👉 **[SENSITIVITY_ANALYSIS_IMPLEMENTATION.md](SENSITIVITY_ANALYSIS_IMPLEMENTATION.md)**

包含：
- 核心实现
- 使用方法
- 输出格式
- 性能考虑

### 我想了解完整的设计方案

👉 **[SENSITIVITY_ANALYSIS_PROPOSAL.md](SENSITIVITY_ANALYSIS_PROPOSAL.md)**

包含：
- 方案设计
- 核心思路
- 关键设计点
- 实现步骤

### 我想验证实现的完整性

👉 **[SENSITIVITY_ANALYSIS_CHECKLIST.md](SENSITIVITY_ANALYSIS_CHECKLIST.md)**

包含：
- 实现清单
- 统计数据
- 功能完整性
- 质量保证

## 📁 代码文件

### 新增文件

| 文件 | 说明 | 行数 |
|------|------|------|
| `sensitivity_analysis.py` | 敏感性分析主脚本 | 335 |
| `test_sensitivity_analysis.py` | 测试脚本 | 298 |

### 修改文件

| 文件 | 修改内容 | 行数 |
|------|---------|------|
| `hexdynamic/dssa_optimizer.py` | 添加冻结资源支持 | +50 |
| `hexdynamic/protection_pipeline.py` | 添加 --freeze-resources 参数 | +20 |

## 🚀 快速命令

### 分析 Patrol 敏感性

```bash
python sensitivity_analysis.py --input pipeline_input.json --resource patrol --range 0 50 5
```

### 分析所有资源

```bash
python sensitivity_analysis.py --input pipeline_input.json --resource all
```

### 使用向量化模式

```bash
python sensitivity_analysis.py --input pipeline_input.json --resource patrol --vectorized
```

### 直接冻结资源

```bash
python hexdynamic/protection_pipeline.py input.json output.json --freeze-resources camera,drone,camp,fence
```

### 运行测试

```bash
python test_sensitivity_analysis.py
```

## 📊 功能清单

### 核心功能

- ✅ 资源冻结机制
- ✅ 敏感性分析脚本
- ✅ 多维度可视化
- ✅ 自动化分析流程

### 支持的资源

- ✅ patrol（巡逻人员）
- ✅ camera（摄像头）
- ✅ drone（无人机）
- ✅ camp（营地）
- ✅ fence（围栏）
- ✅ all（所有资源）

### 输出

- ✅ JSON 结果文件
- ✅ PNG 敏感性曲线图
- ✅ 数据表格汇总

## 🎓 学习路径

### 初级（了解基础）

1. 阅读 [SENSITIVITY_ANALYSIS_README.md](SENSITIVITY_ANALYSIS_README.md)
2. 查看快速开始部分
3. 运行一个简单的分析

### 中级（掌握使用）

1. 阅读 [SENSITIVITY_ANALYSIS_QUICK_START.md](SENSITIVITY_ANALYSIS_QUICK_START.md)
2. 尝试不同的资源分析
3. 学习结果解读

### 高级（深入理解）

1. 阅读 [SENSITIVITY_ANALYSIS_IMPLEMENTATION.md](SENSITIVITY_ANALYSIS_IMPLEMENTATION.md)
2. 阅读 [SENSITIVITY_ANALYSIS_PROPOSAL.md](SENSITIVITY_ANALYSIS_PROPOSAL.md)
3. 查看源代码实现

## 💡 常见问题

### Q: 从哪里开始？

**A**: 从 [SENSITIVITY_ANALYSIS_README.md](SENSITIVITY_ANALYSIS_README.md) 开始，5 分钟了解基础。

### Q: 如何快速上手？

**A**: 按照 [SENSITIVITY_ANALYSIS_QUICK_START.md](SENSITIVITY_ANALYSIS_QUICK_START.md) 中的示例运行。

### Q: 如何理解结果？

**A**: 查看 [SENSITIVITY_ANALYSIS_QUICK_START.md](SENSITIVITY_ANALYSIS_QUICK_START.md) 中的"理解输出"部分。

### Q: 如何优化性能？

**A**: 查看 [SENSITIVITY_ANALYSIS_IMPLEMENTATION.md](SENSITIVITY_ANALYSIS_IMPLEMENTATION.md) 中的"性能考虑"部分。

### Q: 如何应用到实际项目？

**A**: 查看 [SENSITIVITY_ANALYSIS_IMPLEMENTATION.md](SENSITIVITY_ANALYSIS_IMPLEMENTATION.md) 中的"应用场景"部分。

## 📈 文档大小

| 文档 | 大小 |
|------|------|
| SENSITIVITY_ANALYSIS_README.md | ~8 KB |
| SENSITIVITY_ANALYSIS_QUICK_START.md | ~6 KB |
| SENSITIVITY_ANALYSIS_IMPLEMENTATION.md | ~11 KB |
| SENSITIVITY_ANALYSIS_PROPOSAL.md | ~11 KB |
| SENSITIVITY_ANALYSIS_SUMMARY.md | ~8 KB |
| IMPLEMENTATION_COMPLETE.md | ~9 KB |
| SENSITIVITY_ANALYSIS_CHECKLIST.md | ~7 KB |
| **总计** | **~60 KB** |

## 🔗 相关文档

### 项目文档

- [FINAL_IMPROVEMENTS_CHECKLIST.md](FINAL_IMPROVEMENTS_CHECKLIST.md) - 所有改进清单
- [FORCE_DEPLOYMENT_IMPLEMENTATION.md](FORCE_DEPLOYMENT_IMPLEMENTATION.md) - 强制部署功能
- [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) - 项目快速开始

### 技术文档

- [hexdynamic/dssa_optimizer.py](hexdynamic/dssa_optimizer.py) - 优化器源代码
- [hexdynamic/protection_pipeline.py](hexdynamic/protection_pipeline.py) - 管道源代码
- [sensitivity_analysis.py](sensitivity_analysis.py) - 敏感性分析源代码

## ✅ 质量指标

- ✅ 代码无错误
- ✅ 文档完整
- ✅ 测试通过
- ✅ 向后兼容
- ✅ 生产就绪

## 🎉 总结

敏感性分析功能已完整实现，包括：

- ✅ 完整的代码实现
- ✅ 详细的文档
- ✅ 全面的测试
- ✅ 生产就绪

**立即开始使用吧！** 👉 [SENSITIVITY_ANALYSIS_README.md](SENSITIVITY_ANALYSIS_README.md)

---

**最后更新**：2026-04-16  
**状态**：✅ 完成  
**质量**：生产就绪
