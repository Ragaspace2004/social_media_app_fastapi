import asyncio
import aiohttp
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime

class DDoSAttackSimulator:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.attack_results = {}
        
    def print_header(self, title):
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}")
    
    async def single_request(self, session, endpoint, method="GET", data=None):
        """Make a single HTTP request"""
        try:
            url = f"{self.base_url}{endpoint}"
            start_time = time.time()
            
            if method == "GET":
                async with session.get(url) as response:
                    response_time = time.time() - start_time
                    return {
                        "status": response.status,
                        "response_time": response_time,
                        "success": response.status not in [429, 500, 503]
                    }
            elif method == "POST":
                headers = {"Content-Type": "application/json"}
                async with session.post(url, json=data, headers=headers) as response:
                    response_time = time.time() - start_time
                    return {
                        "status": response.status,
                        "response_time": response_time,
                        "success": response.status not in [429, 500, 503]
                    }
        except Exception as e:
            return {
                "status": 0,
                "response_time": 999,
                "success": False,
                "error": str(e)
            }
    
    async def burst_attack(self, endpoint="/", concurrent_requests=100, total_requests=500):
        """Simulate burst DDoS attack - many requests at once"""
        self.print_header(f"BURST ATTACK SIMULATION - {concurrent_requests} concurrent requests")
        
        results = []
        connector = aiohttp.TCPConnector(limit=200, limit_per_host=200)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for batch in range(0, total_requests, concurrent_requests):
                batch_size = min(concurrent_requests, total_requests - batch)
                print(f"Launching batch {batch//concurrent_requests + 1}: {batch_size} requests...")
                
                # Create concurrent requests
                tasks = [
                    self.single_request(session, endpoint)
                    for _ in range(batch_size)
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                results.extend([r for r in batch_results if not isinstance(r, Exception)])
                
                # Small delay between batches
                await asyncio.sleep(0.1)
        
        return self.analyze_results(results, "Burst Attack")
    
    async def sustained_attack(self, endpoint="/", duration_seconds=30, requests_per_second=20):
        """Simulate sustained DDoS attack - consistent high load"""
        self.print_header(f"SUSTAINED ATTACK SIMULATION - {requests_per_second} req/sec for {duration_seconds}s")
        
        results = []
        start_time = time.time()
        
        connector = aiohttp.TCPConnector(limit=100)
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            while time.time() - start_time < duration_seconds:
                # Send batch of requests
                tasks = [
                    self.single_request(session, endpoint)
                    for _ in range(requests_per_second)
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                results.extend([r for r in batch_results if not isinstance(r, Exception)])
                
                # Wait for next second
                await asyncio.sleep(1)
                elapsed = time.time() - start_time
                print(f"{elapsed:.1f}s: Sent {len(results)} total requests")
        
        return self.analyze_results(results, "Sustained Attack")
    
    async def distributed_attack(self, endpoint="/", num_ips=10, requests_per_ip=50):
        """Simulate distributed attack from multiple IPs"""
        self.print_header(f"DISTRIBUTED ATTACK SIMULATION - {num_ips} IPs, {requests_per_ip} requests each")
        
        # Generate fake IP addresses
        fake_ips = [f"192.168.{random.randint(1,255)}.{random.randint(1,255)}" for _ in range(num_ips)]
        
        results = []
        connector = aiohttp.TCPConnector(limit=200)
        timeout = aiohttp.ClientTimeout(total=20)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for ip in fake_ips:
                print(f"Attacking from IP: {ip}")
                
                # Create headers to simulate different IP
                headers = {
                    "X-Forwarded-For": ip,
                    "X-Real-IP": ip,
                    "User-Agent": f"AttackBot-{random.randint(1000,9999)}"
                }
                
                # Send requests from this "IP"
                for _ in range(requests_per_ip):
                    try:
                        url = f"{self.base_url}{endpoint}"
                        async with session.get(url, headers=headers) as response:
                            results.append({
                                "status": response.status,
                                "success": response.status not in [429, 500, 503],
                                "ip": ip
                            })
                    except Exception as e:
                        results.append({
                            "status": 0,
                            "success": False,
                            "ip": ip,
                            "error": str(e)
                        })
                
                await asyncio.sleep(0.1)  # Small delay between IPs
        
        return self.analyze_results(results, "Distributed Attack")
    
    async def slowloris_attack(self, endpoint="/", connections=50, duration=20):
        """Simulate Slowloris attack - slow, persistent connections"""
        self.print_header(f"SLOWLORIS ATTACK SIMULATION - {connections} slow connections for {duration}s")
        
        results = []
        start_time = time.time()
        
        # Use longer timeouts for slowloris
        timeout = aiohttp.ClientTimeout(total=duration + 10)
        connector = aiohttp.TCPConnector(limit=connections * 2)
        
        async def slow_request(session, delay):
            try:
                url = f"{self.base_url}{endpoint}"
                await asyncio.sleep(delay)  # Simulate slow client
                async with session.get(url) as response:
                    return {
                        "status": response.status,
                        "success": response.status not in [429, 500, 503],
                        "attack_type": "slowloris"
                    }
            except Exception as e:
                return {
                    "status": 0,
                    "success": False,
                    "attack_type": "slowloris",
                    "error": str(e)
                }
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Create slow requests with random delays
            tasks = [
                slow_request(session, random.uniform(0, duration))
                for _ in range(connections)
            ]
            
            print(f"Launching {connections} slow connections...")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            results = [r for r in results if not isinstance(r, Exception)]
        
        return self.analyze_results(results, "Slowloris Attack")
    
    async def auth_endpoint_attack(self, login_attempts=100):
        """Test rate limiting on authentication endpoints"""
        self.print_header(f"AUTHENTICATION ENDPOINT ATTACK - {login_attempts} login attempts")
        
        results = []
        connector = aiohttp.TCPConnector(limit=50)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            for i in range(login_attempts):
                fake_credentials = {
                    "username": f"attacker{i % 10}",
                    "password": f"password{i}"
                }
                
                result = await self.single_request(
                    session, 
                    "/v1/auth/login", 
                    method="POST", 
                    data=fake_credentials
                )
                results.append(result)
                
                if i % 20 == 0:
                    print(f"Attempted {i} login attacks...")
        
        return self.analyze_results(results, "Auth Endpoint Attack")
    
    def analyze_results(self, results, attack_type):
        """Analyze attack results and rate limiter effectiveness"""
        if not results:
            return {"attack_type": attack_type, "blocked": True, "effectiveness": "100%"}
        
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r.get("success", False))
        blocked_requests = total_requests - successful_requests
        rate_limited = sum(1 for r in results if r.get("status") == 429)
        
        # Calculate response times
        response_times = [r.get("response_time", 0) for r in results if r.get("response_time")]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Determine protection effectiveness
        block_rate = (blocked_requests / total_requests) * 100
        if block_rate > 90:
            effectiveness = "EXCELLENT"
        elif block_rate > 70:
            effectiveness = "GOOD"
        elif block_rate > 50:
            effectiveness = "MODERATE"
        else:
            effectiveness = "POOR"
        
        result = {
            "attack_type": attack_type,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "blocked_requests": blocked_requests,
            "rate_limited_429": rate_limited,
            "block_rate_percent": round(block_rate, 2),
            "avg_response_time": round(avg_response_time, 3),
            "effectiveness": effectiveness
        }
        
        self.print_results(result)
        return result
    
    def print_results(self, result):
        """Print attack results in a formatted way"""
        print(f"\n{result['attack_type']} Results:")
        print(f"Total Requests: {result['total_requests']}")
        print(f"Successful: {result['successful_requests']}")
        print(f"Blocked: {result['blocked_requests']}")
        print(f"429 Rate Limited: {result.get('rate_limited_429', 0)}")
        print(f"Block Rate: {result['block_rate_percent']}%")
        print(f"Avg Response Time: {result.get('avg_response_time', 0)}s")
        print(f"Protection Level: {result['effectiveness']}")
    
    async def run_comprehensive_ddos_test(self):
        """Run all DDoS attack simulations"""
        print("COMPREHENSIVE DDoS PROTECTION TESTING")
        print("="*60)
        print("WARNING: This will test your server's rate limiting!")
        print("Make sure your server is running: uvicorn main:app --reload")
        print("="*60)
        
        # Test server availability first
        try:
            connector = aiohttp.TCPConnector()
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(f"{self.base_url}/") as response:
                    if response.status == 404:
                        print("Server is running (404 is expected for root endpoint)")
                    else:
                        print(f"Server is running (status: {response.status})")
        except Exception as e:
            print(f"Server not accessible: {e}")
            print("Please start your server with: uvicorn main:app --reload")
            return
        
        all_results = []
        
        # Run different attack simulations
        attack_tests = [
            ("Burst Attack", self.burst_attack("/", 50, 200)),
            ("Sustained Attack", self.sustained_attack("/", 15, 15)),
            ("Distributed Attack", self.distributed_attack("/", 5, 20)),
            ("Auth Attack", self.auth_endpoint_attack(50)),
            ("Slowloris Attack", self.slowloris_attack("/", 20, 10)),
        ]
        
        for test_name, test_coro in attack_tests:
            try:
                print(f"\nStarting {test_name}...")
                result = await test_coro
                all_results.append(result)
                
                # Cool down between attacks
                print(f"Cooling down for 3 seconds...")
                await asyncio.sleep(3)
                
            except Exception as e:
                print(f"{test_name} failed: {e}")
                all_results.append({
                    "attack_type": test_name,
                    "error": str(e),
                    "effectiveness": "ERROR"
                })
        
        # Generate final report
        self.generate_final_report(all_results)
    
    def generate_final_report(self, results):
        """Generate comprehensive DDoS protection report"""
        self.print_header("FINAL DDoS PROTECTION REPORT")
        
        total_tests = len(results)
        excellent_protection = sum(1 for r in results if r.get("effectiveness") == "EXCELLENT")
        good_protection = sum(1 for r in results if r.get("effectiveness") == "GOOD")
        errors = sum(1 for r in results if r.get("effectiveness") == "ERROR")
        
        print(f"\nTEST SUMMARY:")
        print(f"Total Tests: {total_tests}")
        print(f"Excellent Protection: {excellent_protection}")
        print(f"Good Protection: {good_protection}")
        print(f"Errors: {errors}")
        
        # Overall protection score
        if excellent_protection >= 3:
            overall_score = "EXCELLENT - Production Ready!"
        elif excellent_protection + good_protection >= 3:
            overall_score = "GOOD - Well Protected!"
        else:
            overall_score = "NEEDS IMPROVEMENT - Consider Better Rate Limiting "
        
        print(f"\nOVERALL DDoS PROTECTION: {overall_score}")
        
        print(f"\nDETAILED RESULTS:")
        for result in results:
            if result.get("error"):
                print(f"{result['attack_type']}: ERROR - {result['error']}")
            else:
                print(f"{result['attack_type']}: {result['effectiveness']} "
                      f"({result.get('block_rate_percent', 0)}% blocked)")
        
        print(f"\nRECOMMENDATIONS:")
        if excellent_protection < 3:
            print("Consider implementing more aggressive rate limiting")
            print("Add IP-based blocking for repeated offenders")
            print("Consider using a CDN or DDoS protection service")
        else:
            print("Your rate limiting is working excellently!")
            print("Good protection against various DDoS attack patterns")
            print("Ready for production deployment")

# Main execution
async def main():
    simulator = DDoSAttackSimulator()
    await simulator.run_comprehensive_ddos_test()

if __name__ == "__main__":
    print("DDoS ATTACK SIMULATION STARTING...")
    print("Make sure your FastAPI server is running!")
    print("Start with: uvicorn main:app --reload")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDDoS simulation stopped by user")
    except Exception as e:
        print(f"\nError during simulation: {e}")
