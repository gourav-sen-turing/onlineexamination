# Enhanced Online Examination System - Quick Setup Guide

## System Requirements
- Ubuntu 20.04+ (or any Linux distribution)
- Python 3.8+ (tested with Python 3.10)
- SQLite3 (included with Python)
- 2GB RAM minimum
- 500MB disk space

## Installation Steps

### 1. Install System Dependencies (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python and pip if not already installed
sudo apt install python3 python3-pip python3-venv

# Install development tools (optional but recommended)
sudo apt install build-essential python3-dev

# Install SQLite (usually pre-installed)
sudo apt install sqlite3

# Install image libraries for Pillow
sudo apt install libjpeg-dev zlib1g-dev libpng-dev
```

### 2. Create Virtual Environment

```bash
# Navigate to project directory
cd /path/to/onlineexamination

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# Or on Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
# Install minimal requirements for SQLite deployment
pip install --upgrade pip
pip install -r requirements_enhanced.txt
```

### 4. Configure Django Settings

Edit `onlinexam/settings.py` and ensure these settings:

```python
# Database Configuration (SQLite - no changes needed)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Add to INSTALLED_APPS if not present
INSTALLED_APPS = [
    # ... existing apps ...
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'exam',
    'student',
    'teacher',
]

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Optional: Add logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'exam_system.log',
        },
    },
    'loggers': {
        'exam': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 5. Update URLs Configuration

In `exam/urls.py`, add the enhanced URLs:

```python
from django.urls import path, include

# Add this at the top of your existing urlpatterns
urlpatterns = [
    # ... your existing patterns ...
]

# Add enhanced URLs
from . import enhanced_views

urlpatterns += [
    # Include all enhanced URLs
    path('teacher/question-types/', enhanced_views.question_type_selection_view, name='teacher-question-type-selection'),
    path('teacher/create-question/<str:question_type>/<int:course_id>/', enhanced_views.create_question_view, name='teacher-create-question'),
    path('teacher/questions/', enhanced_views.view_questions_view, name='teacher-view-questions'),
    path('teacher/questions/<int:course_id>/', enhanced_views.view_questions_view, name='teacher-view-questions-course'),
    path('teacher/edit-question/<str:question_type>/<int:question_id>/', enhanced_views.edit_question_view, name='teacher-edit-question'),
    path('teacher/delete-question/<str:question_type>/<int:question_id>/', enhanced_views.delete_question_view, name='teacher-delete-question'),
    path('teacher/import-questions/', enhanced_views.import_questions_view, name='teacher-import-questions'),
    path('teacher/exam-analytics/<int:course_id>/', enhanced_views.exam_analytics_view, name='teacher-exam-analytics'),
    path('teacher/export-results/<int:course_id>/', enhanced_views.export_results_view, name='teacher-export-results'),
    path('student/take-exam/<int:course_id>/', enhanced_views.take_exam_view, name='student-take-exam'),
    path('student/view-result/<int:result_id>/', enhanced_views.view_result_view, name='student-view-result'),
    path('api/save-progress/', enhanced_views.save_exam_progress_view, name='save-exam-progress'),
    path('api/question-stats/<int:question_id>/', enhanced_views.get_question_stats_view, name='question-stats'),
]
```

### 6. Run Migrations

```bash
# Make migrations for the new models
python manage.py makemigrations exam

# Apply migrations
python manage.py migrate

# Create superuser if not exists
python manage.py createsuperuser
```

### 7. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 8. Test the Installation

```bash
# Run development server
python manage.py runserver

# Access the application
# Open browser and go to: http://localhost:8000
```

## Quick Test

### 1. Create Sample Data

```python
# Run in Django shell
python manage.py shell

from exam.models_enhanced import *
from student.models import Student
from teacher.models import Teacher
from django.contrib.auth.models import User, Group

# Create teacher group if not exists
teacher_group, _ = Group.objects.get_or_create(name='TEACHER')
student_group, _ = Group.objects.get_or_create(name='STUDENT')

# Create a test course
course = Course.objects.create(
    course_name="Python Programming",
    question_number=10,
    total_marks=100,
    duration_minutes=60,
    pass_percentage=40.0
)

# Create sample questions
mcq = MCQQuestion.objects.create(
    course=course,
    question_text="What is Python?",
    option1="A programming language",
    option2="A snake",
    option3="A framework",
    option4="A database",
    correct_option=1,
    marks=10
)

tf = TrueFalseQuestion.objects.create(
    course=course,
    question_text="Python is a compiled language",
    correct_answer=False,
    marks=5
)

fb = FillBlankQuestion.objects.create(
    course=course,
    question_text="The founder of Python is ___",
    correct_answers=["Guido van Rossum", "Guido"],
    marks=10
)

sa = ShortAnswerQuestion.objects.create(
    course=course,
    question_text="Explain what is a Python list",
    model_answer="A Python list is an ordered, mutable collection of items",
    min_words=10,
    max_words=50,
    keywords=["ordered", "mutable", "collection"],
    marks=15
)

matching = MatchingQuestion.objects.create(
    course=course,
    question_text="Match Python concepts with descriptions",
    left_items=["List", "Tuple", "Dictionary"],
    right_items=["Mutable sequence", "Immutable sequence", "Key-value pairs"],
    correct_pairs={
        "List": "Mutable sequence",
        "Tuple": "Immutable sequence",
        "Dictionary": "Key-value pairs"
    },
    marks=15
)

num = NumericalQuestion.objects.create(
    course=course,
    question_text="What is 2 + 2?",
    correct_answer=4,
    tolerance=0.01,
    marks=5
)

print("Sample data created successfully!")
```

### 2. Access Admin Panel

1. Go to: http://localhost:8000/admin
2. Login with superuser credentials
3. You can manage questions from the admin panel

### 3. Teacher Access

1. Login as a teacher
2. Go to: http://localhost:8000/teacher/question-types/
3. Create new questions of different types
4. View and manage questions

### 4. Student Access

1. Login as a student
2. Take an exam: http://localhost:8000/student/take-exam/1/
3. View results after submission

## Troubleshooting

### Common Issues and Solutions

#### 1. ImportError: No module named 'exam.models_enhanced'
**Solution:** Make sure you've copied all the enhanced files to the exam directory.

#### 2. Migration Errors
**Solution:** 
```bash
# Reset migrations if needed
python manage.py migrate exam zero
python manage.py makemigrations exam
python manage.py migrate
```

#### 3. Static Files Not Loading
**Solution:**
```bash
python manage.py collectstatic
# Ensure DEBUG = True in settings.py for development
```

#### 4. JSONField Not Working
**Solution:** Upgrade Django to 3.2+
```bash
pip install --upgrade Django>=3.2,<4.0
```

## Production Deployment

For production deployment:

1. **Use a proper database** (PostgreSQL recommended):
```bash
# Install PostgreSQL adapter
pip install psycopg2-binary

# Update DATABASES in settings.py
```

2. **Configure static files serving**:
```bash
pip install whitenoise
# Add to middleware in settings.py
```

3. **Use a production server**:
```bash
pip install gunicorn
gunicorn onlinexam.wsgi:application
```

4. **Set environment variables**:
```bash
export DJANGO_SETTINGS_MODULE=onlinexam.settings
export SECRET_KEY='your-secret-key'
export DEBUG=False
```

## API Endpoints

### Teacher Endpoints
- `GET /teacher/question-types/` - Question type selection
- `POST /teacher/create-question/<type>/<course_id>/` - Create question
- `GET /teacher/questions/` - View all questions
- `GET /teacher/exam-analytics/<course_id>/` - View analytics

### Student Endpoints
- `GET /student/take-exam/<course_id>/` - Take exam
- `GET /student/view-result/<result_id>/` - View result

### API Endpoints
- `POST /api/save-progress/` - Auto-save exam progress
- `GET /api/question-stats/<question_id>/` - Get question statistics

## Support

For issues or questions:
1. Check the logs in `exam_system.log`
2. Verify all files are in the correct directories
3. Ensure Python version is 3.8+
4. Check Django version is 3.2+

## Next Steps

1. **Customize Templates**: Create custom templates for better UI
2. **Add Authentication**: Implement proper authentication views
3. **Configure Email**: Set up email for notifications
4. **Add Caching**: Install Redis for better performance
5. **Implement API**: Add REST API for mobile apps

## License

This enhanced system is provided as an extension to the original online examination system.
