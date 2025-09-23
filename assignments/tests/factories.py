"""
Test factories for assignments app using model-bakery.
Provides comprehensive test data generation for all models.
"""

import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from model_bakery import baker
from model_bakery.recipe import Recipe, foreign_key

from assignments.models import (
    AssignmentCategory, Assignment, AssignmentSubmission, AssignmentFile,
    AssignmentGrade, AssignmentComment, AssignmentGroup, AssignmentTemplate,
    AssignmentRubric, AssignmentRubricGrade, AssignmentPeerReview,
    AssignmentPlagiarismCheck, AssignmentLearningOutcome, AssignmentAnalytics,
    AssignmentNotification, AssignmentSchedule
)


# Base User Factory (assuming User model exists)
def user_factory():
    """Create a user for testing"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return baker.make(User, email=f"test_{uuid.uuid4().hex[:8]}@example.com")


# Faculty Factory (assuming Faculty model exists)
def faculty_factory():
    """Create a faculty member for testing"""
    from faculty.models import Faculty
    faculty = baker.make(
        Faculty, 
        name=f"Faculty {uuid.uuid4().hex[:8]}",
        first_name=f"Faculty{uuid.uuid4().hex[:4]}",
        last_name="Test",
        email=f"faculty_{uuid.uuid4().hex[:8]}@example.com",
        apaar_faculty_id=f"APAAR_{uuid.uuid4().hex[:8]}",
        employee_id=f"EMP_{uuid.uuid4().hex[:8]}",
        highest_degree="PhD",
        designation_at_joining="Assistant Professor",
        present_designation="Assistant Professor",
        phone_number="+12345678901"
    )
    # Align permissions: faculty should not be staff/admin in tests
    if getattr(faculty, 'user', None):
        faculty.user.is_staff = False
        faculty.user.is_superuser = False
        faculty.user.save(update_fields=["is_staff", "is_superuser"])
    return faculty


# Student Factory (assuming Student model exists)
def student_factory():
    """Create a student for testing"""
    from students.models import Student
    batch = student_batch_factory()
    return baker.make(
        Student,
        roll_number=f"ROLL_{uuid.uuid4().hex[:8]}",
        first_name=f"Student{uuid.uuid4().hex[:4]}",
        last_name="Test",
        date_of_birth=timezone.now().date() - timedelta(days=365*20),  # 20 years old
        gender="M",
        email=f"student_{uuid.uuid4().hex[:8]}@example.com",
        student_batch=batch
    )


# Academic Year Factory
def academic_year_factory():
    """Create an academic year for testing"""
    from students.models import AcademicYear
    return baker.make(
        AcademicYear, 
        year=f"2024-{uuid.uuid4().hex[:4]}",
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timedelta(days=365),
        is_current=True,
        is_active=True
    )


# Semester Factory
def semester_factory():
    """Create a semester for testing"""
    from students.models import Semester
    academic_year = academic_year_factory()
    return baker.make(
        Semester, 
        name=f"Semester {uuid.uuid4().hex[:4]}",
        academic_year=academic_year,
        semester_type="ODD"
    )


# Department Factory
def department_factory():
    """Create a department for testing"""
    from departments.models import Department
    return baker.make(
        Department, 
        name=f"Department {uuid.uuid4().hex[:4]}",
        short_name=f"D{uuid.uuid4().hex[:3].upper()}",
        code=f"DEPT{uuid.uuid4().hex[:4].upper()}",
        phone="+12345678901",
        email=f"dept_{uuid.uuid4().hex[:6]}@example.com",
        building="Main Block",
        established_date=timezone.now().date(),
        description="Test department"
    )


# Course Factory
def course_factory():
    """Create a course for testing"""
    from academics.models import Course
    return baker.make(
        Course, 
        name=f"Course {uuid.uuid4().hex[:4]}",
        code=f"CRS{uuid.uuid4().hex[:4].upper()}",
        credits=3
    )


# Course Section Factory
def course_section_factory():
    """Create a course section for testing"""
    from academics.models import CourseSection
    course = course_factory()
    return baker.make(
        CourseSection, 
        name=f"Section {uuid.uuid4().hex[:4]}",
        course=course,
        section_code=f"SEC{uuid.uuid4().hex[:4].upper()}"
    )


# Academic Program Factory
def academic_program_factory():
    """Create an academic program for testing"""
    from academics.models import AcademicProgram
    department = department_factory()
    return baker.make(
        AcademicProgram, 
        name=f"Program {uuid.uuid4().hex[:4]}",
        code=f"PROG{uuid.uuid4().hex[:4].upper()}",
        department=department
    )


# Student Batch Factory
def student_batch_factory():
    """Create a student batch for testing"""
    from students.models import StudentBatch
    program = academic_program_factory()
    academic_year = academic_year_factory()
    # Ensure department is supplied explicitly to avoid bakery creating an invalid Department
    return baker.make(
        StudentBatch, 
        batch_code=f"BATCH_{uuid.uuid4().hex[:4]}",
        academic_program=program,
        academic_year=academic_year,
        department=program.department,
        year_of_study="1",
        semester="1"
    )


# Assignment Category Factory
assignment_category_factory = Recipe(
    AssignmentCategory,
    name=lambda: f"Category {uuid.uuid4().hex[:8]}",
    description="Test category description",
    color_code="#007bff",
    is_active=True
)


# Assignment Factory
assignment_factory = Recipe(
    Assignment,
    title=lambda: f"Assignment {uuid.uuid4().hex[:8]}",
    description="Test assignment description",
    instructions="Test assignment instructions",
    category=foreign_key(assignment_category_factory),
    faculty=faculty_factory,
    assignment_type="HOMEWORK",
    difficulty_level="INTERMEDIATE",
    max_marks=Decimal("100.00"),
    due_date=lambda: timezone.now() + timedelta(days=7),
    late_submission_allowed=True,
    late_penalty_percentage=Decimal("10.00"),
    status="DRAFT",
    is_group_assignment=False,
    max_group_size=1,
    is_apaar_compliant=True,
    requires_plagiarism_check=True,
    plagiarism_threshold=Decimal("15.00"),
    estimated_time_hours=2,
    submission_reminder_days=1,
    is_active=True
)


# Assignment Submission Factory
assignment_submission_factory = Recipe(
    AssignmentSubmission,
    assignment=foreign_key(assignment_factory),
    student=student_factory,
    content="Test submission content",
    notes="Test submission notes",
    status="SUBMITTED",
    is_late=False,
    attachment_files=[]
)


# Assignment File Factory
assignment_file_factory = Recipe(
    AssignmentFile,
    assignment=foreign_key(assignment_factory),
    file_name=lambda: f"test_file_{uuid.uuid4().hex[:8]}.pdf",
    file_type="ASSIGNMENT",
    file_size=1024,
    mime_type="application/pdf",
    uploaded_by=user_factory
)


# Assignment Grade Factory
assignment_grade_factory = Recipe(
    AssignmentGrade,
    marks_obtained=Decimal("85.00"),
    grade_letter="B+",
    feedback="Good work!",
    graded_by=user_factory
)


# Assignment Comment Factory
assignment_comment_factory = Recipe(
    AssignmentComment,
    assignment=foreign_key(assignment_factory),
    author=user_factory,
    content="Test comment content",
    comment_type="GENERAL"
)


# Assignment Group Factory
assignment_group_factory = Recipe(
    AssignmentGroup,
    assignment=foreign_key(assignment_factory),
    group_name=lambda: f"Group {uuid.uuid4().hex[:8]}",
    leader=student_factory
)


# Assignment Template Factory
assignment_template_factory = Recipe(
    AssignmentTemplate,
    name=lambda: f"Template {uuid.uuid4().hex[:8]}",
    description="Test template description",
    instructions="Test template instructions",
    category=foreign_key(assignment_category_factory),
    max_marks=Decimal("100.00"),
    is_group_assignment=False,
    max_group_size=1,
    template_data={},
    created_by=user_factory,
    is_public=False
)


# Assignment Rubric Factory
assignment_rubric_factory = Recipe(
    AssignmentRubric,
    name=lambda: f"Rubric {uuid.uuid4().hex[:8]}",
    description="Test rubric description",
    rubric_type="ANALYTIC",
    criteria=[
        {"name": "Content", "description": "Quality of content", "points": 40},
        {"name": "Structure", "description": "Organization and structure", "points": 30},
        {"name": "Grammar", "description": "Grammar and spelling", "points": 30}
    ],
    total_points=Decimal("100.00"),
    created_by=user_factory,
    is_public=False
)


# Assignment Rubric Grade Factory
assignment_rubric_grade_factory = Recipe(
    AssignmentRubricGrade,
    submission=foreign_key(assignment_submission_factory),
    rubric=foreign_key(assignment_rubric_factory),
    criteria_scores={
        "Content": 35,
        "Structure": 25,
        "Grammar": 28
    },
    total_score=Decimal("88.00"),
    feedback="Good work overall",
    graded_by=user_factory
)


# Assignment Peer Review Factory
assignment_peer_review_factory = Recipe(
    AssignmentPeerReview,
    assignment=foreign_key(assignment_factory),
    reviewer=student_factory,
    reviewee=student_factory,
    submission=foreign_key(assignment_submission_factory),
    content_rating=4,
    clarity_rating=3,
    creativity_rating=4,
    overall_rating=4,
    strengths="Good content and structure",
    improvements="Could improve clarity",
    additional_comments="Overall good work",
    is_completed=True,
    submitted_at=timezone.now()
)


# Assignment Plagiarism Check Factory
assignment_plagiarism_check_factory = Recipe(
    AssignmentPlagiarismCheck,
    submission=foreign_key(assignment_submission_factory),
    status="CLEAN",
    similarity_percentage=Decimal("5.00"),
    sources=[],
    checked_by=user_factory,
    notes="No plagiarism detected"
)


# Assignment Learning Outcome Factory
assignment_learning_outcome_factory = Recipe(
    AssignmentLearningOutcome,
    assignment=foreign_key(assignment_factory),
    outcome_code=lambda: f"LO{uuid.uuid4().hex[:2]}",
    description="Test learning outcome description",
    bloom_level="APPLY",
    weight=Decimal("25.00")
)


# Assignment Analytics Factory
assignment_analytics_factory = Recipe(
    AssignmentAnalytics,
    assignment=foreign_key(assignment_factory),
    total_expected_submissions=30,
    actual_submissions=25,
    submission_rate=Decimal("83.33"),
    average_grade=Decimal("78.50"),
    median_grade=Decimal("80.00"),
    grade_distribution={
        "A": 5,
        "B": 10,
        "C": 8,
        "D": 2
    },
    late_submission_rate=Decimal("20.00"),
    outcome_achievement={
        "LO1": 85.0,
        "LO2": 78.0
    },
    plagiarism_rate=Decimal("5.00")
)


# Assignment Notification Factory
assignment_notification_factory = Recipe(
    AssignmentNotification,
    assignment=foreign_key(assignment_factory),
    recipient=user_factory,
    notification_type="ASSIGNMENT_CREATED",
    title="New Assignment Created",
    message="A new assignment has been created for you",
    is_read=False,
    context_data={}
)


# Assignment Schedule Factory
assignment_schedule_factory = Recipe(
    AssignmentSchedule,
    name=lambda: f"Schedule {uuid.uuid4().hex[:8]}",
    description="Test schedule description",
    template=foreign_key(assignment_template_factory),
    schedule_type="WEEKLY",
    interval_days=7,
    is_active=True,
    start_date=timezone.now(),
    end_date=timezone.now() + timedelta(days=30),
    created_by=user_factory
)


# Specialized Factories for Edge Cases

def published_assignment_factory():
    """Create a published assignment"""
    return assignment_factory.make(status="PUBLISHED")


def overdue_assignment_factory():
    """Create an overdue assignment"""
    return assignment_factory.make(
        status="PUBLISHED",
        due_date=timezone.now() - timedelta(days=1)
    )


def group_assignment_factory():
    """Create a group assignment"""
    return assignment_factory.make(
        is_group_assignment=True,
        max_group_size=4
    )


def late_submission_factory():
    """Create a late submission"""
    assignment = overdue_assignment_factory()
    return assignment_submission_factory.make(
        assignment=assignment,
        is_late=True,
        status="LATE"
    )


def graded_submission_factory():
    """Create a graded submission"""
    submission = assignment_submission_factory.make()
    grade = assignment_grade_factory.make()
    submission.grade = grade
    submission.graded_by = grade.graded_by
    submission.graded_at = timezone.now()
    submission.save()
    return submission


def assignment_with_files_factory():
    """Create an assignment with files"""
    assignment = assignment_factory.make()
    assignment_file_factory.make(assignment=assignment, file_type="ASSIGNMENT")
    return assignment


def assignment_with_submissions_factory(num_submissions=3):
    """Create an assignment with multiple submissions"""
    assignment = published_assignment_factory()
    submissions = []
    for _ in range(num_submissions):
        submission = assignment_submission_factory.make(assignment=assignment)
        submissions.append(submission)
    return assignment, submissions


def assignment_with_comments_factory(num_comments=2):
    """Create an assignment with comments"""
    assignment = assignment_factory.make()
    comments = []
    for _ in range(num_comments):
        comment = assignment_comment_factory.make(assignment=assignment)
        comments.append(comment)
    return assignment, comments


def assignment_with_analytics_factory():
    """Create an assignment with analytics"""
    assignment = assignment_factory.make()
    analytics = assignment_analytics_factory.make(assignment=assignment)
    return assignment, analytics


# Factory for creating complete assignment workflow
def complete_assignment_workflow_factory():
    """Create a complete assignment workflow with all related objects"""
    # Create base objects
    faculty = faculty_factory()
    student = student_factory()
    category = assignment_category_factory.make()
    
    # Create assignment
    assignment = assignment_factory.make(
        faculty=faculty,
        category=category,
        status="PUBLISHED"
    )
    
    # Create submission
    submission = assignment_submission_factory.make(
        assignment=assignment,
        student=student
    )
    
    # Create grade
    grade = assignment_grade_factory.make()
    submission.grade = grade
    submission.graded_by = grade.graded_by
    submission.graded_at = timezone.now()
    submission.save()
    
    # Create file
    file_obj = assignment_file_factory.make(
        assignment=assignment,
        submission=submission,
        file_type="SUBMISSION"
    )
    
    # Create comment
    comment = assignment_comment_factory.make(
        assignment=assignment,
        author=faculty.user if hasattr(faculty, 'user') else user_factory()
    )
    
    return {
        'assignment': assignment,
        'submission': submission,
        'grade': grade,
        'file': file_obj,
        'comment': comment,
        'faculty': faculty,
        'student': student,
        'category': category
    }


# Utility functions for test data
def create_test_assignment_data():
    """Create comprehensive test data for assignments"""
    return {
        'categories': [assignment_category_factory.make() for _ in range(3)],
        'assignments': [assignment_factory.make() for _ in range(5)],
        'submissions': [assignment_submission_factory.make() for _ in range(10)],
        'grades': [assignment_grade_factory.make() for _ in range(8)],
        'comments': [assignment_comment_factory.make() for _ in range(6)],
        'files': [assignment_file_factory.make() for _ in range(4)],
    }


def create_test_user_data():
    """Create test users with different roles"""
    return {
        'faculty': [faculty_factory() for _ in range(3)],
        'students': [student_factory() for _ in range(10)],
        'users': [user_factory() for _ in range(5)],
    }
