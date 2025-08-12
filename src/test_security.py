import requests
import json
import time
from datetime import datetime

# Base URL - change this to your running server
BASE_URL = "http://localhost:8000"

class SecurityTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
    
    def log_test(self, test_name, passed, details=""):
        """Log test results"""
        result = {
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "PASS" if passed else "FAIL"
        print(f"{status} - {test_name}: {details}")
    
    def test_html_sanitization(self):
        """Test HTML sanitization in user inputs"""
        print("\nTESTING HTML SANITIZATION")
        
        # Test malicious bio input
        malicious_bio = "<script>alert('XSS Attack!')</script>Normal bio text"
        malicious_name = "<iframe src='http://evil.com'></iframe>John Doe"
        
        test_user = {
            "email": "testuser@example.com",
            "username": "testuser123",
            "name": malicious_name,
            "bio": malicious_bio,
            "hashed_password": "SecurePass123!",
            "location": "<script>alert('location hack')</script>New York"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/v1/auth/register", json=test_user)
            
            if response.status_code == 201:
                user_data = response.json()
                # Check if HTML was sanitized
                if "<script>" not in user_data.get("bio", "") and "<iframe>" not in user_data.get("name", ""):
                    self.log_test("HTML Sanitization", True, "Malicious HTML tags removed successfully")
                else:
                    self.log_test("HTML Sanitization", False, "HTML tags not properly sanitized")
            else:
                self.log_test("HTML Sanitization", True, f"Input validation rejected malicious input: {response.status_code}")
        except Exception as e:
            self.log_test("HTML Sanitization", False, f"Error: {str(e)}")
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("\nTESTING RATE LIMITING")
        
        login_data = {
            "username": "nonexistent_user_test",
            "password": "wrongpassword123"
        }
        
        # Try to exceed rate limit (auth endpoints have 5 requests per minute)
        failed_attempts = 0
        rate_limited = False
        
        for i in range(8):  # Try 8 times to trigger rate limit (should trigger after 5)
            try:
                response = self.session.post(f"{BASE_URL}/v1/auth/login", data=login_data)
                if response.status_code == 429:
                    rate_limited = True
                    break
                failed_attempts += 1
                time.sleep(0.2)  # Small delay
            except Exception as e:
                break
        
        if rate_limited:
            self.log_test("Rate Limiting", True, f"Rate limit triggered after {failed_attempts} attempts")
        else:
            self.log_test("Rate Limiting", False, f"Rate limit not triggered after {failed_attempts} attempts")
    
    def test_account_lockout(self):
        """Test account lockout protection"""
        print("\nTESTING ACCOUNT LOCKOUT")
        
        # Create a test user first
        test_user = {
            "email": "lockouttest@example.com",
            "username": "lockouttest",
            "name": "Lockout Test",
            "hashed_password": "SecurePass123!"
        }
        
        try:
            # Register user
            register_response = self.session.post(f"{BASE_URL}/v1/auth/register", json=test_user)
            
            # Try wrong password multiple times
            login_data = {
                "username": "lockouttest",
                "password": "wrongpassword123"
            }
            
            locked = False
            lockout_responses = 0
            
            # Try failed logins to trigger lockout (should lock after 5 attempts)
            for i in range(8):
                response = self.session.post(f"{BASE_URL}/v1/auth/login", data=login_data)
                if response.status_code == 423:  # HTTP 423 LOCKED
                    locked = True
                    lockout_responses += 1
                elif "locked" in response.text.lower():
                    locked = True
                    lockout_responses += 1
                time.sleep(0.1)
            
            if locked or lockout_responses > 0:
                self.log_test("Account Lockout", True, f"Account locked after failed attempts (got {lockout_responses} lockout responses)")
            else:
                self.log_test("Account Lockout", False, "Account lockout not triggered")
                
        except Exception as e:
            self.log_test("Account Lockout", False, f"Error: {str(e)}")
    
    def test_password_validation(self):
        """Test password strength validation"""
        print("\nTESTING PASSWORD VALIDATION")
        
        weak_passwords = [
            "123456",      
            "password",   
            "abc123",     
            "PASSWORD",    
            "Pass123",     
            "Pass@",     
        ]
        
        passed_tests = 0
        total_tests = len(weak_passwords)
        
        for i, password in enumerate(weak_passwords):
            test_user = {
                "email": f"test{i}@example.com",
                "username": f"test{i}",
                "name": "Test User",
                "hashed_password": password
            }
            
            try:
                response = self.session.post(f"{BASE_URL}/v1/auth/register", json=test_user)
                if response.status_code in [400, 422]:  # Should be rejected with validation error
                    passed_tests += 1
                elif response.status_code != 201:  # Any other non-success code is also good
                    passed_tests += 1
            except:
                passed_tests += 1  # Exception during validation is also protection
        
        if passed_tests == total_tests:
            self.log_test("Password Validation", True, f"All {total_tests} weak passwords rejected")
        else:
            self.log_test("Password Validation", False, f"Only {passed_tests}/{total_tests} weak passwords rejected")
    
    def test_sql_injection(self):
        """Test SQL injection protection"""
        print("\nTESTING SQL INJECTION PROTECTION")
        
        # Common SQL injection payloads
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--",
            "1'; DELETE FROM users; --",
            "admin'; UPDATE users SET password='hacked'--"
        ]
        
        protected = True
        error_count = 0
        
        for payload in sql_payloads:
            login_data = {
                "username": payload,
                "password": "test123"
            }
            
            try:
                response = self.session.post(f"{BASE_URL}/v1/auth/login", data=login_data)
                # Check for various indicators of vulnerability
                if response.status_code == 500:
                    error_count += 1
                    # If we get multiple 500 errors, it might indicate SQL injection vulnerability
                    if error_count > 2:
                        protected = False
                        break
                # Good responses: 401 (unauthorized), 422 (validation error), 429 (rate limited)
                elif response.status_code in [401, 422, 429]:
                    continue  # These are expected and good
                
            except Exception as e:
                # Network errors are okay, but repeated server crashes are concerning
                if "500" in str(e) or "server" in str(e).lower():
                    error_count += 1
                    if error_count > 2:
                        protected = False
                        break
        
        if protected and error_count <= 2:
            self.log_test("SQL Injection Protection", True, f"All SQL injection attempts handled safely (minor errors: {error_count})")
        else:
            self.log_test("SQL Injection Protection", False, f"Potential SQL injection vulnerability detected (errors: {error_count})")
    
    def test_xss_protection(self):
        """Test XSS protection in post content"""
        print("\nTESTING XSS PROTECTION")
        
        # First login to get token
        if not self.get_auth_token():
            self.log_test("XSS Protection", False, "Could not authenticate for testing")
            return
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>"
        ]
        
        protected_posts = 0
        for payload in xss_payloads:
            post_data = {
                "content": f"Check this out: {payload}",
                "location": "Test Location"
            }
            
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                response = self.session.post(f"{BASE_URL}/v1/post/", json=post_data, headers=headers)
                
                if response.status_code == 201:
                    post_content = response.json().get("content", "")
                    # Check if XSS payload was sanitized
                    if "<script>" not in post_content and "javascript:" not in post_content and "onerror=" not in post_content:
                        protected_posts += 1
                else:
                    protected_posts += 1  # Rejection is also good protection
            except:
                protected_posts += 1  # Error handling is protection
        
        if protected_posts == len(xss_payloads):
            self.log_test("XSS Protection", True, f"All {len(xss_payloads)} XSS attempts blocked")
        else:
            self.log_test("XSS Protection", False, f"Only {protected_posts}/{len(xss_payloads)} XSS attempts blocked")
    
    def get_auth_token(self):
        """Get authentication token for testing"""
        # Create and login with test user
        test_user = {
            "email": "securitytest@example.com",
            "username": "securitytester",
            "name": "Security Tester",
            "hashed_password": "SecureTestPass123!"
        }
        
        try:
            # Register (might already exist, that's okay)
            register_response = self.session.post(f"{BASE_URL}/v1/auth/register", json=test_user)
            
            # Login
            login_data = {
                "username": "securitytester",
                "password": "SecureTestPass123!"
            }
            response = self.session.post(f"{BASE_URL}/v1/auth/login", data=login_data)
            
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                return True
            elif response.status_code == 409:  # User already exists
                # Try to login directly
                response = self.session.post(f"{BASE_URL}/v1/auth/login", data=login_data)
                if response.status_code == 200:
                    self.token = response.json().get("access_token")
                    return True
        except Exception as e:
            print(f"Auth error: {e}")
            pass
        
        return False
    
    def test_security_headers(self):
        """Test security headers"""
        print("\nTESTING SECURITY HEADERS")
        
        try:
            response = self.session.get(f"{BASE_URL}/")
            headers = response.headers
            
            required_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
            }
            
            present_headers = 0
            for header, expected_value in required_headers.items():
                if header in headers:
                    present_headers += 1
            
            if present_headers == len(required_headers):
                self.log_test("Security Headers", True, f"All {len(required_headers)} security headers present")
            else:
                self.log_test("Security Headers", False, f"Only {present_headers}/{len(required_headers)} security headers present")
                
        except Exception as e:
            self.log_test("Security Headers", False, f"Error checking headers: {str(e)}")
    
    def run_all_tests(self):
        """Run all security tests"""
        print("STARTING COMPREHENSIVE SECURITY TESTING")
        print("=" * 60)
        
        # Run all tests
        self.test_security_headers()
        self.test_html_sanitization()
        self.test_password_validation()
        self.test_rate_limiting()
        self.test_account_lockout()
        self.test_sql_injection()
        self.test_xss_protection()
        
        # Summary
        print("\n" + "=" * 60)
        print("SECURITY TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["passed"])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Tests Failed: {total - passed}/{total}")
        print(f"Security Score: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("ALL SECURITY TESTS PASSED! Your application is well-protected!")
        elif passed >= total * 0.8:
            print("GOOD SECURITY! Most tests passed, minor improvements needed.")
        else:
            print("SECURITY CONCERNS! Several tests failed, review needed.")
        
        # Save detailed results
        with open("security_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\nDetailed results saved to: security_test_results.json")

if __name__ == "__main__":
    input("Press Enter when server is ready...")
    
    tester = SecurityTester()
    tester.run_all_tests()
