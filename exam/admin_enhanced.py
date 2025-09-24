"""
Enhanced Admin Interface for Multiple Question Types
"""
from django.contrib import admin
from django.db import models
from django.forms import Textarea, TextInput
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models_enhanced import (
    Course, MCQQuestion, TrueFalseQuestion, FillBlankQuestion,
    ShortAnswerQuestion, MatchingQuestion, DragDropQuestion,
    NumericalQuestion, Question, Result
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_name', 'question_number', 'total_marks', 'duration_minutes', 
                    'pass_percentage', 'created_at', 'question_count']
    list_filter = ['randomize_questions', 'show_result_immediately', 'allow_review', 'created_at']
    search_fields = ['course_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course_name', 'description', 'question_number', 'total_marks')
        }),
        ('Exam Settings', {
            'fields': ('duration_minutes', 'pass_percentage', 'randomize_questions', 
                      'show_result_immediately', 'allow_review')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def question_count(self, obj):
        """Count total questions across all types"""
        count = 0
        count += obj.mcq_questions.filter(is_active=True).count()
        count += obj.tf_questions.filter(is_active=True).count()
        count += obj.fb_questions.filter(is_active=True).count()
        count += obj.sa_questions.filter(is_active=True).count()
        count += obj.mt_questions.filter(is_active=True).count()
        count += obj.dd_questions.filter(is_active=True).count()
        count += obj.num_questions.filter(is_active=True).count()
        count += obj.unified_questions.filter(is_active=True).count()
        return count
    question_count.short_description = 'Total Questions'


class BaseQuestionAdmin(admin.ModelAdmin):
    """Base admin class for all question types"""
    list_display = ['get_question_preview', 'course', 'marks', 'difficulty_level', 
                    'is_active', 'success_rate']
    list_filter = ['course', 'difficulty_level', 'is_active', 'created_at']
    search_fields = ['question_text', 'tags']
    readonly_fields = ['times_attempted', 'times_correct', 'success_rate', 
                       'created_at', 'updated_at']
    list_per_page = 20
    
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80})},
        models.CharField: {'widget': TextInput(attrs={'size': '60'})},
    }
    
    def get_question_preview(self, obj):
        """Show truncated question text"""
        return obj.question_text[:100] + '...' if len(obj.question_text) > 100 else obj.question_text
    get_question_preview.short_description = 'Question'
    
    def success_rate(self, obj):
        """Display success rate with color coding"""
        rate = obj.get_success_rate()
        color = 'green' if rate >= 70 else 'orange' if rate >= 40 else 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, rate
        )
    success_rate.short_description = 'Success Rate'


@admin.register(MCQQuestion)
class MCQQuestionAdmin(BaseQuestionAdmin):
    fieldsets = (
        ('Question', {
            'fields': ('course', 'question_text', 'marks', 'difficulty_level', 'explanation')
        }),
        ('Options', {
            'fields': ('option1', 'option2', 'option3', 'option4')
        }),
        ('Answer', {
            'fields': ('correct_option', 'allow_multiple', 'correct_options')
        }),
        ('Metadata', {
            'fields': ('tags', 'time_limit_seconds', 'config', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('times_attempted', 'times_correct', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_list_display(self, request):
        """Customize list display for MCQ"""
        return ['get_question_preview', 'course', 'get_options_count', 'correct_option', 
                'marks', 'difficulty_level', 'is_active', 'success_rate']
    
    def get_options_count(self, obj):
        """Count non-empty options"""
        count = sum(1 for i in range(1, 5) if getattr(obj, f'option{i}'))
        return f"{count} options"
    get_options_count.short_description = 'Options'


@admin.register(TrueFalseQuestion)
class TrueFalseQuestionAdmin(BaseQuestionAdmin):
    fieldsets = (
        ('Question', {
            'fields': ('course', 'question_text', 'marks', 'difficulty_level', 'explanation')
        }),
        ('Answer', {
            'fields': ('correct_answer',)
        }),
        ('Metadata', {
            'fields': ('tags', 'time_limit_seconds', 'config', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('times_attempted', 'times_correct', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_list_display(self, request):
        return ['get_question_preview', 'course', 'get_answer_display', 
                'marks', 'difficulty_level', 'is_active', 'success_rate']
    
    def get_answer_display(self, obj):
        """Display answer with icon"""
        if obj.correct_answer:
            return format_html('<span style="color: green;">✓ True</span>')
        else:
            return format_html('<span style="color: red;">✗ False</span>')
    get_answer_display.short_description = 'Correct Answer'


@admin.register(FillBlankQuestion)
class FillBlankQuestionAdmin(BaseQuestionAdmin):
    fieldsets = (
        ('Question', {
            'fields': ('course', 'question_text', 'marks', 'difficulty_level', 'explanation')
        }),
        ('Answers', {
            'fields': ('correct_answers', 'case_sensitive', 'exact_match', 'partial_credit')
        }),
        ('Advanced Matching', {
            'fields': ('regex_pattern', 'synonyms'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('tags', 'time_limit_seconds', 'config', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('times_attempted', 'times_correct', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_list_display(self, request):
        return ['get_question_preview', 'course', 'get_answers_count', 
                'case_sensitive', 'marks', 'difficulty_level', 'is_active', 'success_rate']
    
    def get_answers_count(self, obj):
        """Count acceptable answers"""
        return f"{len(obj.correct_answers)} answer(s)"
    get_answers_count.short_description = 'Acceptable Answers'


@admin.register(ShortAnswerQuestion)
class ShortAnswerQuestionAdmin(BaseQuestionAdmin):
    fieldsets = (
        ('Question', {
            'fields': ('course', 'question_text', 'marks', 'difficulty_level', 'explanation')
        }),
        ('Answer Requirements', {
            'fields': ('model_answer', 'min_words', 'max_words')
        }),
        ('Grading', {
            'fields': ('keywords', 'keyword_weights', 'use_ai_grading')
        }),
        ('Metadata', {
            'fields': ('tags', 'time_limit_seconds', 'config', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('times_attempted', 'times_correct', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_list_display(self, request):
        return ['get_question_preview', 'course', 'get_word_limits', 'get_keywords_count',
                'marks', 'difficulty_level', 'is_active', 'success_rate']
    
    def get_word_limits(self, obj):
        """Display word limits"""
        return f"{obj.min_words}-{obj.max_words} words"
    get_word_limits.short_description = 'Word Limits'
    
    def get_keywords_count(self, obj):
        """Count keywords"""
        return f"{len(obj.keywords)} keyword(s)" if obj.keywords else "No keywords"
    get_keywords_count.short_description = 'Keywords'


@admin.register(MatchingQuestion)
class MatchingQuestionAdmin(BaseQuestionAdmin):
    fieldsets = (
        ('Question', {
            'fields': ('course', 'question_text', 'marks', 'difficulty_level', 'explanation')
        }),
        ('Matching Items', {
            'fields': ('left_items', 'right_items', 'correct_pairs')
        }),
        ('Settings', {
            'fields': ('allow_partial_credit', 'shuffle_items')
        }),
        ('Metadata', {
            'fields': ('tags', 'time_limit_seconds', 'config', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('times_attempted', 'times_correct', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_list_display(self, request):
        return ['get_question_preview', 'course', 'get_pairs_count', 
                'allow_partial_credit', 'marks', 'difficulty_level', 'is_active', 'success_rate']
    
    def get_pairs_count(self, obj):
        """Count matching pairs"""
        return f"{len(obj.correct_pairs)} pair(s)"
    get_pairs_count.short_description = 'Pairs'


@admin.register(DragDropQuestion)
class DragDropQuestionAdmin(BaseQuestionAdmin):
    fieldsets = (
        ('Question', {
            'fields': ('course', 'question_text', 'marks', 'difficulty_level', 'explanation')
        }),
        ('Drag and Drop Items', {
            'fields': ('drop_zones', 'draggable_items', 'correct_mapping')
        }),
        ('Settings', {
            'fields': ('allow_multiple_per_zone', 'show_zones_labels')
        }),
        ('Metadata', {
            'fields': ('tags', 'time_limit_seconds', 'config', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('times_attempted', 'times_correct', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_list_display(self, request):
        return ['get_question_preview', 'course', 'get_zones_count', 'get_items_count',
                'marks', 'difficulty_level', 'is_active', 'success_rate']
    
    def get_zones_count(self, obj):
        """Count drop zones"""
        return f"{len(obj.drop_zones)} zone(s)"
    get_zones_count.short_description = 'Drop Zones'
    
    def get_items_count(self, obj):
        """Count draggable items"""
        return f"{len(obj.draggable_items)} item(s)"
    get_items_count.short_description = 'Items'


@admin.register(NumericalQuestion)
class NumericalQuestionAdmin(BaseQuestionAdmin):
    fieldsets = (
        ('Question', {
            'fields': ('course', 'question_text', 'marks', 'difficulty_level', 'explanation')
        }),
        ('Answer', {
            'fields': ('correct_answer', 'tolerance', 'tolerance_type')
        }),
        ('Units and Format', {
            'fields': ('units', 'require_units', 'decimal_places', 'scientific_notation')
        }),
        ('Metadata', {
            'fields': ('tags', 'time_limit_seconds', 'config', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('times_attempted', 'times_correct', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_list_display(self, request):
        return ['get_question_preview', 'course', 'get_answer_display', 'get_tolerance_display',
                'marks', 'difficulty_level', 'is_active', 'success_rate']
    
    def get_answer_display(self, obj):
        """Display answer with units"""
        answer = str(obj.correct_answer)
        if obj.units:
            answer += f" {obj.units}"
        return answer
    get_answer_display.short_description = 'Correct Answer'
    
    def get_tolerance_display(self, obj):
        """Display tolerance with type"""
        if obj.tolerance == 0:
            return "Exact"
        tolerance_str = f"±{obj.tolerance}"
        if obj.tolerance_type == 'percentage':
            tolerance_str += "%"
        return tolerance_str
    get_tolerance_display.short_description = 'Tolerance'


@admin.register(Question)
class UnifiedQuestionAdmin(admin.ModelAdmin):
    list_display = ['get_question_preview', 'course', 'question_type', 'marks', 
                    'is_active', 'created_at']
    list_filter = ['question_type', 'course', 'is_active', 'created_at']
    search_fields = ['question_data']
    readonly_fields = ['times_attempted', 'times_correct', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'question_type', 'marks')
        }),
        ('Question Data', {
            'fields': ('question_data',),
            'description': 'JSON data containing all question-specific fields'
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
        """Extract question text from JSON data"""
        try:
            question_text = obj.question_data.get('question_text', 'No question text')
            return question_text[:100] + '...' if len(question_text) > 100 else question_text
        except:
            return 'Invalid question data'
    get_question_preview.short_description = 'Question'


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'exam', 'marks', 'percentage', 'grade', 
                    'is_passed', 'date', 'time_taken']
    list_filter = ['exam', 'is_passed', 'grade', 'date', 'is_reviewed']
    search_fields = ['student__user__first_name', 'student__user__last_name', 
                     'student__user__email', 'exam__course_name']
    readonly_fields = ['student', 'exam', 'marks', 'percentage', 'grade', 
                       'is_passed', 'date', 'time_taken_seconds', 'question_scores', 
                       'answers_data']
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'exam', 'date')
        }),
        ('Scores', {
            'fields': ('marks', 'percentage', 'grade', 'is_passed')
        }),
        ('Time', {
            'fields': ('time_taken_seconds', 'time_taken')
        }),
        ('Detailed Scores', {
            'fields': ('question_scores', 'answers_data'),
            'classes': ('collapse',)
        }),
        ('Review', {
            'fields': ('is_reviewed', 'review_notes'),
            'classes': ('collapse',)
        })
    )
    
    def student_name(self, obj):
        """Display student full name"""
        return obj.student.get_name
    student_name.short_description = 'Student'
    
    def time_taken(self, obj):
        """Display time taken in readable format"""
        if obj.time_taken_seconds:
            minutes = obj.time_taken_seconds // 60
            seconds = obj.time_taken_seconds % 60
            return f"{minutes}m {seconds}s"
        return "N/A"
    time_taken.short_description = 'Time Taken'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'student__user', 'exam'
        )
    
    actions = ['export_to_csv', 'mark_as_reviewed']
    
    def export_to_csv(self, request, queryset):
        """Export selected results to CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="exam_results.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Student', 'Email', 'Exam', 'Marks', 'Percentage', 
                        'Grade', 'Status', 'Date'])
        
        for result in queryset:
            writer.writerow([
                result.student.get_name,
                result.student.user.email,
                result.exam.course_name,
                result.marks,
                result.percentage,
                result.grade,
                'Passed' if result.is_passed else 'Failed',
                result.date.strftime('%Y-%m-%d %H:%M')
            ])
        
        return response
    export_to_csv.short_description = "Export selected results to CSV"
    
    def mark_as_reviewed(self, request, queryset):
        """Mark selected results as reviewed"""
        updated = queryset.update(is_reviewed=True)
        self.message_user(request, f"{updated} result(s) marked as reviewed.")
    mark_as_reviewed.short_description = "Mark selected as reviewed"


# Inline admins for related questions
class MCQQuestionInline(admin.TabularInline):
    model = MCQQuestion
    extra = 1
    fields = ['question_text', 'marks', 'difficulty_level', 'is_active']


class TrueFalseQuestionInline(admin.TabularInline):
    model = TrueFalseQuestion
    extra = 1
    fields = ['question_text', 'correct_answer', 'marks', 'is_active']


# Register inline admins with Course
class CourseWithQuestionsAdmin(admin.ModelAdmin):
    list_display = ['course_name', 'question_number', 'total_marks', 'created_at']
    inlines = [MCQQuestionInline, TrueFalseQuestionInline]
    
    def get_urls(self):
        """Add custom URLs for question management"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:course_id>/add-question/', 
                 self.admin_site.admin_view(self.add_question_view),
                 name='exam_course_add_question'),
            path('<int:course_id>/question-stats/', 
                 self.admin_site.admin_view(self.question_stats_view),
                 name='exam_course_question_stats'),
        ]
        return custom_urls + urls
    
    def add_question_view(self, request, course_id):
        """Custom view for adding questions"""
        # Implementation for custom question adding interface
        pass
    
    def question_stats_view(self, request, course_id):
        """View question statistics for a course"""
        # Implementation for viewing statistics
        pass
