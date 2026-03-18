import requests
import json

# 测试JEPA-DT-MPC API接口
def test_jepa_activation():
    """测试激活JEPA-DT-MPC控制器"""
    url = "http://localhost:8002/api/jepa-dtmpc/activate"
    headers = {"Content-Type": "application/json"}
    data = {
        "controller_params": {
            "control_switch": True,
            "robust_control_switch": True
        },
        "mv_params": {
            "operation_range": [-100, 100],
            "rate_limits": [-10, 10]
        },
        "cv_params": {
            "setpoint": 10.0,
            "safety_range": [-50, 50]
        },
        "model_params": {
            "prediction_horizon": 20,
            "system_gain": 2.0,
            "time_constant": 10
        },
        "jepa_params": {
            "enabled": True,
            "embedding_dim": 10,
            "prediction_horizon": 20
        }
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"激活JEPA-DT-MPC控制器: {response.status_code}")
        print(f"响应内容: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"激活JEPA-DT-MPC控制器失败: {str(e)}")
        return False

def test_jepa_status():
    """测试获取JEPA-DT-MPC控制器状态"""
    url = "http://localhost:8002/api/jepa-dtmpc/status"
    
    try:
        response = requests.get(url)
        print(f"获取JEPA-DT-MPC控制器状态: {response.status_code}")
        print(f"响应内容: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"获取JEPA-DT-MPC控制器状态失败: {str(e)}")
        return False

def test_jepa_prediction():
    """测试获取JEPA预测结果"""
    url = "http://localhost:8002/api/jepa-dtmpc/prediction"
    
    try:
        response = requests.get(url)
        print(f"获取JEPA预测结果: {response.status_code}")
        print(f"响应内容: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"获取JEPA预测结果失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始测试JEPA-DT-MPC API接口...")
    print("=" * 50)
    
    # 测试激活
    activation_success = test_jepa_activation()
    print("=" * 50)
    
    # 测试状态
    status_success = test_jepa_status()
    print("=" * 50)
    
    # 测试预测
    prediction_success = test_jepa_prediction()
    print("=" * 50)
    
    # 总结
    print("测试结果总结:")
    print(f"激活接口: {'通过' if activation_success else '失败'}")
    print(f"状态接口: {'通过' if status_success else '失败'}")
    print(f"预测接口: {'通过' if prediction_success else '失败'}")
    
    if activation_success and status_success and prediction_success:
        print("\n🎉 所有JEPA-DT-MPC API接口测试通过！")
    else:
        print("\n⚠️ 部分JEPA-DT-MPC API接口测试失败！")
