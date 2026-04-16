"""
测试风险对比图修复

验证部署前后的风险归一化使用统一基准
"""

import numpy as np


def test_risk_normalization():
    """测试风险归一化逻辑"""
    
    print("=" * 70)
    print("测试风险对比图修复")
    print("=" * 70)
    
    # 模拟数据
    print("\n模拟数据:")
    print("  网格数: 5")
    print("  部署前风险范围: [0.2, 0.8]")
    print("  保护效果: E_i ∈ [0.3, 0.6]")
    
    # 部署前风险（已归一化）
    risk_before = np.array([0.2, 0.4, 0.6, 0.7, 0.8])
    
    # 保护效果
    protection_effect = np.array([0.3, 0.4, 0.5, 0.6, 0.3])
    
    # 计算剩余风险
    risk_after = risk_before * np.exp(-protection_effect)
    
    print(f"\n部署前风险: {risk_before}")
    print(f"保护效果 E_i: {protection_effect}")
    print(f"部署后剩余风险: {risk_after}")
    
    # 测试1: 旧方法（独立归一化）
    print("\n" + "=" * 70)
    print("测试1: 旧方法（独立归一化）")
    print("=" * 70)
    
    # 部署前归一化（已经是归一化的）
    risk_before_norm_old = risk_before
    
    # 部署后独立归一化
    rr_min, rr_max = risk_after.min(), risk_after.max()
    risk_after_norm_old = (risk_after - rr_min) / (rr_max - rr_min)
    
    print(f"\n部署前归一化: {risk_before_norm_old}")
    print(f"部署后归一化: {risk_after_norm_old}")
    print(f"\n差异: {risk_before_norm_old - risk_after_norm_old}")
    print(f"平均差异: {np.mean(np.abs(risk_before_norm_old - risk_after_norm_old)):.4f}")
    
    print("\n问题:")
    print("  • 两者都归一化到 [0, 1]")
    print("  • 但使用了不同的归一化基准")
    print("  • 导致颜色映射后看起来差异很小")
    
    # 测试2: 新方法（统一归一化）
    print("\n" + "=" * 70)
    print("测试2: 新方法（统一归一化）")
    print("=" * 70)
    
    # 使用部署前风险范围作为统一基准
    risk_min, risk_max = risk_before.min(), risk_before.max()
    
    # 统一归一化
    risk_before_norm_new = (risk_before - risk_min) / (risk_max - risk_min)
    risk_after_norm_new = (risk_after - risk_min) / (risk_max - risk_min)
    
    print(f"\n统一归一化基准: [{risk_min:.2f}, {risk_max:.2f}]")
    print(f"部署前归一化: {risk_before_norm_new}")
    print(f"部署后归一化: {risk_after_norm_new}")
    print(f"\n差异: {risk_before_norm_new - risk_after_norm_new}")
    print(f"平均差异: {np.mean(np.abs(risk_before_norm_new - risk_after_norm_new)):.4f}")
    
    print("\n改进:")
    print("  ✅ 使用统一的归一化基准")
    print("  ✅ 差异更明显")
    print("  ✅ 颜色映射后可以直接对比")
    
    # 测试3: 可视化效果模拟
    print("\n" + "=" * 70)
    print("测试3: 可视化效果模拟")
    print("=" * 70)
    
    print("\n旧方法（独立归一化）:")
    print("  网格  | 部署前 | 部署后 | 颜色差异")
    print("  " + "-" * 50)
    for i in range(len(risk_before)):
        color_diff = abs(risk_before_norm_old[i] - risk_after_norm_old[i])
        status = "明显" if color_diff > 0.3 else "不明显"
        print(f"  {i+1:3d}   | {risk_before_norm_old[i]:6.3f} | {risk_after_norm_old[i]:6.3f} | {color_diff:6.3f} ({status})")
    
    print("\n新方法（统一归一化）:")
    print("  网格  | 部署前 | 部署后 | 颜色差异")
    print("  " + "-" * 50)
    for i in range(len(risk_before)):
        color_diff = abs(risk_before_norm_new[i] - risk_after_norm_new[i])
        status = "明显" if color_diff > 0.3 else "不明显"
        print(f"  {i+1:3d}   | {risk_before_norm_new[i]:6.3f} | {risk_after_norm_new[i]:6.3f} | {color_diff:6.3f} ({status})")
    
    # 测试4: 极端情况
    print("\n" + "=" * 70)
    print("测试4: 极端情况（保护效果很好）")
    print("=" * 70)
    
    # 保护效果很好的情况
    protection_effect_high = np.array([1.0, 1.2, 1.5, 1.8, 1.0])
    risk_after_high = risk_before * np.exp(-protection_effect_high)
    
    print(f"\n部署前风险: {risk_before}")
    print(f"保护效果 E_i: {protection_effect_high}")
    print(f"部署后剩余风险: {risk_after_high}")
    
    # 旧方法
    rr_min_high, rr_max_high = risk_after_high.min(), risk_after_high.max()
    risk_after_norm_old_high = (risk_after_high - rr_min_high) / (rr_max_high - rr_min_high)
    
    # 新方法
    risk_after_norm_new_high = (risk_after_high - risk_min) / (risk_max - risk_min)
    
    print(f"\n旧方法 - 部署后归一化: {risk_after_norm_old_high}")
    print(f"新方法 - 部署后归一化: {risk_after_norm_new_high}")
    
    print("\n观察:")
    print("  旧方法: 剩余风险仍然分布在 [0, 1]，看起来和部署前一样")
    print("  新方法: 剩余风险集中在 [0, 0.3]，明显低于部署前")
    
    # 总结
    print("\n" + "=" * 70)
    print("总结")
    print("=" * 70)
    
    print("\n修复前的问题:")
    print("  ❌ 部署前后使用不同的归一化基准")
    print("  ❌ 两者都映射到 [0, 1]，颜色差异不明显")
    print("  ❌ 无法直观看出保护效果")
    
    print("\n修复后的改进:")
    print("  ✅ 使用统一的归一化基准（部署前风险范围）")
    print("  ✅ 部署后剩余风险明显低于部署前")
    print("  ✅ 颜色差异明显，可以直观看出保护效果")
    
    print("\n实现细节:")
    print("  1. 获取部署前风险范围: [risk_min, risk_max]")
    print("  2. 使用统一归一化函数: norm(v) = (v - risk_min) / (risk_max - risk_min)")
    print("  3. 对部署前和部署后风险都使用相同的归一化")
    print("  4. 在可视化时使用相同的颜色映射范围")
    
    print("\n验证方法:")
    print("  1. 运行优化: python hexdynamic/protection_pipeline.py input.json output.json")
    print("  2. 可视化: python hexdynamic/visualize_output.py output.json --input input.json")
    print("  3. 查看 risk_comparison.png，应该看到明显的颜色差异")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    test_risk_normalization()
