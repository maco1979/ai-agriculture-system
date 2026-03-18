"""
性能测试脚本
验证系统优化效果
"""

import asyncio
import time
import statistics
import requests
from datetime import datetime
from typing import List, Dict, Any
import json


class PerformanceTester:
    """性能测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """初始化性能测试器
        
        Args:
            base_url: 基础URL
        """
        self.base_url = base_url
        self.results: Dict[str, List[float]] = {}
    
    async def test_endpoint(self, endpoint: str, method: str = "GET", 
                        data: Any = None, iterations: int = 100) -> Dict[str, Any]:
        """测试单个端点
        
        Args:
            endpoint: 端点路径
            method: HTTP方法
            data: 请求数据
            iterations: 测试次数
        
        Returns:
            测试结果
        """
        url = f"{self.base_url}{endpoint}"
        response_times = []
        success_count = 0
        error_count = 0
        
        print(f"🧪 测试端点: {endpoint}")
        print(f"📍 URL: {url}")
        print(f"🔄 迭代次数: {iterations}")
        
        for i in range(iterations):
            try:
                start_time = time.time()
                
                if method == "GET":
                    response = requests.get(url, timeout=10)
                elif method == "POST":
                    response = requests.post(url, json=data, timeout=10)
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # 转换为毫秒
                
                response_times.append(response_time)
                
                if response.status_code < 400:
                    success_count += 1
                else:
                    error_count += 1
                
                if (i + 1) % 20 == 0:
                    print(f"   进度: {i + 1}/{iterations}")
                    
            except Exception as e:
                print(f"   ❌ 请求失败: {e}")
                error_count += 1
        
        # 计算统计指标
        if response_times:
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            sorted_times = sorted(response_times)
            p95_time = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
            p99_time = sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0
        else:
            avg_time = median_time = min_time = max_time = p95_time = p99_time = 0
        
        success_rate = (success_count / iterations * 100) if iterations > 0 else 0
        
        result = {
            "endpoint": endpoint,
            "method": method,
            "iterations": iterations,
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": round(success_rate, 2),
            "avg_response_time": round(avg_time, 2),
            "median_response_time": round(median_time, 2),
            "min_response_time": round(min_time, 2),
            "max_response_time": round(max_time, 2),
            "p95_response_time": round(p95_time, 2),
            "p99_response_time": round(p99_time, 2),
            "requests_per_second": round(iterations / (sum(response_times) / 1000), 2) if response_times else 0
        }
        
        self.results[endpoint] = response_times
        
        return result
    
    async def run_concurrent_test(self, endpoint: str, method: str = "GET",
                                data: Any = None, concurrent_users: int = 10,
                                requests_per_user: int = 10) -> Dict[str, Any]:
        """运行并发测试
        
        Args:
            endpoint: 端点路径
            method: HTTP方法
            data: 请求数据
            concurrent_users: 并发用户数
            requests_per_user: 每个用户的请求数
        
        Returns:
            并发测试结果
        """
        url = f"{self.base_url}{endpoint}"
        total_requests = concurrent_users * requests_per_user
        
        print(f"🧪 并发测试端点: {endpoint}")
        print(f"📍 URL: {url}")
        print(f"👥 并发用户数: {concurrent_users}")
        print(f"🔄 总请求数: {total_requests}")
        
        async def make_request(user_id: int, request_id: int) -> Dict[str, Any]:
            """发起单个请求"""
            try:
                start_time = time.time()
                
                if method == "GET":
                    response = requests.get(url, timeout=10)
                elif method == "POST":
                    response = requests.post(url, json=data, timeout=10)
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # 转换为毫秒
                
                return {
                    "user_id": user_id,
                    "request_id": request_id,
                    "success": response.status_code < 400,
                    "status_code": response.status_code,
                    "response_time": response_time
                }
            except Exception as e:
                return {
                    "user_id": user_id,
                    "request_id": request_id,
                    "success": False,
                    "status_code": 0,
                    "response_time": 0,
                    "error": str(e)
                }
        
        # 创建并发任务
        tasks = []
        for user_id in range(concurrent_users):
            for request_id in range(requests_per_user):
                tasks.append(make_request(user_id, request_id))
        
        # 执行并发请求
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # 分析结果
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]
        
        response_times = [r["response_time"] for r in successful_results if r["response_time"] > 0]
        
        if response_times:
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            sorted_times = sorted(response_times)
            p95_time = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
            p99_time = sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0
        else:
            avg_time = median_time = min_time = max_time = p95_time = p99_time = 0
        
        success_rate = (len(successful_results) / total_requests * 100) if total_requests > 0 else 0
        
        result = {
            "endpoint": endpoint,
            "method": method,
            "concurrent_users": concurrent_users,
            "requests_per_user": requests_per_user,
            "total_requests": total_requests,
            "total_time": round(total_time, 2),
            "successful_requests": len(successful_results),
            "failed_requests": len(failed_results),
            "success_rate": round(success_rate, 2),
            "avg_response_time": round(avg_time, 2),
            "median_response_time": round(median_time, 2),
            "min_response_time": round(min_time, 2),
            "max_response_time": round(max_time, 2),
            "p95_response_time": round(p95_time, 2),
            "p99_response_time": round(p99_time, 2),
            "requests_per_second": round(total_requests / total_time, 2) if total_time > 0 else 0
        }
        
        return result
    
    def print_result(self, result: Dict[str, Any]):
        """打印测试结果"""
        print(f"\n{'='*60}")
        print(f"📊 测试结果: {result['endpoint']}")
        print(f"{'='*60}")
        print(f"✅ 成功率: {result['success_rate']}%")
        print(f"📈 平均响应时间: {result['avg_response_time']}ms")
        print(f"📊 中位数响应时间: {result['median_response_time']}ms")
        print(f"📉 最小响应时间: {result['min_response_time']}ms")
        print(f"📈 最大响应时间: {result['max_response_time']}ms")
        print(f"📊 P95响应时间: {result['p95_response_time']}ms")
        print(f"📊 P99响应时间: {result['p99_response_time']}ms")
        print(f"⚡ 请求吞吐量: {result['requests_per_second']} RPS")
        
        if 'concurrent_users' in result:
            print(f"👥 并发用户数: {result['concurrent_users']}")
            print(f"⏱️  总测试时间: {result['total_time']}s")
        
        print(f"{'='*60}\n")
    
    def save_results(self, filename: str = "performance_test_results.json"):
        """保存测试结果
        
        Args:
            filename: 文件名
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "test_time": datetime.now().isoformat(),
                "base_url": self.base_url,
                "results": self.results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"💾 测试结果已保存到: {filename}")


async def main():
    """主函数"""
    print("🚀 开始性能测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 测试地址: http://localhost:8000")
    print()
    
    tester = PerformanceTester(base_url="http://localhost:8000")
    
    # 测试关键端点
    endpoints = [
        ("/api/system/health", "GET"),
        ("/api/system/info", "GET"),
        ("/api/system/stats", "GET"),
        ("/api/system/metrics", "GET"),
        ("/api/performance/summary", "GET"),
    ]
    
    all_results = []
    
    # 顺序测试
    for endpoint, method in endpoints:
        try:
            result = await tester.test_endpoint(endpoint, method, iterations=50)
            tester.print_result(result)
            all_results.append(result)
        except Exception as e:
            print(f"❌ 测试端点 {endpoint} 失败: {e}")
    
    # 并发测试
    print("\n🧪 开始并发测试")
    print(f"{'='*60}\n")
    
    for endpoint, method in endpoints[:3]:  # 只测试前3个端点
        try:
            result = await tester.run_concurrent_test(endpoint, method, 
                                                  concurrent_users=20, 
                                                  requests_per_user=5)
            tester.print_result(result)
            all_results.append(result)
        except Exception as e:
            print(f"❌ 并发测试端点 {endpoint} 失败: {e}")
    
    # 保存结果
    tester.save_results()
    
    # 生成总结报告
    print(f"\n{'='*60}")
    print("📋 性能测试总结报告")
    print(f"{'='*60}")
    
    # 计算整体性能指标
    successful_results = [r for r in all_results if r['success_rate'] > 90]
    
    if successful_results:
        avg_response_time = statistics.mean([r['avg_response_time'] for r in successful_results])
        avg_success_rate = statistics.mean([r['success_rate'] for r in successful_results])
        avg_rps = statistics.mean([r['requests_per_second'] for r in successful_results])
        
        print(f"✅ 成功测试的端点数: {len(successful_results)}/{len(all_results)}")
        print(f"📈 平均响应时间: {round(avg_response_time, 2)}ms")
        print(f"✅ 平均成功率: {round(avg_success_rate, 2)}%")
        print(f"⚡ 平均请求吞吐量: {round(avg_rps, 2)} RPS")
        
        # 性能评估
        if avg_response_time < 100:
            print("🎯 性能评估: 优秀")
        elif avg_response_time < 300:
            print("🎯 性能评估: 良好")
        elif avg_response_time < 500:
            print("🎯 性能评估: 一般")
        else:
            print("🎯 性能评估: 需要优化")
        
        if avg_success_rate > 99:
            print("🎯 可靠性评估: 优秀")
        elif avg_success_rate > 95:
            print("🎯 可靠性评估: 良好")
        else:
            print("🎯 可靠性评估: 需要改进")
    else:
        print("❌ 没有成功的测试结果")
    
    print(f"{'='*60}\n")
    print("✅ 性能测试完成")


if __name__ == "__main__":
    asyncio.run(main())