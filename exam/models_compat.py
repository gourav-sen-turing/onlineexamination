"""
Compatibility layer for existing models
This allows polymorphic questions to work alongside existing Question model
"""
from django.db import models
from exam.models import Course, Question, Result
from exam.models_polymorphic import PolymorphicQuestion, QuestionType
import json


def migrate_existing_questions():
    """
    Migrate existing MCQ questions to polymorphic model
    Run this once after applying migrations
    """
    migrated = 0
    for old_q in Question.objects.all():
        # Check if already migrated
        if PolymorphicQuestion.objects.filter(
            course=old_q.course,
            question_text=old_q.question
        ).exists():
            continue
        
        # Create polymorphic question
        data = {
            'option1': old_q.option1,
            'option2': old_q.option2,
            'option3': old_q.option3 if old_q.option3 else '',
            'option4': old_q.option4 if old_q.option4 else '',
            'correct_option': 1 if old_q.answer == 'Option1' else 
                             2 if old_q.answer == 'Option2' else
                             3 if old_q.answer == 'Option3' else 4,
            'allow_multiple': False
        }
        
        poly_q = PolymorphicQuestion(
            course=old_q.course,
            question_type=QuestionType.MCQ,
            question_text=old_q.question,
            marks=old_q.marks,
            question_data=json.dumps(data)
        )
        poly_q.save()
        migrated += 1
    
    return migrated


def create_mcq_question(course, question_text, option1, option2, option3='', option4='', 
                        correct_option=1, marks=1, explanation=''):
    """
    Helper function to create MCQ question
    Maintains compatibility with existing code
    """
    data = {
        'option1': option1,
        'option2': option2,
        'option3': option3,
        'option4': option4,
        'correct_option': correct_option,
        'allow_multiple': False
    }
    
    return PolymorphicQuestion.objects.create(
        course=course,
        question_type=QuestionType.MCQ,
        question_text=question_text,
        marks=marks,
        explanation=explanation,
        question_data=json.dumps(data)
    )


def create_true_false_question(course, question_text, correct_answer, marks=1, explanation=''):
    """Helper function to create True/False question"""
    data = {
        'correct_answer': correct_answer
    }
    
    return PolymorphicQuestion.objects.create(
        course=course,
        question_type=QuestionType.TRUE_FALSE,
        question_text=question_text,
        marks=marks,
        explanation=explanation,
        question_data=json.dumps(data)
    )


def create_fill_blank_question(course, question_text, correct_answers, marks=1, 
                              case_sensitive=False, explanation=''):
    """Helper function to create Fill in the Blank question"""
    if isinstance(correct_answers, str):
        correct_answers = [correct_answers]
    
    data = {
        'correct_answers': correct_answers,
        'case_sensitive': case_sensitive
    }
    
    return PolymorphicQuestion.objects.create(
        course=course,
        question_type=QuestionType.FILL_BLANK,
        question_text=question_text,
        marks=marks,
        explanation=explanation,
        question_data=json.dumps(data)
    )


def create_short_answer_question(course, question_text, keywords=None, min_words=10, 
                                max_words=100, marks=1, explanation=''):
    """Helper function to create Short Answer question"""
    data = {
        'keywords': keywords or [],
        'min_words': min_words,
        'max_words': max_words
    }
    
    return PolymorphicQuestion.objects.create(
        course=course,
        question_type=QuestionType.SHORT_ANSWER,
        question_text=question_text,
        marks=marks,
        explanation=explanation,
        question_data=json.dumps(data)
    )


def create_matching_question(course, question_text, left_items, right_items, 
                            correct_pairs, marks=1, explanation=''):
    """Helper function to create Matching question"""
    data = {
        'left_items': left_items,
        'right_items': right_items,
        'correct_pairs': correct_pairs
    }
    
    return PolymorphicQuestion.objects.create(
        course=course,
        question_type=QuestionType.MATCHING,
        question_text=question_text,
        marks=marks,
        explanation=explanation,
        question_data=json.dumps(data)
    )


def create_drag_drop_question(course, question_text, drop_zones, draggable_items,
                             correct_mapping, marks=1, explanation=''):
    """Helper function to create Drag and Drop question"""
    data = {
        'drop_zones': drop_zones,
        'draggable_items': draggable_items,
        'correct_mapping': correct_mapping
    }
    
    return PolymorphicQuestion.objects.create(
        course=course,
        question_type=QuestionType.DRAG_DROP,
        question_text=question_text,
        marks=marks,
        explanation=explanation,
        question_data=json.dumps(data)
    )


def create_numerical_question(course, question_text, correct_answer, tolerance=0,
                             marks=1, explanation=''):
    """Helper function to create Numerical question"""
    data = {
        'correct_answer': float(correct_answer),
        'tolerance': float(tolerance)
    }
    
    return PolymorphicQuestion.objects.create(
        course=course,
        question_type=QuestionType.NUMERICAL,
        question_text=question_text,
        marks=marks,
        explanation=explanation,
        question_data=json.dumps(data)
    )


class QuestionProxy:
    """
    Proxy class to make polymorphic questions work with existing views
    that expect the old Question model structure
    """
    def __init__(self, poly_question):
        self.poly_question = poly_question
        self.id = poly_question.id
        self.course = poly_question.course
        self.marks = poly_question.marks
        
        # Map to old field names
        self.question = poly_question.question_text
        
        # For MCQ compatibility
        data = poly_question.get_data()
        if poly_question.question_type == QuestionType.MCQ:
            self.option1 = data.get('option1', '')
            self.option2 = data.get('option2', '')
            self.option3 = data.get('option3', '')
            self.option4 = data.get('option4', '')
            correct_opt = data.get('correct_option', 1)
            self.answer = f'Option{correct_opt}'
    
    def validate_answer(self, user_answer):
        """Proxy to polymorphic validation"""
        return self.poly_question.validate_answer(user_answer)


def get_all_questions_for_course(course):
    """
    Get all questions for a course (both old and new)
    Returns list of QuestionProxy objects for compatibility
    """
    questions = []
    
    # Get old MCQ questions
    for q in Question.objects.filter(course=course):
        # Wrap in proxy if needed
        questions.append(q)
    
    # Get polymorphic questions
    for pq in PolymorphicQuestion.objects.filter(course=course, is_active=True):
        questions.append(QuestionProxy(pq))
    
    return questions
