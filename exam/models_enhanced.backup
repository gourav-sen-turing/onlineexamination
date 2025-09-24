"""
Enhanced Models for Polymorphic Question Type System
Compatible with SQLite/MySQL/PostgreSQL - No external dependencies required
Supports: MCQ, True/False, Fill-in-the-Blank, Short Answer, 
Matching, Drag-and-Drop, and Numerical questions
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.core.cache import cache
import json
import re
from decimal import Decimal
from typing import Dict, List, Any, Optional, Union
import logging

from student.models import Student

logger = logging.getLogger(__name__)


class Course(models.Model):
    """Enhanced Course model with support for multiple question types"""
    course_name = models.CharField(max_length=50, db_index=True)
    question_number = models.PositiveIntegerField()
    total_marks = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=60)
    pass_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=40.00)
    randomize_questions = models.BooleanField(default=False)
    show_result_immediately = models.BooleanField(default=True)
    allow_review = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.course_name
    
    def get_questions_by_type(self):
        """Get questions grouped by type"""
        from collections import defaultdict
        questions_by_type = defaultdict(list)
        
        # Collect questions from all types
        for question in self.mcq_questions.filter(is_active=True):
            questions_by_type['MCQ'].append(question)
        for question in self.tf_questions.filter(is_active=True):
            questions_by_type['TF'].append(question)
        for question in self.fb_questions.filter(is_active=True):
            questions_by_type['FB'].append(question)
        for question in self.sa_questions.filter(is_active=True):
            questions_by_type['SA'].append(question)
        for question in self.mt_questions.filter(is_active=True):
            questions_by_type['MT'].append(question)
        for question in self.dd_questions.filter(is_active=True):
            questions_by_type['DD'].append(question)
        for question in self.num_questions.filter(is_active=True):
            questions_by_type['NUM'].append(question)
            
        return dict(questions_by_type)
    
    def clean(self):
        if self.pass_percentage < 0 or self.pass_percentage > 100:
            raise ValidationError(_('Pass percentage must be between 0 and 100'))


class QuestionType(models.TextChoices):
    """Enumeration of supported question types"""
    MCQ = 'MCQ', _('Multiple Choice Question')
    TRUE_FALSE = 'TF', _('True/False')
    FILL_BLANK = 'FB', _('Fill in the Blank')
    SHORT_ANSWER = 'SA', _('Short Answer')
    MATCHING = 'MT', _('Matching')
    DRAG_DROP = 'DD', _('Drag and Drop')
    NUMERICAL = 'NUM', _('Numerical')


class BaseQuestion(models.Model):
    """
    Abstract base model for all question types
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    question_type = models.CharField(max_length=10, choices=QuestionType.choices, db_index=True)
    question_text = models.TextField(help_text="The main question text")
    marks = models.PositiveIntegerField(default=1)
    explanation = models.TextField(blank=True, help_text="Explanation shown after answering")
    difficulty_level = models.IntegerField(
        choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Hard')],
        default=2
    )
    time_limit_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    # Store tags as JSON instead of ArrayField for compatibility
    tags = models.JSONField(default=list, blank=True, help_text="Tags for categorizing questions")
    
    # Metadata for question configuration
    config = models.JSONField(default=dict, help_text="Additional configuration specific to question type")
    
    # Statistics
    times_attempted = models.PositiveIntegerField(default=0)
    times_correct = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True
    
    def get_success_rate(self) -> float:
        """Calculate the success rate of this question"""
        if self.times_attempted == 0:
            return 0.0
        return (self.times_correct / self.times_attempted) * 100
    
    def validate_answer(self, user_answer: Any, **kwargs) -> Dict[str, Any]:
        """
        Validate user answer. Must be implemented by subclasses.
        Returns dictionary with 'is_correct', 'score', and 'feedback'
        """
        raise NotImplementedError("Subclasses must implement validate_answer")
    
    def get_display_data(self) -> Dict[str, Any]:
        """
        Get data for rendering the question in frontend
        Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement get_display_data")
    
    def clean(self):
        """Validate question data"""
        if self.marks < 0:
            raise ValidationError(_('Marks cannot be negative'))
        if self.difficulty_level not in [1, 2, 3]:
            raise ValidationError(_('Invalid difficulty level'))


class MCQQuestion(BaseQuestion):
    """Multiple Choice Question model - backward compatible with existing data"""
    option1 = models.CharField(max_length=500)
    option2 = models.CharField(max_length=500)
    option3 = models.CharField(max_length=500, blank=True)
    option4 = models.CharField(max_length=500, blank=True)
    correct_option = models.IntegerField(
        choices=[(1, 'Option 1'), (2, 'Option 2'), (3, 'Option 3'), (4, 'Option 4')]
    )
    allow_multiple = models.BooleanField(default=False)
    # Store multiple correct options as JSON for compatibility
    correct_options = models.JSONField(default=list, blank=True, null=True, help_text="For multiple correct answers")
    
    class Meta:
        verbose_name = "Multiple Choice Question"
        verbose_name_plural = "Multiple Choice Questions"
        
    def save(self, *args, **kwargs):
        self.question_type = QuestionType.MCQ
        super().save(*args, **kwargs)
    
    def get_options(self) -> List[str]:
        """Get list of non-empty options"""
        options = []
        for i in range(1, 5):
            option = getattr(self, f'option{i}', '')
            if option:
                options.append(option)
        return options
    
    def validate_answer(self, user_answer: Union[int, List[int]], **kwargs) -> Dict[str, Any]:
        """Validate MCQ answer"""
        if self.allow_multiple and self.correct_options:
            user_answers = user_answer if isinstance(user_answer, list) else [user_answer]
            is_correct = set(user_answers) == set(self.correct_options)
            score = self.marks if is_correct else 0
        else:
            is_correct = int(user_answer) == self.correct_option
            score = self.marks if is_correct else 0
        
        return {
            'is_correct': is_correct,
            'score': score,
            'feedback': self.explanation if self.explanation else '',
            'correct_answer': self.correct_options if self.allow_multiple else self.correct_option
        }
    
    def get_display_data(self) -> Dict[str, Any]:
        """Get MCQ display data"""
        return {
            'type': 'mcq',
            'question': self.question_text,
            'options': self.get_options(),
            'allow_multiple': self.allow_multiple,
            'marks': self.marks
        }


class TrueFalseQuestion(BaseQuestion):
    """True/False Question model"""
    correct_answer = models.BooleanField()
    
    class Meta:
        verbose_name = "True/False Question"
        verbose_name_plural = "True/False Questions"
    
    def save(self, *args, **kwargs):
        self.question_type = QuestionType.TRUE_FALSE
        super().save(*args, **kwargs)
    
    def validate_answer(self, user_answer: bool, **kwargs) -> Dict[str, Any]:
        """Validate True/False answer"""
        # Handle string answers
        if isinstance(user_answer, str):
            user_bool = user_answer.lower() in ['true', 't', 'yes', '1']
        else:
            user_bool = bool(user_answer)
            
        is_correct = user_bool == self.correct_answer
        
        return {
            'is_correct': is_correct,
            'score': self.marks if is_correct else 0,
            'feedback': self.explanation if self.explanation else '',
            'correct_answer': self.correct_answer
        }
    
    def get_display_data(self) -> Dict[str, Any]:
        """Get True/False display data"""
        return {
            'type': 'true_false',
            'question': self.question_text,
            'marks': self.marks
        }


class FillBlankQuestion(BaseQuestion):
    """Fill in the Blank Question model"""
    # Store as JSON for compatibility
    correct_answers = models.JSONField(default=list, help_text="List of acceptable answers")
    case_sensitive = models.BooleanField(default=False)
    exact_match = models.BooleanField(default=False)
    regex_pattern = models.CharField(max_length=500, blank=True, help_text="Regular expression for answer validation")
    synonyms = models.JSONField(default=dict, blank=True, help_text="Dictionary of synonyms for answers")
    partial_credit = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Fill in the Blank Question"
        verbose_name_plural = "Fill in the Blank Questions"
    
    def save(self, *args, **kwargs):
        self.question_type = QuestionType.FILL_BLANK
        super().save(*args, **kwargs)
    
    def validate_answer(self, user_answer: str, **kwargs) -> Dict[str, Any]:
        """Validate Fill in the Blank answer with advanced text processing"""
        user_answer = user_answer.strip()
        correct_answers = self.correct_answers
        
        if not self.case_sensitive:
            user_answer = user_answer.lower()
            correct_answers = [ans.lower() for ans in correct_answers]
        
        is_correct = False
        score = 0
        
        # Check regex pattern first if provided
        if self.regex_pattern:
            try:
                pattern = re.compile(self.regex_pattern)
                if pattern.match(user_answer):
                    is_correct = True
                    score = self.marks
            except re.error:
                logger.error(f"Invalid regex pattern for question {self.id}")
        
        # Check exact match
        if not is_correct and self.exact_match:
            is_correct = user_answer in correct_answers
            if is_correct:
                score = self.marks
        
        # Check with synonyms
        if not is_correct and self.synonyms:
            for answer in correct_answers:
                if answer in self.synonyms:
                    synonym_list = self.synonyms[answer]
                    if not self.case_sensitive:
                        synonym_list = [s.lower() for s in synonym_list]
                    if user_answer in synonym_list:
                        is_correct = True
                        score = self.marks
                        break
        
        # Fuzzy matching for partial credit
        if not is_correct and self.partial_credit and not self.exact_match:
            try:
                from difflib import SequenceMatcher
                max_similarity = 0
                for answer in correct_answers:
                    similarity = SequenceMatcher(None, user_answer, answer).ratio()
                    max_similarity = max(max_similarity, similarity)
                
                if max_similarity >= 0.8:
                    is_correct = True
                    score = int(self.marks * max_similarity)
                elif max_similarity >= 0.5:
                    score = int(self.marks * max_similarity * 0.5)
            except:
                pass
        
        # Final check for exact match without special processing
        if not is_correct and not score:
            is_correct = user_answer in correct_answers
            if is_correct:
                score = self.marks
        
        return {
            'is_correct': is_correct,
            'score': score,
            'feedback': self.explanation if self.explanation else '',
            'correct_answers': self.correct_answers,
            'partial_credit_given': score > 0 and score < self.marks
        }
    
    def get_display_data(self) -> Dict[str, Any]:
        """Get Fill in the Blank display data"""
        question_with_blanks = self.question_text.replace('___', '<input type="text" class="fill-blank-input" />')
        
        return {
            'type': 'fill_blank',
            'question': self.question_text,
            'question_html': question_with_blanks,
            'marks': self.marks,
            'case_sensitive': self.case_sensitive
        }


class ShortAnswerQuestion(BaseQuestion):
    """Short Answer Question model"""
    model_answer = models.TextField(help_text="Model answer for reference")
    max_words = models.PositiveIntegerField(default=100)
    keywords = models.JSONField(default=list, blank=True, help_text="Keywords that should be present in the answer")
    keyword_weights = models.JSONField(default=dict, blank=True, help_text="Weights for each keyword for scoring")
    use_ai_grading = models.BooleanField(default=False)
    min_words = models.PositiveIntegerField(default=10)
    
    class Meta:
        verbose_name = "Short Answer Question"
        verbose_name_plural = "Short Answer Questions"
    
    def save(self, *args, **kwargs):
        self.question_type = QuestionType.SHORT_ANSWER
        super().save(*args, **kwargs)
    
    def validate_answer(self, user_answer: str, **kwargs) -> Dict[str, Any]:
        """Validate Short Answer with keyword matching and text analysis"""
        user_answer = user_answer.strip()
        word_count = len(user_answer.split())
        
        # Check word count constraints
        if word_count < self.min_words:
            return {
                'is_correct': False,
                'score': 0,
                'feedback': f'Answer too short. Minimum {self.min_words} words required.',
                'word_count': word_count
            }
        
        if word_count > self.max_words:
            return {
                'is_correct': False,
                'score': 0,
                'feedback': f'Answer too long. Maximum {self.max_words} words allowed.',
                'word_count': word_count
            }
        
        score = 0
        max_score = self.marks
        feedback_points = []
        
        # Keyword-based scoring
        if self.keywords:
            user_answer_lower = user_answer.lower()
            keywords_found = []
            keywords_missed = []
            
            for keyword in self.keywords:
                keyword_lower = keyword.lower()
                weight = self.keyword_weights.get(keyword, 1.0) if self.keyword_weights else 1.0
                
                if keyword_lower in user_answer_lower:
                    keywords_found.append(keyword)
                    score += weight
                else:
                    keywords_missed.append(keyword)
            
            # Normalize score
            total_weight = sum(self.keyword_weights.values()) if self.keyword_weights else len(self.keywords)
            if total_weight > 0:
                score = int((score / total_weight) * max_score)
            
            if keywords_found:
                feedback_points.append(f"Keywords found: {', '.join(keywords_found)}")
            if keywords_missed:
                feedback_points.append(f"Keywords missing: {', '.join(keywords_missed)}")
        else:
            # If no keywords, give full marks if word count is correct
            score = max_score
        
        is_correct = score >= (max_score * 0.5)
        
        feedback = '\n'.join(feedback_points) if feedback_points else ''
        if self.explanation:
            feedback = f"{feedback}\n\n{self.explanation}" if feedback else self.explanation
        
        return {
            'is_correct': is_correct,
            'score': score,
            'feedback': feedback,
            'word_count': word_count,
            'model_answer': self.model_answer
        }
    
    def get_display_data(self) -> Dict[str, Any]:
        """Get Short Answer display data"""
        return {
            'type': 'short_answer',
            'question': self.question_text,
            'marks': self.marks,
            'max_words': self.max_words,
            'min_words': self.min_words
        }


class MatchingQuestion(BaseQuestion):
    """Matching Question model"""
    left_items = models.JSONField(default=list, help_text="Items on the left side")
    right_items = models.JSONField(default=list, help_text="Items on the right side")
    correct_pairs = models.JSONField(help_text="Dictionary mapping left items to right items")
    allow_partial_credit = models.BooleanField(default=True)
    shuffle_items = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Matching Question"
        verbose_name_plural = "Matching Questions"
    
    def save(self, *args, **kwargs):
        self.question_type = QuestionType.MATCHING
        super().save(*args, **kwargs)
    
    def clean(self):
        super().clean()
        if len(self.left_items) != len(self.right_items):
            raise ValidationError(_('Number of left items must equal number of right items'))
        
        # Validate correct_pairs structure
        for left_item in self.correct_pairs.keys():
            if left_item not in self.left_items:
                raise ValidationError(f'Invalid left item in correct_pairs: {left_item}')
            if self.correct_pairs[left_item] not in self.right_items:
                raise ValidationError(f'Invalid right item in correct_pairs: {self.correct_pairs[left_item]}')
    
    def validate_answer(self, user_answer: Dict[str, str], **kwargs) -> Dict[str, Any]:
        """Validate Matching answer"""
        correct_count = 0
        total_pairs = len(self.correct_pairs)
        feedback_items = []
        
        for left_item, right_item in user_answer.items():
            if left_item in self.correct_pairs:
                if self.correct_pairs[left_item] == right_item:
                    correct_count += 1
                    feedback_items.append(f"✓ {left_item} → {right_item}")
                else:
                    feedback_items.append(
                        f"✗ {left_item} → {right_item} (Correct: {self.correct_pairs[left_item]})"
                    )
        
        if self.allow_partial_credit:
            score = int((correct_count / total_pairs) * self.marks) if total_pairs > 0 else 0
        else:
            score = self.marks if correct_count == total_pairs else 0
        
        is_correct = correct_count == total_pairs
        
        feedback = '\n'.join(feedback_items)
        if self.explanation:
            feedback = f"{feedback}\n\n{self.explanation}"
        
        return {
            'is_correct': is_correct,
            'score': score,
            'feedback': feedback,
            'correct_pairs': correct_count,
            'total_pairs': total_pairs
        }
    
    def get_display_data(self) -> Dict[str, Any]:
        """Get Matching display data"""
        import random
        
        left_items = self.left_items.copy()
        right_items = self.right_items.copy()
        
        if self.shuffle_items:
            random.shuffle(right_items)
        
        return {
            'type': 'matching',
            'question': self.question_text,
            'left_items': left_items,
            'right_items': right_items,
            'marks': self.marks
        }


class DragDropQuestion(BaseQuestion):
    """Drag and Drop Question model"""
    drop_zones = models.JSONField(default=list, help_text="Names of drop zones")
    draggable_items = models.JSONField(default=list, help_text="Items that can be dragged")
    correct_mapping = models.JSONField(help_text="Mapping of drop zones to correct items")
    allow_multiple_per_zone = models.BooleanField(default=False)
    show_zones_labels = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Drag and Drop Question"
        verbose_name_plural = "Drag and Drop Questions"
    
    def save(self, *args, **kwargs):
        self.question_type = QuestionType.DRAG_DROP
        super().save(*args, **kwargs)
    
    def validate_answer(self, user_answer: Dict[str, List[str]], **kwargs) -> Dict[str, Any]:
        """Validate Drag and Drop answer"""
        correct_placements = 0
        total_items = len(self.draggable_items)
        feedback_items = []
        
        for zone, items in user_answer.items():
            if zone in self.correct_mapping:
                correct_items = self.correct_mapping[zone]
                if not isinstance(correct_items, list):
                    correct_items = [correct_items]
                
                for item in items:
                    if item in correct_items:
                        correct_placements += 1
                        feedback_items.append(f"✓ {item} in {zone}")
                    else:
                        feedback_items.append(f"✗ {item} in {zone}")
        
        score = int((correct_placements / total_items) * self.marks) if total_items > 0 else 0
        is_correct = correct_placements == total_items
        
        feedback = '\n'.join(feedback_items)
        if self.explanation:
            feedback = f"{feedback}\n\n{self.explanation}"
        
        return {
            'is_correct': is_correct,
            'score': score,
            'feedback': feedback,
            'correct_placements': correct_placements,
            'total_items': total_items
        }
    
    def get_display_data(self) -> Dict[str, Any]:
        """Get Drag and Drop display data"""
        import random
        
        draggable_items = self.draggable_items.copy()
        random.shuffle(draggable_items)
        
        return {
            'type': 'drag_drop',
            'question': self.question_text,
            'drop_zones': self.drop_zones,
            'draggable_items': draggable_items,
            'allow_multiple_per_zone': self.allow_multiple_per_zone,
            'show_zones_labels': self.show_zones_labels,
            'marks': self.marks
        }


class NumericalQuestion(BaseQuestion):
    """Numerical Question model"""
    correct_answer = models.DecimalField(max_digits=20, decimal_places=10)
    tolerance = models.DecimalField(max_digits=20, decimal_places=10, default=0, 
                                   help_text="Acceptable deviation from correct answer")
    tolerance_type = models.CharField(
        max_length=20,
        choices=[
            ('absolute', 'Absolute'),
            ('percentage', 'Percentage'),
            ('significant_figures', 'Significant Figures')
        ],
        default='absolute'
    )
    units = models.CharField(max_length=50, blank=True)
    require_units = models.BooleanField(default=False)
    decimal_places = models.PositiveIntegerField(null=True, blank=True, 
                                                help_text="Required decimal places in answer")
    scientific_notation = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Numerical Question"
        verbose_name_plural = "Numerical Questions"
    
    def save(self, *args, **kwargs):
        self.question_type = QuestionType.NUMERICAL
        super().save(*args, **kwargs)
    
    def validate_answer(self, user_answer: Union[str, float], **kwargs) -> Dict[str, Any]:
        """Validate Numerical answer with tolerance ranges"""
        try:
            # Parse user answer
            if isinstance(user_answer, str):
                match = re.match(r'^([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*(.*)$', user_answer.strip())
                if match:
                    number_str, unit_str = match.groups()
                    user_value = Decimal(number_str)
                    user_unit = unit_str.strip()
                else:
                    raise ValueError("Invalid numerical format")
            else:
                user_value = Decimal(str(user_answer))
                user_unit = ''
            
            # Check units if required
            if self.require_units:
                if user_unit != self.units:
                    return {
                        'is_correct': False,
                        'score': 0,
                        'feedback': f'Incorrect units. Expected: {self.units}, Got: {user_unit}',
                        'correct_answer': f'{self.correct_answer} {self.units}'
                    }
            
            # Calculate tolerance
            correct_value = self.correct_answer
            
            if self.tolerance_type == 'absolute':
                is_within_tolerance = abs(user_value - correct_value) <= self.tolerance
            elif self.tolerance_type == 'percentage':
                if correct_value != 0:
                    percentage_diff = abs((user_value - correct_value) / correct_value) * 100
                    is_within_tolerance = percentage_diff <= float(self.tolerance)
                else:
                    is_within_tolerance = user_value == 0
            else:
                is_within_tolerance = user_value == correct_value
            
            score = self.marks if is_within_tolerance else 0
            
            feedback = ''
            if not is_within_tolerance:
                feedback = f'Your answer: {user_value}'
                if self.units:
                    feedback += f' {user_unit}'
                feedback += f'\nCorrect answer: {self.correct_answer}'
                if self.units:
                    feedback += f' {self.units}'
                if self.tolerance > 0:
                    feedback += f'\nTolerance: ±{self.tolerance}'
                    if self.tolerance_type == 'percentage':
                        feedback += '%'
            
            if self.explanation:
                feedback = f"{feedback}\n\n{self.explanation}" if feedback else self.explanation
            
            return {
                'is_correct': is_within_tolerance,
                'score': score,
                'feedback': feedback,
                'correct_answer': f'{self.correct_answer} {self.units}'.strip(),
                'user_value': float(user_value),
                'tolerance': float(self.tolerance)
            }
            
        except (ValueError, TypeError, ArithmeticError) as e:
            return {
                'is_correct': False,
                'score': 0,
                'feedback': f'Invalid numerical format: {str(e)}',
                'correct_answer': f'{self.correct_answer} {self.units}'.strip()
            }
    
    def get_display_data(self) -> Dict[str, Any]:
        """Get Numerical display data"""
        hint = []
        if self.units:
            hint.append(f"Units: {self.units}")
        if self.decimal_places is not None:
            hint.append(f"Use {self.decimal_places} decimal places")
        if self.scientific_notation:
            hint.append("Use scientific notation")
        
        return {
            'type': 'numerical',
            'question': self.question_text,
            'marks': self.marks,
            'units': self.units,
            'require_units': self.require_units,
            'hint': ', '.join(hint) if hint else None
        }


class Result(models.Model):
    """Enhanced Result model with detailed scoring"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_results')
    exam = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exam_results')
    marks = models.PositiveIntegerField()
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=10, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    # Detailed scoring breakdown
    question_scores = models.JSONField(default=list, help_text="List of question-wise scores")
    answers_data = models.JSONField(default=dict, help_text="Complete answers data for review")
    
    # Status flags
    is_passed = models.BooleanField(default=False)
    is_reviewed = models.BooleanField(default=False)
    review_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.student.get_name} - {self.exam.course_name} - {self.marks}"
    
    def calculate_grade(self):
        """Calculate grade based on percentage"""
        if self.percentage >= 90:
            return 'A+'
        elif self.percentage >= 80:
            return 'A'
        elif self.percentage >= 70:
            return 'B'
        elif self.percentage >= 60:
            return 'C'
        elif self.percentage >= 50:
            return 'D'
        elif self.percentage >= 40:
            return 'E'
        else:
            return 'F'
    
    def save(self, *args, **kwargs):
        """Auto-calculate percentage and grade"""
        if self.exam.total_marks > 0:
            self.percentage = Decimal((self.marks / self.exam.total_marks) * 100).quantize(Decimal('0.01'))
            self.is_passed = self.percentage >= self.exam.pass_percentage
            self.grade = self.calculate_grade()
        super().save(*args, **kwargs)
    
    @transaction.atomic
    def calculate_result(self, answers: Dict[int, Any]) -> Dict[str, Any]:
        """
        Thread-safe result calculation with detailed scoring
        Returns complete result data
        """
        total_score = 0
        question_scores = []
        answers_data = {}
        
        # Get all questions for this course
        all_questions = []
        
        # Collect all question types
        all_questions.extend(MCQQuestion.objects.filter(course=self.exam, is_active=True))
        all_questions.extend(TrueFalseQuestion.objects.filter(course=self.exam, is_active=True))
        all_questions.extend(FillBlankQuestion.objects.filter(course=self.exam, is_active=True))
        all_questions.extend(ShortAnswerQuestion.objects.filter(course=self.exam, is_active=True))
        all_questions.extend(MatchingQuestion.objects.filter(course=self.exam, is_active=True))
        all_questions.extend(DragDropQuestion.objects.filter(course=self.exam, is_active=True))
        all_questions.extend(NumericalQuestion.objects.filter(course=self.exam, is_active=True))
        
        for question in all_questions:
            question_id = question.id
            user_answer = answers.get(question_id)
            
            if user_answer is not None:
                # Validate answer
                validation_result = question.validate_answer(user_answer)
                score = validation_result.get('score', 0)
                
                # Update question statistics
                question.times_attempted += 1
                if validation_result.get('is_correct', False):
                    question.times_correct += 1
                question.save(update_fields=['times_attempted', 'times_correct'])
                
                # Store scoring data
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
                # Question not attempted
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
        self.question_scores = question_scores
        self.answers_data = answers_data
        self.save()
        
        return {
            'total_score': total_score,
            'percentage': float(self.percentage) if self.percentage else 0,
            'grade': self.grade,
            'is_passed': self.is_passed,
            'question_scores': question_scores,
            'total_questions': len(question_scores),
            'attempted_questions': sum(1 for qs in question_scores if qs['feedback'] != 'Not attempted'),
            'correct_questions': sum(1 for qs in question_scores if qs['is_correct'])
        }


# Backward compatibility - keep old Question model reference
Question = MCQQuestion
