import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import random

class SimpleDDoSTest:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.results = []
        
    # 1. single HTTP request
    def single_request(self, endpoint="/", headers=None):
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}{endpoint}", headers=headers, timeout=5)
            response_time = time.time() - start_time
            
            return {
                "status": response.status_code,
                "response_time": response_time,
                "success": response.status_code not in [429, 500, 503],
                "blocked": response.status_code == 429
            }
        except requests.exceptions.Timeout:
            return {"status": 0, "success": False, "error": "Timeout", "blocked": False}
        except Exception as e:
            return {"status": 0, "success": False, "error": str(e), "blocked": False}
        
    
    # 2. Brute force attack -> 20 thread attack with 10 requests per thread
    def burst_attack_test(self, num_threads=20, requests_per_thread=10):
        print(f"\nBURST ATTACK TEST")
        print(f"Launching {num_threads} threads, {requests_per_thread} requests each")
        print(f"Total: {num_threads * requests_per_thread} requests")
        print("-" * 50)
        
        results = []
        
        def worker():
            thread_results = []
            for _ in range(requests_per_thread):
                result = self.single_request()
                thread_results.append(result)
            return thread_results
        
        # Launch threads
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker) for i in range(num_threads)]
            
            for future in futures:
                results.extend(future.result())
        
        total_time = time.time() - start_time
        self.analyze_and_print_results(results, "Burst Attack", total_time)
        return results
    
     # 3. Sustained attack over time - testing the server on applying steady pressure 
    
    def sustained_attack_test(self, duration_seconds=20, requests_per_second=10):
        print(f"\nSUSTAINED ATTACK TEST")
        print(f"Duration: {duration_seconds} seconds")
        print(f"Rate: {requests_per_second} requests/second")
        print("-" * 50)
        
        results = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            # Send requests for this second
            with ThreadPoolExecutor(max_workers=requests_per_second) as executor:
                futures = [executor.submit(self.single_request) for i in range(requests_per_second)]
                
                for future in futures:
                    results.append(future.result())
            
            elapsed = time.time() - start_time
            print(f"{elapsed:.1f}s: {len(results)} total requests sent")
            
            # Wait for next second (if needed)
            time.sleep(max(0, 1 - (time.time() - start_time - int(elapsed))))
        
        total_time = time.time() - start_time
        self.analyze_and_print_results(results, "Sustained Attack", total_time)
        return results
    
    # 4. A Botnet attack- simulating requests from different IPs    
    def distributed_ip_test(self, num_fake_ips=5, requests_per_ip=20):
        print(f"\nDISTRIBUTED IP TEST")
        print(f"Simulating {num_fake_ips} different IPs")
        print(f"{requests_per_ip} requests per IP")
        print("-" * 50)
        
        results = []
        
        for i in range(num_fake_ips):
            fake_ip = f"192.168.{random.randint(1,255)}.{random.randint(1,255)}"
            headers = {
                "X-Forwarded-For": fake_ip,
                "X-Real-IP": fake_ip,
                "User-Agent": f"TestBot-{i}"
            }
            
            print(f"Attacking from IP: {fake_ip}")
            
            # Send requests from this IP
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(self.single_request, "/", headers)
                    for _ in range(requests_per_ip)
                ]
                
                for future in futures:
                    result = future.result()
                    result["source_ip"] = fake_ip
                    results.append(result)
            
            time.sleep(0.5) 
        
        self.analyze_and_print_results(results, "Distributed IP Attack")
        return results
    
    # 4. Test rate limiting on authentication endpoint
    def auth_endpoint_test(self, num_attempts=50):
        print(f"\nAUTH ENDPOINT ATTACK TEST")
        print(f"Testing {num_attempts} login attempts")
        print("-" * 50)
        
        results = []
        
        def login_attempt(i):
            try:
                fake_credentials = {
                    "username": f"attacker{i % 5}",
                    "password": f"password{i}"
                }
                
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/v1/auth/login",
                    json=fake_credentials,
                    timeout=5
                )
                response_time = time.time() - start_time
                
                return {
                    "status": response.status_code,
                    "response_time": response_time,
                    "success": response.status_code == 200,
                    "blocked": response.status_code == 429,
                    "endpoint": "auth"
                }
            except Exception as e:
                return {
                    "status": 0,
                    "success": False,
                    "error": str(e),
                    "blocked": False,
                    "endpoint": "auth"
                }
        
        # login attempts
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(login_attempt, i) for i in range(num_attempts)]
            
            for i, future in enumerate(futures):
                results.append(future.result())
                if i % 10 == 0:
                    print(f"Completed {i} login attempts...")
        
        self.analyze_and_print_results(results, "Auth Endpoint Attack")
        return results
    
    def analyze_and_print_results(self, results, test_name, total_time=None):
        """Analyze and display test results"""
        if not results:
            print(f"No results for {test_name}")
            return
        
        total_requests = len(results)
        successful = sum(1 for r in results if r.get("success", False))
        blocked_429 = sum(1 for r in results if r.get("blocked", False))
        errors = sum(1 for r in results if r.get("error"))
        
        # rates calculation
        success_rate = (successful / total_requests) * 100
        block_rate = (blocked_429 / total_requests) * 100
        error_rate = (errors / total_requests) * 100
        
        # Response time analysis
        response_times = [r.get("response_time", 0) for r in results if r.get("response_time")]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Determining protection effectiveness
        if block_rate > 80:
            protection_level = "EXCELLENT"
        elif block_rate > 60:
            protection_level = "GOOD"
        elif block_rate > 40:
            protection_level = "MODERATE"
        else:
            protection_level = "POOR"
        
        # Print results
        print(f"\n{test_name} Results:")
        print(f"Total Requests: {total_requests}")
        print(f"Successful: {successful} ({success_rate:.1f}%)")
        print(f"Rate Limited (429): {blocked_429} ({block_rate:.1f}%)")
        print(f"Errors: {errors} ({error_rate:.1f}%)")
        print(f"Avg Response Time: {avg_response_time:.3f}s")
        if total_time:
            print(f"Total Time: {total_time:.2f}s")
            print(f"Requests/Second: {total_requests/total_time:.2f}")
        print(f"Protection Level: {protection_level}")
        
        # Status code breakdown
        status_codes = {}
        for result in results:
            status = result.get("status", 0)
            status_codes[status] = status_codes.get(status, 0) + 1
        
        print(f"Status Code Breakdown:")
        for status, count in sorted(status_codes.items()):
            print(f"      {status}: {count} requests")
    
    #Run comprehensive DDoS protection tests
    def run_all_tests(self):
        print("SIMPLE DDoS PROTECTION TESTING")
        print("=" * 60)
        
        # Test server connectivity first
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 404:
                print("Server is running (404 expected for root)")
            else:
                print(f"Server is running (Status: {response.status_code})")
        except Exception as e:
            print(f"Cannot connect to server: {e}")
            print("Please start your server: uvicorn main:app --reload")
            return
        
        print(f"Target: {self.base_url}")
        print("=" * 60)
        
        # Run tests
        all_results = []
        
        try:
            results1 = self.burst_attack_test(15, 8)
            all_results.extend(results1)
            time.sleep(2)
            
            results2 = self.sustained_attack_test(15, 8)
            all_results.extend(results2)
            time.sleep(2)
            
            results3 = self.distributed_ip_test(3, 15)
            all_results.extend(results3)
            time.sleep(2)
            
            results4 = self.auth_endpoint_test(30)
            all_results.extend(results4)
            
            # Final summary
            self.print_final_summary(all_results)
            
        except KeyboardInterrupt:
            print("\nTests stopped by user")
        except Exception as e:
            print(f"\nError during testing: {e}")
    
    def print_final_summary(self, all_results):
        """Print final test summary"""
        print("\n" + "=" * 60)
        print("FINAL DDoS PROTECTION SUMMARY")
        print("=" * 60)
        
        total_requests = len(all_results)
        total_blocked = sum(1 for r in all_results if r.get("blocked", False))
        total_successful = sum(1 for r in all_results if r.get("success", False))
        
        overall_block_rate = (total_blocked / total_requests) * 100 if total_requests > 0 else 0
        
        print(f"OVERALL STATISTICS:")
        print(f"Total Test Requests: {total_requests}")
        print(f"Total Blocked (429): {total_blocked}")
        print(f"Total Successful: {total_successful}")
        print(f"Overall Block Rate: {overall_block_rate:.1f}%")
        
        # Determine overall protection rating
        if overall_block_rate > 75:
            rating = "EXCELLENT - Production Ready!"
            recommendations = [
                "Your rate limiter is working excellently!",
                "Good protection against DDoS attacks",
                "Ready for production deployment"
            ]
        elif overall_block_rate > 50:
            rating = "GOOD - Well Protected"
            recommendations = [
                "Consider lowering rate limits for better protection",
                "Monitor server resources under load",
                "Acceptable for most production use cases"
            ]
        elif overall_block_rate > 25:
            rating = "MODERATE - Needs Improvement"
            recommendations = [
                "Consider implementing stricter rate limits",
                "Add IP-based blocking for repeat offenders",
                "Consider using a CDN or DDoS protection service"
            ]
        else:
            rating = "POOR - Vulnerable to DDoS"
            recommendations = [
                "URGENT: Implement proper rate limiting",
                "Your server is vulnerable to DDoS attacks",
                "Consider using a reverse proxy (nginx) with rate limiting"
            ]
        
        print(f"\nPROTECTION RATING: {rating}")
        print(f"\nRECOMMENDATIONS:")
        for rec in recommendations:
            print(f"   {rec}")

# Run the tests
if __name__ == "__main__":
    print("STARTING DDoS PROTECTION TEST")
    print()
    
    tester = SimpleDDoSTest()
    tester.run_all_tests()
