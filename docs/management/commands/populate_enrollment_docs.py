from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from docs.models import Category, Tutorial, Step, CodeExample


User = get_user_model()


class Command(BaseCommand):
    help = 'Populate Tutorials for Enrollment module (beginner friendly)'

    def handle(self, *args, **options):
        self.stdout.write('Creating Enrollment documentation...')

        category, _ = Category.objects.get_or_create(
            slug='enrollment-api',
            defaults={
                'name': 'Enrollment API',
                'description': 'Requests, approvals, waitlist, and student enrollment plans',
                'icon': 'fas fa-user-plus',
                'color': '#2ecc71',
                'order': 50,
                'is_active': True,
            },
        )

        author = User.objects.filter(is_staff=True).first() or User.objects.first()

        tutorials = [
            {
                'slug': 'enrollment-overview',
                'title': 'Enrollment – Overview',
                'desc': 'How students enroll: plan courses, submit enrollment requests, get approved or waitlisted, then become enrolled.',
                'order': 1,
                'steps': [
                    ('Base models', 'Key models: StudentEnrollmentPlan, PlannedCourse, EnrollmentRequest, WaitlistEntry.'),
                    ('Typical flow', '1) Advisor creates plan -> 2) Student requests enrollment -> 3) Approver approves -> 4) CourseEnrollment created.'),
                    ('Auth', 'All endpoints require JWT access token in `Authorization` header.'),
                ],
                'code': [
                    ('bash', "echo 'Use /api/v1/academics/api/enrollments/ for CourseEnrollment once approved'"),
                ],
            },
            {
                'slug': 'enrollment-plan-guide',
                'title': 'Enrollment Plan – Create and Add Courses',
                'desc': 'Create a plan for a student, then attach planned courses in priority order.',
                'order': 2,
                'steps': [
                    ('Create plan', 'POST `/api/v1/enrollment/plans/` with JSON including `student`, `academic_program`, `academic_year`, `semester`, `year_of_study`.'),
                    ('Add planned course', 'POST `/api/v1/enrollment/plans/<plan_id>/courses/` with `{ "course": <course_id>, "priority": 1 }`'),
                    ('Compute credits', 'GET `/api/v1/enrollment/plans/<plan_id>/` to see `total_credits`.'),
                ],
                'code': [
                    ('bash', "# Example curl placeholders (adjust to your actual endpoints if implemented)\necho 'POST /api/v1/enrollment/plans/'"),
                ],
            },
            {
                'slug': 'enrollment-requests-guide',
                'title': 'Enrollment Requests – Submit, Approve, Reject',
                'desc': 'Students request to enroll into a course section; approver can approve or reject. On approval, a CourseEnrollment is created automatically.',
                'order': 3,
                'steps': [
                    ('Submit request', 'POST `/api/v1/enrollment/requests/` with `{ "student": <id>, "course_section": <id>, "enrollment_plan": <id> }`'),
                    ('Approve', 'POST `/api/v1/enrollment/requests/<id>/approve/` – creates CourseEnrollment.'),
                    ('Reject', 'POST `/api/v1/enrollment/requests/<id>/reject/` with `{ "reason": "Clashes with timetable" }`'),
                ],
                'code': [
                    ('bash', "echo 'POST /api/v1/enrollment/requests/ then approve/reject endpoints as per your implementation'"),
                ],
            },
            {
                'slug': 'enrollment-waitlist-guide',
                'title': 'Waitlist – Manage Overflow',
                'desc': 'If a course is full, create a waitlist entry and promote when capacity frees up.',
                'order': 4,
                'steps': [
                    ('Add to waitlist', 'POST `/api/v1/enrollment/waitlist/` linking `enrollment_request` and `course_section`.'),
                    ('Promote first', 'POST `/api/v1/enrollment/waitlist/<id>/promote/` will create CourseEnrollment if slot available.'),
                ],
                'code': [
                    ('bash', "echo 'POST /api/v1/enrollment/waitlist/ and promote when possible'"),
                ],
            },
        ]

        for spec in tutorials:
            tut, _ = Tutorial.objects.update_or_create(
                slug=spec['slug'],
                defaults={
                    'title': spec['title'],
                    'description': spec['desc'],
                    'content': spec['desc'],
                    'category': category,
                    'difficulty': 'beginner',
                    'estimated_time': 10,
                    'tags': 'enrollment,plan,waitlist,requests,postman,react',
                    'author': author,
                    'order': spec['order'],
                },
            )
            Step.objects.filter(tutorial=tut).delete()
            for idx, (title, content) in enumerate(spec['steps'], start=1):
                Step.objects.create(tutorial=tut, title=title, content=content, order=idx)
            CodeExample.objects.filter(tutorial=tut).delete()
            for idx, (lang, code) in enumerate(spec['code'], start=1):
                CodeExample.objects.create(tutorial=tut, language=lang, code=code, title=f'Example {idx}', order=idx)

        self.stdout.write(self.style.SUCCESS('Enrollment documentation ready. Visit /docs/tutorials/'))


