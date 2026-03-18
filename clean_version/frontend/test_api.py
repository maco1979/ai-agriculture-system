import requests

try:
    # 测试直接访问后端
    response = requests.get('http://localhost:8001/api/system/health', timeout=3)
    print('直接访问后端 - Status code:', response.status_code)
    print('直接访问后端 - Response:', response.json())
    
    # 测试通过前端代理访问后端
    proxy_response = requests.get('http://localhost:3000/api/system/health', timeout=3)
    print('通过前端代理访问 - Status code:', proxy_response.status_code)
    print('通过前端代理访问 - Response:', proxy_response.json())
    
except Exception as e:
    print('Error:', e)
