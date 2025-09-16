from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from assignments.models import (
    AssignmentCategory, AssignmentRubric, AssignmentTemplate,
    AssignmentLearningOutcome
)
from academics.models import AcademicProgram, Course
from departments.models import Department

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up AP-specific assignment features and templates'

    def handle(self, *args, **options):
        self.stdout.write('Setting up AP-specific assignment features...')
        
        # Create AP-specific assignment categories
        self.create_ap_categories()
        
        # Create standard rubrics for AP universities
        self.create_ap_rubrics()
        
        # Create assignment templates
        self.create_ap_templates()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up AP assignment features!')
        )

    def create_ap_categories(self):
        """Create AP-specific assignment categories"""
        categories = [
            {
                'name': 'Research Project',
                'description': 'Independent research projects aligned with AP academic standards',
                'color_code': '#2E8B57'
            },
            {
                'name': 'Laboratory Assignment',
                'description': 'Practical laboratory work and experiments',
                'color_code': '#4169E1'
            },
            {
                'name': 'Field Work',
                'description': 'Field studies and practical applications',
                'color_code': '#FF6347'
            },
            {
                'name': 'Case Study',
                'description': 'Real-world case analysis and problem solving',
                'color_code': '#9370DB'
            },
            {
                'name': 'Portfolio',
                'description': 'Comprehensive portfolio of student work',
                'color_code': '#FFD700'
            },
            {
                'name': 'Presentation',
                'description': 'Oral presentations and demonstrations',
                'color_code': '#FF69B4'
            },
            {
                'name': 'Internship Report',
                'description': 'Reports from industry internships and placements',
                'color_code': '#20B2AA'
            },
            {
                'name': 'Thesis/Dissertation',
                'description': 'Final year thesis and dissertation work',
                'color_code': '#8B4513'
            }
        ]
        
        for cat_data in categories:
            category, created = AssignmentCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
            else:
                self.stdout.write(f'Category already exists: {category.name}')

    def create_ap_rubrics(self):
        """Create standard rubrics for AP universities"""
        rubrics = [
            {
                'name': 'AP Research Project Rubric',
                'description': 'Comprehensive rubric for research projects in AP universities',
                'rubric_type': 'ANALYTIC',
                'total_points': 100,
                'criteria': [
                    {
                        'name': 'Research Quality',
                        'description': 'Depth and quality of research conducted',
                        'max_points': 25,
                        'levels': [
                            {'description': 'Excellent research with multiple sources', 'points': 25},
                            {'description': 'Good research with adequate sources', 'points': 20},
                            {'description': 'Basic research with limited sources', 'points': 15},
                            {'description': 'Poor research with minimal sources', 'points': 10},
                            {'description': 'No research conducted', 'points': 0}
                        ]
                    },
                    {
                        'name': 'Analysis and Critical Thinking',
                        'description': 'Quality of analysis and critical thinking demonstrated',
                        'max_points': 25,
                        'levels': [
                            {'description': 'Excellent analysis with deep insights', 'points': 25},
                            {'description': 'Good analysis with clear insights', 'points': 20},
                            {'description': 'Basic analysis with some insights', 'points': 15},
                            {'description': 'Limited analysis with few insights', 'points': 10},
                            {'description': 'No analysis or critical thinking', 'points': 0}
                        ]
                    },
                    {
                        'name': 'Writing and Communication',
                        'description': 'Quality of writing and communication',
                        'max_points': 20,
                        'levels': [
                            {'description': 'Excellent writing with clear communication', 'points': 20},
                            {'description': 'Good writing with mostly clear communication', 'points': 16},
                            {'description': 'Adequate writing with some clarity issues', 'points': 12},
                            {'description': 'Poor writing with communication problems', 'points': 8},
                            {'description': 'Unclear or incomprehensible writing', 'points': 0}
                        ]
                    },
                    {
                        'name': 'APAAR Compliance',
                        'description': 'Compliance with AP Academic Assessment and Accreditation Requirements',
                        'max_points': 15,
                        'levels': [
                            {'description': 'Fully compliant with APAAR standards', 'points': 15},
                            {'description': 'Mostly compliant with minor issues', 'points': 12},
                            {'description': 'Partially compliant with some issues', 'points': 9},
                            {'description': 'Minimally compliant with major issues', 'points': 6},
                            {'description': 'Not compliant with APAAR standards', 'points': 0}
                        ]
                    },
                    {
                        'name': 'Originality and Plagiarism',
                        'description': 'Originality of work and absence of plagiarism',
                        'max_points': 15,
                        'levels': [
                            {'description': 'Completely original work', 'points': 15},
                            {'description': 'Mostly original with proper citations', 'points': 12},
                            {'description': 'Some originality with minor citation issues', 'points': 9},
                            {'description': 'Limited originality with citation problems', 'points': 6},
                            {'description': 'Plagiarized or unoriginal work', 'points': 0}
                        ]
                    }
                ]
            },
            {
                'name': 'AP Laboratory Assignment Rubric',
                'description': 'Rubric for laboratory assignments and practical work',
                'rubric_type': 'ANALYTIC',
                'total_points': 100,
                'criteria': [
                    {
                        'name': 'Experimental Design',
                        'description': 'Quality of experimental design and methodology',
                        'max_points': 30,
                        'levels': [
                            {'description': 'Excellent experimental design', 'points': 30},
                            {'description': 'Good experimental design', 'points': 24},
                            {'description': 'Adequate experimental design', 'points': 18},
                            {'description': 'Poor experimental design', 'points': 12},
                            {'description': 'No experimental design', 'points': 0}
                        ]
                    },
                    {
                        'name': 'Data Collection and Analysis',
                        'description': 'Quality of data collection and analysis',
                        'max_points': 25,
                        'levels': [
                            {'description': 'Excellent data collection and analysis', 'points': 25},
                            {'description': 'Good data collection and analysis', 'points': 20},
                            {'description': 'Adequate data collection and analysis', 'points': 15},
                            {'description': 'Poor data collection and analysis', 'points': 10},
                            {'description': 'No data collection or analysis', 'points': 0}
                        ]
                    },
                    {
                        'name': 'Safety and Procedures',
                        'description': 'Adherence to safety protocols and procedures',
                        'max_points': 20,
                        'levels': [
                            {'description': 'Excellent safety adherence', 'points': 20},
                            {'description': 'Good safety adherence', 'points': 16},
                            {'description': 'Adequate safety adherence', 'points': 12},
                            {'description': 'Poor safety adherence', 'points': 8},
                            {'description': 'Unsafe practices', 'points': 0}
                        ]
                    },
                    {
                        'name': 'Report Quality',
                        'description': 'Quality of laboratory report',
                        'max_points': 25,
                        'levels': [
                            {'description': 'Excellent report quality', 'points': 25},
                            {'description': 'Good report quality', 'points': 20},
                            {'description': 'Adequate report quality', 'points': 15},
                            {'description': 'Poor report quality', 'points': 10},
                            {'description': 'No report submitted', 'points': 0}
                        ]
                    }
                ]
            }
        ]
        
        # Get or create a system user for rubrics
        system_user, created = User.objects.get_or_create(
            email='system@apuniversity.edu',
            defaults={
                'username': 'system',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        for rubric_data in rubrics:
            rubric, created = AssignmentRubric.objects.get_or_create(
                name=rubric_data['name'],
                defaults={
                    **rubric_data,
                    'created_by': system_user,
                    'is_public': True
                }
            )
            if created:
                self.stdout.write(f'Created rubric: {rubric.name}')
            else:
                self.stdout.write(f'Rubric already exists: {rubric.name}')

    def create_ap_templates(self):
        """Create assignment templates for AP universities"""
        templates = [
            {
                'name': 'AP Research Project Template',
                'description': 'Template for research projects in AP universities',
                'instructions': '''
# Research Project Guidelines

## Objective
Conduct independent research on a topic relevant to your field of study, demonstrating critical thinking and analytical skills.

## Requirements
1. **Research Proposal** (20%): Submit a detailed research proposal including:
   - Research question and objectives
   - Literature review
   - Methodology
   - Timeline

2. **Research Implementation** (40%): Conduct the research including:
   - Data collection
   - Analysis
   - Interpretation

3. **Final Report** (40%): Submit a comprehensive report including:
   - Executive summary
   - Introduction and literature review
   - Methodology
   - Results and analysis
   - Conclusions and recommendations
   - References (APA format)

## APAAR Compliance
- Ensure all work meets AP Academic Assessment and Accreditation Requirements
- Maintain academic integrity and avoid plagiarism
- Follow ethical guidelines for research

## Submission Guidelines
- Submit all documents in PDF format
- Include all source materials and data
- Ensure proper citations and references
                ''',
                'max_marks': 100,
                'is_group_assignment': False,
                'template_data': {
                    'estimated_hours': 40,
                    'difficulty_level': 'ADVANCED',
                    'requires_plagiarism_check': True,
                    'plagiarism_threshold': 10.0,
                    'enable_peer_review': True,
                    'peer_review_weight': 10
                }
            },
            {
                'name': 'AP Laboratory Assignment Template',
                'description': 'Template for laboratory assignments in AP universities',
                'instructions': '''
# Laboratory Assignment Guidelines

## Objective
Complete the assigned laboratory experiment and submit a comprehensive report.

## Requirements
1. **Pre-lab Preparation** (15%):
   - Read and understand the experiment
   - Complete pre-lab questions
   - Prepare necessary materials

2. **Laboratory Work** (35%):
   - Follow safety protocols
   - Conduct experiment as instructed
   - Record observations and data

3. **Post-lab Analysis** (50%):
   - Analyze collected data
   - Answer post-lab questions
   - Submit comprehensive report

## Safety Requirements
- Follow all safety protocols
- Wear appropriate protective equipment
- Report any accidents immediately

## Report Format
- Title page
- Objective
- Materials and methods
- Results and observations
- Data analysis
- Conclusions
- References

## Submission Guidelines
- Submit report within 48 hours of lab completion
- Include all raw data and calculations
- Ensure neat and professional presentation
                ''',
                'max_marks': 100,
                'is_group_assignment': True,
                'max_group_size': 3,
                'template_data': {
                    'estimated_hours': 6,
                    'difficulty_level': 'INTERMEDIATE',
                    'requires_plagiarism_check': False,
                    'enable_peer_review': False
                }
            },
            {
                'name': 'AP Case Study Template',
                'description': 'Template for case study assignments in AP universities',
                'instructions': '''
# Case Study Assignment Guidelines

## Objective
Analyze the provided case study and develop comprehensive solutions.

## Requirements
1. **Case Analysis** (30%):
   - Identify key issues and problems
   - Analyze stakeholders and their interests
   - Consider multiple perspectives

2. **Solution Development** (40%):
   - Develop multiple solution alternatives
   - Evaluate pros and cons of each
   - Recommend best solution with justification

3. **Implementation Plan** (30%):
   - Develop detailed implementation plan
   - Consider resource requirements
   - Identify potential risks and mitigation strategies

## Analysis Framework
Use appropriate analytical frameworks such as:
- SWOT Analysis
- PEST Analysis
- Root Cause Analysis
- Cost-Benefit Analysis

## Presentation Requirements
- Prepare 15-minute presentation
- Use visual aids effectively
- Be prepared for Q&A session

## Submission Guidelines
- Submit written analysis (2000-3000 words)
- Include presentation slides
- Ensure professional formatting
                ''',
                'max_marks': 100,
                'is_group_assignment': True,
                'max_group_size': 4,
                'template_data': {
                    'estimated_hours': 20,
                    'difficulty_level': 'ADVANCED',
                    'requires_plagiarism_check': True,
                    'plagiarism_threshold': 15.0,
                    'enable_peer_review': True,
                    'peer_review_weight': 15
                }
            }
        ]
        
        # Get or create a system user for templates
        system_user, created = User.objects.get_or_create(
            email='system@apuniversity.edu',
            defaults={
                'username': 'system',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        # Get research project category
        research_category = AssignmentCategory.objects.filter(name='Research Project').first()
        
        for template_data in templates:
            template, created = AssignmentTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    **template_data,
                    'category': research_category,
                    'created_by': system_user,
                    'is_public': True
                }
            )
            if created:
                self.stdout.write(f'Created template: {template.name}')
            else:
                self.stdout.write(f'Template already exists: {template.name}')
