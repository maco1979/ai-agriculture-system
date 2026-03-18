import subprocess
import time
import os

# 查找并停止占用8001端口的进程
def find_and_kill_process(port):
    try:
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.strip().split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                    print(f"Stopped process {pid}")
                    return True
    except Exception as e:
        print(f"Error: {e}")
    return False

# 主逻辑
print("Stopping backend...")
find_and_kill_process(8001)
time.sleep(2)

print("Starting backend...")
backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'simple_api.py')
log_path = os.path.join(os.path.dirname(__file__), 'backend', 'logs', 'backend.log')
os.makedirs(os.path.dirname(log_path), exist_ok=True)

try:
    with open(log_path, 'a') as log_file:
        process = subprocess.Popen(
            [subprocess.sys.executable, backend_path],
            stdout=log_file,
            stderr=log_file,
            cwd=os.path.dirname(backend_path)
        )
    print(f"Backend started with PID {process.pid}")
    time.sleep(3)
    
    # 验证
    import urllib.request
    r = urllib.request.urlopen('http://localhost:8001/health', timeout=5)
    print(f"Health check: {r.read().decode()}")
except Exception as e:
    print(f"Error: {e}")
