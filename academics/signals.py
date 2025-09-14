from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Course, Syllabus, Timetable, CourseEnrollment, AcademicCalendar, BatchCourseEnrollment


@receiver(post_save, sender=Course)
def course_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for Course model"""
    if created:
        # Log course creation
        print(f"New course created: {instance.code} - {instance.title}")
    
    # Update related models if needed
    if instance.status == 'INACTIVE':
        # Deactivate related timetables linked via course_section
        Timetable.objects.filter(course_section__course=instance).update(is_active=False)


@receiver(post_save, sender=Syllabus)
def syllabus_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for Syllabus model"""
    if created:
        print(f"New syllabus created for course: {instance.course.code}")
    
    # If syllabus is approved, update course status if needed
    if instance.status == 'APPROVED' and instance.approved_at:
        print(f"Syllabus approved for course: {instance.course.code}")


@receiver(post_save, sender=Timetable)
def timetable_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for Timetable model"""
    if created and instance.course_section_id:
        print(f"New timetable entry created for course: {instance.course_section.course.code}")
    
            # Check for potential conflicts
        if instance.is_active:
            conflicts = Timetable.objects.filter(
                course_section=instance.course_section,
                day_of_week=instance.day_of_week,
                room=instance.room,
                is_active=True
            ).exclude(id=instance.id)
            
            if conflicts.exists():
                print(f"Warning: Potential timetable conflict detected for room {instance.room}")


@receiver(post_save, sender=CourseEnrollment)
def enrollment_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for CourseEnrollment model"""
    if created:
        print(f"New enrollment: {instance.student.roll_number} in {instance.course.code}")
    
    # Update enrollment status based on academic year (only for testing purposes)
    # In production, this should be more sophisticated
    # current_year = timezone.now().year
    # if instance.academic_year and int(instance.academic_year.split('-')[0]) < current_year:
    #     if instance.status == 'ENROLLED':
    #         instance.status = 'COMPLETED'
    #         instance.save(update_fields=['status'])


@receiver(post_save, sender=AcademicCalendar)
def calendar_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for AcademicCalendar model"""
    if created:
        print(f"New academic calendar event: {instance.title}")
    
    # Validate date ranges
    if instance.start_date and instance.end_date:
        if instance.start_date > instance.end_date:
            print(f"Warning: Invalid date range for event: {instance.title}")


@receiver(pre_save, sender=Course)
def course_pre_save(sender, instance, **kwargs):
    """Handle pre-save actions for Course model"""
    # Ensure course code is uppercase
    if instance.code:
        instance.code = instance.code.upper()
    
    # Validate credits
    if instance.credits and instance.credits <= 0:
        instance.credits = 3  # Default value


@receiver(pre_save, sender=Syllabus)
def syllabus_pre_save(sender, instance, **kwargs):
    """Handle pre-save actions for Syllabus model"""
    # Auto-approve if approved_by is set
    if instance.approved_by and instance.status == 'DRAFT':
        instance.status = 'APPROVED'
        instance.approved_at = timezone.now()


@receiver(post_delete, sender=Course)
def course_post_delete(sender, instance, **kwargs):
    """Handle post-delete actions for Course model"""
    print(f"Course deleted: {instance.code} - {instance.title}")


@receiver(post_delete, sender=Timetable)
def timetable_post_delete(sender, instance, **kwargs):
    """Handle post-delete actions for Timetable model"""
    if instance.course_section_id:
        print(f"Timetable entry deleted for course: {instance.course_section.course.code}")


# Batch Enrollment Signals
@receiver(post_save, sender=BatchCourseEnrollment)
def batch_enrollment_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for BatchCourseEnrollment model"""
    if created:
        print(f"New batch enrollment created: {instance.student_batch.batch_name} → {instance.course.code}")
        
        # Auto-enroll students if enabled
        if instance.auto_enroll_new_students and instance.status == 'ACTIVE':
            result = instance.enroll_batch_students()
            if result['success']:
                print(f"Auto-enrolled {result['enrolled_count']} students from batch {instance.student_batch.batch_name}")
            else:
                print(f"Auto-enrollment failed: {result['message']}")


@receiver(post_save, sender='students.Student')
def student_batch_assignment(sender, instance, created, **kwargs):
    """Handle automatic enrollment when student is assigned to a batch"""
    if created and instance.student_batch:
        # Get all active batch enrollments for this student's batch
        batch_enrollments = BatchCourseEnrollment.objects.filter(
            student_batch=instance.student_batch,
            status='ACTIVE',
            auto_enroll_new_students=True
        )
        
        for batch_enrollment in batch_enrollments:
            # Check if student is already enrolled
            existing_enrollment = CourseEnrollment.objects.filter(
                student=instance,
                course_section__course=batch_enrollment.course,
                course_section__academic_year=batch_enrollment.academic_year,
                course_section__semester=batch_enrollment.semester
            ).first()
            
            if not existing_enrollment:
                # Auto-enroll the student
                result = batch_enrollment.enroll_batch_students()
                if result['success']:
                    print(f"Auto-enrolled new student {instance.roll_number} in {batch_enrollment.course.code}")


@receiver(post_save, sender='students.StudentBatch')
def batch_student_count_update(sender, instance, created, **kwargs):
    """Update student count when batch is modified"""
    if not created:
        # Update the current count
        instance.update_student_count()
        print(f"Updated student count for batch {instance.batch_name}: {instance.current_count}")
