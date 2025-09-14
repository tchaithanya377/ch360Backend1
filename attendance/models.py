from django.db import models


class AttendanceSession(models.Model):
    """A scheduled class meeting for a `CourseSection` derived from `Timetable`."""
    course_section = models.ForeignKey('academics.CourseSection', on_delete=models.CASCADE, related_name='attendance_sessions')
    timetable = models.ForeignKey('academics.Timetable', on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_sessions')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, blank=True)
    is_cancelled = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('course_section', 'date', 'start_time')
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.course_section} @ {self.date} {self.start_time}-{self.end_time}"


class AttendanceRecord(models.Model):
    """Per-student attendance status for a given `AttendanceSession`."""
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('EXCUSED', 'Excused'),
    ]

    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='attendance_records')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PRESENT')
    check_in_time = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('session', 'student')
        ordering = ['student__roll_number']

    def __str__(self):
        return f"{self.student.roll_number} - {self.session.date} - {self.status}"

