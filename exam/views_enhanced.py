"""
Enhanced Views for Multiple Question Types
Handles CRUD operations and exam taking for all question types
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
import json
import csv
import logging
from typing import Dict, Any, List

from .models_enhanced import (
    Course, MCQQuestion, TrueFalseQuestion, FillBlankQuestion,
    ShortAnswerQuestion, MatchingQuestion, DragDropQuestion,
    NumericalQuestion, Question, Result, QuestionType
)
from .forms_enhanced import (
    CourseForm, MCQQuestionForm, TrueFalseQuestionForm,
    FillBlankQuestionForm, ShortAnswerQuestionForm,
    MatchingQuestionForm, DragDropQuestionForm,
    NumericalQuestionForm, UnifiedQuestionForm,
    DynamicQuestionAnswerForm, QuestionBankImportForm
)
from student.models import Student
from teacher.models import Teacher

logger = logging.getLogger(__name__)


def is_teacher(user):
    """Check if user is a teacher"""
    return user.groups.filter(name='TEACHER').exists()


def is_student(user):
    """Check if user is a student"""
    return user.groups.filter(name='STUDENT').exists()


# Teacher Views for Question Management

@login_required
@user_passes_test(is_teacher)
def question_type_selection_view(request):
    """View for selecting question type to create"""
    question_types = [
        {
            'type': 'mcq',
            'name': 'Multiple Choice Question',
            'icon': 'fas fa-list-ol',
            'description': 'Questions with multiple options where students select one or more correct answers'
        },
        {
            'type': 'true_false',
            'name': 'True/False',
            'icon': 'fas fa-check-circle',
            'description': 'Simple true or false questions'
        },
        {
            'type': 'fill_blank',
            'name': 'Fill in the Blank',
            'icon': 'fas fa-edit',
            'description': 'Questions where students fill in missing words or phrases'
        },
        {
            'type': 'short_answer',
            'name': 'Short Answer',
            'icon': 'fas fa-paragraph',
            'description': 'Questions requiring brief written responses'
        },
        {
            'type': 'matching',
            'name': 'Matching',
            'icon': 'fas fa-exchange-alt',
            'description': 'Match items from two columns'
        },
        {
            'type': 'drag_drop',
            'name': 'Drag and Drop',
            'icon': 'fas fa-hand-pointer',
            'description': 'Drag items to correct positions'
        },
        {
            'type': 'numerical',
            'name': 'Numerical',
            'icon': 'fas fa-calculator',
            'description': 'Questions requiring numerical answers with tolerance ranges'
        }
    ]
    
    courses = Course.objects.all()
    
    context = {
        'question_types': question_types,
        'courses': courses
    }
    return render(request, 'exam/teacher_question_type_selection.html', context)


@login_required
@user_passes_test(is_teacher)
def create_question_view(request, question_type, course_id):
    """Dynamic view for creating questions based on type"""
    course = get_object_or_404(Course, id=course_id)
    
    # Map question types to form classes
    form_classes = {
        'mcq': MCQQuestionForm,
        'true_false': TrueFalseQuestionForm,
        'fill_blank': FillBlankQuestionForm,
        'short_answer': ShortAnswerQuestionForm,
        'matching': MatchingQuestionForm,
        'drag_drop': DragDropQuestionForm,
        'numerical': NumericalQuestionForm,
    }
    
    form_class = form_classes.get(question_type)
    if not form_class:
        messages.error(request, 'Invalid question type')
        return redirect('teacher-question-type-selection')
    
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.course = course
            question.save()
            messages.success(request, f'{question_type.replace("_", " ").title()} question created successfully!')
            
            # Check if user wants to add another question
            if 'add_another' in request.POST:
                return redirect('teacher-create-question', question_type=question_type, course_id=course_id)
            else:
                return redirect('teacher-view-questions', course_id=course_id)
    else:
        form = form_class()
    
    context = {
        'form': form,
        'course': course,
        'question_type': question_type,
        'question_type_display': question_type.replace('_', ' ').title()
    }
    return render(request, 'exam/teacher_create_question.html', context)


@login_required
@user_passes_test(is_teacher)
def view_questions_view(request, course_id=None):
    """View all questions with filtering and pagination"""
    questions = []
    
    # Get all question types
    question_models = [
        MCQQuestion, TrueFalseQuestion, FillBlankQuestion,
        ShortAnswerQuestion, MatchingQuestion, DragDropQuestion,
        NumericalQuestion
    ]
    
    # Filter by course if specified
    if course_id:
        course = get_object_or_404(Course, id=course_id)
        for model in question_models:
            questions.extend(model.objects.filter(course=course, is_active=True))
    else:
        for model in question_models:
            questions.extend(model.objects.filter(is_active=True))
    
    # Apply filters
    question_type_filter = request.GET.get('type')
    difficulty_filter = request.GET.get('difficulty')
    search_query = request.GET.get('search')
    
    if question_type_filter:
        questions = [q for q in questions if q.question_type == question_type_filter]
    
    if difficulty_filter:
        questions = [q for q in questions if str(q.difficulty_level) == difficulty_filter]
    
    if search_query:
        questions = [q for q in questions if search_query.lower() in q.question_text.lower()]
    
    # Sort questions
    questions.sort(key=lambda x: x.created_at, reverse=True)
    
    # Pagination
    paginator = Paginator(questions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'course': course if course_id else None,
        'courses': Course.objects.all(),
        'question_types': QuestionType.choices,
        'difficulty_levels': [(1, 'Easy'), (2, 'Medium'), (3, 'Hard')],
        'filters': {
            'type': question_type_filter,
            'difficulty': difficulty_filter,
            'search': search_query
        }
    }
    return render(request, 'exam/teacher_view_questions.html', context)


@login_required
@user_passes_test(is_teacher)
def edit_question_view(request, question_type, question_id):
    """Edit existing question"""
    # Map question types to model classes
    model_classes = {
        'MCQ': MCQQuestion,
        'TF': TrueFalseQuestion,
        'FB': FillBlankQuestion,
        'SA': ShortAnswerQuestion,
        'MT': MatchingQuestion,
        'DD': DragDropQuestion,
        'NUM': NumericalQuestion,
    }
    
    form_classes = {
        'MCQ': MCQQuestionForm,
        'TF': TrueFalseQuestionForm,
        'FB': FillBlankQuestionForm,
        'SA': ShortAnswerQuestionForm,
        'MT': MatchingQuestionForm,
        'DD': DragDropQuestionForm,
        'NUM': NumericalQuestionForm,
    }
    
    model_class = model_classes.get(question_type)
    form_class = form_classes.get(question_type)
    
    if not model_class or not form_class:
        messages.error(request, 'Invalid question type')
        return redirect('teacher-view-questions')
    
    question = get_object_or_404(model_class, id=question_id)
    
    if request.method == 'POST':
        form = form_class(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question updated successfully!')
            return redirect('teacher-view-questions', course_id=question.course.id)
    else:
        form = form_class(instance=question)
    
    context = {
        'form': form,
        'question': question,
        'question_type': question_type,
        'course': question.course
    }
    return render(request, 'exam/teacher_edit_question.html', context)


@login_required
@user_passes_test(is_teacher)
def delete_question_view(request, question_type, question_id):
    """Soft delete a question"""
    model_classes = {
        'MCQ': MCQQuestion,
        'TF': TrueFalseQuestion,
        'FB': FillBlankQuestion,
        'SA': ShortAnswerQuestion,
        'MT': MatchingQuestion,
        'DD': DragDropQuestion,
        'NUM': NumericalQuestion,
    }
    
    model_class = model_classes.get(question_type)
    if not model_class:
        messages.error(request, 'Invalid question type')
        return redirect('teacher-view-questions')
    
    question = get_object_or_404(model_class, id=question_id)
    
    if request.method == 'POST':
        # Soft delete
        question.is_active = False
        question.save()
        messages.success(request, 'Question deleted successfully!')
        return redirect('teacher-view-questions', course_id=question.course.id)
    
    context = {
        'question': question,
        'question_type': question_type
    }
    return render(request, 'exam/teacher_delete_question.html', context)


@login_required
@user_passes_test(is_teacher)
def import_questions_view(request):
    """Import questions from file"""
    if request.method == 'POST':
        form = QuestionBankImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            file_format = form.cleaned_data['file_format']
            course = form.cleaned_data['course']
            
            try:
                imported_count = import_questions(file, file_format, course)
                messages.success(request, f'Successfully imported {imported_count} questions!')
                return redirect('teacher-view-questions', course_id=course.id)
            except Exception as e:
                messages.error(request, f'Import failed: {str(e)}')
    else:
        form = QuestionBankImportForm()
    
    context = {
        'form': form
    }
    return render(request, 'exam/teacher_import_questions.html', context)


def import_questions(file, file_format, course):
    """Import questions from file"""
    imported_count = 0
    
    if file_format == 'csv':
        # CSV import logic
        import csv
        reader = csv.DictReader(file.read().decode('utf-8').splitlines())
        
        for row in reader:
            question_type = row.get('type', 'MCQ')
            
            if question_type == 'MCQ':
                MCQQuestion.objects.create(
                    course=course,
                    question_text=row['question'],
                    option1=row.get('option1', ''),
                    option2=row.get('option2', ''),
                    option3=row.get('option3', ''),
                    option4=row.get('option4', ''),
                    correct_option=int(row.get('correct_option', 1)),
                    marks=int(row.get('marks', 1)),
                    explanation=row.get('explanation', ''),
                    difficulty_level=int(row.get('difficulty', 2))
                )
                imported_count += 1
            # Add other question types...
    
    elif file_format == 'json':
        # JSON import logic
        data = json.loads(file.read().decode('utf-8'))
        
        for item in data.get('questions', []):
            question_type = item.get('type', 'MCQ')
            
            # Create unified question
            Question.objects.create(
                course=course,
                question_type=question_type,
                marks=item.get('marks', 1),
                question_data=item
            )
            imported_count += 1
    
    return imported_count


# Student Views for Taking Exams

@login_required
@user_passes_test(is_student)
def take_exam_view(request, course_id):
    """Enhanced exam taking view with support for all question types"""
    course = get_object_or_404(Course, id=course_id)
    student = Student.objects.get(user=request.user)
    
    # Check if student has already taken this exam
    existing_result = Result.objects.filter(student=student, exam=course).first()
    if existing_result and not course.allow_review:
        messages.warning(request, 'You have already taken this exam.')
        return redirect('student-view-result', result_id=existing_result.id)
    
    # Get all questions for the course
    questions = []
    question_models = [
        MCQQuestion, TrueFalseQuestion, FillBlankQuestion,
        ShortAnswerQuestion, MatchingQuestion, DragDropQuestion,
        NumericalQuestion
    ]
    
    for model in question_models:
        questions.extend(model.objects.filter(course=course, is_active=True))
    
    # Randomize if needed
    if course.randomize_questions:
        import random
        random.shuffle(questions)
    
    # Limit to course question number
    questions = questions[:course.question_number]
    
    if request.method == 'POST':
        # Process exam submission
        answers = {}
        for question in questions:
            form = DynamicQuestionAnswerForm(question, request.POST)
            if form.is_valid():
                answer = form.get_answer()
                if answer is not None:
                    answers[question.id] = answer
        
        # Calculate result
        with transaction.atomic():
            result = Result.objects.create(
                student=student,
                exam=course,
                marks=0  # Will be calculated
            )
            
            # Calculate scores
            result_data = result.calculate_result(answers)
            
            # Save time taken if provided
            time_taken = request.POST.get('time_taken_seconds')
            if time_taken:
                result.time_taken_seconds = int(time_taken)
                result.save()
        
        if course.show_result_immediately:
            return redirect('student-view-result', result_id=result.id)
        else:
            messages.success(request, 'Exam submitted successfully! Results will be available later.')
            return redirect('student-dashboard')
    
    # Create forms for questions
    question_forms = []
    for question in questions:
        form = DynamicQuestionAnswerForm(question)
        question_forms.append({
            'question': question,
            'form': form,
            'number': len(question_forms) + 1
        })
    
    context = {
        'course': course,
        'question_forms': question_forms,
        'total_questions': len(questions),
        'total_marks': sum(q.marks for q in questions),
        'duration_seconds': course.duration_minutes * 60
    }
    return render(request, 'exam/student_take_exam.html', context)


@login_required
@user_passes_test(is_student)
def view_result_view(request, result_id):
    """View detailed exam result"""
    result = get_object_or_404(Result, id=result_id)
    
    # Check if student has permission to view this result
    if result.student.user != request.user:
        messages.error(request, 'You do not have permission to view this result.')
        return redirect('student-dashboard')
    
    # Get question details if review is allowed
    question_details = []
    if result.exam.allow_review:
        for score_data in result.question_scores:
            question_id = score_data['question_id']
            question_type = score_data['question_type']
            
            # Get question based on type
            model_classes = {
                'MCQ': MCQQuestion,
                'TF': TrueFalseQuestion,
                'FB': FillBlankQuestion,
                'SA': ShortAnswerQuestion,
                'MT': MatchingQuestion,
                'DD': DragDropQuestion,
                'NUM': NumericalQuestion,
            }
            
            model_class = model_classes.get(question_type)
            if model_class:
                try:
                    question = model_class.objects.get(id=question_id)
                    question_details.append({
                        'question': question,
                        'score_data': score_data,
                        'user_answer': result.answers_data.get(str(question_id), {}).get('user_answer'),
                        'correct_answer': result.answers_data.get(str(question_id), {}).get('correct_answer')
                    })
                except model_class.DoesNotExist:
                    pass
    
    context = {
        'result': result,
        'question_details': question_details,
        'allow_review': result.exam.allow_review
    }
    return render(request, 'exam/student_view_result.html', context)


# API Views for Dynamic Interactions

@csrf_exempt
@login_required
def save_exam_progress_view(request):
    """Auto-save exam progress"""
    if request.method == 'POST':
        data = json.loads(request.body)
        exam_id = data.get('exam_id')
        answers = data.get('answers', {})
        
        # Store in session or cache
        session_key = f'exam_progress_{exam_id}'
        request.session[session_key] = answers
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def get_question_stats_view(request, question_id):
    """Get statistics for a question"""
    question_type = request.GET.get('type')
    
    model_classes = {
        'MCQ': MCQQuestion,
        'TF': TrueFalseQuestion,
        'FB': FillBlankQuestion,
        'SA': ShortAnswerQuestion,
        'MT': MatchingQuestion,
        'DD': DragDropQuestion,
        'NUM': NumericalQuestion,
    }
    
    model_class = model_classes.get(question_type)
    if not model_class:
        return JsonResponse({'error': 'Invalid question type'}, status=400)
    
    question = get_object_or_404(model_class, id=question_id)
    
    stats = {
        'times_attempted': question.times_attempted,
        'times_correct': question.times_correct,
        'success_rate': question.get_success_rate(),
        'difficulty_level': question.get_difficulty_level_display()
    }
    
    return JsonResponse(stats)


# Analytics Views

@login_required
@user_passes_test(is_teacher)
def exam_analytics_view(request, course_id):
    """View exam analytics and statistics"""
    course = get_object_or_404(Course, id=course_id)
    
    # Get all results for this exam
    results = Result.objects.filter(exam=course)
    
    # Calculate statistics
    stats = {
        'total_attempts': results.count(),
        'average_score': results.aggregate(Avg('marks'))['marks__avg'] or 0,
        'average_percentage': results.aggregate(Avg('percentage'))['percentage__avg'] or 0,
        'pass_rate': (results.filter(is_passed=True).count() / results.count() * 100) if results.count() > 0 else 0,
        'highest_score': results.aggregate(Max('marks'))['marks__max'] or 0,
        'lowest_score': results.aggregate(Min('marks'))['marks__min'] or 0,
    }
    
    # Question-wise statistics
    question_stats = []
    questions = []
    
    question_models = [
        MCQQuestion, TrueFalseQuestion, FillBlankQuestion,
        ShortAnswerQuestion, MatchingQuestion, DragDropQuestion,
        NumericalQuestion
    ]
    
    for model in question_models:
        questions.extend(model.objects.filter(course=course, is_active=True))
    
    for question in questions:
        question_stats.append({
            'question': question,
            'success_rate': question.get_success_rate(),
            'attempts': question.times_attempted,
            'correct': question.times_correct
        })
    
    # Sort by difficulty (lowest success rate first)
    question_stats.sort(key=lambda x: x['success_rate'])
    
    context = {
        'course': course,
        'stats': stats,
        'question_stats': question_stats,
        'results': results.order_by('-date')[:10]  # Latest 10 results
    }
    return render(request, 'exam/teacher_exam_analytics.html', context)


@login_required
@user_passes_test(is_teacher)
def export_results_view(request, course_id):
    """Export exam results to CSV"""
    course = get_object_or_404(Course, id=course_id)
    results = Result.objects.filter(exam=course).select_related('student__user')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="exam_results_{course.course_name}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Student Name', 'Email', 'Marks', 'Percentage', 'Grade', 'Status', 'Date', 'Time Taken (seconds)'])
    
    for result in results:
        writer.writerow([
            result.student.get_name,
            result.student.user.email,
            result.marks,
            result.percentage,
            result.grade,
            'Passed' if result.is_passed else 'Failed',
            result.date.strftime('%Y-%m-%d %H:%M:%S'),
            result.time_taken_seconds or 'N/A'
        ])
    
    return response
