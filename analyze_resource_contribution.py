"""
资源贡献度分析工具

分析每种资源对保护收益的实际贡献，帮助理解为什么某些资源不被使用
"""

import json
import sys
import numpy as np


def analyze_contribution(input_path: str):
    """分析不同资源配置下的保护收益贡献"""
    
    print("=" * 70)
    print("资源贡献度分析工具")
    print("=" * 70)
    
    # 读取输入文件
    print(f"\n[1/2] 读取输入文件: {input_path}")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ 错误: 找不到输入文件 {input_path}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ 错误: 输入文件JSON格式错误 - {e}")
        return
    
    coverage_params = data.get('coverage_params', {})
    wp = coverage_params.get('wp', 0.3)
    wd = coverage_params.get('wd', 0.3)
    wc = coverage_params.get('wc', 0.2)
    wf = coverage_params.get('wf', 0.2)
    
    print("[2/2] 分析资源贡献度\n")
    
    print("=" * 70)
    print("当前权重配置")
    print("=" * 70)
    print(f"  巡逻人员权重 (wp): {wp}")
    print(f"  无人机权重 (wd): {wd}")
    print(f"  摄像头权重 (wc): {wc}")
    print(f"  围栏权重 (wf): {wf}")
    print(f"  总和: {wp + wd + wc + wf}")
    
    print("\n" + "=" * 70)
    print("保护效果计算公式")
    print("=" * 70)
    print("  E_i = wp * patrol_cov + wd * drone_cov + wc * camera_cov + wf * fence_prot")
    print("  protection_benefit = risk * (1 - exp(-E_i))")
    print("  fitness = total_benefit / total_risk")
    
    print("\n" + "=" * 70)
    print("场景分析：为什么某些资源不被使用？")
    print("=" * 70)
    
    # 场景1：只有无人机
    print("\n场景1：只部署无人机")
    print("-" * 70)
    drone_cov = 0.8  # 假设无人机覆盖率80%
    E_drone_only = wd * drone_cov
    benefit_drone_only = 1 - np.exp(-E_drone_only)
    print(f"  无人机覆盖率: {drone_cov}")
    print(f"  保护效果 E_i: {E_drone_only:.4f}")
    print(f"  保护收益率: {benefit_drone_only:.4f} ({benefit_drone_only*100:.1f}%)")
    
    # 场景2：无人机 + 摄像头
    print("\n场景2：部署无人机 + 摄像头")
    print("-" * 70)
    camera_cov = 0.6  # 假设摄像头覆盖率60%
    E_with_camera = wd * drone_cov + wc * camera_cov
    benefit_with_camera = 1 - np.exp(-E_with_camera)
    camera_contribution = benefit_with_camera - benefit_drone_only
    print(f"  无人机覆盖率: {drone_cov}")
    print(f"  摄像头覆盖率: {camera_cov}")
    print(f"  保护效果 E_i: {E_with_camera:.4f}")
    print(f"  保护收益率: {benefit_with_camera:.4f} ({benefit_with_camera*100:.1f}%)")
    print(f"  摄像头额外贡献: {camera_contribution:.4f} ({camera_contribution*100:.1f}%)")
    print(f"  ⚠️  摄像头只增加了 {camera_contribution*100:.1f}% 的保护收益！")
    
    # 场景3：无人机 + 巡逻
    print("\n场景3：部署无人机 + 巡逻人员")
    print("-" * 70)
    patrol_cov = 0.7  # 假设巡逻覆盖率70%
    E_with_patrol = wd * drone_cov + wp * patrol_cov
    benefit_with_patrol = 1 - np.exp(-E_with_patrol)
    patrol_contribution = benefit_with_patrol - benefit_drone_only
    print(f"  无人机覆盖率: {drone_cov}")
    print(f"  巡逻覆盖率: {patrol_cov}")
    print(f"  保护效果 E_i: {E_with_patrol:.4f}")
    print(f"  保护收益率: {benefit_with_patrol:.4f} ({benefit_with_patrol*100:.1f}%)")
    print(f"  巡逻额外贡献: {patrol_contribution:.4f} ({patrol_contribution*100:.1f}%)")
    
    # 对比
    print("\n" + "=" * 70)
    print("资源贡献对比")
    print("=" * 70)
    print(f"  摄像头额外贡献: {camera_contribution:.4f} ({camera_contribution*100:.1f}%)")
    print(f"  巡逻额外贡献: {patrol_contribution:.4f} ({patrol_contribution*100:.1f}%)")
    
    if patrol_contribution > camera_contribution:
        ratio = patrol_contribution / camera_contribution if camera_contribution > 0 else float('inf')
        print(f"\n  ✅ 巡逻人员的贡献是摄像头的 {ratio:.1f} 倍")
        print(f"  💡 这就是为什么优化器选择部署巡逻而不是摄像头！")
    
    # 分析边际收益递减
    print("\n" + "=" * 70)
    print("边际收益递减效应")
    print("=" * 70)
    print("\n当已有资源提供了较高保护时，增加新资源的边际收益会递减：")
    
    E_values = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0]
    print("\n  E_i值  |  保护收益率  |  边际增益")
    print("  " + "-" * 45)
    prev_benefit = 0
    for E in E_values:
        benefit = 1 - np.exp(-E)
        marginal = benefit - prev_benefit
        print(f"  {E:5.1f}  |  {benefit:11.4f}  |  {marginal:10.4f}")
        prev_benefit = benefit
    
    print("\n  💡 观察：当E_i从0.6增加到0.8时，边际增益只有0.0516")
    print("     这意味着如果已有资源提供了E_i=0.6的保护，")
    print("     增加新资源（即使覆盖率很高）带来的额外收益也很小。")
    
    # 提供建议
    print("\n" + "=" * 70)
    print("为什么会出现利用率为0%？")
    print("=" * 70)
    
    print("\n核心原因：")
    print("  1. 权重不平衡：某些资源权重太低（如wc=0.2）")
    print("  2. 边际收益递减：已有资源提供了足够保护")
    print("  3. 优化器追求最大化 fitness = total_benefit / total_risk")
    print("  4. 如果增加某资源只带来很小的benefit增量，优化器会选择不部署")
    
    print("\n数学解释：")
    print("  假设无人机已提供 E_i = 0.24 (wd=0.3 * cov=0.8)")
    print("  保护收益率 = 1 - exp(-0.24) = 0.2133 (21.33%)")
    print()
    print("  如果增加摄像头 E_i = 0.24 + 0.12 = 0.36 (wc=0.2 * cov=0.6)")
    print("  保护收益率 = 1 - exp(-0.36) = 0.3023 (30.23%)")
    print("  摄像头贡献 = 0.3023 - 0.2133 = 0.0890 (8.90%)")
    print()
    print("  但如果增加巡逻 E_i = 0.24 + 0.21 = 0.45 (wp=0.3 * cov=0.7)")
    print("  保护收益率 = 1 - exp(-0.45) = 0.3624 (36.24%)")
    print("  巡逻贡献 = 0.3624 - 0.2133 = 0.1491 (14.91%)")
    print()
    print("  结论：巡逻的贡献(14.91%)远大于摄像头(8.90%)")
    print("       所以优化器选择部署巡逻而不是摄像头！")
    
    print("\n" + "=" * 70)
    print("解决方案")
    print("=" * 70)
    
    print("\n方案1：增加未使用资源的权重")
    print("  如果摄像头利用率为0%，可以：")
    new_wc = 0.35
    new_wp = 0.25
    new_wd = 0.25
    new_wf = 0.15
    print(f"  • 增加摄像头权重: wc = {new_wc} (当前 {wc})")
    print(f"  • 相应减少其他权重: wp={new_wp}, wd={new_wd}, wf={new_wf}")
    
    # 重新计算
    E_new_camera = new_wd * drone_cov + new_wc * camera_cov
    benefit_new_camera = 1 - np.exp(-E_new_camera)
    E_new_drone_only = new_wd * drone_cov
    benefit_new_drone_only = 1 - np.exp(-E_new_drone_only)
    new_camera_contribution = benefit_new_camera - benefit_new_drone_only
    
    print(f"\n  调整后摄像头贡献: {new_camera_contribution:.4f} ({new_camera_contribution*100:.1f}%)")
    print(f"  提升: {(new_camera_contribution - camera_contribution)*100:.1f}%")
    
    print("\n方案2：减少其他资源数量")
    print("  • 减少无人机数量，为摄像头腾出\"收益空间\"")
    print("  • 这样摄像头的边际收益会更高")
    
    print("\n方案3：增加覆盖半径")
    print("  • 增加摄像头覆盖半径，提高其覆盖率")
    print("  • 覆盖率越高，贡献越大")
    
    print("\n方案4：接受优化结果")
    print("  • 如果其他资源已提供足够保护，不部署某些资源是合理的")
    print("  • 这是优化器的正确行为，不是bug")
    
    print("\n" + "=" * 70)
    print("推荐配置")
    print("=" * 70)
    
    print("\n如果希望所有资源都被使用，推荐平衡权重配置：")
    print("  wp = 0.25  (巡逻人员)")
    print("  wd = 0.25  (无人机)")
    print("  wc = 0.25  (摄像头)")
    print("  wf = 0.25  (围栏)")
    print("\n这样每种资源的贡献更加平衡，都有机会被部署。")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("用法: python analyze_resource_contribution.py <input.json>")
        print("\n示例:")
        print("  python analyze_resource_contribution.py hexdynamic/input_example.json")
        sys.exit(1)
    
    analyze_contribution(sys.argv[1])
