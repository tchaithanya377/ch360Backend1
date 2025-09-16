#!/usr/bin/env python3
"""
Basic test script for the enhanced Assignment Management System
Tests basic functionality without authentication
"""

import requests
import json
from datetime import datetime
import sys

# Configuration
BASE_URL = "http://127.0.0.1:8000"

class BasicAssignmentTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, success, message="", data=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
    def test_server_health(self):
        """Test if server is running"""
        try:
            response = self.session.get(f"{BASE_URL}/admin/")
            if response.status_code == 200:
                self.log_test("Server Health Check", True, "Server is running")
                return True
            else:
                self.log_test("Server Health Check", False, f"Server returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Server Health Check", False, f"Server connection failed: {str(e)}")
            return False
    
    def test_admin_interface(self):
        """Test admin interface accessibility"""
        try:
            # Test admin login page
            response = self.session.get(f"{BASE_URL}/admin/login/")
            if response.status_code == 200:
                self.log_test("Admin Login Page", True, "Admin login page accessible")
            else:
                self.log_test("Admin Login Page", False, f"Admin login page returned status {response.status_code}")
            
            # Test admin interface (should redirect to login)
            response = self.session.get(f"{BASE_URL}/admin/")
            if response.status_code in [200, 302]:
                self.log_test("Admin Interface", True, "Admin interface accessible")
            else:
                self.log_test("Admin Interface", False, f"Admin interface returned status {response.status_code}")
                
        except Exception as e:
            self.log_test("Admin Interface Test", False, f"Exception: {str(e)}")
    
    def test_api_endpoints_exist(self):
        """Test that API endpoints exist (even if they require auth)"""
        endpoints_to_test = [
            "/api/v1/assignments/",
            "/api/v1/assignments/categories/",
            "/api/v1/assignments/rubrics/",
            "/api/v1/assignments/notifications/",
            "/api/v1/assignments/schedules/",
            "/api/auth/token/",
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                # We expect 401 (Unauthorized) or 405 (Method Not Allowed) for protected endpoints
                if response.status_code in [200, 401, 403, 405]:
                    self.log_test(f"API Endpoint {endpoint}", True, f"Endpoint exists (status: {response.status_code})")
                else:
                    self.log_test(f"API Endpoint {endpoint}", False, f"Unexpected status: {response.status_code}")
            except Exception as e:
                self.log_test(f"API Endpoint {endpoint}", False, f"Exception: {str(e)}")
    
    def test_database_models(self):
        """Test database models through Django shell"""
        try:
            import subprocess
            result = subprocess.run([
                'python', 'manage.py', 'shell', '-c',
                '''
from assignments.models import *
print("Assignment Categories:", AssignmentCategory.objects.count())
print("Assignment Rubrics:", AssignmentRubric.objects.count())
print("Assignments:", Assignment.objects.count())
print("Assignment Submissions:", AssignmentSubmission.objects.count())
print("Assignment Analytics:", AssignmentAnalytics.objects.count())
print("Assignment Notifications:", AssignmentNotification.objects.count())
print("Assignment Schedules:", AssignmentSchedule.objects.count())
print("Assignment Learning Outcomes:", AssignmentLearningOutcome.objects.count())
print("Assignment Peer Reviews:", AssignmentPeerReview.objects.count())
print("Assignment Plagiarism Checks:", AssignmentPlagiarismCheck.objects.count())
                '''
            ], capture_output=True, text=True, cwd='.')
            
            if result.returncode == 0:
                self.log_test("Database Models", True, "All models accessible", result.stdout)
            else:
                self.log_test("Database Models", False, f"Error: {result.stderr}")
                
        except Exception as e:
            self.log_test("Database Models Test", False, f"Exception: {str(e)}")
    
    def test_migrations(self):
        """Test that migrations are applied"""
        try:
            import subprocess
            result = subprocess.run([
                'python', 'manage.py', 'showmigrations', 'assignments'
            ], capture_output=True, text=True, cwd='.')
            
            if result.returncode == 0:
                # Check if all migrations are applied
                lines = result.stdout.split('\n')
                applied_migrations = [line for line in lines if '[X]' in line]
                total_migrations = [line for line in lines if '[' in line and ']' in line]
                
                if len(applied_migrations) == len(total_migrations) and len(total_migrations) > 0:
                    self.log_test("Migrations", True, f"All {len(applied_migrations)} migrations applied")
                else:
                    self.log_test("Migrations", False, f"Some migrations not applied: {len(applied_migrations)}/{len(total_migrations)}")
            else:
                self.log_test("Migrations", False, f"Error: {result.stderr}")
                
        except Exception as e:
            self.log_test("Migrations Test", False, f"Exception: {str(e)}")
    
    def test_management_commands(self):
        """Test management commands"""
        try:
            import subprocess
            result = subprocess.run([
                'python', 'manage.py', 'setup_ap_assignment_features'
            ], capture_output=True, text=True, cwd='.')
            
            if result.returncode == 0:
                self.log_test("Management Commands", True, "AP setup command executed successfully", result.stdout)
            else:
                self.log_test("Management Commands", False, f"Error: {result.stderr}")
                
        except Exception as e:
            self.log_test("Management Commands Test", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Basic Assignment Management System Tests")
        print("=" * 60)
        
        # Test server health first
        if not self.test_server_health():
            print("❌ Server is not running. Please start the Django server first.")
            return False
        
        # Run all tests
        self.test_admin_interface()
        self.test_api_endpoints_exist()
        self.test_database_models()
        self.test_migrations()
        self.test_management_commands()
        
        # Generate test report
        self.generate_test_report()
        
        return True
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 BASIC TEST REPORT SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result['success']:
                print(f"  - {result['test']}: {result['message']}")
        
        # Save detailed report to file
        report_file = f"assignment_basic_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    tester = BasicAssignmentTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
