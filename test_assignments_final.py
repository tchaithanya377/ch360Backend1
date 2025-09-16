#!/usr/bin/env python3
"""
Final comprehensive test script for the enhanced Assignment Management System
Tests all API endpoints with proper authentication and sample data
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
import sys

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api/v1"

class FinalAssignmentTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_objects = {}
        self.auth_token = None
        
    def authenticate(self):
        """Authenticate with the system using test user"""
        try:
            auth_data = {
                "email": "test@example.com",
                "password": "testpass123"
            }
            
            response = self.session.post(f"{BASE_URL}/api/auth/token/", json=auth_data)
            if response.status_code == 200:
                auth_result = response.json()
                self.auth_token = auth_result.get('access')
                if self.auth_token:
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.auth_token}'
                    })
                    self.log_test("Authentication", True, "Successfully authenticated with test user")
                    return True
            
            self.log_test("Authentication", False, f"Login failed: {response.text}")
            return False
            
        except Exception as e:
            self.log_test("Authentication", False, f"Authentication exception: {str(e)}")
            return False
    
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
        
    def test_assignment_categories(self):
        """Test assignment categories API"""
        try:
            # Test GET categories
            response = self.session.get(f"{API_BASE}/assignments/categories/")
            if response.status_code == 200:
                categories = response.json()
                self.log_test("Get Assignment Categories", True, f"Found {len(categories)} categories", categories)
                
                # Test creating a new category
                new_category = {
                    "name": "Final Test Category",
                    "description": "Final test category for comprehensive testing",
                    "color_code": "#FF5733",
                    "is_active": True
                }
                response = self.session.post(f"{API_BASE}/assignments/categories/", json=new_category)
                if response.status_code == 201:
                    category_data = response.json()
                    self.created_objects['test_category'] = category_data['id']
                    self.log_test("Create Assignment Category", True, "Category created successfully", category_data)
                    
                    # Test GET specific category
                    response = self.session.get(f"{API_BASE}/assignments/categories/{category_data['id']}/")
                    if response.status_code == 200:
                        category_detail = response.json()
                        self.log_test("Get Assignment Category Detail", True, "Category detail retrieved", category_detail)
                    else:
                        self.log_test("Get Assignment Category Detail", False, f"Failed to get category detail: {response.text}")
                        
                else:
                    self.log_test("Create Assignment Category", False, f"Failed to create category: {response.text}")
            else:
                self.log_test("Get Assignment Categories", False, f"Failed to get categories: {response.text}")
        except Exception as e:
            self.log_test("Assignment Categories Test", False, f"Exception: {str(e)}")
    
    def test_assignment_rubrics(self):
        """Test assignment rubrics API"""
        try:
            # Test GET rubrics
            response = self.session.get(f"{API_BASE}/assignments/rubrics/")
            if response.status_code == 200:
                rubrics = response.json()
                self.log_test("Get Assignment Rubrics", True, f"Found {len(rubrics)} rubrics", rubrics)
                
                # Test creating a new rubric
                test_rubric = {
                    "name": "Final Test Rubric",
                    "description": "Comprehensive rubric for final testing",
                    "rubric_type": "ANALYTIC",
                    "total_points": 100,
                    "is_public": True,
                    "criteria": [
                        {
                            "name": "Content Quality",
                            "description": "Quality and depth of content",
                            "points": 40,
                            "weight": 0.40
                        },
                        {
                            "name": "Presentation",
                            "description": "Clarity and organization",
                            "points": 30,
                            "weight": 0.30
                        },
                        {
                            "name": "Originality",
                            "description": "Originality and creativity",
                            "points": 30,
                            "weight": 0.30
                        }
                    ]
                }
                response = self.session.post(f"{API_BASE}/assignments/rubrics/", json=test_rubric)
                if response.status_code == 201:
                    rubric_data = response.json()
                    self.created_objects['test_rubric'] = rubric_data['id']
                    self.log_test("Create Assignment Rubric", True, "Rubric created successfully", rubric_data)
                    
                    # Test GET specific rubric
                    response = self.session.get(f"{API_BASE}/assignments/rubrics/{rubric_data['id']}/")
                    if response.status_code == 200:
                        rubric_detail = response.json()
                        self.log_test("Get Assignment Rubric Detail", True, "Rubric detail retrieved", rubric_detail)
                    else:
                        self.log_test("Get Assignment Rubric Detail", False, f"Failed to get rubric detail: {response.text}")
                        
                else:
                    self.log_test("Create Assignment Rubric", False, f"Failed to create rubric: {response.text}")
            else:
                self.log_test("Get Assignment Rubrics", False, f"Failed to get rubrics: {response.text}")
        except Exception as e:
            self.log_test("Assignment Rubrics Test", False, f"Exception: {str(e)}")
    
    def test_assignments_crud(self):
        """Test assignments CRUD operations"""
        try:
            # Test GET assignments
            response = self.session.get(f"{API_BASE}/assignments/")
            if response.status_code == 200:
                assignments = response.json()
                self.log_test("Get Assignments", True, f"Found {len(assignments)} assignments", assignments)
                
                # Test GET my assignments
                response = self.session.get(f"{API_BASE}/assignments/my-assignments/")
                if response.status_code == 200:
                    my_assignments = response.json()
                    self.log_test("Get My Assignments", True, f"Found {len(my_assignments)} my assignments", my_assignments)
                else:
                    self.log_test("Get My Assignments", False, f"Failed to get my assignments: {response.text}")
                    
            else:
                self.log_test("Get Assignments", False, f"Failed to get assignments: {response.text}")
        except Exception as e:
            self.log_test("Assignments CRUD Test", False, f"Exception: {str(e)}")
    
    def test_assignment_analytics(self):
        """Test assignment analytics API"""
        try:
            # First get assignments to find one to test analytics
            response = self.session.get(f"{API_BASE}/assignments/")
            if response.status_code == 200:
                assignments = response.json()
                if assignments:
                    assignment_id = assignments[0]['id']
                    response = self.session.get(f"{API_BASE}/assignments/{assignment_id}/analytics/")
                    if response.status_code == 200:
                        analytics = response.json()
                        self.log_test("Get Assignment Analytics", True, "Analytics retrieved successfully", analytics)
                    else:
                        self.log_test("Get Assignment Analytics", False, f"Failed to get analytics: {response.text}")
                else:
                    self.log_test("Get Assignment Analytics", False, "No assignments available for analytics test")
            else:
                self.log_test("Get Assignment Analytics", False, "Failed to get assignments for analytics test")
        except Exception as e:
            self.log_test("Assignment Analytics Test", False, f"Exception: {str(e)}")
    
    def test_assignment_notifications(self):
        """Test assignment notifications API"""
        try:
            # Test GET notifications
            response = self.session.get(f"{API_BASE}/assignments/notifications/")
            if response.status_code == 200:
                notifications = response.json()
                self.log_test("Get Assignment Notifications", True, f"Found {len(notifications)} notifications", notifications)
                
                # Test creating a new notification
                notification_data = {
                    "notification_type": "ASSIGNMENT_CREATED",
                    "title": "Final Test Notification",
                    "message": "A new assignment has been created for testing",
                    "is_read": False,
                    "context_data": {"assignment_id": "test-assignment-id"}
                }
                response = self.session.post(f"{API_BASE}/assignments/notifications/", json=notification_data)
                if response.status_code == 201:
                    notification_result = response.json()
                    self.created_objects['test_notification'] = notification_result['id']
                    self.log_test("Create Assignment Notification", True, "Notification created successfully", notification_result)
                else:
                    self.log_test("Create Assignment Notification", False, f"Failed to create notification: {response.text}")
            else:
                self.log_test("Get Assignment Notifications", False, f"Failed to get notifications: {response.text}")
        except Exception as e:
            self.log_test("Assignment Notifications Test", False, f"Exception: {str(e)}")
    
    def test_assignment_schedules(self):
        """Test assignment schedules API"""
        try:
            # Test GET schedules
            response = self.session.get(f"{API_BASE}/assignments/schedules/")
            if response.status_code == 200:
                schedules = response.json()
                self.log_test("Get Assignment Schedules", True, f"Found {len(schedules)} schedules", schedules)
                
                # Test creating a new schedule
                schedule_data = {
                    "name": "Final Test Schedule",
                    "description": "Automated test schedule creation",
                    "frequency": "WEEKLY",
                    "interval": 1,
                    "start_date": datetime.now().isoformat(),
                    "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
                    "is_active": True
                }
                response = self.session.post(f"{API_BASE}/assignments/schedules/", json=schedule_data)
                if response.status_code == 201:
                    schedule_result = response.json()
                    self.created_objects['test_schedule'] = schedule_result['id']
                    self.log_test("Create Assignment Schedule", True, "Schedule created successfully", schedule_result)
                else:
                    self.log_test("Create Assignment Schedule", False, f"Failed to create schedule: {response.text}")
            else:
                self.log_test("Get Assignment Schedules", False, f"Failed to get schedules: {response.text}")
        except Exception as e:
            self.log_test("Assignment Schedules Test", False, f"Exception: {str(e)}")
    
    def test_peer_reviews(self):
        """Test peer review functionality"""
        try:
            # First get assignments to find one to test peer reviews
            response = self.session.get(f"{API_BASE}/assignments/")
            if response.status_code == 200:
                assignments = response.json()
                if assignments:
                    assignment_id = assignments[0]['id']
                    
                    # Test GET peer reviews for assignment
                    response = self.session.get(f"{API_BASE}/assignments/{assignment_id}/peer-reviews/")
                    if response.status_code == 200:
                        peer_reviews = response.json()
                        self.log_test("Get Assignment Peer Reviews", True, f"Found {len(peer_reviews)} peer reviews", peer_reviews)
                    else:
                        self.log_test("Get Assignment Peer Reviews", False, f"Failed to get peer reviews: {response.text}")
                        
                    # Test assign peer reviews
                    response = self.session.post(f"{API_BASE}/assignments/{assignment_id}/assign-peer-reviews/")
                    if response.status_code in [200, 201]:
                        assign_result = response.json()
                        self.log_test("Assign Peer Reviews", True, "Peer reviews assigned successfully", assign_result)
                    else:
                        self.log_test("Assign Peer Reviews", False, f"Failed to assign peer reviews: {response.text}")
                else:
                    self.log_test("Peer Reviews Test", False, "No assignments available for peer review test")
            else:
                self.log_test("Peer Reviews Test", False, "Failed to get assignments for peer review test")
        except Exception as e:
            self.log_test("Peer Reviews Test", False, f"Exception: {str(e)}")
    
    def test_plagiarism_checks(self):
        """Test plagiarism check functionality"""
        try:
            # First get assignments to find one to test plagiarism checks
            response = self.session.get(f"{API_BASE}/assignments/")
            if response.status_code == 200:
                assignments = response.json()
                if assignments:
                    assignment_id = assignments[0]['id']
                    
                    # Test GET plagiarism checks for assignment
                    response = self.session.get(f"{API_BASE}/assignments/{assignment_id}/plagiarism-checks/")
                    if response.status_code == 200:
                        plagiarism_checks = response.json()
                        self.log_test("Get Assignment Plagiarism Checks", True, f"Found {len(plagiarism_checks)} plagiarism checks", plagiarism_checks)
                    else:
                        self.log_test("Get Assignment Plagiarism Checks", False, f"Failed to get plagiarism checks: {response.text}")
                else:
                    self.log_test("Plagiarism Checks Test", False, "No assignments available for plagiarism check test")
            else:
                self.log_test("Plagiarism Checks Test", False, "Failed to get assignments for plagiarism check test")
        except Exception as e:
            self.log_test("Plagiarism Checks Test", False, f"Exception: {str(e)}")
    
    def test_learning_outcomes(self):
        """Test learning outcomes functionality"""
        try:
            # First get assignments to find one to test learning outcomes
            response = self.session.get(f"{API_BASE}/assignments/")
            if response.status_code == 200:
                assignments = response.json()
                if assignments:
                    assignment_id = assignments[0]['id']
                    
                    # Test GET learning outcomes for assignment
                    response = self.session.get(f"{API_BASE}/assignments/{assignment_id}/learning-outcomes/")
                    if response.status_code == 200:
                        learning_outcomes = response.json()
                        self.log_test("Get Assignment Learning Outcomes", True, f"Found {len(learning_outcomes)} learning outcomes", learning_outcomes)
                        
                        # Test creating a new learning outcome
                        outcome_data = {
                            "outcome": "Students will understand advanced machine learning concepts",
                            "bloom_taxonomy_level": "ANALYZE",
                            "weight": 0.4,
                            "achievement_threshold": 75.0
                        }
                        response = self.session.post(f"{API_BASE}/assignments/{assignment_id}/learning-outcomes/", json=outcome_data)
                        if response.status_code == 201:
                            outcome_result = response.json()
                            self.created_objects['test_learning_outcome'] = outcome_result['id']
                            self.log_test("Create Learning Outcome", True, "Learning outcome created successfully", outcome_result)
                        else:
                            self.log_test("Create Learning Outcome", False, f"Failed to create learning outcome: {response.text}")
                    else:
                        self.log_test("Get Assignment Learning Outcomes", False, f"Failed to get learning outcomes: {response.text}")
                else:
                    self.log_test("Learning Outcomes Test", False, "No assignments available for learning outcome test")
            else:
                self.log_test("Learning Outcomes Test", False, "Failed to get assignments for learning outcome test")
        except Exception as e:
            self.log_test("Learning Outcomes Test", False, f"Exception: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        try:
            # Test invalid assignment ID
            response = self.session.get(f"{API_BASE}/assignments/invalid-uuid/")
            if response.status_code == 404:
                self.log_test("Error Handling - Invalid Assignment ID", True, "Correctly returned 404 for invalid ID")
            else:
                self.log_test("Error Handling - Invalid Assignment ID", False, f"Expected 404, got {response.status_code}")
            
            # Test invalid rubric ID
            response = self.session.get(f"{API_BASE}/assignments/rubrics/invalid-uuid/")
            if response.status_code == 404:
                self.log_test("Error Handling - Invalid Rubric ID", True, "Correctly returned 404 for invalid ID")
            else:
                self.log_test("Error Handling - Invalid Rubric ID", False, f"Expected 404, got {response.status_code}")
            
            # Test invalid data for assignment creation
            invalid_assignment = {
                "title": "",  # Empty title should fail
                "max_marks": -10,  # Negative marks should fail
            }
            response = self.session.post(f"{API_BASE}/assignments/", json=invalid_assignment)
            if response.status_code == 400:
                self.log_test("Error Handling - Invalid Assignment Data", True, "Correctly returned 400 for invalid data")
            else:
                self.log_test("Error Handling - Invalid Assignment Data", False, f"Expected 400, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Error Handling Test", False, f"Exception: {str(e)}")
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        try:
            # Delete created objects in reverse order
            for obj_type, obj_id in reversed(list(self.created_objects.items())):
                if obj_type == 'test_assignment':
                    response = self.session.delete(f"{API_BASE}/assignments/{obj_id}/")
                elif obj_type == 'test_rubric':
                    response = self.session.delete(f"{API_BASE}/assignments/rubrics/{obj_id}/")
                elif obj_type == 'test_category':
                    response = self.session.delete(f"{API_BASE}/assignments/categories/{obj_id}/")
                elif obj_type == 'test_notification':
                    response = self.session.delete(f"{API_BASE}/assignments/notifications/{obj_id}/")
                elif obj_type == 'test_schedule':
                    response = self.session.delete(f"{API_BASE}/assignments/schedules/{obj_id}/")
                elif obj_type == 'test_learning_outcome':
                    # Learning outcomes are deleted with assignments, so skip
                    continue
                
                if response.status_code in [200, 204, 404]:
                    self.log_test(f"Cleanup {obj_type}", True, f"Successfully deleted {obj_type}")
                else:
                    self.log_test(f"Cleanup {obj_type}", False, f"Failed to delete {obj_type}: {response.text}")
        except Exception as e:
            self.log_test("Cleanup Test Data", False, f"Exception during cleanup: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Final Comprehensive Assignment Management System Tests")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Please check credentials.")
            return False
        
        # Run all tests
        self.test_assignment_categories()
        self.test_assignment_rubrics()
        self.test_assignments_crud()
        self.test_assignment_analytics()
        self.test_assignment_notifications()
        self.test_assignment_schedules()
        self.test_peer_reviews()
        self.test_plagiarism_checks()
        self.test_learning_outcomes()
        self.test_error_handling()
        
        # Clean up test data
        print("\n🧹 Cleaning up test data...")
        self.cleanup_test_data()
        
        # Generate test report
        self.generate_test_report()
        
        return True
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("📊 FINAL COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        
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
        report_file = f"assignment_final_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    tester = FinalAssignmentTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
