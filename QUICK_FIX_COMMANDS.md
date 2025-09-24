# Quick Fix Commands for Django 3.2 with Python 3.12

## Complete Installation Commands (Copy & Paste)

### Step 1: Create and activate virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# OR for Windows:
# venv\Scripts\activate
```

### Step 2: Install ALL required packages (in exact order)
```bash
# Upgrade pip first
pip install --upgrade pip

# Install Django 3.2 LTS (most stable)
pip install Django==3.2.23

# Install Pillow for image handling
pip install Pillow==10.1.0

# CRITICAL: Install widget_tweaks (fixes the import error)
pip install django-widget-tweaks==1.5.0

# Install crispy forms (optional but recommended)
pip install django-crispy-forms==1.14.0

# Install timezone and date utilities
pip install pytz==2023.3
pip install python-dateutil==2.8.2

# Install text processing for enhanced questions
pip install fuzzywuzzy==0.18.0
pip install python-Levenshtein==0.23.0

# Install numpy for numerical questions
pip install numpy==1.24.4
```

### Step 3: Fix settings.py
```bash
# Backup existing settings
cp onlinexam/settings.py onlinexam/settings_backup.py

# Use the fixed settings
cp onlinexam/settings_fixed.py onlinexam/settings.py
```

### OR manually edit onlinexam/settings.py:

```python
# At the top of settings.py, ensure these imports:
import os
from pathlib import Path

# Fix BASE_DIR (use one of these approaches):
# Option 1: Path approach (recommended)
BASE_DIR = Path(__file__).resolve().parent.parent

# Option 2: os.path approach (alternative)
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Fix database configuration:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),  # Use os.path.join
        # OR if using Path:
        # 'NAME': str(BASE_DIR / 'db.sqlite3'),
    }
}

# Add to INSTALLED_APPS (if not present):
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'exam',
    'student',
    'teacher',
    'widget_tweaks',  # Add this line
    'crispy_forms',   # Optional but recommended
]

# Add at the bottom:
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

### Step 4: Create required directories
```bash
mkdir -p exam/management/commands
touch exam/management/__init__.py
touch exam/management/commands/__init__.py

mkdir -p static
mkdir -p media
mkdir -p staticfiles
mkdir -p templates/exam/enhanced
```

### Step 5: Run migrations
```bash
# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# If migrations fail, try:
python manage.py migrate --run-syncdb
```

### Step 6: Verify installation
```bash
# Quick test
python manage.py check

# Run verification script
python verify_setup.py

# Test enhanced models
python manage.py shell
>>> from exam.models_enhanced import *
>>> print("Success if no errors!")
>>> exit()
```

### Step 7: Create superuser and run server
```bash
# Create admin account
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Run development server
python manage.py runserver
```

## Common Error Fixes

### Error: "No module named 'widget_tweaks'"
```bash
pip install django-widget-tweaks==1.5.0
# Then add 'widget_tweaks' to INSTALLED_APPS in settings.py
```

### Error: "unsupported operand type(s) for /: 'str' and 'str'"
```bash
# In settings.py, change:
# 'NAME': BASE_DIR / 'db.sqlite3',
# To:
'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
```

### Error: "No module named 'exam.models_enhanced'"
```bash
# Ensure the models_enhanced.py file is in the exam directory
ls exam/models_enhanced.py
# If missing, copy it from the provided files
```

### Error: "relation does not exist"
```bash
# Reset and recreate database
rm db.sqlite3
python manage.py makemigrations
python manage.py migrate
```

## Test Enhanced Question Types

### Create test questions in Django shell:
```python
python manage.py shell

from exam.models_enhanced import *

# Create a test course
course = Course.objects.create(
    course_name="Test Course",
    question_number=10,
    total_marks=100
)

# Create True/False question
tf = TrueFalseQuestion.objects.create(
    course=course,
    question_text="Python is statically typed",
    correct_answer=False,
    marks=5
)

# Create Fill in the Blank
fb = FillBlankQuestion.objects.create(
    course=course,
    question_text="Python was created by ___",
    correct_answers=["Guido van Rossum"],
    marks=10
)

# Create Numerical question
num = NumericalQuestion.objects.create(
    course=course,
    question_text="What is 10 + 15?",
    correct_answer=25,
    tolerance=0.1,
    marks=5
)

print("Questions created successfully!")

# Test validation
print(tf.validate_answer(False))  # Should return is_correct: True
print(fb.validate_answer("Guido van Rossum"))  # Should return is_correct: True
print(num.validate_answer(25))  # Should return is_correct: True
```

## One-Line Installation (Linux/Mac)

```bash
# Complete setup in one command
python3 -m venv venv && source venv/bin/activate && pip install Django==3.2.23 Pillow==10.1.0 django-widget-tweaks==1.5.0 django-crispy-forms==1.14.0 pytz==2023.3 python-dateutil==2.8.2 fuzzywuzzy==0.18.0 python-Levenshtein==0.23.0 numpy==1.24.4 && python manage.py migrate && python manage.py runserver
```

## URLs to test after setup:

- Admin: http://localhost:8000/admin
- Teacher question types: http://localhost:8000/teacher/question-types/
- Create questions: http://localhost:8000/teacher/create-question/mcq/1/
- Student exam: http://localhost:8000/student/take-exam/1/

## Success Indicators:
✓ Server starts without errors
✓ Admin panel accessible
✓ Can create all question types
✓ No import errors in console
✓ Database migrations complete
