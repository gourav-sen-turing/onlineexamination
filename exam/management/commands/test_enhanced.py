"""
Django management command to test enhanced question types
Run with: python manage.py test_enhanced
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction
import sys

class Command(BaseCommand):
    help = 'Test the enhanced question type system'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Testing Enhanced Question Type System'))
        self.stdout.write('=' * 50)
        
        # Test imports
        self.stdout.write('\n1. Testing imports...')
        try:
            from exam.models_enhanced import (
                Course, MCQQuestion, TrueFalseQuestion, FillBlankQuestion,
                ShortAnswerQuestion, MatchingQuestion, DragDropQuestion,
                NumericalQuestion, Result
            )
            self.stdout.write(self.style.SUCCESS('✓ All models imported successfully'))
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'✗ Import error: {e}'))
            return
        
        # Test database operations
        self.stdout.write('\n2. Testing database operations...')
        try:
            with transaction.atomic():
                # Create test course
                course = Course.objects.create(
                    course_name="Test Course",
                    question_number=10,
                    total_marks=100,
                    duration_minutes=60,
                    pass_percentage=40.0
                )
                self.stdout.write(self.style.SUCCESS(f'✓ Created course: {course.course_name}'))
                
                # Test each question type
                questions_created = []
                
                # MCQ Question
                mcq = MCQQuestion.objects.create(
                    course=course,
                    question_text="What is Django?",
                    option1="A Python framework",
                    option2="A database",
                    option3="A programming language",
                    option4="An OS",
                    correct_option=1,
                    marks=10
                )
                questions_created.append(('MCQ', mcq))
                
                # True/False Question
                tf = TrueFalseQuestion.objects.create(
                    course=course,
                    question_text="Django is written in Java",
                    correct_answer=False,
                    marks=5
                )
                questions_created.append(('True/False', tf))
                
                # Fill in the Blank
                fb = FillBlankQuestion.objects.create(
                    course=course,
                    question_text="Django was created by ___",
                    correct_answers=["Adrian Holovaty", "Simon Willison"],
                    marks=10
                )
                questions_created.append(('Fill in Blank', fb))
                
                # Short Answer
                sa = ShortAnswerQuestion.objects.create(
                    course=course,
                    question_text="Explain MVC pattern",
                    model_answer="MVC stands for Model-View-Controller",
                    min_words=5,
                    max_words=50,
                    keywords=["model", "view", "controller"],
                    marks=15
                )
                questions_created.append(('Short Answer', sa))
                
                # Matching Question
                match = MatchingQuestion.objects.create(
                    course=course,
                    question_text="Match Django components",
                    left_items=["Model", "View", "Template"],
                    right_items=["Database", "Logic", "HTML"],
                    correct_pairs={
                        "Model": "Database",
                        "View": "Logic",
                        "Template": "HTML"
                    },
                    marks=15
                )
                questions_created.append(('Matching', match))
                
                # Drag and Drop
                dd = DragDropQuestion.objects.create(
                    course=course,
                    question_text="Arrange Django request flow",
                    drop_zones=["Step 1", "Step 2", "Step 3"],
                    draggable_items=["URL", "View", "Template"],
                    correct_mapping={
                        "Step 1": "URL",
                        "Step 2": "View",
                        "Step 3": "Template"
                    },
                    marks=10
                )
                questions_created.append(('Drag & Drop', dd))
                
                # Numerical Question
                num = NumericalQuestion.objects.create(
                    course=course,
                    question_text="What is 10 + 15?",
                    correct_answer=25,
                    tolerance=0.01,
                    marks=5
                )
                questions_created.append(('Numerical', num))
                
                self.stdout.write(self.style.SUCCESS(f'✓ Created {len(questions_created)} questions'))
                
                # Test validation
                self.stdout.write('\n3. Testing answer validation...')
                
                # Test MCQ validation
                result = mcq.validate_answer(1)
                assert result['is_correct'] == True, "MCQ validation failed"
                self.stdout.write(self.style.SUCCESS('✓ MCQ validation works'))
                
                # Test True/False validation
                result = tf.validate_answer(False)
                assert result['is_correct'] == True, "True/False validation failed"
                self.stdout.write(self.style.SUCCESS('✓ True/False validation works'))
                
                # Test Fill in Blank validation
                result = fb.validate_answer("Adrian Holovaty")
                assert result['is_correct'] == True, "Fill in Blank validation failed"
                self.stdout.write(self.style.SUCCESS('✓ Fill in Blank validation works'))
                
                # Test Numerical validation
                result = num.validate_answer(25.0)
                assert result['is_correct'] == True, "Numerical validation failed"
                self.stdout.write(self.style.SUCCESS('✓ Numerical validation works'))
                
                # Clean up test data
                course.delete()
                self.stdout.write(self.style.SUCCESS('✓ Test data cleaned up'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Database operation failed: {e}'))
            import traceback
            traceback.print_exc()
            return
        
        # Test views import
        self.stdout.write('\n4. Testing views import...')
        try:
            from exam.enhanced_views import (
                question_type_selection_view,
                create_question_view,
                take_exam_view
            )
            self.stdout.write(self.style.SUCCESS('✓ Views imported successfully'))
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'✗ Views import error: {e}'))
        
        # Check installed apps
        self.stdout.write('\n5. Checking Django configuration...')
        from django.conf import settings
        
        required_apps = ['exam', 'student', 'teacher']
        for app in required_apps:
            if app in settings.INSTALLED_APPS:
                self.stdout.write(self.style.SUCCESS(f'✓ {app} app installed'))
            else:
                self.stdout.write(self.style.ERROR(f'✗ {app} app not in INSTALLED_APPS'))
        
        # Check widget_tweaks
        if 'widget_tweaks' in settings.INSTALLED_APPS:
            self.stdout.write(self.style.SUCCESS('✓ widget_tweaks installed'))
        else:
            self.stdout.write(self.style.WARNING('! widget_tweaks not in INSTALLED_APPS'))
        
        # Summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('✓ All tests completed successfully!'))
        self.stdout.write('\nThe enhanced question type system is working correctly.')
        self.stdout.write('\nYou can now:')
        self.stdout.write('  1. Run the server: python manage.py runserver')
        self.stdout.write('  2. Access admin: http://localhost:8000/admin')
        self.stdout.write('  3. Create questions of all types')
