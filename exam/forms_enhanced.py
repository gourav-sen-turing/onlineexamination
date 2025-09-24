"""
Enhanced Forms for Multiple Question Types
Dynamic form generation based on question type
"""
from django import forms
from django.forms import formset_factory, BaseFormSet
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
import json
from typing import Dict, Any, List

from .models_enhanced import (
    Course, MCQQuestion, TrueFalseQuestion, FillBlankQuestion,
    ShortAnswerQuestion, MatchingQuestion, DragDropQuestion,
    NumericalQuestion, Question, QuestionType
)


class CourseForm(forms.ModelForm):
    """Enhanced Course Form"""
    class Meta:
        model = Course
        fields = [
            'course_name', 'question_number', 'total_marks',
            'description', 'duration_minutes', 'pass_percentage',
            'randomize_questions', 'show_result_immediately', 'allow_review'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'course_name': forms.TextInput(attrs={'class': 'form-control'}),
            'question_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'pass_percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }


class BaseQuestionForm(forms.Form):
    """Base form for common question fields"""
    question_text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        label="Question"
    )
    marks = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        initial=1
    )
    explanation = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        label="Explanation (shown after answering)"
    )
    difficulty_level = forms.ChoiceField(
        choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Hard')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial=2
    )
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated tags'}),
        help_text="Enter tags separated by commas"
    )
    
    def clean_tags(self):
        """Convert comma-separated tags to list"""
        tags = self.cleaned_data.get('tags', '')
        if tags:
            return [tag.strip() for tag in tags.split(',') if tag.strip()]
        return []


class MCQQuestionForm(BaseQuestionForm, forms.ModelForm):
    """Form for Multiple Choice Questions"""
    class Meta:
        model = MCQQuestion
        fields = [
            'question_text', 'option1', 'option2', 'option3', 'option4',
            'correct_option', 'allow_multiple', 'correct_options',
            'marks', 'explanation', 'difficulty_level', 'tags'
        ]
        widgets = {
            'option1': forms.TextInput(attrs={'class': 'form-control'}),
            'option2': forms.TextInput(attrs={'class': 'form-control'}),
            'option3': forms.TextInput(attrs={'class': 'form-control'}),
            'option4': forms.TextInput(attrs={'class': 'form-control'}),
            'correct_option': forms.Select(attrs={'class': 'form-control'}),
        }
    
    correct_options = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=[(1, 'Option 1'), (2, 'Option 2'), (3, 'Option 3'), (4, 'Option 4')]
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.allow_multiple and self.instance.correct_options:
                self.fields['correct_options'].initial = self.instance.correct_options
    
    def clean(self):
        cleaned_data = super().clean()
        allow_multiple = cleaned_data.get('allow_multiple')
        
        if allow_multiple:
            correct_options = cleaned_data.get('correct_options')
            if not correct_options:
                raise ValidationError("Please select at least one correct option for multiple choice.")
            cleaned_data['correct_options'] = [int(opt) for opt in correct_options]
        else:
            correct_option = cleaned_data.get('correct_option')
            if not correct_option:
                raise ValidationError("Please select the correct option.")
        
        # Validate that selected options have corresponding text
        for i in range(1, 5):
            option_field = f'option{i}'
            if i <= 2 and not cleaned_data.get(option_field):
                raise ValidationError(f"Option {i} is required.")
        
        return cleaned_data


class TrueFalseQuestionForm(BaseQuestionForm, forms.ModelForm):
    """Form for True/False Questions"""
    class Meta:
        model = TrueFalseQuestion
        fields = ['question_text', 'correct_answer', 'marks', 'explanation', 'difficulty_level', 'tags']
        widgets = {
            'correct_answer': forms.RadioSelect(choices=[(True, 'True'), (False, 'False')])
        }


class FillBlankQuestionForm(BaseQuestionForm, forms.ModelForm):
    """Form for Fill in the Blank Questions"""
    class Meta:
        model = FillBlankQuestion
        fields = [
            'question_text', 'correct_answers', 'case_sensitive', 'exact_match',
            'regex_pattern', 'partial_credit', 'marks', 'explanation',
            'difficulty_level', 'tags'
        ]
        widgets = {
            'regex_pattern': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional regex pattern'}),
        }
    
    correct_answers = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        help_text="Enter acceptable answers, one per line"
    )
    
    synonyms_input = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        help_text="Enter synonyms in format: answer:synonym1,synonym2 (one per line)",
        label="Synonyms"
    )
    
    def clean_correct_answers(self):
        """Convert multiline text to list of answers"""
        answers = self.cleaned_data.get('correct_answers', '')
        return [ans.strip() for ans in answers.split('\n') if ans.strip()]
    
    def clean_synonyms_input(self):
        """Parse synonyms input into dictionary"""
        synonyms_text = self.cleaned_data.get('synonyms_input', '')
        synonyms = {}
        
        for line in synonyms_text.split('\n'):
            if ':' in line:
                answer, syns = line.split(':', 1)
                synonyms[answer.strip()] = [s.strip() for s in syns.split(',')]
        
        return synonyms
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.synonyms = self.cleaned_data.get('synonyms_input', {})
        if commit:
            instance.save()
        return instance


class ShortAnswerQuestionForm(BaseQuestionForm, forms.ModelForm):
    """Form for Short Answer Questions"""
    class Meta:
        model = ShortAnswerQuestion
        fields = [
            'question_text', 'model_answer', 'max_words', 'min_words',
            'keywords', 'use_ai_grading', 'marks', 'explanation',
            'difficulty_level', 'tags'
        ]
        widgets = {
            'model_answer': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'max_words': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'min_words': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
    
    keywords = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        help_text="Enter keywords, one per line"
    )
    
    keyword_weights_input = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        help_text="Enter keyword weights as keyword:weight (one per line)",
        label="Keyword Weights"
    )
    
    def clean_keywords(self):
        """Convert multiline text to list of keywords"""
        keywords = self.cleaned_data.get('keywords', '')
        return [kw.strip() for kw in keywords.split('\n') if kw.strip()]
    
    def clean_keyword_weights_input(self):
        """Parse keyword weights input"""
        weights_text = self.cleaned_data.get('keyword_weights_input', '')
        weights = {}
        
        for line in weights_text.split('\n'):
            if ':' in line:
                keyword, weight = line.split(':', 1)
                try:
                    weights[keyword.strip()] = float(weight.strip())
                except ValueError:
                    pass
        
        return weights
    
    def clean(self):
        cleaned_data = super().clean()
        min_words = cleaned_data.get('min_words')
        max_words = cleaned_data.get('max_words')
        
        if min_words and max_words and min_words > max_words:
            raise ValidationError("Minimum words cannot be greater than maximum words.")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.keyword_weights = self.cleaned_data.get('keyword_weights_input', {})
        if commit:
            instance.save()
        return instance


class MatchingQuestionForm(BaseQuestionForm, forms.ModelForm):
    """Form for Matching Questions"""
    class Meta:
        model = MatchingQuestion
        fields = [
            'question_text', 'allow_partial_credit', 'shuffle_items',
            'marks', 'explanation', 'difficulty_level', 'tags'
        ]
    
    pairs_input = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 6, 'class': 'form-control'}),
        help_text="Enter pairs as: left item -> right item (one per line)",
        label="Matching Pairs"
    )
    
    def clean_pairs_input(self):
        """Parse pairs input into left items, right items, and correct pairs"""
        pairs_text = self.cleaned_data.get('pairs_input', '')
        left_items = []
        right_items = []
        correct_pairs = {}
        
        for line in pairs_text.split('\n'):
            if '->' in line:
                left, right = line.split('->', 1)
                left = left.strip()
                right = right.strip()
                
                if left and right:
                    left_items.append(left)
                    right_items.append(right)
                    correct_pairs[left] = right
        
        if len(left_items) < 2:
            raise ValidationError("Please enter at least 2 matching pairs.")
        
        return {
            'left_items': left_items,
            'right_items': right_items,
            'correct_pairs': correct_pairs
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        pairs_data = self.cleaned_data['pairs_input']
        instance.left_items = pairs_data['left_items']
        instance.right_items = pairs_data['right_items']
        instance.correct_pairs = pairs_data['correct_pairs']
        if commit:
            instance.save()
        return instance


class DragDropQuestionForm(BaseQuestionForm, forms.ModelForm):
    """Form for Drag and Drop Questions"""
    class Meta:
        model = DragDropQuestion
        fields = [
            'question_text', 'allow_multiple_per_zone', 'show_zones_labels',
            'marks', 'explanation', 'difficulty_level', 'tags'
        ]
    
    zones_input = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        help_text="Enter drop zone names, one per line",
        label="Drop Zones"
    )
    
    items_input = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        help_text="Enter draggable items, one per line",
        label="Draggable Items"
    )
    
    mapping_input = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        help_text="Enter mapping as: zone -> item1, item2 (one per line)",
        label="Correct Mapping"
    )
    
    def clean_zones_input(self):
        """Parse zones input"""
        zones = self.cleaned_data.get('zones_input', '')
        return [z.strip() for z in zones.split('\n') if z.strip()]
    
    def clean_items_input(self):
        """Parse items input"""
        items = self.cleaned_data.get('items_input', '')
        return [i.strip() for i in items.split('\n') if i.strip()]
    
    def clean_mapping_input(self):
        """Parse mapping input"""
        mapping_text = self.cleaned_data.get('mapping_input', '')
        mapping = {}
        
        for line in mapping_text.split('\n'):
            if '->' in line:
                zone, items = line.split('->', 1)
                zone = zone.strip()
                items = [i.strip() for i in items.split(',')]
                
                if zone and items:
                    mapping[zone] = items if len(items) > 1 else items[0]
        
        return mapping
    
    def clean(self):
        cleaned_data = super().clean()
        zones = cleaned_data.get('zones_input', [])
        items = cleaned_data.get('items_input', [])
        mapping = cleaned_data.get('mapping_input', {})
        
        if not zones or not items:
            raise ValidationError("Please enter at least one drop zone and one draggable item.")
        
        # Validate mapping
        for zone in mapping.keys():
            if zone not in zones:
                raise ValidationError(f"Invalid zone in mapping: {zone}")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.drop_zones = self.cleaned_data['zones_input']
        instance.draggable_items = self.cleaned_data['items_input']
        instance.correct_mapping = self.cleaned_data['mapping_input']
        if commit:
            instance.save()
        return instance


class NumericalQuestionForm(BaseQuestionForm, forms.ModelForm):
    """Form for Numerical Questions"""
    class Meta:
        model = NumericalQuestion
        fields = [
            'question_text', 'correct_answer', 'tolerance', 'tolerance_type',
            'units', 'require_units', 'decimal_places', 'scientific_notation',
            'marks', 'explanation', 'difficulty_level', 'tags'
        ]
        widgets = {
            'correct_answer': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'tolerance': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'tolerance_type': forms.Select(attrs={'class': 'form-control'}),
            'units': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., kg, m/s'}),
            'decimal_places': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class UnifiedQuestionForm(forms.ModelForm):
    """Unified form for JSON-based questions"""
    class Meta:
        model = Question
        fields = ['course', 'question_type', 'marks']
        widgets = {
            'question_type': forms.Select(attrs={'class': 'form-control', 'id': 'question-type-select'}),
            'marks': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
    
    # Dynamic field that will be populated based on question type
    question_data_json = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add dynamic fields based on question type
        if self.instance and self.instance.pk:
            self._add_type_specific_fields(self.instance.question_type)
    
    def _add_type_specific_fields(self, question_type):
        """Add fields specific to the question type"""
        # This would be implemented to dynamically add fields
        # based on the selected question type
        pass


class DynamicQuestionAnswerForm(forms.Form):
    """Dynamic form for answering questions based on type"""
    
    def __init__(self, question, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.question = question
        self._build_form_fields()
    
    def _build_form_fields(self):
        """Build form fields based on question type"""
        if isinstance(self.question, MCQQuestion):
            self._build_mcq_fields()
        elif isinstance(self.question, TrueFalseQuestion):
            self._build_true_false_fields()
        elif isinstance(self.question, FillBlankQuestion):
            self._build_fill_blank_fields()
        elif isinstance(self.question, ShortAnswerQuestion):
            self._build_short_answer_fields()
        elif isinstance(self.question, MatchingQuestion):
            self._build_matching_fields()
        elif isinstance(self.question, DragDropQuestion):
            self._build_drag_drop_fields()
        elif isinstance(self.question, NumericalQuestion):
            self._build_numerical_fields()
        elif isinstance(self.question, Question):
            # Handle unified JSON-based questions
            self._build_unified_fields()
    
    def _build_mcq_fields(self):
        """Build MCQ answer fields"""
        choices = []
        for i in range(1, 5):
            option = getattr(self.question, f'option{i}', '')
            if option:
                choices.append((i, option))
        
        if self.question.allow_multiple:
            self.fields['answer'] = forms.MultipleChoiceField(
                choices=choices,
                widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
                required=False
            )
        else:
            self.fields['answer'] = forms.ChoiceField(
                choices=choices,
                widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                required=False
            )
    
    def _build_true_false_fields(self):
        """Build True/False answer fields"""
        self.fields['answer'] = forms.ChoiceField(
            choices=[(True, 'True'), (False, 'False')],
            widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
            required=False
        )
    
    def _build_fill_blank_fields(self):
        """Build Fill in the Blank answer fields"""
        # Count the number of blanks in the question
        num_blanks = self.question.question_text.count('___')
        
        if num_blanks > 1:
            for i in range(num_blanks):
                self.fields[f'answer_{i}'] = forms.CharField(
                    widget=forms.TextInput(attrs={'class': 'form-control fill-blank-input'}),
                    required=False
                )
        else:
            self.fields['answer'] = forms.CharField(
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                required=False
            )
    
    def _build_short_answer_fields(self):
        """Build Short Answer fields"""
        self.fields['answer'] = forms.CharField(
            widget=forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'data-max-words': self.question.max_words,
                'data-min-words': self.question.min_words
            }),
            required=False
        )
    
    def _build_matching_fields(self):
        """Build Matching answer fields"""
        for left_item in self.question.left_items:
            choices = [('', '-- Select --')] + [(item, item) for item in self.question.right_items]
            self.fields[f'match_{left_item}'] = forms.ChoiceField(
                choices=choices,
                widget=forms.Select(attrs={'class': 'form-control'}),
                label=left_item,
                required=False
            )
    
    def _build_drag_drop_fields(self):
        """Build Drag and Drop answer fields"""
        # This would typically be handled with JavaScript
        # Here we create hidden fields to store the mapping
        self.fields['drag_drop_mapping'] = forms.CharField(
            widget=forms.HiddenInput(),
            required=False
        )
    
    def _build_numerical_fields(self):
        """Build Numerical answer fields"""
        attrs = {'class': 'form-control', 'step': 'any'}
        
        if self.question.units and self.question.require_units:
            attrs['placeholder'] = f'Answer in {self.question.units}'
        
        self.fields['answer'] = forms.CharField(
            widget=forms.TextInput(attrs=attrs),
            required=False
        )
    
    def _build_unified_fields(self):
        """Build fields for unified JSON-based questions"""
        display_data = self.question.get_display_data()
        question_type = display_data.get('type')
        
        # Route to appropriate builder based on type
        type_builders = {
            'mcq': self._build_mcq_fields,
            'true_false': self._build_true_false_fields,
            'fill_blank': self._build_fill_blank_fields,
            'short_answer': self._build_short_answer_fields,
            'matching': self._build_matching_fields,
            'drag_drop': self._build_drag_drop_fields,
            'numerical': self._build_numerical_fields,
        }
        
        builder = type_builders.get(question_type)
        if builder:
            # Temporarily set question data for builder
            self.question._temp_data = display_data
            builder()
    
    def get_answer(self):
        """Extract answer from form data"""
        if not self.is_valid():
            return None
        
        question_type = self.question.question_type if hasattr(self.question, 'question_type') else None
        
        if question_type == QuestionType.MCQ:
            return self.cleaned_data.get('answer')
        elif question_type == QuestionType.TRUE_FALSE:
            answer = self.cleaned_data.get('answer')
            return answer == 'True' if isinstance(answer, str) else answer
        elif question_type == QuestionType.FILL_BLANK:
            # Handle multiple blanks
            answers = []
            i = 0
            while f'answer_{i}' in self.cleaned_data:
                answers.append(self.cleaned_data[f'answer_{i}'])
                i += 1
            return answers[0] if len(answers) == 1 else answers if answers else self.cleaned_data.get('answer')
        elif question_type == QuestionType.MATCHING:
            # Build matching pairs
            pairs = {}
            for field_name, value in self.cleaned_data.items():
                if field_name.startswith('match_') and value:
                    left_item = field_name.replace('match_', '')
                    pairs[left_item] = value
            return pairs
        elif question_type == QuestionType.DRAG_DROP:
            # Parse JSON mapping
            mapping_json = self.cleaned_data.get('drag_drop_mapping', '{}')
            try:
                return json.loads(mapping_json)
            except json.JSONDecodeError:
                return {}
        else:
            return self.cleaned_data.get('answer')


class QuestionBankImportForm(forms.Form):
    """Form for importing questions from various formats"""
    file = forms.FileField(
        label="Question Bank File",
        help_text="Upload CSV, JSON, or Excel file with questions"
    )
    file_format = forms.ChoiceField(
        choices=[
            ('csv', 'CSV'),
            ('json', 'JSON'),
            ('excel', 'Excel'),
            ('qti', 'QTI (Question & Test Interoperability)')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def clean_file(self):
        """Validate uploaded file"""
        file = self.cleaned_data['file']
        
        # Check file size (max 10MB)
        if file.size > 10 * 1024 * 1024:
            raise ValidationError("File size must not exceed 10MB")
        
        # Check file extension
        valid_extensions = {
            'csv': ['.csv'],
            'json': ['.json'],
            'excel': ['.xlsx', '.xls'],
            'qti': ['.xml', '.zip']
        }
        
        file_format = self.cleaned_data.get('file_format')
        if file_format:
            ext = file.name.split('.')[-1].lower()
            if f'.{ext}' not in valid_extensions.get(file_format, []):
                raise ValidationError(f"Invalid file extension for {file_format} format")
        
        return file


# Formset for bulk question creation
QuestionFormSet = formset_factory(
    BaseQuestionForm,
    extra=5,
    can_delete=True,
    can_order=True
)
