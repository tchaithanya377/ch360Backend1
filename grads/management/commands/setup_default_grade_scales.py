from django.core.management.base import BaseCommand
from grads.models import GradeScale


class Command(BaseCommand):
    help = 'Setup default grade scales for the system'

    def handle(self, *args, **options):
        # Clear existing grade scales
        GradeScale.objects.all().delete()
        self.stdout.write('Cleared existing grade scales...')

        # Create Indian 10-point grade scales (CBCS compliant)
        default_scales = [
            {'letter': 'O', 'min_score': 90, 'max_score': 100, 'grade_points': 10, 'description': 'Outstanding'},
            {'letter': 'A+', 'min_score': 80, 'max_score': 89, 'grade_points': 9, 'description': 'Excellent'},
            {'letter': 'A', 'min_score': 70, 'max_score': 79, 'grade_points': 8, 'description': 'Very Good'},
            {'letter': 'B+', 'min_score': 60, 'max_score': 69, 'grade_points': 7, 'description': 'Good'},
            {'letter': 'B', 'min_score': 50, 'max_score': 59, 'grade_points': 6, 'description': 'Above Average'},
            {'letter': 'C', 'min_score': 45, 'max_score': 49, 'grade_points': 5, 'description': 'Average'},
            {'letter': 'P', 'min_score': 40, 'max_score': 44, 'grade_points': 4, 'description': 'Pass'},
            {'letter': 'F', 'min_score': 0, 'max_score': 39, 'grade_points': 0, 'description': 'Fail'},
        ]

        created_count = 0
        for scale_data in default_scales:
            grade_scale, created = GradeScale.objects.get_or_create(
                letter=scale_data['letter'],
                defaults=scale_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'Created grade scale: {grade_scale}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully setup {created_count} Indian 10-point grade scales (CBCS compliant)!'
            )
        )
        self.stdout.write('\nIndian Grade Scale Summary:')
        for scale in GradeScale.objects.all().order_by('-grade_points'):
            self.stdout.write(f'  {scale.letter} ({scale.description}): {scale.min_score}-{scale.max_score}% → {scale.grade_points} points')
