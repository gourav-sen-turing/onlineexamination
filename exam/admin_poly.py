"""
Admin configuration for polymorphic questions
Add this to your exam/admin.py
"""
from django.contrib import admin
from django import forms
import json
from exam.models_polymorphic import PolymorphicQuestion, CourseExtended, ResultExtended, QuestionType


class PolymorphicQuestionAdminForm(forms.ModelForm):
    """Custom form for editing polymorphic questions in admin"""
    
    # Add fields for different question types
    # MCQ fields
    option1 = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': 60}))
    option2 = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': 60}))
    option3 = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': 60}))
    option4 = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': 60}))
    correct_option = forms.IntegerField(required=False, min_value=1, max_value=4)
    
    # True/False fields
    correct_answer = forms.BooleanField(required=False)
    
    # Fill in Blank fields
    correct_answers = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text="One answer per line"
    )
    
    # Numerical fields
    correct_number = forms.DecimalField(required=False, decimal_places=2)
    tolerance = forms.DecimalField(required=False, decimal_places=2, initial=0)
    
    class Meta:
        model = PolymorphicQuestion
        fields = ['course', 'question_type', 'question_text', 'marks', 
                 'explanation', 'difficulty_level', 'is_active']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Load data from question_data field
            data = self.instance.get_data()
            
            if self.instance.question_type == QuestionType.MCQ:
                self.fields['option1'].initial = data.get('option1', '')
                self.fields['option2'].initial = data.get('option2', '')
                self.fields['option3'].initial = data.get('option3', '')
                self.fields['option4'].initial = data.get('option4', '')
                self.fields['correct_option'].initial = data.get('correct_option', 1)
            
            elif self.instance.question_type == QuestionType.TRUE_FALSE:
                self.fields['correct_answer'].initial = data.get('correct_answer', False)
            
            elif self.instance.question_type == QuestionType.FILL_BLANK:
                answers = data.get('correct_answers', [])
                self.fields['correct_answers'].initial = '\n'.join(answers)
            
            elif self.instance.question_type == QuestionType.NUMERICAL:
                self.fields['correct_number'].initial = data.get('correct_answer', 0)
                self.fields['tolerance'].initial = data.get('tolerance', 0)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Build question_data based on question type
        data = {}
        
        if instance.question_type == QuestionType.MCQ:
            data = {
                'option1': self.cleaned_data.get('option1', ''),
                'option2': self.cleaned_data.get('option2', ''),
                'option3': self.cleaned_data.get('option3', ''),
                'option4': self.cleaned_data.get('option4', ''),
                'correct_option': self.cleaned_data.get('correct_option', 1),
                'allow_multiple': False
            }
        
        elif instance.question_type == QuestionType.TRUE_FALSE:
            data = {
                'correct_answer': self.cleaned_data.get('correct_answer', False)
            }
        
        elif instance.question_type == QuestionType.FILL_BLANK:
            answers_text = self.cleaned_data.get('correct_answers', '')
            answers = [a.strip() for a in answers_text.split('\n') if a.strip()]
            data = {
                'correct_answers': answers,
                'case_sensitive': False
            }
        
        elif instance.question_type == QuestionType.NUMERICAL:
            data = {
                'correct_answer': float(self.cleaned_data.get('correct_number', 0)),
                'tolerance': float(self.cleaned_data.get('tolerance', 0))
            }
        
        elif instance.question_type == QuestionType.SHORT_ANSWER:
            data = {
                'keywords': [],
                'min_words': 10,
                'max_words': 100
            }
        
        elif instance.question_type == QuestionType.MATCHING:
            data = {
                'left_items': [],
                'right_items': [],
                'correct_pairs': {}
            }
        
        elif instance.question_type == QuestionType.DRAG_DROP:
            data = {
                'drop_zones': [],
                'draggable_items': [],
                'correct_mapping': {}
            }
        
        instance.set_data(data)
        
        if commit:
            instance.save()
        return instance


@admin.register(PolymorphicQuestion)
class PolymorphicQuestionAdmin(admin.ModelAdmin):
    form = PolymorphicQuestionAdminForm
    list_display = ['get_question_preview', 'question_type', 'course', 'marks', 
                   'difficulty_level', 'is_active', 'created_at']
    list_filter = ['question_type', 'course', 'difficulty_level', 'is_active']
    search_fields = ['question_text']
    readonly_fields = ['times_attempted', 'times_correct', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'question_type', 'question_text', 'marks', 
                      'difficulty_level', 'explanation')
        }),
        ('Question Type Specific', {
            'fields': ('option1', 'option2', 'option3', 'option4', 'correct_option',
                      'correct_answer', 'correct_answers', 'correct_number', 'tolerance'),
            'description': 'Fill in the fields relevant to your question type'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Statistics', {
            'fields': ('times_attempted', 'times_correct', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_question_preview(self, obj):
        """Show truncated question text"""
        return obj.question_text[:100] + '...' if len(obj.question_text) > 100 else obj.question_text
    get_question_preview.short_description = 'Question'
    
    class Media:
        js = ('admin/js/question_type_handler.js',)


@admin.register(CourseExtended)
class CourseExtendedAdmin(admin.ModelAdmin):
    list_display = ['course', 'duration_minutes', 'pass_percentage', 
                   'randomize_questions', 'created_at']
    list_filter = ['randomize_questions', 'show_result_immediately', 'allow_review']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ResultExtended)
class ResultExtendedAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'marks', 'percentage', 'grade', 
                   'is_passed', 'date']
    list_filter = ['is_passed', 'grade', 'date']
    search_fields = ['student__user__username', 'exam__course_name']
    readonly_fields = ['date', 'question_scores', 'answers_data']
    
    def has_add_permission(self, request):
        # Prevent manual creation of results
        return False
