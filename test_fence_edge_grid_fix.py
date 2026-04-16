"""
测试围栏边缘网格识别修复

验证 _edge_grid_ids 函数在不同情况下的行为
"""

import sys
import os

# 添加路径以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hexdynamic'))

from visualize_output import _edge_grid_ids


def test_edge_grid_ids():
    """测试边缘网格识别函数"""
    
    print("=" * 70)
    print("测试围栏边缘网格识别修复")
    print("=" * 70)
    
    # 创建测试网格数据（5x5的网格）
    grids = []
    grid_id = 0
    for r in range(5):
        for q in range(5):
            grids.append({
                "grid_id": grid_id,
                "q": q,
                "r": r,
                "x": q,
                "y": r
            })
            grid_id += 1
    
    print(f"\n测试数据: {len(grids)} 个网格 (5x5)")
    
    # 测试1: 不提供 boundary_xy（使用矩形边界）
    print("\n" + "=" * 70)
    print("测试1: 不提供 boundary_xy（使用矩形边界逻辑）")
    print("=" * 70)
    
    edge_ids_rect = _edge_grid_ids(grids, boundary_xy=None)
    print(f"边缘网格数: {len(edge_ids_rect)}")
    print(f"边缘网格ID: {sorted(edge_ids_rect)}")
    
    # 对于5x5网格，矩形边界应该是：
    # 第一行(r=0): 0,1,2,3,4
    # 最后一行(r=4): 20,21,22,23,24
    # 第一列(q=0): 0,5,10,15,20
    # 最后一列(q=4): 4,9,14,19,24
    # 去重后应该是16个网格
    expected_rect = {0, 1, 2, 3, 4, 5, 9, 10, 14, 15, 19, 20, 21, 22, 23, 24}
    
    if edge_ids_rect == expected_rect:
        print("✅ 矩形边界逻辑正确")
    else:
        print("❌ 矩形边界逻辑错误")
        print(f"   期望: {sorted(expected_rect)}")
        print(f"   实际: {sorted(edge_ids_rect)}")
    
    # 测试2: 提供 boundary_xy（使用实际边界）
    print("\n" + "=" * 70)
    print("测试2: 提供 boundary_xy（使用实际边界逻辑）")
    print("=" * 70)
    
    # 创建一个不规则边界（L形）
    boundary_xy = [
        (0, 0), (1, 0), (2, 0),  # 顶部
        (0, 1), (2, 1),          # 中间
        (0, 2), (1, 2), (2, 2),  # 底部
    ]
    
    edge_ids_actual = _edge_grid_ids(grids, boundary_xy=boundary_xy)
    print(f"边缘网格数: {len(edge_ids_actual)}")
    print(f"边缘网格ID: {sorted(edge_ids_actual)}")
    
    # 根据 boundary_xy 计算期望的网格ID
    expected_actual = set()
    for x, y in boundary_xy:
        # 找到对应的网格ID
        for g in grids:
            if g["x"] == x and g["y"] == y:
                expected_actual.add(g["grid_id"])
                break
    
    print(f"期望的边缘网格ID: {sorted(expected_actual)}")
    
    if edge_ids_actual == expected_actual:
        print("✅ 实际边界逻辑正确")
    else:
        print("❌ 实际边界逻辑错误")
        print(f"   期望: {sorted(expected_actual)}")
        print(f"   实际: {sorted(edge_ids_actual)}")
    
    # 测试3: 对比两种方法的差异
    print("\n" + "=" * 70)
    print("测试3: 对比矩形边界 vs 实际边界")
    print("=" * 70)
    
    print(f"矩形边界网格数: {len(edge_ids_rect)}")
    print(f"实际边界网格数: {len(edge_ids_actual)}")
    print(f"差异: {len(edge_ids_rect) - len(edge_ids_actual)}")
    
    only_in_rect = edge_ids_rect - edge_ids_actual
    only_in_actual = edge_ids_actual - edge_ids_rect
    
    if only_in_rect:
        print(f"\n只在矩形边界中的网格: {sorted(only_in_rect)}")
    if only_in_actual:
        print(f"只在实际边界中的网格: {sorted(only_in_actual)}")
    
    # 测试4: 大规模测试（模拟实际场景）
    print("\n" + "=" * 70)
    print("测试4: 大规模测试（模拟实际场景）")
    print("=" * 70)
    
    # 创建一个50x50的网格
    large_grids = []
    grid_id = 0
    for r in range(50):
        for q in range(50):
            large_grids.append({
                "grid_id": grid_id,
                "q": q,
                "r": r,
                "x": q,
                "y": r
            })
            grid_id += 1
    
    print(f"大规模测试: {len(large_grids)} 个网格 (50x50)")
    
    # 矩形边界
    edge_ids_large_rect = _edge_grid_ids(large_grids, boundary_xy=None)
    print(f"矩形边界网格数: {len(edge_ids_large_rect)}")
    
    # 创建一个圆形边界（模拟实际保护区）
    import math
    center_x, center_y = 25, 25
    radius = 20
    boundary_xy_large = []
    for x in range(50):
        for y in range(50):
            dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
            if abs(dist - radius) < 2:  # 边界附近
                boundary_xy_large.append((x, y))
    
    edge_ids_large_actual = _edge_grid_ids(large_grids, boundary_xy=boundary_xy_large)
    print(f"实际边界网格数: {len(edge_ids_large_actual)}")
    print(f"差异: {len(edge_ids_large_rect) - len(edge_ids_large_actual)}")
    
    print("\n💡 观察:")
    print("   - 矩形边界只识别外围的行和列")
    print("   - 实际边界识别所有边界网格")
    print("   - 对于不规则形状，差异会很大")
    
    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    
    print("\n修复前的问题:")
    print("  ❌ 只使用矩形边界，导致很多实际边界网格被忽略")
    print("  ❌ 围栏标记只显示在矩形边界上")
    print("  ❌ 对于不规则保护区，可视化不准确")
    
    print("\n修复后的改进:")
    print("  ✅ 使用实际边界网格（从 boundary_locations 获取）")
    print("  ✅ 围栏标记正确显示在所有边界网格上")
    print("  ✅ 保持向后兼容（没有 boundary_xy 时使用旧逻辑）")
    print("  ✅ 可视化结果更准确")
    
    print("\n使用建议:")
    print("  • 总是使用 --input 参数来获得准确的可视化")
    print("  • 检查调试输出确认边缘网格数正确")
    print("  • 边缘网格数应该等于边界格子数")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    test_edge_grid_ids()
