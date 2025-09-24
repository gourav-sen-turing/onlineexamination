"""
Comprehensive Test Suite for Enhanced Question Types
"""
from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth.models import User, Group
from django.db import transaction
from django.urls import reverse
from decimal import Decimal
import json
import threading
from concurrent.futures import ThreadPoolExecutor

from student.models import Student
from teacher.models import Teacher
from .models_enhanced import (
    Course, MCQQuestion, TrueFalseQuestion, FillBlankQuestion,
    ShortAnswerQuestion, MatchingQuestion, DragDropQuestion,
    NumericalQuestion, Question, Result, QuestionType
)
from .validators import (
    MCQValidator, TrueFalseValidator, FillBlankValidator,
    ShortAnswerValidator, MatchingValidator, DragDropValidator,
    NumericalValidator, get_question_validator
)


class CourseModelTest(TestCase):
    """Test Course model enhancements"""
    
    def setUp(self):
        self.course = Course.objects.create(
            course_name="Test Course",
            question_number=10,
            total_marks=100,
            duration_minutes=60,
            pass_percentage=40.0
        )
    
    def test_course_creation(self):
        """Test course is created with correct attributes"""
        self.assertEqual(self.course.course_name, "Test Course")
        self.assertEqual(self.course.duration_minutes, 60)
        self.assertEqual(self.course.pass_percentage, 40.0)
    
    def test_course_validation(self):
        """Test course validation"""
        self.course.pass_percentage = 150
        with self.assertRaises(Exception):
            self.course.clean()
    
    def test_get_questions_by_type(self):
        """Test grouping questions by type"""
        MCQQuestion.objects.create(
            course=self.course,
            question_text="MCQ Test",
            option1="A", option2="B",
            correct_option=1,
            marks=5
        )
        TrueFalseQuestion.objects.create(
            course=self.course,
            question_text="TF Test",
            correct_answer=True,
            marks=2
        )
        
        questions_by_type = self.course.get_questions_by_type()
        self.assertIn(QuestionType.MCQ, questions_by_type)
        self.assertIn(QuestionType.TRUE_FALSE, questions_by_type)


class MCQQuestionTest(TestCase):
    """Test MCQ Question functionality"""
    
    def setUp(self):
        self.course = Course.objects.create(
            course_name="Test Course",
            question_number=10,
            total_marks=100
        )
        
        self.mcq = MCQQuestion.objects.create(
            course=self.course,
            question_text="What is Python?",
            option1="A programming language",
            option2="A snake",
            option3="A framework",
            option4="A database",
            correct_option=1,
            marks=5
        )
    
    def test_mcq_creation(self):
        """Test MCQ question creation"""
        self.assertEqual(self.mcq.question_type, QuestionType.MCQ)
        self.assertEqual(self.mcq.correct_option, 1)
        self.assertEqual(len(self.mcq.get_options()), 4)
    
    def test_mcq_validation_correct(self):
        """Test MCQ validation with correct answer"""
        result = self.mcq.validate_answer(1)
        self.assertTrue(result['is_correct'])
        self.assertEqual(result['score'], 5)
    
    def test_mcq_validation_incorrect(self):
        """Test MCQ validation with incorrect answer"""
        result = self.mcq.validate_answer(2)
        self.assertFalse(result['is_correct'])
        self.assertEqual(result['score'], 0)
    
    def test_mcq_multiple_correct(self):
        """Test MCQ with multiple correct answers"""
        mcq_multi = MCQQuestion.objects.create(
            course=self.course,
            question_text="Select all programming languages",
            option1="Python",
            option2="Java",
            option3="HTML",
            option4="CSS",
            correct_option=1,
            allow_multiple=True,
            correct_options=[1, 2],
            marks=4
        )
        
        result = mcq_multi.validate_answer([1, 2])
        self.assertTrue(result['is_correct'])
        self.assertEqual(result['score'], 4)
        
        result = mcq_multi.validate_answer([1, 3])
        self.assertFalse(result['is_correct'])
        self.assertEqual(result['score'], 0)


class TrueFalseQuestionTest(TestCase):
    """Test True/False Question functionality"""
    
    def setUp(self):
        self.course = Course.objects.create(
            course_name="Test Course",
            question_number=10,
            total_marks=100
        )
        
        self.tf_question = TrueFalseQuestion.objects.create(
            course=self.course,
            question_text="Python is a compiled language",
            correct_answer=False,
            marks=2
        )
    
    def test_true_false_creation(self):
        """Test True/False question creation"""
        self.assertEqual(self.tf_question.question_type, QuestionType.TRUE_FALSE)
        self.assertFalse(self.tf_question.correct_answer)
    
    def test_true_false_validation(self):
        """Test True/False validation"""
        result = self.tf_question.validate_answer(False)
        self.assertTrue(result['is_correct'])
        self.assertEqual(result['score'], 2)
        
        result = self.tf_question.validate_answer(True)
        self.assertFalse(result['is_correct'])
        self.assertEqual(result['score'], 0)


class FillBlankQuestionTest(TestCase):
    """Test Fill in the Blank Question functionality"""
    
    def setUp(self):
        self.course = Course.objects.create(
            course_name="Test Course",
            question_number=10,
            total_marks=100
        )
        
        self.fb_question = FillBlankQuestion.objects.create(
            course=self.course,
            question_text="The capital of France is ___",
            correct_answers=["Paris", "paris"],
            case_sensitive=False,
            marks=3
        )
    
    def test_fill_blank_creation(self):
        """Test Fill in the Blank question creation"""
        self.assertEqual(self.fb_question.question_type, QuestionType.FILL_BLANK)
        self.assertIn("Paris", self.fb_question.correct_answers)
    
    def test_fill_blank_case_insensitive(self):
        """Test case-insensitive matching"""
        result = self.fb_question.validate_answer("PARIS")
        self.assertTrue(result['is_correct'])
        self.assertEqual(result['score'], 3)
    
    def test_fill_blank_with_synonyms(self):
        """Test synonym recognition"""
        self.fb_question.synonyms = {"Paris": ["City of Light", "Paname"]}
        self.fb_question.save()
        
        result = self.fb_question.validate_answer("City of Light")
        self.assertTrue(result['is_correct'])
    
    def test_fill_blank_with_regex(self):
        """Test regex pattern matching"""
        fb_regex = FillBlankQuestion.objects.create(
            course=self.course,
            question_text="Enter a valid email",
            correct_answers=["test@example.com"],
            regex_pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$',
            marks=5
        )
        
        result = fb_regex.validate_answer("user@domain.com")
        self.assertTrue(result['is_correct'])
        
        result = fb_regex.validate_answer("invalid-email")
        self.assertFalse(result['is_correct'])
    
    def test_fill_blank_partial_credit(self):
        """Test partial credit with fuzzy matching"""
        self.fb_question.partial_credit = True
        self.fb_question.exact_match = False
        self.fb_question.save()
        
        result = self.fb_question.validate_answer("Pari")  # Close to "Paris"
        self.assertGreater(result['score'], 0)
        self.assertLess(result['score'], self.fb_question.marks)


class ShortAnswerQuestionTest(TestCase):
    """Test Short Answer Question functionality"""
    
    def setUp(self):
        self.course = Course.objects.create(
            course_name="Test Course",
            question_number=10,
            total_marks=100
        )
        
        self.sa_question = ShortAnswerQuestion.objects.create(
            course=self.course,
            question_text="Explain the concept of inheritance in OOP",
            model_answer="Inheritance allows a class to inherit properties and methods from another class",
            min_words=20,
            max_words=100,
            keywords=["inheritance", "class", "properties", "methods"],
            marks=10
        )
    
    def test_short_answer_word_count(self):
        """Test word count validation"""
        # Too short
        result = self.sa_question.validate_answer("Short answer")
        self.assertFalse(result['is_correct'])
        self.assertEqual(result['score'], 0)
        
        # Within range
        valid_answer = " ".join(["word"] * 25)
        result = self.sa_question.validate_answer(valid_answer)
        self.assertIsNotNone(result['word_count'])
        self.assertEqual(result['word_count'], 25)
    
    def test_short_answer_keyword_matching(self):
        """Test keyword-based scoring"""
        answer = "Inheritance in programming allows one class to inherit properties and behaviors from another class"
        result = self.sa_question.validate_answer(answer)
        
        # Should find at least some keywords
        self.assertGreater(result['score'], 0)
    
    def test_short_answer_keyword_weights(self):
        """Test weighted keyword scoring"""
        self.sa_question.keyword_weights = {
            "inheritance": 2.0,
            "class": 1.0,
            "properties": 1.5,
            "methods": 1.5
        }
        self.sa_question.save()
        
        answer = "Inheritance is a fundamental concept where a class can inherit from another"
        result = self.sa_question.validate_answer(answer)
        self.assertGreater(result['score'], 0)


class MatchingQuestionTest(TestCase):
    """Test Matching Question functionality"""
    
    def setUp(self):
        self.course = Course.objects.create(
            course_name="Test Course",
            question_number=10,
            total_marks=100
        )
        
        self.match_question = MatchingQuestion.objects.create(
            course=self.course,
            question_text="Match programming languages with their creators",
            left_items=["Python", "Java", "C"],
            right_items=["Guido van Rossum", "James Gosling", "Dennis Ritchie"],
            correct_pairs={
                "Python": "Guido van Rossum",
                "Java": "James Gosling",
                "C": "Dennis Ritchie"
            },
            marks=6
        )
    
    def test_matching_creation(self):
        """Test Matching question creation"""
        self.assertEqual(len(self.match_question.left_items), 3)
        self.assertEqual(len(self.match_question.correct_pairs), 3)
    
    def test_matching_all_correct(self):
        """Test matching with all correct pairs"""
        user_answer = {
            "Python": "Guido van Rossum",
            "Java": "James Gosling",
            "C": "Dennis Ritchie"
        }
        result = self.match_question.validate_answer(user_answer)
        self.assertTrue(result['is_correct'])
        self.assertEqual(result['score'], 6)
    
    def test_matching_partial_credit(self):
        """Test partial credit for matching"""
        user_answer = {
            "Python": "Guido van Rossum",
            "Java": "Dennis Ritchie",  # Wrong
            "C": "James Gosling"  # Wrong
        }
        result = self.match_question.validate_answer(user_answer)
        self.assertFalse(result['is_correct'])
        self.assertEqual(result['correct_pairs'], 1)
        self.assertEqual(result['score'], 2)  # 1/3 * 6 marks


class DragDropQuestionTest(TestCase):
    """Test Drag and Drop Question functionality"""
    
    def setUp(self):
        self.course = Course.objects.create(
            course_name="Test Course",
            question_number=10,
            total_marks=100
        )
        
        self.dd_question = DragDropQuestion.objects.create(
            course=self.course,
            question_text="Arrange the steps of SDLC",
            drop_zones=["Step 1", "Step 2", "Step 3"],
            draggable_items=["Planning", "Design", "Implementation"],
            correct_mapping={
                "Step 1": "Planning",
                "Step 2": "Design",
                "Step 3": "Implementation"
            },
            marks=9
        )
    
    def test_drag_drop_creation(self):
        """Test Drag and Drop question creation"""
        self.assertEqual(len(self.dd_question.drop_zones), 3)
        self.assertEqual(len(self.dd_question.draggable_items), 3)
    
    def test_drag_drop_validation(self):
        """Test Drag and Drop validation"""
        user_answer = {
            "Step 1": ["Planning"],
            "Step 2": ["Design"],
            "Step 3": ["Implementation"]
        }
        result = self.dd_question.validate_answer(user_answer)
        self.assertTrue(result['is_correct'])
        self.assertEqual(result['score'], 9)


class NumericalQuestionTest(TestCase):
    """Test Numerical Question functionality"""
    
    def setUp(self):
        self.course = Course.objects.create(
            course_name="Test Course",
            question_number=10,
            total_marks=100
        )
        
        self.num_question = NumericalQuestion.objects.create(
            course=self.course,
            question_text="Calculate 15.5 + 24.3",
            correct_answer=Decimal("39.8"),
            tolerance=Decimal("0.1"),
            tolerance_type="absolute",
            marks=4
        )
    
    def test_numerical_exact_answer(self):
        """Test numerical with exact answer"""
        result = self.num_question.validate_answer(39.8)
        self.assertTrue(result['is_correct'])
        self.assertEqual(result['score'], 4)
    
    def test_numerical_within_tolerance(self):
        """Test numerical within tolerance"""
        result = self.num_question.validate_answer(39.85)  # Within ±0.1
        self.assertTrue(result['is_correct'])
        
        result = self.num_question.validate_answer(39.95)  # Outside tolerance
        self.assertFalse(result['is_correct'])
    
    def test_numerical_percentage_tolerance(self):
        """Test percentage-based tolerance"""
        num_pct = NumericalQuestion.objects.create(
            course=self.course,
            question_text="Calculate large number",
            correct_answer=Decimal("1000"),
            tolerance=Decimal("5"),  # 5%
            tolerance_type="percentage",
            marks=5
        )
        
        result = num_pct.validate_answer(1040)  # 4% off
        self.assertTrue(result['is_correct'])
        
        result = num_pct.validate_answer(1060)  # 6% off
        self.assertFalse(result['is_correct'])
    
    def test_numerical_with_units(self):
        """Test numerical with units"""
        num_units = NumericalQuestion.objects.create(
            course=self.course,
            question_text="Speed calculation",
            correct_answer=Decimal("50"),
            units="m/s",
            require_units=True,
            marks=5
        )
        
        result = num_units.validate_answer("50 m/s")
        self.assertTrue(result['is_correct'])
        
        result = num_units.validate_answer("50 km/h")  # Wrong units
        self.assertFalse(result['is_correct'])
        
        result = num_units.validate_answer("50")  # Missing units
        self.assertFalse(result['is_correct'])


class ValidatorTest(TestCase):
    """Test question validators"""
    
    def test_get_question_validator(self):
        """Test validator factory function"""
        validator = get_question_validator('MCQ')
        self.assertIsInstance(validator, MCQValidator)
        
        validator = get_question_validator('TF')
        self.assertIsInstance(validator, TrueFalseValidator)
        
        with self.assertRaises(ValueError):
            get_question_validator('INVALID')
    
    def test_mcq_validator(self):
        """Test MCQ validator"""
        validator = MCQValidator()
        
        question_data = {
            'question_text': 'Test question',
            'options': ['A', 'B', 'C', 'D'],
            'correct_option': 2,
            'marks': 5
        }
        
        result = validator.validate(question_data, 2)
        self.assertTrue(result['is_correct'])
        self.assertEqual(result['score'], 5)
    
    def test_fill_blank_validator_fuzzy(self):
        """Test Fill Blank validator with fuzzy matching"""
        validator = FillBlankValidator()
        
        question_data = {
            'question_text': 'Capital of France is ___',
            'correct_answers': ['Paris'],
            'partial_credit': True,
            'exact_match': False,
            'marks': 3
        }
        
        # Exact match
        result = validator.validate(question_data, 'Paris')
        self.assertTrue(result['is_correct'])
        
        # Close match
        result = validator.validate(question_data, 'Pari')
        self.assertGreater(result['score'], 0)


class ResultCalculationTest(TransactionTestCase):
    """Test result calculation with thread safety"""
    
    def setUp(self):
        self.user = User.objects.create_user('student', 'student@test.com', 'pass')
        self.student = Student.objects.create(user=self.user, address='Test', mobile='1234567890')
        
        self.course = Course.objects.create(
            course_name="Test Course",
            question_number=5,
            total_marks=20,
            pass_percentage=40
        )
        
        # Create various question types
        self.mcq = MCQQuestion.objects.create(
            course=self.course,
            question_text="MCQ Test",
            option1="A", option2="B",
            correct_option=1,
            marks=5
        )
        
        self.tf = TrueFalseQuestion.objects.create(
            course=self.course,
            question_text="TF Test",
            correct_answer=True,
            marks=5
        )
        
        self.fb = FillBlankQuestion.objects.create(
            course=self.course,
            question_text="FB Test",
            correct_answers=["answer"],
            marks=5
        )
        
        self.num = NumericalQuestion.objects.create(
            course=self.course,
            question_text="Num Test",
            correct_answer=Decimal("42"),
            tolerance=Decimal("0.1"),
            marks=5
        )
    
    def test_result_calculation(self):
        """Test comprehensive result calculation"""
        result = Result.objects.create(
            student=self.student,
            exam=self.course,
            marks=0
        )
        
        answers = {
            self.mcq.id: 1,  # Correct
            self.tf.id: True,  # Correct
            self.fb.id: "answer",  # Correct
            self.num.id: 42.05  # Correct (within tolerance)
        }
        
        result_data = result.calculate_result(answers)
        
        self.assertEqual(result_data['total_score'], 20)
        self.assertEqual(result_data['percentage'], 100)
        self.assertTrue(result_data['is_passed'])
        self.assertEqual(result_data['correct_questions'], 4)
    
    def test_partial_scoring(self):
        """Test partial scoring in results"""
        result = Result.objects.create(
            student=self.student,
            exam=self.course,
            marks=0
        )
        
        answers = {
            self.mcq.id: 2,  # Wrong
            self.tf.id: False,  # Wrong
            self.fb.id: "answer",  # Correct
            self.num.id: 50  # Wrong (outside tolerance)
        }
        
        result_data = result.calculate_result(answers)
        
        self.assertEqual(result_data['total_score'], 5)  # Only FB correct
        self.assertEqual(result_data['percentage'], 25)
        self.assertFalse(result_data['is_passed'])
    
    def test_concurrent_result_calculation(self):
        """Test thread-safe result calculation"""
        results = []
        
        def calculate_result_thread(student_id):
            result = Result.objects.create(
                student_id=student_id,
                exam=self.course,
                marks=0
            )
            answers = {
                self.mcq.id: 1,
                self.tf.id: True
            }
            return result.calculate_result(answers)
        
        # Create multiple students
        students = []
        for i in range(5):
            user = User.objects.create_user(f'student{i}', f'student{i}@test.com', 'pass')
            student = Student.objects.create(user=user, address='Test', mobile='123456789' + str(i))
            students.append(student.id)
        
        # Run concurrent calculations
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(calculate_result_thread, sid) for sid in students]
            results = [f.result() for f in futures]
        
        # All should complete successfully
        self.assertEqual(len(results), 5)
        for result_data in results:
            self.assertIn('total_score', result_data)
            self.assertEqual(result_data['total_score'], 10)  # MCQ + TF


class IntegrationTest(TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        self.client = Client()
        
        # Create teacher user
        self.teacher_user = User.objects.create_user('teacher', 'teacher@test.com', 'pass')
        teacher_group = Group.objects.create(name='TEACHER')
        self.teacher_user.groups.add(teacher_group)
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            address='Test',
            mobile='1234567890',
            status=True
        )
        
        # Create student user
        self.student_user = User.objects.create_user('student', 'student@test.com', 'pass')
        student_group = Group.objects.create(name='STUDENT')
        self.student_user.groups.add(student_group)
        self.student = Student.objects.create(
            user=self.student_user,
            address='Test',
            mobile='0987654321'
        )
        
        # Create course
        self.course = Course.objects.create(
            course_name="Integration Test Course",
            question_number=10,
            total_marks=100,
            show_result_immediately=True
        )
    
    def test_teacher_create_question_flow(self):
        """Test teacher creating different question types"""
        self.client.login(username='teacher', password='pass')
        
        # Test creating MCQ
        response = self.client.post(
            reverse('teacher-create-question', kwargs={
                'question_type': 'mcq',
                'course_id': self.course.id
            }),
            {
                'question_text': 'Test MCQ',
                'option1': 'A',
                'option2': 'B',
                'option3': 'C',
                'option4': 'D',
                'correct_option': 1,
                'marks': 5,
                'difficulty_level': 2
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(MCQQuestion.objects.filter(question_text='Test MCQ').exists())
    
    def test_student_take_exam_flow(self):
        """Test student taking an exam with multiple question types"""
        # Create questions
        mcq = MCQQuestion.objects.create(
            course=self.course,
            question_text="Test MCQ",
            option1="A", option2="B",
            correct_option=1,
            marks=10
        )
        
        tf = TrueFalseQuestion.objects.create(
            course=self.course,
            question_text="Test TF",
            correct_answer=True,
            marks=10
        )
        
        self.client.login(username='student', password='pass')
        
        # Take exam
        response = self.client.post(
            reverse('student-take-exam', kwargs={'course_id': self.course.id}),
            {
                f'answer_{mcq.id}': '1',
                f'answer_{tf.id}': 'True',
                'time_taken_seconds': '120'
            }
        )
        
        # Check result created
        result = Result.objects.filter(student=self.student, exam=self.course).first()
        self.assertIsNotNone(result)
        self.assertEqual(result.marks, 20)  # Both correct


class PerformanceTest(TestCase):
    """Performance and optimization tests"""
    
    def setUp(self):
        self.course = Course.objects.create(
            course_name="Performance Test",
            question_number=100,
            total_marks=500
        )
    
    def test_bulk_question_creation(self):
        """Test bulk creation of questions"""
        questions = []
        for i in range(100):
            questions.append(MCQQuestion(
                course=self.course,
                question_text=f"Question {i}",
                option1="A", option2="B",
                correct_option=1,
                marks=5
            ))
        
        MCQQuestion.objects.bulk_create(questions)
        self.assertEqual(MCQQuestion.objects.filter(course=self.course).count(), 100)
    
    def test_question_statistics_update(self):
        """Test efficient statistics update"""
        mcq = MCQQuestion.objects.create(
            course=self.course,
            question_text="Stats Test",
            option1="A", option2="B",
            correct_option=1,
            marks=5
        )
        
        # Simulate multiple attempts
        for i in range(100):
            mcq.times_attempted += 1
            if i % 2 == 0:  # 50% correct
                mcq.times_correct += 1
        
        mcq.save()
        
        success_rate = mcq.get_success_rate()
        self.assertEqual(success_rate, 50.0)


# Run all tests
if __name__ == '__main__':
    import unittest
    unittest.main()
