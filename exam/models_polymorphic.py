"""
Polymorphic Question Models - SQLite Compatible
No PostgreSQL dependencies, works with existing exam app
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import transaction
import json
import re
from decimal import Decimal
from typing import Dict, List, Any, Optional, Union
import logging

from student.models import Student

logger = logging.getLogger(__name__)


# Keep original Course model to avoid conflicts
# Just extend it with new fields
class CourseExtended(models.Model):
    """Extended fields for Course - can be added to existing Course model"""
    course = models.OneToOneField('Course', on_delete=models.CASCADE, related_name='extended')
    description = models.TextField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=60)
    pass_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=40.00)
    randomize_questions = models.BooleanField(default=False)
    show_result_immediately = models.BooleanField(default=True)
    allow_review = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'exam_course_extended'


class QuestionType(models.TextChoices):
    """Enumeration of supported question types"""
    MCQ = 'MCQ', _('Multiple Choice Question')
    TRUE_FALSE = 'TF', _('True/False')
    FILL_BLANK = 'FB', _('Fill in the Blank')
    SHORT_ANSWER = 'SA', _('Short Answer')
    MATCHING = 'MT', _('Matching')
    DRAG_DROP = 'DD', _('Drag and Drop')
    NUMERICAL = 'NUM', _('Numerical')


class PolymorphicQuestion(models.Model):
    """
    Single model for all question types using JSON storage
    Works with SQLite, no PostgreSQL dependencies
    """
    # Reference to original Course model
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='poly_questions')
    
    # Common fields
    question_type = models.CharField(max_length=10, choices=QuestionType.choices, db_index=True)
    question_text = models.TextField()
    marks = models.PositiveIntegerField(default=1)
    explanation = models.TextField(blank=True)
    difficulty_level = models.IntegerField(
        choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Hard')],
        default=2
    )
    
    # Store all type-specific data as JSON (works with SQLite)
    question_data = models.TextField(default='{}')  # Store JSON as text for SQLite compatibility
    
    # Statistics
    times_attempted = models.PositiveIntegerField(default=0)
    times_correct = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'exam_polymorphic_question'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Ensure question_data is a string
        if isinstance(self.question_data, dict):
            self.question_data = json.dumps(self.question_data)
        super().save(*args, **kwargs)
    
    def get_data(self) -> Dict:
        """Get question data as dictionary"""
        if isinstance(self.question_data, str):
            try:
                return json.loads(self.question_data)
            except json.JSONDecodeError:
                return {}
        return self.question_data or {}
    
    def set_data(self, data: Dict):
        """Set question data from dictionary"""
        self.question_data = json.dumps(data)
    
    def get_success_rate(self) -> float:
        """Calculate success rate"""
        if self.times_attempted == 0:
            return 0.0
        return (self.times_correct / self.times_attempted) * 100
    
    def validate_answer(self, user_answer: Any) -> Dict[str, Any]:
        """Validate answer based on question type"""
        data = self.get_data()
        
        if self.question_type == QuestionType.MCQ:
            return self._validate_mcq(user_answer, data)
        elif self.question_type == QuestionType.TRUE_FALSE:
            return self._validate_true_false(user_answer, data)
        elif self.question_type == QuestionType.FILL_BLANK:
            return self._validate_fill_blank(user_answer, data)
        elif self.question_type == QuestionType.SHORT_ANSWER:
            return self._validate_short_answer(user_answer, data)
        elif self.question_type == QuestionType.MATCHING:
            return self._validate_matching(user_answer, data)
        elif self.question_type == QuestionType.DRAG_DROP:
            return self._validate_drag_drop(user_answer, data)
        elif self.question_type == QuestionType.NUMERICAL:
            return self._validate_numerical(user_answer, data)
        
        return {'is_correct': False, 'score': 0, 'feedback': 'Unknown question type'}
    
    def _validate_mcq(self, user_answer, data):
        """Validate MCQ answer"""
        correct_option = data.get('correct_option', 1)
        allow_multiple = data.get('allow_multiple', False)
        
        if allow_multiple:
            correct_options = data.get('correct_options', [])
            user_answers = user_answer if isinstance(user_answer, list) else [user_answer]
            is_correct = set(user_answers) == set(correct_options)
        else:
            is_correct = int(user_answer) == correct_option
        
        return {
            'is_correct': is_correct,
            'score': self.marks if is_correct else 0,
            'feedback': self.explanation,
            'correct_answer': data.get('correct_options') if allow_multiple else correct_option
        }
    
    def _validate_true_false(self, user_answer, data):
        """Validate True/False answer"""
        correct_answer = data.get('correct_answer', False)
        
        if isinstance(user_answer, str):
            user_bool = user_answer.lower() in ['true', 't', 'yes', '1']
        else:
            user_bool = bool(user_answer)
        
        is_correct = user_bool == correct_answer
        
        return {
            'is_correct': is_correct,
            'score': self.marks if is_correct else 0,
            'feedback': self.explanation,
            'correct_answer': correct_answer
        }
    
    def _validate_fill_blank(self, user_answer, data):
        """Validate Fill in the Blank answer"""
        correct_answers = data.get('correct_answers', [])
        case_sensitive = data.get('case_sensitive', False)
        
        user_answer = user_answer.strip()
        if not case_sensitive:
            user_answer = user_answer.lower()
            correct_answers = [ans.lower() for ans in correct_answers]
        
        is_correct = user_answer in correct_answers
        
        # Check with regex if provided
        regex_pattern = data.get('regex_pattern', '')
        if regex_pattern and not is_correct:
            try:
                pattern = re.compile(regex_pattern)
                is_correct = bool(pattern.match(user_answer))
            except re.error:
                pass
        
        return {
            'is_correct': is_correct,
            'score': self.marks if is_correct else 0,
            'feedback': self.explanation,
            'correct_answers': data.get('correct_answers', [])
        }
    
    def _validate_short_answer(self, user_answer, data):
        """Validate Short Answer"""
        keywords = data.get('keywords', [])
        min_words = data.get('min_words', 10)
        max_words = data.get('max_words', 100)
        
        user_answer = user_answer.strip()
        word_count = len(user_answer.split())
        
        if word_count < min_words or word_count > max_words:
            return {
                'is_correct': False,
                'score': 0,
                'feedback': f'Answer must be {min_words}-{max_words} words',
                'word_count': word_count
            }
        
        # Keyword scoring
        score = 0
        if keywords:
            user_answer_lower = user_answer.lower()
            keywords_found = sum(1 for kw in keywords if kw.lower() in user_answer_lower)
            score = int((keywords_found / len(keywords)) * self.marks)
        else:
            score = self.marks  # Full marks if no keywords specified
        
        return {
            'is_correct': score >= (self.marks * 0.5),
            'score': score,
            'feedback': self.explanation,
            'word_count': word_count
        }
    
    def _validate_matching(self, user_answer, data):
        """Validate Matching answer"""
        correct_pairs = data.get('correct_pairs', {})
        
        if not isinstance(user_answer, dict):
            return {
                'is_correct': False,
                'score': 0,
                'feedback': 'Invalid answer format',
                'correct_pairs': 0,
                'total_pairs': len(correct_pairs)
            }
        
        correct_count = sum(
            1 for left, right in user_answer.items()
            if correct_pairs.get(left) == right
        )
        
        total_pairs = len(correct_pairs)
        score = int((correct_count / total_pairs) * self.marks) if total_pairs > 0 else 0
        
        return {
            'is_correct': correct_count == total_pairs,
            'score': score,
            'feedback': self.explanation,
            'correct_pairs': correct_count,
            'total_pairs': total_pairs
        }
    
    def _validate_drag_drop(self, user_answer, data):
        """Validate Drag and Drop answer"""
        correct_mapping = data.get('correct_mapping', {})
        total_items = len(data.get('draggable_items', []))
        
        correct_placements = 0
        for zone, items in user_answer.items():
            if zone in correct_mapping:
                correct_items = correct_mapping[zone]
                if not isinstance(correct_items, list):
                    correct_items = [correct_items]
                correct_placements += sum(1 for item in items if item in correct_items)
        
        score = int((correct_placements / total_items) * self.marks) if total_items > 0 else 0
        
        return {
            'is_correct': correct_placements == total_items,
            'score': score,
            'feedback': self.explanation,
            'correct_placements': correct_placements,
            'total_items': total_items
        }
    
    def _validate_numerical(self, user_answer, data):
        """Validate Numerical answer"""
        try:
            correct_answer = Decimal(str(data.get('correct_answer', 0)))
            tolerance = Decimal(str(data.get('tolerance', 0)))
            
            # Parse user answer
            if isinstance(user_answer, str):
                # Extract number from string (might include units)
                match = re.match(r'^([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)', user_answer.strip())
                if match:
                    user_value = Decimal(match.group(1))
                else:
                    raise ValueError("Invalid number format")
            else:
                user_value = Decimal(str(user_answer))
            
            # Check tolerance
            is_within_tolerance = abs(user_value - correct_answer) <= tolerance
            
            return {
                'is_correct': is_within_tolerance,
                'score': self.marks if is_within_tolerance else 0,
                'feedback': self.explanation,
                'correct_answer': float(correct_answer),
                'user_value': float(user_value),
                'tolerance': float(tolerance)
            }
            
        except (ValueError, TypeError, ArithmeticError) as e:
            return {
                'is_correct': False,
                'score': 0,
                'feedback': f'Invalid numerical format: {str(e)}',
                'correct_answer': data.get('correct_answer', 0)
            }


class ResultExtended(models.Model):
    """Extended Result model for polymorphic questions"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey('Course', on_delete=models.CASCADE)
    marks = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=10, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    # Store detailed scores as text (JSON)
    question_scores = models.TextField(default='[]')
    answers_data = models.TextField(default='{}')
    
    is_passed = models.BooleanField(default=False)
    is_reviewed = models.BooleanField(default=False)
    review_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'exam_result_extended'
        ordering = ['-date']
    
    def get_question_scores(self):
        """Get question scores as list"""
        try:
            return json.loads(self.question_scores)
        except json.JSONDecodeError:
            return []
    
    def set_question_scores(self, scores):
        """Set question scores from list"""
        self.question_scores = json.dumps(scores)
    
    def get_answers_data(self):
        """Get answers data as dict"""
        try:
            return json.loads(self.answers_data)
        except json.JSONDecodeError:
            return {}
    
    def set_answers_data(self, data):
        """Set answers data from dict"""
        self.answers_data = json.dumps(data)
    
    @transaction.atomic
    def calculate_result(self, answers: Dict[int, Any]) -> Dict[str, Any]:
        """Calculate result for polymorphic questions"""
        questions = PolymorphicQuestion.objects.filter(
            course=self.exam, 
            is_active=True
        ).select_for_update()
        
        total_score = 0
        question_scores = []
        answers_data = {}
        
        for question in questions:
            question_id = question.id
            user_answer = answers.get(question_id)
            
            if user_answer is not None:
                validation_result = question.validate_answer(user_answer)
                score = validation_result.get('score', 0)
                
                # Update statistics
                question.times_attempted += 1
                if validation_result.get('is_correct', False):
                    question.times_correct += 1
                question.save(update_fields=['times_attempted', 'times_correct'])
                
                question_scores.append({
                    'question_id': question_id,
                    'question_type': question.question_type,
                    'marks': question.marks,
                    'scored': score,
                    'is_correct': validation_result.get('is_correct', False),
                    'feedback': validation_result.get('feedback', '')
                })
                
                answers_data[str(question_id)] = {
                    'user_answer': user_answer,
                    'correct_answer': validation_result.get('correct_answer'),
                    'score': score
                }
                
                total_score += score
            else:
                question_scores.append({
                    'question_id': question_id,
                    'question_type': question.question_type,
                    'marks': question.marks,
                    'scored': 0,
                    'is_correct': False,
                    'feedback': 'Not attempted'
                })
        
        # Update result
        self.marks = total_score
        self.set_question_scores(question_scores)
        self.set_answers_data(answers_data)
        
        # Calculate percentage
        from exam.models import Course
        course = Course.objects.get(id=self.exam_id)
        if course.total_marks > 0:
            self.percentage = Decimal((total_score / course.total_marks) * 100).quantize(Decimal('0.01'))
        
        self.save()
        
        return {
            'total_score': total_score,
            'percentage': float(self.percentage) if self.percentage else 0,
            'question_scores': question_scores,
            'total_questions': len(question_scores)
        }
