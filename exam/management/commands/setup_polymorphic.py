"""
Management command to set up polymorphic question system
Run: python manage.py setup_polymorphic
"""
from django.core.management.base import BaseCommand
from django.db import connection
import os


class Command(BaseCommand):
    help = 'Set up the polymorphic question system'

    def handle(self, *args, **kwargs):
        self.stdout.write('Setting up Polymorphic Question System...\n')
        
        # Step 1: Check if migrations table exists
        self.stdout.write('1. Checking database...')
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='django_migrations'
            """)
            if cursor.fetchone():
                self.stdout.write(self.style.SUCCESS('   ✓ Database initialized'))
            else:
                self.stdout.write(self.style.WARNING('   ! Database not initialized, run migrate first'))
                return
        
        # Step 2: Check if polymorphic tables exist
        self.stdout.write('\n2. Checking polymorphic tables...')
        tables_to_check = [
            'exam_polymorphic_question',
            'exam_course_extended',
            'exam_result_extended'
        ]
        
        with connection.cursor() as cursor:
            for table in tables_to_check:
                cursor.execute(f"""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='{table}'
                """)
                if cursor.fetchone():
                    self.stdout.write(self.style.SUCCESS(f'   ✓ Table {table} exists'))
                else:
                    self.stdout.write(self.style.WARNING(f'   ! Table {table} not found'))
                    self.stdout.write('     Run: python manage.py migrate exam')
                    return
        
        # Step 3: Import and test models
        self.stdout.write('\n3. Testing model imports...')
        try:
            from exam.models_polymorphic import (
                PolymorphicQuestion, CourseExtended, 
                ResultExtended, QuestionType
            )
            self.stdout.write(self.style.SUCCESS('   ✓ Models imported successfully'))
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'   ✗ Import error: {e}'))
            return
        
        # Step 4: Create sample questions
        self.stdout.write('\n4. Creating sample questions...')
        try:
            from exam.models import Course
            
            # Get or create a test course
            course, created = Course.objects.get_or_create(
                course_name="Sample Course",
                defaults={
                    'question_number': 10,
                    'total_marks': 100
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'   ✓ Created course: {course.course_name}'))
            else:
                self.stdout.write(f'   Using existing course: {course.course_name}')
            
            # Create extended course settings
            from exam.models_polymorphic import CourseExtended
            extended, created = CourseExtended.objects.get_or_create(
                course=course,
                defaults={
                    'duration_minutes': 60,
                    'pass_percentage': 40.0
                }
            )
            
            # Create one of each question type
            from exam.models_compat import (
                create_mcq_question,
                create_true_false_question,
                create_fill_blank_question,
                create_short_answer_question,
                create_matching_question,
                create_drag_drop_question,
                create_numerical_question
            )
            
            questions_created = []
            
            # MCQ
            q = create_mcq_question(
                course, "What is 2 + 2?", 
                "3", "4", "5", "6", 
                correct_option=2, marks=5
            )
            questions_created.append(('MCQ', q))
            
            # True/False
            q = create_true_false_question(
                course, "The Earth is flat", 
                correct_answer=False, marks=5
            )
            questions_created.append(('True/False', q))
            
            # Fill in Blank
            q = create_fill_blank_question(
                course, "The capital of France is ___",
                correct_answers=["Paris", "paris"], marks=5
            )
            questions_created.append(('Fill in Blank', q))
            
            # Short Answer
            q = create_short_answer_question(
                course, "Describe photosynthesis in plants",
                keywords=["sunlight", "chlorophyll", "oxygen"],
                marks=10
            )
            questions_created.append(('Short Answer', q))
            
            # Matching
            q = create_matching_question(
                course, "Match countries with capitals",
                left_items=["USA", "UK", "France"],
                right_items=["Washington", "London", "Paris"],
                correct_pairs={"USA": "Washington", "UK": "London", "France": "Paris"},
                marks=10
            )
            questions_created.append(('Matching', q))
            
            # Drag and Drop
            q = create_drag_drop_question(
                course, "Order the steps",
                drop_zones=["First", "Second", "Third"],
                draggable_items=["Plan", "Execute", "Review"],
                correct_mapping={"First": "Plan", "Second": "Execute", "Third": "Review"},
                marks=10
            )
            questions_created.append(('Drag & Drop', q))
            
            # Numerical
            q = create_numerical_question(
                course, "What is π (pi) to 2 decimal places?",
                correct_answer=3.14, tolerance=0.01, marks=5
            )
            questions_created.append(('Numerical', q))
            
            self.stdout.write(self.style.SUCCESS(f'   ✓ Created {len(questions_created)} sample questions'))
            
            for qtype, q in questions_created:
                self.stdout.write(f'     - {qtype}: Question ID {q.id}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ Error creating questions: {e}'))
            import traceback
            traceback.print_exc()
            return
        
        # Step 5: Test validation
        self.stdout.write('\n5. Testing answer validation...')
        try:
            # Test each question type
            for qtype, question in questions_created:
                if qtype == 'MCQ':
                    result = question.validate_answer(2)  # Correct answer
                elif qtype == 'True/False':
                    result = question.validate_answer(False)  # Correct
                elif qtype == 'Fill in Blank':
                    result = question.validate_answer("Paris")  # Correct
                elif qtype == 'Numerical':
                    result = question.validate_answer(3.14)  # Correct
                else:
                    continue  # Skip complex types for now
                
                if result.get('is_correct'):
                    self.stdout.write(self.style.SUCCESS(f'   ✓ {qtype} validation works'))
                else:
                    self.stdout.write(self.style.WARNING(f'   ! {qtype} validation issue'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ Validation error: {e}'))
        
        # Step 6: Admin setup instructions
        self.stdout.write('\n6. Admin Setup:')
        self.stdout.write('   Add to exam/admin.py:')
        self.stdout.write('   from exam.admin_poly import *')
        self.stdout.write('')
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('✓ Polymorphic Question System Setup Complete!'))
        self.stdout.write('\nYou can now:')
        self.stdout.write('  1. Access admin: http://localhost:8000/admin')
        self.stdout.write('  2. View polymorphic questions in admin')
        self.stdout.write('  3. Create questions of all types')
        self.stdout.write('\nTest with:')
        self.stdout.write('  python manage.py shell')
        self.stdout.write('  >>> from exam.models_polymorphic import PolymorphicQuestion')
        self.stdout.write('  >>> PolymorphicQuestion.objects.all()')
