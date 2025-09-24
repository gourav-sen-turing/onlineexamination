"""
Enhanced URLs for Multiple Question Types
Add these to your existing exam/urls.py
"""
from django.urls import path
from . import enhanced_views

app_name = 'exam'

urlpatterns = [
    # Teacher URLs for Question Management
    path('teacher/question-types/', 
         enhanced_views.question_type_selection_view, 
         name='teacher-question-type-selection'),
    
    path('teacher/create-question/<str:question_type>/<int:course_id>/', 
         enhanced_views.create_question_view, 
         name='teacher-create-question'),
    
    path('teacher/questions/', 
         enhanced_views.view_questions_view, 
         name='teacher-view-questions'),
    
    path('teacher/questions/<int:course_id>/', 
         enhanced_views.view_questions_view, 
         name='teacher-view-questions'),
    
    path('teacher/edit-question/<str:question_type>/<int:question_id>/', 
         enhanced_views.edit_question_view, 
         name='teacher-edit-question'),
    
    path('teacher/delete-question/<str:question_type>/<int:question_id>/', 
         enhanced_views.delete_question_view, 
         name='teacher-delete-question'),
    
    path('teacher/import-questions/', 
         enhanced_views.import_questions_view, 
         name='teacher-import-questions'),
    
    path('teacher/exam-analytics/<int:course_id>/', 
         enhanced_views.exam_analytics_view, 
         name='teacher-exam-analytics'),
    
    path('teacher/export-results/<int:course_id>/', 
         enhanced_views.export_results_view, 
         name='teacher-export-results'),
    
    # Student URLs for Taking Exams
    path('student/take-exam/<int:course_id>/', 
         enhanced_views.take_exam_view, 
         name='student-take-exam'),
    
    path('student/view-result/<int:result_id>/', 
         enhanced_views.view_result_view, 
         name='student-view-result'),
    
    # API URLs for Dynamic Interactions
    path('api/save-progress/', 
         enhanced_views.save_exam_progress_view, 
         name='save-exam-progress'),
    
    path('api/question-stats/<int:question_id>/', 
         enhanced_views.get_question_stats_view, 
         name='question-stats'),
    
    # Dashboard redirects
    path('student/dashboard/', 
         enhanced_views.student_dashboard, 
         name='student-dashboard'),
    
    path('teacher/dashboard/', 
         enhanced_views.teacher_dashboard, 
         name='teacher-dashboard'),
]
