"""
测试资源利用率显示

测试不同约束配置下的利用率显示
"""

def test_utilization_display():
    """测试利用率显示逻辑"""
    
    # 测试场景1: 正常配置
    print("=" * 70)
    print("场景1: 正常配置（所有资源都有）")
    print("=" * 70)
    
    constraints = {
        'total_cameras': 10,
        'total_drones': 5,
        'total_camps': 3,
        'total_patrol': 20
    }
    
    deployed = {
        'cameras': 8,
        'drones': 5,
        'camps': 2,
        'rangers': 18
    }
    
    print_utilization(constraints, deployed)
    
    # 测试场景2: 部分资源为0
    print("\n" + "=" * 70)
    print("场景2: 部分资源未配置（摄像头和营地为0）")
    print("=" * 70)
    
    constraints = {
        'total_cameras': 0,
        'total_drones': 5,
        'total_camps': 0,
        'total_patrol': 20
    }
    
    deployed = {
        'cameras': 0,
        'drones': 5,
        'camps': 0,
        'rangers': 20
    }
    
    print_utilization(constraints, deployed)
    
    # 测试场景3: 部分未充分利用
    print("\n" + "=" * 70)
    print("场景3: 部分资源未充分利用")
    print("=" * 70)
    
    constraints = {
        'total_cameras': 10,
        'total_drones': 5,
        'total_camps': 3,
        'total_patrol': 20
    }
    
    deployed = {
        'cameras': 0,  # 完全未使用
        'drones': 5,   # 100%使用
        'camps': 0,    # 完全未使用
        'rangers': 20  # 100%使用
    }
    
    print_utilization(constraints, deployed)
    print("\n⚠️  注意: 如果某些资源利用率为0%，可能的原因：")
    print("   1. 优化器认为部署这些资源不划算（成本高于收益）")
    print("   2. 约束条件限制了资源部署（如地形限制）")
    print("   3. 其他资源已经提供了足够的保护")
    print("   4. 需要调整覆盖参数（wp, wd, wc, wf）来平衡资源权重")


def print_utilization(constraints, deployed):
    """打印利用率统计"""
    print(f"\n📊 部署统计:")
    
    # 摄像头利用率
    if constraints['total_cameras'] > 0:
        camera_util = deployed['cameras'] / constraints['total_cameras'] * 100
        print(f"   摄像头利用率: {camera_util:.1f}%")
    else:
        print(f"   摄像头利用率: N/A (未配置摄像头资源)")
    
    # 无人机利用率
    if constraints['total_drones'] > 0:
        drone_util = deployed['drones'] / constraints['total_drones'] * 100
        print(f"   无人机利用率: {drone_util:.1f}%")
    else:
        print(f"   无人机利用率: N/A (未配置无人机资源)")
    
    # 营地利用率
    if constraints['total_camps'] > 0:
        camp_util = deployed['camps'] / constraints['total_camps'] * 100
        print(f"   营地利用率: {camp_util:.1f}%")
    else:
        print(f"   营地利用率: N/A (未配置营地资源)")
    
    # 巡逻人员利用率
    if constraints['total_patrol'] > 0:
        ranger_util = deployed['rangers'] / constraints['total_patrol'] * 100
        print(f"   巡逻人员利用率: {ranger_util:.1f}%")
    else:
        print(f"   巡逻人员利用率: N/A (未配置巡逻人员资源)")


if __name__ == '__main__':
    test_utilization_display()
