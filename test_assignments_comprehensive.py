#!/usr/bin/env python3
"""
Comprehensive test script for the enhanced Assignment Management System
Tests all API endpoints with various test cases and sample data
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
import sys

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test data
SAMPLE_DATA = {
    "faculty_email": "admin@mits.ac.in",
    "student_email": "student@mits.ac.in",
    "test_assignment": {
        "title": "AP Research Project - Machine Learning Applications",
        "description": "A comprehensive research project on machine learning applications in healthcare",
        "instructions": "Research and analyze machine learning applications in healthcare sector. Submit a detailed report with case studies.",
        "assignment_type": "RESEARCH_PAPER",
        "difficulty_level": "ADVANCED",
        "max_marks": 100.00,
        "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "late_submission_allowed": True,
        "late_penalty_percentage": 10.00,
        "is_apaar_compliant": True,
        "requires_plagiarism_check": True,
        "plagiarism_threshold": 15.00,
        "enable_peer_review": True,
        "peer_review_weight": 20.00,
        "learning_objectives": "Students will understand machine learning concepts, analyze real-world applications, and develop critical thinking skills",
        "estimated_time_hours": 40,
        "submission_reminder_days": 3
    },
    "test_rubric": {
        "name": "AP Research Project Test Rubric",
        "description": "Comprehensive rubric for research project assessment",
        "rubric_type": "ANALYTIC",
        "total_points": 100,
        "is_public": True,
        "criteria": [
            {
                "name": "Research Quality",
                "description": "Depth and quality of research",
                "points": 30,
                "weight": 0.30
            },
            {
                "name": "Analysis",
                "description": "Critical analysis and insights",
                "points": 25,
                "weight": 0.25
            },
            {
                "name": "Presentation",
                "description": "Clarity and organization of presentation",
                "points": 20,
                "weight": 0.20
            },
            {
                "name": "References",
                "description": "Quality and relevance of references",
                "points": 15,
                "weight": 0.15
            },
            {
                "name": "Innovation",
                "description": "Originality and innovation in approach",
                "points": 10,
                "weight": 0.10
            }
        ]
    }
}

class AssignmentTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_objects = {}
        
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
                    "name": "Test Category",
                    "description": "Test category for API testing",
                    "is_active": True
                }
                response = self.session.post(f"{API_BASE}/assignments/categories/", json=new_category)
                if response.status_code == 201:
                    category_data = response.json()
                    self.created_objects['test_category'] = category_data['id']
                    self.log_test("Create Assignment Category", True, "Category created successfully", category_data)
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
                response = self.session.post(f"{API_BASE}/assignments/rubrics/", json=SAMPLE_DATA["test_rubric"])
                if response.status_code == 201:
                    rubric_data = response.json()
                    self.created_objects['test_rubric'] = rubric_data['id']
                    self.log_test("Create Assignment Rubric", True, "Rubric created successfully", rubric_data)
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
                
                # Test creating a new assignment
                assignment_data = SAMPLE_DATA["test_assignment"].copy()
                # Add required fields
                assignment_data.update({
                    "faculty": 1,  # Assuming faculty ID 1 exists
                    "academic_year": 1,  # Assuming academic year ID 1 exists
                    "semester": 1,  # Assuming semester ID 1 exists
                })
                
                response = self.session.post(f"{API_BASE}/assignments/", json=assignment_data)
                if response.status_code == 201:
                    assignment_result = response.json()
                    self.created_objects['test_assignment'] = assignment_result['id']
                    self.log_test("Create Assignment", True, "Assignment created successfully", assignment_result)
                    
                    # Test GET specific assignment
                    assignment_id = assignment_result['id']
                    response = self.session.get(f"{API_BASE}/assignments/{assignment_id}/")
                    if response.status_code == 200:
                        assignment_detail = response.json()
                        self.log_test("Get Assignment Detail", True, "Assignment detail retrieved", assignment_detail)
                    else:
                        self.log_test("Get Assignment Detail", False, f"Failed to get assignment detail: {response.text}")
                        
                    # Test UPDATE assignment
                    update_data = {"title": "Updated AP Research Project - ML Applications"}
                    response = self.session.patch(f"{API_BASE}/assignments/{assignment_id}/", json=update_data)
                    if response.status_code == 200:
                        updated_assignment = response.json()
                        self.log_test("Update Assignment", True, "Assignment updated successfully", updated_assignment)
                    else:
                        self.log_test("Update Assignment", False, f"Failed to update assignment: {response.text}")
                        
                else:
                    self.log_test("Create Assignment", False, f"Failed to create assignment: {response.text}")
            else:
                self.log_test("Get Assignments", False, f"Failed to get assignments: {response.text}")
        except Exception as e:
            self.log_test("Assignments CRUD Test", False, f"Exception: {str(e)}")
    
    def test_assignment_analytics(self):
        """Test assignment analytics API"""
        try:
            if 'test_assignment' in self.created_objects:
                assignment_id = self.created_objects['test_assignment']
                response = self.session.get(f"{API_BASE}/assignments/{assignment_id}/analytics/")
                if response.status_code == 200:
                    analytics = response.json()
                    self.log_test("Get Assignment Analytics", True, "Analytics retrieved successfully", analytics)
                else:
                    self.log_test("Get Assignment Analytics", False, f"Failed to get analytics: {response.text}")
            else:
                self.log_test("Get Assignment Analytics", False, "No test assignment available")
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
                    "title": "New Assignment Created",
                    "message": "A new assignment has been created for your course",
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
                    "name": "Weekly Quiz Schedule",
                    "description": "Automated weekly quiz creation",
                    "template_id": None,  # Would need a template ID
                    "frequency": "WEEKLY",
                    "interval": 1,
                    "start_date": datetime.now().isoformat(),
                    "end_date": (datetime.now() + timedelta(days=90)).isoformat(),
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
                
                if response.status_code in [200, 204, 404]:
                    self.log_test(f"Cleanup {obj_type}", True, f"Successfully deleted {obj_type}")
                else:
                    self.log_test(f"Cleanup {obj_type}", False, f"Failed to delete {obj_type}: {response.text}")
        except Exception as e:
            self.log_test("Cleanup Test Data", False, f"Exception during cleanup: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive Assignment Management System Tests")
        print("=" * 60)
        
        # Test server health first
        if not self.test_server_health():
            print("❌ Server is not running. Please start the Django server first.")
            return False
        
        # Run all tests
        self.test_assignment_categories()
        self.test_assignment_rubrics()
        self.test_assignments_crud()
        self.test_assignment_analytics()
        self.test_assignment_notifications()
        self.test_assignment_schedules()
        self.test_error_handling()
        
        # Clean up test data
        print("\n🧹 Cleaning up test data...")
        self.cleanup_test_data()
        
        # Generate test report
        self.generate_test_report()
        
        return True
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 TEST REPORT SUMMARY")
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
        report_file = f"assignment_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    tester = AssignmentTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
