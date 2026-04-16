"""
资源利用率诊断工具

分析为什么某些资源没有被充分利用
"""

import json
import sys


def diagnose_utilization(input_path: str, output_path: str):
    """诊断资源利用率问题"""
    
    print("=" * 70)
    print("资源利用率诊断工具")
    print("=" * 70)
    
    # 读取输入文件
    print(f"\n[1/3] 读取输入文件: {input_path}")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ 错误: 找不到输入文件 {input_path}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ 错误: 输入文件JSON格式错误 - {e}")
        return
    
    # 读取输出文件
    print(f"[2/3] 读取输出文件: {output_path}")
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            output_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ 错误: 找不到输出文件 {output_path}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ 错误: 输出文件JSON格式错误 - {e}")
        return
    
    # 分析约束和部署
    print("[3/3] 分析资源利用情况\n")
    
    constraints = input_data.get('constraints', {})
    coverage_params = input_data.get('coverage_params', {})
    resources_deployed = output_data.get('summary', {}).get('resources_deployed', {})
    
    print("=" * 70)
    print("约束配置 (Constraints)")
    print("=" * 70)
    print(f"  摄像头总数: {constraints.get('total_cameras', 0)}")
    print(f"  无人机总数: {constraints.get('total_drones', 0)}")
    print(f"  营地总数: {constraints.get('total_camps', 0)}")
    print(f"  巡逻人员总数: {constraints.get('total_patrol', 0)}")
    print(f"  围栏总长度: {constraints.get('total_fence_length', 0)}")
    
    print("\n" + "=" * 70)
    print("实际部署 (Deployed)")
    print("=" * 70)
    print(f"  摄像头: {resources_deployed.get('total_cameras', 0)}")
    print(f"  无人机: {resources_deployed.get('total_drones', 0)}")
    print(f"  营地: {resources_deployed.get('total_camps', 0)}")
    print(f"  巡逻人员: {resources_deployed.get('total_rangers', 0)}")
    print(f"  围栏段数: {resources_deployed.get('fence_segments', 0)}")
    
    print("\n" + "=" * 70)
    print("利用率分析 (Utilization Analysis)")
    print("=" * 70)
    
    # 分析每种资源
    analyze_resource(
        "摄像头",
        constraints.get('total_cameras', 0),
        resources_deployed.get('total_cameras', 0),
        coverage_params.get('wc', 0.2),
        coverage_params.get('camera_radius', 2.0)
    )
    
    analyze_resource(
        "无人机",
        constraints.get('total_drones', 0),
        resources_deployed.get('total_drones', 0),
        coverage_params.get('wd', 0.3),
        coverage_params.get('drone_radius', 6.0)
    )
    
    analyze_resource(
        "营地",
        constraints.get('total_camps', 0),
        resources_deployed.get('total_camps', 0),
        None,  # 营地没有直接权重
        None
    )
    
    analyze_resource(
        "巡逻人员",
        constraints.get('total_patrol', 0),
        resources_deployed.get('total_rangers', 0),
        coverage_params.get('wp', 0.3),
        coverage_params.get('patrol_radius', 3.0)
    )
    
    # 提供建议
    print("\n" + "=" * 70)
    print("诊断建议 (Recommendations)")
    print("=" * 70)
    
    suggestions = []
    
    # 检查摄像头
    if constraints.get('total_cameras', 0) > 0 and resources_deployed.get('total_cameras', 0) == 0:
        suggestions.append({
            'resource': '摄像头',
            'issue': '完全未使用',
            'reasons': [
                f"权重过低 (wc={coverage_params.get('wc', 0.2)})",
                f"覆盖半径过小 (camera_radius={coverage_params.get('camera_radius', 2.0)})",
                "其他资源已提供足够保护（边际收益递减）",
                "巡逻/无人机的权重更高，贡献更大"
            ],
            'solutions': [
                "增加摄像头权重 wc (例如从0.2增加到0.3或0.35)",
                "增加摄像头覆盖半径 camera_radius (例如从2.0增加到4.0)",
                "减少其他资源的权重或数量",
                "使用平衡权重配置 (0.25, 0.25, 0.25, 0.25)",
                "运行 python analyze_resource_contribution.py input.json 查看详细分析"
            ]
        })
    
    # 检查营地
    if constraints.get('total_camps', 0) > 0 and resources_deployed.get('total_camps', 0) == 0:
        suggestions.append({
            'resource': '营地',
            'issue': '完全未使用',
            'reasons': [
                "营地本身不直接提供保护收益",
                "营地只是巡逻人员的部署点",
                "巡逻人员可以不依赖营地独立部署",
                "优化器倾向于直接部署巡逻人员"
            ],
            'solutions': [
                "这可能是正常的优化结果",
                "如果需要强制使用营地，可以修改约束逻辑",
                "增加巡逻人员权重 wp 可能间接增加营地使用",
                "或者接受当前结果（营地不是必需的）"
            ]
        })
    
    # 检查无人机
    if constraints.get('total_drones', 0) > 0 and resources_deployed.get('total_drones', 0) == 0:
        suggestions.append({
            'resource': '无人机',
            'issue': '完全未使用',
            'reasons': [
                f"权重过低 (wd={coverage_params.get('wd', 0.3)})",
                "其他资源已提供足够保护（边际收益递减）"
            ],
            'solutions': [
                "增加无人机权重 wd",
                "减少其他资源的数量",
                "运行 python analyze_resource_contribution.py input.json 查看详细分析"
            ]
        })
    
    # 检查巡逻人员
    if constraints.get('total_patrol', 0) > 0 and resources_deployed.get('total_rangers', 0) == 0:
        suggestions.append({
            'resource': '巡逻人员',
            'issue': '完全未使用',
            'reasons': [
                f"权重过低 (wp={coverage_params.get('wp', 0.3)})",
                "其他资源已提供足够保护（边际收益递减）"
            ],
            'solutions': [
                "增加巡逻人员权重 wp",
                "减少其他资源的数量",
                "运行 python analyze_resource_contribution.py input.json 查看详细分析"
            ]
        })
    
    if suggestions:
        for i, sug in enumerate(suggestions, 1):
            print(f"\n{i}. {sug['resource']} - {sug['issue']}")
            print(f"\n   可能原因:")
            for reason in sug['reasons']:
                print(f"   • {reason}")
            print(f"\n   解决方案:")
            for solution in sug['solutions']:
                print(f"   • {solution}")
    else:
        print("\n✅ 所有配置的资源都已被使用，没有发现问题。")
    
    # 权重平衡建议
    print("\n" + "=" * 70)
    print("权重平衡建议 (Weight Balance)")
    print("=" * 70)
    
    wp = coverage_params.get('wp', 0.3)
    wd = coverage_params.get('wd', 0.3)
    wc = coverage_params.get('wc', 0.2)
    wf = coverage_params.get('wf', 0.2)
    total_weight = wp + wd + wc + wf
    
    print(f"\n当前权重配置:")
    print(f"  巡逻人员权重 (wp): {wp} ({wp/total_weight*100:.1f}%)")
    print(f"  无人机权重 (wd): {wd} ({wd/total_weight*100:.1f}%)")
    print(f"  摄像头权重 (wc): {wc} ({wc/total_weight*100:.1f}%)")
    print(f"  围栏权重 (wf): {wf} ({wf/total_weight*100:.1f}%)")
    print(f"  总和: {total_weight}")
    
    if abs(total_weight - 1.0) > 0.01:
        print(f"\n⚠️  警告: 权重总和应该为1.0，当前为{total_weight}")
    
    print("\n建议的权重配置（根据资源利用情况）:")
    
    # 根据未使用的资源提供建议
    if resources_deployed.get('total_cameras', 0) == 0 and constraints.get('total_cameras', 0) > 0:
        print(f"  • 增加摄像头权重: wc = 0.3 (当前 {wc})")
    
    if resources_deployed.get('total_camps', 0) == 0 and constraints.get('total_camps', 0) > 0:
        print(f"  • 营地使用与巡逻人员相关，考虑增加: wp = 0.4 (当前 {wp})")
    
    print("\n" + "=" * 70)


def analyze_resource(name: str, total: int, deployed: int, weight: float, radius: float):
    """分析单个资源的利用情况"""
    
    if total == 0:
        print(f"\n{name}:")
        print(f"  状态: ⚪ 未配置")
        return
    
    utilization = deployed / total * 100
    
    if utilization == 0:
        status = "❌ 完全未使用"
    elif utilization < 50:
        status = "⚠️  利用率低"
    elif utilization < 100:
        status = "✅ 部分使用"
    else:
        status = "✅ 完全使用"
    
    print(f"\n{name}:")
    print(f"  配置数量: {total}")
    print(f"  实际部署: {deployed}")
    print(f"  利用率: {utilization:.1f}%")
    print(f"  状态: {status}")
    
    if weight is not None:
        print(f"  权重: {weight}")
    if radius is not None:
        print(f"  覆盖半径: {radius}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("用法: python diagnose_resource_utilization.py <input.json> <output.json>")
        print("\n示例:")
        print("  python diagnose_resource_utilization.py hexdynamic/input_example.json hexdynamic/output_example.json")
        sys.exit(1)
    
    diagnose_utilization(sys.argv[1], sys.argv[2])
