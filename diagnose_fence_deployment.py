"""
诊断脚本：检查围栏部署情况

用法：
    python diagnose_fence_deployment.py output.json
    python diagnose_fence_deployment.py output.json --input input.json
"""

import json
import argparse
import sys


def diagnose_fence(output_path, input_path=None):
    """诊断围栏部署情况"""
    
    print("=" * 70)
    print("围栏部署诊断 (Fence Deployment Diagnosis)")
    print("=" * 70)
    
    # 读取输出JSON
    with open(output_path, 'r', encoding='utf-8') as f:
        output = json.load(f)
    
    # 读取输入JSON（可选）
    input_data = None
    if input_path:
        with open(input_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
    
    # 1. 检查约束条件
    print("\n1️⃣  约束条件检查:")
    if input_data:
        constraints = input_data.get('constraints', {})
        total_fence = constraints.get('total_fence_length', 0)
        print(f"   总围栏长度约束: {total_fence}")
        if total_fence == 0:
            print("   ⚠️  警告：围栏长度约束为0，不会部署围栏")
    else:
        print("   ℹ️  未提供输入JSON，跳过约束检查")
    
    # 2. 检查输出中的围栏信息
    print("\n2️⃣  输出JSON中的围栏信息:")
    fence_edges = output.get('fence_edges', [])
    print(f"   部署的围栏边数: {len(fence_edges)}")
    
    if fence_edges:
        print(f"   前5条围栏边:")
        for i, edge in enumerate(fence_edges[:5]):
            gid1 = edge.get('grid_id_1')
            gid2 = edge.get('grid_id_2')
            print(f"      [{i+1}] Grid {gid1} - Grid {gid2}")
        
        if len(fence_edges) > 5:
            print(f"      ... 还有 {len(fence_edges) - 5} 条围栏边")
    else:
        print("   ❌ 没有部署任何围栏")
    
    # 3. 检查资源部署统计
    print("\n3️⃣  资源部署统计:")
    summary = output.get('summary', {})
    resources = summary.get('resources_deployed', {})
    
    print(f"   摄像头: {resources.get('total_cameras', 0)}")
    print(f"   无人机: {resources.get('total_drones', 0)}")
    print(f"   营地: {resources.get('total_camps', 0)}")
    print(f"   巡逻人员: {resources.get('total_rangers', 0)}")
    print(f"   围栏段数: {resources.get('fence_segments', 0)}")
    
    # 4. 检查边缘网格中的围栏
    print("\n4️⃣  边缘网格分析:")
    grids = output.get('grids', [])
    
    # 计算边缘网格
    rows = [g['r'] for g in grids]
    cols = [g['q'] + g['r'] // 2 for g in grids]
    min_r, max_r = min(rows), max(rows)
    min_c, max_c = min(cols), max(cols)
    
    edge_grid_ids = {g['grid_id'] for g in grids
                     if g['r'] in (min_r, max_r) or (g['q'] + g['r'] // 2) in (min_c, max_c)}
    
    print(f"   总网格数: {len(grids)}")
    print(f"   边缘网格数: {len(edge_grid_ids)}")
    
    # 检查边缘网格中有多少个是围栏端点
    fence_grid_ids = {gid for (a, b) in [(e['grid_id_1'], e['grid_id_2']) for e in fence_edges]
                      for gid in (a, b) if gid in edge_grid_ids}
    
    print(f"   围栏端点网格数: {len(fence_grid_ids)}")
    
    if fence_grid_ids:
        print(f"   围栏端点网格ID: {sorted(fence_grid_ids)}")
    
    # 5. 检查每个网格的部署情况
    print("\n5️⃣  网格部署详情:")
    
    # 统计有围栏的网格
    fenced_grids = []
    for g in grids:
        if g['grid_id'] in fence_grid_ids:
            fenced_grids.append(g)
    
    if fenced_grids:
        print(f"   有围栏的网格数: {len(fenced_grids)}")
        print(f"   前5个有围栏的网格:")
        for i, g in enumerate(fenced_grids[:5]):
            print(f"      Grid {g['grid_id']}: 位置({g['q']}, {g['r']}), 地形={g['terrain_type']}")
    else:
        print(f"   没有网格有围栏")
    
    # 6. 诊断结论
    print("\n6️⃣  诊断结论:")
    
    if len(fence_edges) == 0:
        print("   ❌ 问题：没有部署任何围栏")
        print("   可能原因：")
        print("      1. 约束条件中 total_fence_length = 0")
        print("      2. 优化器认为不需要部署围栏")
        print("      3. 围栏部署被其他约束阻止")
    elif len(fence_grid_ids) == len(edge_grid_ids):
        print("   ⚠️  警告：所有边缘网格都是围栏端点")
        print("   这可能表示：")
        print("      1. 围栏覆盖了整个边界")
        print("      2. 或者可视化脚本有问题")
    elif len(fence_grid_ids) > 0:
        print("   ✅ 正常：部分边缘网格有围栏")
        print(f"   围栏覆盖率: {len(fence_grid_ids) / len(edge_grid_ids) * 100:.1f}%")
    else:
        print("   ⚠️  警告：有围栏边但没有边缘网格有围栏")
        print("   这可能表示围栏边的端点不在边缘")
    
    # 7. 建议
    print("\n7️⃣  建议:")
    if len(fence_edges) == 0:
        print("   • 检查输入JSON中的 total_fence_length 是否 > 0")
        print("   • 尝试增加 total_fence_length 的值")
        print("   • 检查地图是否有边界网格")
    else:
        print("   • 运行可视化脚本查看热力图")
        print("   • 检查围栏是否正确显示在热力图上")
        print("   • 如果显示不正确，检查可视化脚本的逻辑")
    
    print("\n" + "=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="诊断围栏部署情况",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("output", help="输出JSON文件路径")
    parser.add_argument("--input", "-i", default=None, help="输入JSON文件路径（可选）")
    
    args = parser.parse_args()
    
    try:
        diagnose_fence(args.output, args.input)
    except FileNotFoundError as e:
        print(f"❌ 错误：文件不存在 - {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ 错误：JSON格式错误 - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
