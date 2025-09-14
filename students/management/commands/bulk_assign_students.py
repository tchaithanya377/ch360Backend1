"""
Management command for bulk student assignment operations.
This command provides a CLI interface for bulk assignment operations.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from students.models import Student, StudentBatch, BulkAssignment, AcademicYear, Semester
from departments.models import Department
from academics.models import AcademicProgram


class Command(BaseCommand):
    help = 'Perform bulk student assignment operations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--operation',
            type=str,
            choices=[
                'assign_department',
                'assign_program', 
                'assign_year',
                'assign_semester',
                'promote_year',
                'create_batch',
                'update_batch_counts'
            ],
            required=True,
            help='Type of operation to perform'
        )
        
        # Common arguments
        parser.add_argument(
            '--student-ids',
            nargs='+',
            help='List of student IDs to process'
        )
        
        parser.add_argument(
            '--criteria',
            type=str,
            help='JSON string with selection criteria'
        )
        
        parser.add_argument(
            '--department-id',
            type=str,
            help='Department ID for assignment'
        )
        
        parser.add_argument(
            '--program-id',
            type=str,
            help='Academic program ID for assignment'
        )
        
        parser.add_argument(
            '--year-id',
            type=str,
            help='Academic year ID for assignment'
        )
        
        parser.add_argument(
            '--semester-id',
            type=str,
            help='Semester ID for assignment'
        )
        
        parser.add_argument(
            '--year-of-study',
            type=str,
            choices=['1', '2', '3', '4', '5'],
            help='Year of study'
        )
        
        parser.add_argument(
            '--section',
            type=str,
            choices=[chr(i) for i in range(ord('A'), ord('T') + 1)],
            help='Section assignment'
        )
        
        parser.add_argument(
            '--max-capacity',
            type=int,
            default=70,
            help='Maximum students per section (default: 70)'
        )
        
        parser.add_argument(
            '--strategy',
            type=str,
            choices=['ROUND_ROBIN', 'BALANCED', 'SEQUENTIAL'],
            default='BALANCED',
            help='Section assignment strategy'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        
        parser.add_argument(
            '--batch-name',
            type=str,
            help='Batch name for create_batch operation'
        )
        
        parser.add_argument(
            '--batch-code',
            type=str,
            help='Batch code for create_batch operation'
        )

    def handle(self, *args, **options):
        operation = options['operation']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        try:
            if operation == 'assign_department':
                self.assign_department(options, dry_run)
            elif operation == 'assign_program':
                self.assign_program(options, dry_run)
            elif operation == 'assign_year':
                self.assign_year(options, dry_run)
            elif operation == 'assign_semester':
                self.assign_semester(options, dry_run)
            elif operation == 'promote_year':
                self.promote_year(options, dry_run)
            elif operation == 'create_batch':
                self.create_batch(options, dry_run)
            elif operation == 'update_batch_counts':
                self.update_batch_counts(options, dry_run)
                
        except Exception as e:
            raise CommandError(f'Operation failed: {str(e)}')

    def assign_department(self, options, dry_run):
        """Assign students to a department"""
        students = self.get_students(options)
        department = self.get_department(options['department_id'])
        
        self.stdout.write(f'Assigning {len(students)} students to department: {department.name}')
        
        if not dry_run:
            with transaction.atomic():
                updated_count = students.update(department=department)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully updated {updated_count} students')
                )
        else:
            self.stdout.write(f'Would update {len(students)} students')

    def assign_program(self, options, dry_run):
        """Assign students to an academic program"""
        students = self.get_students(options)
        program = self.get_program(options['program_id'])
        
        self.stdout.write(f'Assigning {len(students)} students to program: {program.name}')
        
        if not dry_run:
            with transaction.atomic():
                updated_count = students.update(academic_program=program)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully updated {updated_count} students')
                )
        else:
            self.stdout.write(f'Would update {len(students)} students')

    def assign_year(self, options, dry_run):
        """Assign students to an academic year"""
        students = self.get_students(options)
        academic_year = self.get_academic_year(options['year_id'])
        
        self.stdout.write(f'Assigning {len(students)} students to academic year: {academic_year.year}')
        
        if not dry_run:
            with transaction.atomic():
                updated_count = students.update(academic_year=academic_year)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully updated {updated_count} students')
                )
        else:
            self.stdout.write(f'Would update {len(students)} students')

    def assign_semester(self, options, dry_run):
        """Assign students to a semester"""
        students = self.get_students(options)
        semester = self.get_semester(options['semester_id'])
        
        self.stdout.write(f'Assigning {len(students)} students to semester: {semester.name}')
        
        if not dry_run:
            with transaction.atomic():
                updated_count = students.update(semester=semester)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully updated {updated_count} students')
                )
        else:
            self.stdout.write(f'Would update {len(students)} students')

    def promote_year(self, options, dry_run):
        """Promote students to next year of study"""
        students = self.get_students(options)
        current_year = options.get('year_of_study', '1')
        next_year = str(int(current_year) + 1)
        
        if next_year not in ['1', '2', '3', '4', '5']:
            raise CommandError('Cannot promote beyond 5th year')
        
        self.stdout.write(f'Promoting {len(students)} students from year {current_year} to year {next_year}')
        
        if not dry_run:
            with transaction.atomic():
                updated_count = students.update(year_of_study=next_year)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully promoted {updated_count} students')
                )
        else:
            self.stdout.write(f'Would promote {len(students)} students')

    def create_batch(self, options, dry_run):
        """Create a new student batch"""
        department = self.get_department(options['department_id'])
        academic_year = self.get_academic_year(options['year_id'])
        semester = self.get_semester(options['semester_id']) if options.get('semester_id') else None
        program = self.get_program(options['program_id']) if options.get('program_id') else None
        
        batch_name = options.get('batch_name') or f"{department.code}-{academic_year.year}-{options['year_of_study']}-{options['section']}"
        batch_code = options.get('batch_code') or f"{department.code}{academic_year.year.replace('-', '')}{options['year_of_study']}{options['section']}"
        
        self.stdout.write(f'Creating batch: {batch_name}')
        
        if not dry_run:
            batch = StudentBatch.objects.create(
                department=department,
                academic_program=program,
                academic_year=academic_year,
                semester=semester,
                year_of_study=options['year_of_study'],
                section=options['section'],
                batch_name=batch_name,
                batch_code=batch_code,
                max_capacity=options['max_capacity']
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created batch: {batch.batch_name}')
            )
        else:
            self.stdout.write(f'Would create batch: {batch_name}')

    def update_batch_counts(self, options, dry_run):
        """Update student counts for all batches"""
        batches = StudentBatch.objects.all()
        
        self.stdout.write(f'Updating student counts for {batches.count()} batches')
        
        if not dry_run:
            updated_count = 0
            for batch in batches:
                old_count = batch.current_count
                batch.update_student_count()
                if batch.current_count != old_count:
                    updated_count += 1
                    self.stdout.write(f'Updated {batch.batch_name}: {old_count} -> {batch.current_count}')
            
            self.stdout.write(
                self.style.SUCCESS(f'Updated {updated_count} batches')
            )
        else:
            for batch in batches:
                current_count = Student.objects.filter(
                    department=batch.department,
                    academic_year=batch.academic_year,
                    year_of_study=batch.year_of_study,
                    section=batch.section,
                    status='ACTIVE'
                ).count()
                self.stdout.write(f'{batch.batch_name}: {batch.current_count} -> {current_count}')

    def get_students(self, options):
        """Get students based on criteria or IDs"""
        if options.get('student_ids'):
            return Student.objects.filter(
                id__in=options['student_ids'],
                status='ACTIVE'
            )
        else:
            # Build queryset based on criteria
            queryset = Student.objects.filter(status='ACTIVE')
            
            # Add criteria filters here if needed
            # This is a simplified version
            
            return queryset

    def get_department(self, department_id):
        """Get department by ID"""
        try:
            return Department.objects.get(id=department_id, is_active=True)
        except Department.DoesNotExist:
            raise CommandError(f'Department with ID {department_id} not found')

    def get_program(self, program_id):
        """Get academic program by ID"""
        try:
            return AcademicProgram.objects.get(id=program_id, is_active=True)
        except AcademicProgram.DoesNotExist:
            raise CommandError(f'Academic program with ID {program_id} not found')

    def get_academic_year(self, year_id):
        """Get academic year by ID"""
        try:
            return AcademicYear.objects.get(id=year_id, is_active=True)
        except AcademicYear.DoesNotExist:
            raise CommandError(f'Academic year with ID {year_id} not found')

    def get_semester(self, semester_id):
        """Get semester by ID"""
        try:
            return Semester.objects.get(id=semester_id, is_active=True)
        except Semester.DoesNotExist:
            raise CommandError(f'Semester with ID {semester_id} not found')
