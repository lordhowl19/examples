import requests
import sys
import json
from datetime import datetime

class BitoleStudiosAPITester:
    def __init__(self, base_url="https://phone-tracker-198.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.worker_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json() if response.text else {}
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                self.failed_tests.append({
                    "test": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:200]
                })
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "test": name,
                "error": str(e)
            })
            return False, {}

    def test_health_check(self):
        """Test API health check"""
        success, response = self.run_test(
            "API Health Check",
            "GET",
            "",
            200
        )
        return success

    def test_init_users(self):
        """Initialize default users"""
        success, response = self.run_test(
            "Initialize Users",
            "POST",
            "init-users",
            200
        )
        return success

    def test_admin_login(self):
        """Test admin login"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        if success and 'token' in response:
            self.admin_token = response['token']
            print(f"   Admin token obtained: {self.admin_token[:20]}...")
            return True
        return False

    def test_worker_login(self):
        """Test worker login (maria)"""
        success, response = self.run_test(
            "Worker Login (maria)",
            "POST",
            "auth/login",
            200,
            data={"username": "maria", "password": "maria123"}
        )
        if success and 'token' in response:
            self.worker_token = response['token']
            print(f"   Worker token obtained: {self.worker_token[:20]}...")
            return True
        return False

    def test_invalid_login(self):
        """Test invalid login credentials"""
        success, response = self.run_test(
            "Invalid Login",
            "POST",
            "auth/login",
            401,
            data={"username": "invalid", "password": "wrong"}
        )
        return success

    def test_get_me_admin(self):
        """Test get current user info for admin"""
        success, response = self.run_test(
            "Get Me (Admin)",
            "GET",
            "auth/me",
            200,
            token=self.admin_token
        )
        if success and response.get('role') == 'admin':
            print(f"   Admin user: {response.get('username')}")
            return True
        return False

    def test_get_me_worker(self):
        """Test get current user info for worker"""
        success, response = self.run_test(
            "Get Me (Worker)",
            "GET",
            "auth/me",
            200,
            token=self.worker_token
        )
        if success and response.get('role') == 'worker':
            print(f"   Worker user: {response.get('username')}")
            return True
        return False

    def test_get_users_admin(self):
        """Test get all users (admin only)"""
        success, response = self.run_test(
            "Get Users (Admin)",
            "GET",
            "users",
            200,
            token=self.admin_token
        )
        if success and isinstance(response, list):
            print(f"   Found {len(response)} users")
            return True
        return False

    def test_get_users_worker_forbidden(self):
        """Test get users with worker token (should fail)"""
        success, response = self.run_test(
            "Get Users (Worker - Should Fail)",
            "GET",
            "users",
            403,
            token=self.worker_token
        )
        return success

    def test_create_user(self):
        """Test creating a new user"""
        test_user = f"testuser_{datetime.now().strftime('%H%M%S')}"
        success, response = self.run_test(
            "Create User",
            "POST",
            "users",
            200,
            data={
                "username": test_user,
                "password": "testpass123",
                "role": "worker"
            },
            token=self.admin_token
        )
        if success:
            self.test_user_id = response.get('id')
            print(f"   Created user: {test_user} with ID: {self.test_user_id}")
            return True
        return False

    def test_create_missed_call(self):
        """Test creating a missed call"""
        success, response = self.run_test(
            "Create Missed Call",
            "POST",
            "missed-calls",
            200,
            data={
                "caller_phone": "6641234567",
                "call_time": datetime.now().isoformat()
            }
        )
        if success:
            self.test_call_id = response.get('id')
            print(f"   Created call with ID: {self.test_call_id}")
            return True
        return False

    def test_get_missed_calls(self):
        """Test getting missed calls"""
        success, response = self.run_test(
            "Get Missed Calls",
            "GET",
            "missed-calls",
            200,
            token=self.worker_token
        )
        if success and isinstance(response, list):
            print(f"   Found {len(response)} missed calls")
            return True
        return False

    def test_update_call_status(self):
        """Test updating call status"""
        if not hasattr(self, 'test_call_id'):
            print("   Skipping - no test call available")
            return True
            
        success, response = self.run_test(
            "Update Call Status",
            "PUT",
            f"missed-calls/{self.test_call_id}",
            200,
            data={"status": "contacted"},
            token=self.worker_token
        )
        if success and response.get('status') == 'contacted':
            print(f"   Updated call status to: contacted")
            return True
        return False

    def test_create_note(self):
        """Test creating a note for a call"""
        if not hasattr(self, 'test_call_id'):
            print("   Skipping - no test call available")
            return True
            
        success, response = self.run_test(
            "Create Note",
            "POST",
            "notes",
            200,
            data={
                "missed_call_id": self.test_call_id,
                "content": "Test note from automated testing"
            },
            token=self.worker_token
        )
        if success:
            self.test_note_id = response.get('id')
            print(f"   Created note with ID: {self.test_note_id}")
            return True
        return False

    def test_get_notes(self):
        """Test getting notes for a call"""
        if not hasattr(self, 'test_call_id'):
            print("   Skipping - no test call available")
            return True
            
        success, response = self.run_test(
            "Get Notes",
            "GET",
            f"notes/{self.test_call_id}",
            200,
            token=self.worker_token
        )
        if success and isinstance(response, list):
            print(f"   Found {len(response)} notes for call")
            return True
        return False

    def test_get_stats(self):
        """Test getting statistics"""
        success, response = self.run_test(
            "Get Stats",
            "GET",
            "stats",
            200,
            token=self.worker_token
        )
        if success and 'total_calls' in response:
            print(f"   Stats: {response.get('total_calls')} total calls, {response.get('pending_calls')} pending")
            return True
        return False

    def test_change_password(self):
        """Test changing user password (admin only)"""
        if not hasattr(self, 'test_user_id'):
            print("   Skipping - no test user available")
            return True
            
        success, response = self.run_test(
            "Change User Password",
            "PUT",
            f"users/{self.test_user_id}/password",
            200,
            data={"password": "newpassword123"},
            token=self.admin_token
        )
        return success

    def test_delete_user(self):
        """Test deleting a user (admin only)"""
        if not hasattr(self, 'test_user_id'):
            print("   Skipping - no test user available")
            return True
            
        success, response = self.run_test(
            "Delete User",
            "DELETE",
            f"users/{self.test_user_id}",
            200,
            token=self.admin_token
        )
        return success

def main():
    print("🚀 Starting Bitole Studios API Testing...")
    print("=" * 60)
    
    tester = BitoleStudiosAPITester()
    
    # Test sequence
    tests = [
        ("Health Check", tester.test_health_check),
        ("Initialize Users", tester.test_init_users),
        ("Admin Login", tester.test_admin_login),
        ("Worker Login", tester.test_worker_login),
        ("Invalid Login", tester.test_invalid_login),
        ("Get Me (Admin)", tester.test_get_me_admin),
        ("Get Me (Worker)", tester.test_get_me_worker),
        ("Get Users (Admin)", tester.test_get_users_admin),
        ("Get Users (Worker - Forbidden)", tester.test_get_users_worker_forbidden),
        ("Create User", tester.test_create_user),
        ("Create Missed Call", tester.test_create_missed_call),
        ("Get Missed Calls", tester.test_get_missed_calls),
        ("Update Call Status", tester.test_update_call_status),
        ("Create Note", tester.test_create_note),
        ("Get Notes", tester.test_get_notes),
        ("Get Stats", tester.test_get_stats),
        ("Change Password", tester.test_change_password),
        ("Delete User", tester.test_delete_user),
    ]
    
    # Run all tests
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} - Exception: {str(e)}")
            tester.failed_tests.append({
                "test": test_name,
                "error": str(e)
            })
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.failed_tests:
        print(f"\n❌ FAILED TESTS ({len(tester.failed_tests)}):")
        for i, failure in enumerate(tester.failed_tests, 1):
            print(f"{i}. {failure.get('test', 'Unknown')}")
            if 'error' in failure:
                print(f"   Error: {failure['error']}")
            elif 'expected' in failure:
                print(f"   Expected: {failure['expected']}, Got: {failure['actual']}")
                if failure.get('response'):
                    print(f"   Response: {failure['response']}")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())