"""
Question Type Validators
Handles validation logic for different question types
"""
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal
import re
import json
from abc import ABC, abstractmethod
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)


class BaseQuestionValidator(ABC):
    """Abstract base class for question validators"""
    
    @abstractmethod
    def validate(self, question_data: Dict, user_answer: Any, **kwargs) -> Dict[str, Any]:
        """
        Validate user answer against question data
        Returns dict with 'is_correct', 'score', and 'feedback'
        """
        pass
    
    @abstractmethod
    def validate_question_data(self, question_data: Dict) -> None:
        """
        Validate question data structure
        Raises ValidationError if invalid
        """
        pass
    
    @abstractmethod
    def get_display_data(self, question_data: Dict) -> Dict[str, Any]:
        """Get data for rendering the question"""
        pass


class MCQValidator(BaseQuestionValidator):
    """Validator for Multiple Choice Questions"""
    
    def validate(self, question_data: Dict, user_answer: Any, **kwargs) -> Dict[str, Any]:
        """Validate MCQ answer"""
        allow_multiple = question_data.get('allow_multiple', False)
        marks = question_data.get('marks', 1)
        
        if allow_multiple:
            correct_options = question_data.get('correct_options', [])
            user_answers = user_answer if isinstance(user_answer, list) else [user_answer]
            is_correct = set(user_answers) == set(correct_options)
            correct_answer = correct_options
        else:
            correct_option = question_data.get('correct_option')
            is_correct = int(user_answer) == correct_option
            correct_answer = correct_option
        
        score = marks if is_correct else 0
        
        return {
            'is_correct': is_correct,
            'score': score,
            'feedback': question_data.get('explanation', ''),
            'correct_answer': correct_answer
        }
    
    def validate_question_data(self, question_data: Dict) -> None:
        """Validate MCQ data structure"""
        required_fields = ['question_text', 'options', 'correct_option', 'marks']
        for field in required_fields:
            if field not in question_data:
                raise ValidationError(f'Missing required field: {field}')
        
        options = question_data.get('options', [])
        if len(options) < 2:
            raise ValidationError('MCQ must have at least 2 options')
        
        correct_option = question_data.get('correct_option')
        if not (1 <= correct_option <= len(options)):
            raise ValidationError('Invalid correct option index')
        
        if question_data.get('allow_multiple'):
            correct_options = question_data.get('correct_options', [])
            if not correct_options:
                raise ValidationError('Multiple choice question must have correct_options')
            for opt in correct_options:
                if not (1 <= opt <= len(options)):
                    raise ValidationError(f'Invalid option index: {opt}')
    
    def get_display_data(self, question_data: Dict) -> Dict[str, Any]:
        """Get MCQ display data"""
        return {
            'type': 'mcq',
            'question': question_data.get('question_text'),
            'options': question_data.get('options'),
            'allow_multiple': question_data.get('allow_multiple', False),
            'marks': question_data.get('marks', 1)
        }


class TrueFalseValidator(BaseQuestionValidator):
    """Validator for True/False Questions"""
    
    def validate(self, question_data: Dict, user_answer: Any, **kwargs) -> Dict[str, Any]:
        """Validate True/False answer"""
        correct_answer = question_data.get('correct_answer')
        user_bool = self._parse_bool(user_answer)
        is_correct = user_bool == correct_answer
        marks = question_data.get('marks', 1)
        
        return {
            'is_correct': is_correct,
            'score': marks if is_correct else 0,
            'feedback': question_data.get('explanation', ''),
            'correct_answer': correct_answer
        }
    
    def _parse_bool(self, value: Any) -> bool:
        """Parse various boolean representations"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', 't', 'yes', 'y', '1')
        return bool(value)
    
    def validate_question_data(self, question_data: Dict) -> None:
        """Validate True/False data structure"""
        required_fields = ['question_text', 'correct_answer', 'marks']
        for field in required_fields:
            if field not in question_data:
                raise ValidationError(f'Missing required field: {field}')
        
        if not isinstance(question_data['correct_answer'], bool):
            raise ValidationError('correct_answer must be a boolean')
    
    def get_display_data(self, question_data: Dict) -> Dict[str, Any]:
        """Get True/False display data"""
        return {
            'type': 'true_false',
            'question': question_data.get('question_text'),
            'marks': question_data.get('marks', 1)
        }


class FillBlankValidator(BaseQuestionValidator):
    """Validator for Fill in the Blank Questions"""
    
    def validate(self, question_data: Dict, user_answer: Any, **kwargs) -> Dict[str, Any]:
        """Validate Fill in the Blank answer with advanced text processing"""
        user_answer = str(user_answer).strip()
        correct_answers = question_data.get('correct_answers', [])
        case_sensitive = question_data.get('case_sensitive', False)
        exact_match = question_data.get('exact_match', False)
        regex_pattern = question_data.get('regex_pattern', '')
        synonyms = question_data.get('synonyms', {})
        partial_credit = question_data.get('partial_credit', False)
        marks = question_data.get('marks', 1)
        
        if not case_sensitive:
            user_answer = user_answer.lower()
            correct_answers = [ans.lower() for ans in correct_answers]
        
        is_correct = False
        score = 0
        
        # Check regex pattern first
        if regex_pattern:
            try:
                pattern = re.compile(regex_pattern)
                if pattern.match(user_answer):
                    is_correct = True
                    score = marks
            except re.error:
                logger.error(f"Invalid regex pattern: {regex_pattern}")
        
        # Check exact match
        if not is_correct and exact_match:
            is_correct = user_answer in correct_answers
            if is_correct:
                score = marks
        
        # Check with synonyms
        if not is_correct and synonyms:
            for answer in correct_answers:
                if answer in synonyms:
                    synonym_list = synonyms[answer]
                    if not case_sensitive:
                        synonym_list = [s.lower() for s in synonym_list]
                    if user_answer in synonym_list:
                        is_correct = True
                        score = marks
                        break
        
        # Fuzzy matching for partial credit
        if not is_correct and partial_credit and not exact_match:
            from difflib import SequenceMatcher
            max_similarity = 0
            for answer in correct_answers:
                similarity = SequenceMatcher(None, user_answer, answer).ratio()
                max_similarity = max(max_similarity, similarity)
            
            if max_similarity >= 0.8:
                is_correct = True
                score = int(marks * max_similarity)
            elif max_similarity >= 0.5:
                score = int(marks * max_similarity * 0.5)
        
        # Final check
        if not is_correct and not score:
            is_correct = user_answer in correct_answers
            if is_correct:
                score = marks
        
        return {
            'is_correct': is_correct,
            'score': score,
            'feedback': question_data.get('explanation', ''),
            'correct_answers': question_data.get('correct_answers', []),
            'partial_credit_given': 0 < score < marks
        }
    
    def validate_question_data(self, question_data: Dict) -> None:
        """Validate Fill in the Blank data structure"""
        required_fields = ['question_text', 'correct_answers', 'marks']
        for field in required_fields:
            if field not in question_data:
                raise ValidationError(f'Missing required field: {field}')
        
        correct_answers = question_data.get('correct_answers', [])
        if not correct_answers:
            raise ValidationError('Must have at least one correct answer')
        
        if question_data.get('regex_pattern'):
            try:
                re.compile(question_data['regex_pattern'])
            except re.error:
                raise ValidationError('Invalid regex pattern')
    
    def get_display_data(self, question_data: Dict) -> Dict[str, Any]:
        """Get Fill in the Blank display data"""
        question_text = question_data.get('question_text', '')
        question_html = question_text.replace('___', '<input type="text" class="fill-blank-input" />')
        
        return {
            'type': 'fill_blank',
            'question': question_text,
            'question_html': question_html,
            'marks': question_data.get('marks', 1),
            'case_sensitive': question_data.get('case_sensitive', False)
        }


class ShortAnswerValidator(BaseQuestionValidator):
    """Validator for Short Answer Questions"""
    
    def validate(self, question_data: Dict, user_answer: Any, **kwargs) -> Dict[str, Any]:
        """Validate Short Answer with keyword matching"""
        user_answer = str(user_answer).strip()
        word_count = len(user_answer.split())
        
        min_words = question_data.get('min_words', 10)
        max_words = question_data.get('max_words', 100)
        keywords = question_data.get('keywords', [])
        keyword_weights = question_data.get('keyword_weights', {})
        marks = question_data.get('marks', 1)
        
        # Check word count
        if word_count < min_words:
            return {
                'is_correct': False,
                'score': 0,
                'feedback': f'Answer too short. Minimum {min_words} words required.',
                'word_count': word_count
            }
        
        if word_count > max_words:
            return {
                'is_correct': False,
                'score': 0,
                'feedback': f'Answer too long. Maximum {max_words} words allowed.',
                'word_count': word_count
            }
        
        score = 0
        feedback_points = []
        
        # Keyword-based scoring
        if keywords:
            user_answer_lower = user_answer.lower()
            keywords_found = []
            keywords_missed = []
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                weight = keyword_weights.get(keyword, 1.0)
                
                if keyword_lower in user_answer_lower:
                    keywords_found.append(keyword)
                    score += weight
                else:
                    keywords_missed.append(keyword)
            
            # Normalize score
            total_weight = sum(keyword_weights.values()) if keyword_weights else len(keywords)
            if total_weight > 0:
                score = int((score / total_weight) * marks)
            
            if keywords_found:
                feedback_points.append(f"Keywords found: {', '.join(keywords_found)}")
            if keywords_missed:
                feedback_points.append(f"Keywords missing: {', '.join(keywords_missed)}")
        
        is_correct = score >= (marks * 0.5)
        
        feedback = '\n'.join(feedback_points)
        if question_data.get('explanation'):
            feedback = f"{feedback}\n\n{question_data['explanation']}" if feedback else question_data['explanation']
        
        return {
            'is_correct': is_correct,
            'score': score,
            'feedback': feedback,
            'word_count': word_count,
            'model_answer': question_data.get('model_answer', '')
        }
    
    def validate_question_data(self, question_data: Dict) -> None:
        """Validate Short Answer data structure"""
        required_fields = ['question_text', 'marks']
        for field in required_fields:
            if field not in question_data:
                raise ValidationError(f'Missing required field: {field}')
        
        min_words = question_data.get('min_words', 10)
        max_words = question_data.get('max_words', 100)
        
        if min_words > max_words:
            raise ValidationError('min_words cannot be greater than max_words')
    
    def get_display_data(self, question_data: Dict) -> Dict[str, Any]:
        """Get Short Answer display data"""
        return {
            'type': 'short_answer',
            'question': question_data.get('question_text'),
            'marks': question_data.get('marks', 1),
            'max_words': question_data.get('max_words', 100),
            'min_words': question_data.get('min_words', 10)
        }


class MatchingValidator(BaseQuestionValidator):
    """Validator for Matching Questions"""
    
    def validate(self, question_data: Dict, user_answer: Any, **kwargs) -> Dict[str, Any]:
        """Validate Matching answer"""
        correct_pairs = question_data.get('correct_pairs', {})
        allow_partial_credit = question_data.get('allow_partial_credit', True)
        marks = question_data.get('marks', 1)
        
        if not isinstance(user_answer, dict):
            return {
                'is_correct': False,
                'score': 0,
                'feedback': 'Invalid answer format',
                'correct_pairs': 0,
                'total_pairs': len(correct_pairs)
            }
        
        correct_count = 0
        total_pairs = len(correct_pairs)
        feedback_items = []
        
        for left_item, right_item in user_answer.items():
            if left_item in correct_pairs:
                if correct_pairs[left_item] == right_item:
                    correct_count += 1
                    feedback_items.append(f"✓ {left_item} → {right_item}")
                else:
                    feedback_items.append(
                        f"✗ {left_item} → {right_item} (Correct: {correct_pairs[left_item]})"
                    )
        
        if allow_partial_credit:
            score = int((correct_count / total_pairs) * marks) if total_pairs > 0 else 0
        else:
            score = marks if correct_count == total_pairs else 0
        
        is_correct = correct_count == total_pairs
        
        feedback = '\n'.join(feedback_items)
        if question_data.get('explanation'):
            feedback = f"{feedback}\n\n{question_data['explanation']}"
        
        return {
            'is_correct': is_correct,
            'score': score,
            'feedback': feedback,
            'correct_pairs': correct_count,
            'total_pairs': total_pairs
        }
    
    def validate_question_data(self, question_data: Dict) -> None:
        """Validate Matching data structure"""
        required_fields = ['question_text', 'left_items', 'right_items', 'correct_pairs', 'marks']
        for field in required_fields:
            if field not in question_data:
                raise ValidationError(f'Missing required field: {field}')
        
        left_items = question_data.get('left_items', [])
        right_items = question_data.get('right_items', [])
        correct_pairs = question_data.get('correct_pairs', {})
        
        if len(left_items) != len(right_items):
            raise ValidationError('Number of left items must equal number of right items')
        
        for left_item in correct_pairs.keys():
            if left_item not in left_items:
                raise ValidationError(f'Invalid left item in correct_pairs: {left_item}')
            if correct_pairs[left_item] not in right_items:
                raise ValidationError(f'Invalid right item in correct_pairs: {correct_pairs[left_item]}')
    
    def get_display_data(self, question_data: Dict) -> Dict[str, Any]:
        """Get Matching display data"""
        import random
        
        left_items = question_data.get('left_items', [])
        right_items = question_data.get('right_items', [])[:]
        
        if question_data.get('shuffle_items', True):
            random.shuffle(right_items)
        
        return {
            'type': 'matching',
            'question': question_data.get('question_text'),
            'left_items': left_items,
            'right_items': right_items,
            'marks': question_data.get('marks', 1)
        }


class DragDropValidator(BaseQuestionValidator):
    """Validator for Drag and Drop Questions"""
    
    def validate(self, question_data: Dict, user_answer: Any, **kwargs) -> Dict[str, Any]:
        """Validate Drag and Drop answer"""
        correct_mapping = question_data.get('correct_mapping', {})
        draggable_items = question_data.get('draggable_items', [])
        marks = question_data.get('marks', 1)
        
        if not isinstance(user_answer, dict):
            return {
                'is_correct': False,
                'score': 0,
                'feedback': 'Invalid answer format',
                'correct_placements': 0,
                'total_items': len(draggable_items)
            }
        
        correct_placements = 0
        total_items = len(draggable_items)
        feedback_items = []
        
        for zone, items in user_answer.items():
            if zone in correct_mapping:
                correct_items = correct_mapping[zone]
                if not isinstance(correct_items, list):
                    correct_items = [correct_items]
                
                for item in items:
                    if item in correct_items:
                        correct_placements += 1
                        feedback_items.append(f"✓ {item} in {zone}")
                    else:
                        feedback_items.append(f"✗ {item} in {zone}")
        
        score = int((correct_placements / total_items) * marks) if total_items > 0 else 0
        is_correct = correct_placements == total_items
        
        feedback = '\n'.join(feedback_items)
        if question_data.get('explanation'):
            feedback = f"{feedback}\n\n{question_data['explanation']}"
        
        return {
            'is_correct': is_correct,
            'score': score,
            'feedback': feedback,
            'correct_placements': correct_placements,
            'total_items': total_items
        }
    
    def validate_question_data(self, question_data: Dict) -> None:
        """Validate Drag and Drop data structure"""
        required_fields = ['question_text', 'drop_zones', 'draggable_items', 'correct_mapping', 'marks']
        for field in required_fields:
            if field not in question_data:
                raise ValidationError(f'Missing required field: {field}')
        
        drop_zones = question_data.get('drop_zones', [])
        draggable_items = question_data.get('draggable_items', [])
        correct_mapping = question_data.get('correct_mapping', {})
        
        if not drop_zones or not draggable_items:
            raise ValidationError('Must have at least one drop zone and draggable item')
        
        # Validate correct_mapping
        all_mapped_items = []
        for zone in correct_mapping.keys():
            if zone not in drop_zones:
                raise ValidationError(f'Invalid drop zone in correct_mapping: {zone}')
            items = correct_mapping[zone]
            if not isinstance(items, list):
                items = [items]
            for item in items:
                if item not in draggable_items:
                    raise ValidationError(f'Invalid draggable item in correct_mapping: {item}')
                all_mapped_items.append(item)
    
    def get_display_data(self, question_data: Dict) -> Dict[str, Any]:
        """Get Drag and Drop display data"""
        import random
        
        draggable_items = question_data.get('draggable_items', [])[:]
        random.shuffle(draggable_items)
        
        return {
            'type': 'drag_drop',
            'question': question_data.get('question_text'),
            'drop_zones': question_data.get('drop_zones', []),
            'draggable_items': draggable_items,
            'allow_multiple_per_zone': question_data.get('allow_multiple_per_zone', False),
            'show_zones_labels': question_data.get('show_zones_labels', True),
            'marks': question_data.get('marks', 1)
        }


class NumericalValidator(BaseQuestionValidator):
    """Validator for Numerical Questions"""
    
    def validate(self, question_data: Dict, user_answer: Any, **kwargs) -> Dict[str, Any]:
        """Validate Numerical answer with tolerance"""
        try:
            correct_answer = Decimal(str(question_data.get('correct_answer')))
            tolerance = Decimal(str(question_data.get('tolerance', 0)))
            tolerance_type = question_data.get('tolerance_type', 'absolute')
            units = question_data.get('units', '')
            require_units = question_data.get('require_units', False)
            marks = question_data.get('marks', 1)
            
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
            
            # Check units
            if require_units and user_unit != units:
                return {
                    'is_correct': False,
                    'score': 0,
                    'feedback': f'Incorrect units. Expected: {units}, Got: {user_unit}',
                    'correct_answer': f'{correct_answer} {units}'.strip()
                }
            
            # Check tolerance
            if tolerance_type == 'absolute':
                is_within_tolerance = abs(user_value - correct_answer) <= tolerance
            elif tolerance_type == 'percentage':
                if correct_answer != 0:
                    percentage_diff = abs((user_value - correct_answer) / correct_answer) * 100
                    is_within_tolerance = percentage_diff <= float(tolerance)
                else:
                    is_within_tolerance = user_value == 0
            elif tolerance_type == 'significant_figures':
                from decimal import getcontext
                getcontext().prec = int(tolerance)
                is_within_tolerance = (
                    user_value.quantize(Decimal(10) ** -int(tolerance)) ==
                    correct_answer.quantize(Decimal(10) ** -int(tolerance))
                )
            else:
                is_within_tolerance = user_value == correct_answer
            
            score = marks if is_within_tolerance else 0
            
            feedback = ''
            if not is_within_tolerance:
                feedback = f'Your answer: {user_value}'
                if units:
                    feedback += f' {user_unit}'
                feedback += f'\nCorrect answer: {correct_answer}'
                if units:
                    feedback += f' {units}'
                if tolerance > 0:
                    feedback += f'\nTolerance: ±{tolerance}'
                    if tolerance_type == 'percentage':
                        feedback += '%'
            
            if question_data.get('explanation'):
                feedback = f"{feedback}\n\n{question_data['explanation']}" if feedback else question_data['explanation']
            
            return {
                'is_correct': is_within_tolerance,
                'score': score,
                'feedback': feedback,
                'correct_answer': f'{correct_answer} {units}'.strip(),
                'user_value': float(user_value),
                'tolerance': float(tolerance)
            }
            
        except (ValueError, TypeError, ArithmeticError) as e:
            return {
                'is_correct': False,
                'score': 0,
                'feedback': f'Invalid numerical format: {str(e)}',
                'correct_answer': f"{question_data.get('correct_answer', '')} {question_data.get('units', '')}".strip()
            }
    
    def validate_question_data(self, question_data: Dict) -> None:
        """Validate Numerical data structure"""
        required_fields = ['question_text', 'correct_answer', 'marks']
        for field in required_fields:
            if field not in question_data:
                raise ValidationError(f'Missing required field: {field}')
        
        try:
            Decimal(str(question_data['correct_answer']))
        except:
            raise ValidationError('Invalid correct_answer: must be a valid number')
        
        if 'tolerance' in question_data:
            try:
                Decimal(str(question_data['tolerance']))
            except:
                raise ValidationError('Invalid tolerance: must be a valid number')
        
        tolerance_type = question_data.get('tolerance_type', 'absolute')
        if tolerance_type not in ['absolute', 'percentage', 'significant_figures']:
            raise ValidationError('Invalid tolerance_type')
    
    def get_display_data(self, question_data: Dict) -> Dict[str, Any]:
        """Get Numerical display data"""
        hint = []
        if question_data.get('units'):
            hint.append(f"Units: {question_data['units']}")
        if question_data.get('decimal_places'):
            hint.append(f"Use {question_data['decimal_places']} decimal places")
        if question_data.get('scientific_notation'):
            hint.append("Use scientific notation")
        
        return {
            'type': 'numerical',
            'question': question_data.get('question_text'),
            'marks': question_data.get('marks', 1),
            'units': question_data.get('units', ''),
            'require_units': question_data.get('require_units', False),
            'hint': ', '.join(hint) if hint else None
        }


# Factory function to get the appropriate validator
def get_question_validator(question_type: str) -> BaseQuestionValidator:
    """Get the appropriate validator for a question type"""
    validators = {
        'MCQ': MCQValidator(),
        'TF': TrueFalseValidator(),
        'FB': FillBlankValidator(),
        'SA': ShortAnswerValidator(),
        'MT': MatchingValidator(),
        'DD': DragDropValidator(),
        'NUM': NumericalValidator(),
    }
    
    validator = validators.get(question_type)
    if not validator:
        raise ValueError(f"Unknown question type: {question_type}")
    
    return validator
