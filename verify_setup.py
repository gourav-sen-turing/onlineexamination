#!/usr/bin/env python3
"""
Quick verification script for Enhanced Online Examination System
Run this to check if everything is set up correctly
"""

import sys
import os
import importlib

def check_python_version():
    """Check if Python version is compatible"""
    print("1. Checking Python version...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    if version.major == 3 and version.minor >= 8:
        print("   ✓ Python version is compatible")
        return True
    else:
        print("   ✗ Python 3.8+ required")
        return False

def check_django():
    """Check if Django is installed and correct version"""
    print("\n2. Checking Django installation...")
    try:
        import django
        version = django.get_version()
        print(f"   Django {version} installed")
        major, minor = version.split('.')[:2]
        if int(major) == 3 and int(minor) >= 2:
            print("   ✓ Django version is compatible")
            return True
        else:
            print("   ✗ Django 3.2+ required")
            return False
    except ImportError:
        print("   ✗ Django not installed")
        return False

def check_required_packages():
    """Check if required packages are installed"""
    print("\n3. Checking required packages...")
    packages = [
        ('PIL', 'Pillow'),
        ('widget_tweaks', 'django-widget-tweaks'),
        ('crispy_forms', 'django-crispy-forms'),
        ('pytz', 'pytz'),
        ('dateutil', 'python-dateutil'),
        ('fuzzywuzzy', 'fuzzywuzzy'),
        ('Levenshtein', 'python-Levenshtein'),
        ('numpy', 'numpy')
    ]
    
    all_installed = True
    for module_name, package_name in packages:
        try:
            importlib.import_module(module_name)
            print(f"   ✓ {package_name} installed")
        except ImportError:
            print(f"   ✗ {package_name} not installed (pip install {package_name})")
            if module_name in ['widget_tweaks']:  # Critical packages
                all_installed = False
    
    return all_installed

def check_django_settings():
    """Check Django settings configuration"""
    print("\n4. Checking Django settings...")
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'onlinexam.settings')
        import django
        django.setup()
        
        from django.conf import settings
        
        # Check BASE_DIR
        print(f"   BASE_DIR: {settings.BASE_DIR}")
        print(f"   BASE_DIR type: {type(settings.BASE_DIR)}")
        
        # Check database
        db_name = settings.DATABASES['default']['NAME']
        print(f"   Database: {db_name}")
        
        # Check INSTALLED_APPS
        required_apps = ['exam', 'student', 'teacher']
        for app in required_apps:
            if app in settings.INSTALLED_APPS:
                print(f"   ✓ {app} in INSTALLED_APPS")
            else:
                print(f"   ✗ {app} not in INSTALLED_APPS")
        
        # Check widget_tweaks
        if 'widget_tweaks' in settings.INSTALLED_APPS:
            print(f"   ✓ widget_tweaks in INSTALLED_APPS")
        else:
            print(f"   ! widget_tweaks not in INSTALLED_APPS (optional)")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error loading Django settings: {e}")
        return False

def check_enhanced_models():
    """Check if enhanced models can be imported"""
    print("\n5. Checking enhanced models...")
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'onlinexam.settings')
        import django
        django.setup()
        
        from exam.models_enhanced import (
            Course, MCQQuestion, TrueFalseQuestion,
            FillBlankQuestion, ShortAnswerQuestion,
            MatchingQuestion, DragDropQuestion,
            NumericalQuestion
        )
        
        question_types = [
            'MCQQuestion', 'TrueFalseQuestion', 'FillBlankQuestion',
            'ShortAnswerQuestion', 'MatchingQuestion', 
            'DragDropQuestion', 'NumericalQuestion'
        ]
        
        for qt in question_types:
            print(f"   ✓ {qt} imported")
        
        return True
        
    except ImportError as e:
        print(f"   ✗ Cannot import enhanced models: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def check_database():
    """Check database connection"""
    print("\n6. Checking database...")
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'onlinexam.settings')
        import django
        django.setup()
        
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("   ✓ Database connection successful")
            
        # Check if migrations are needed
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command('showmigrations', '--plan', stdout=out)
        migrations = out.getvalue()
        
        if '[ ]' in migrations:
            print("   ! Unmigrated changes detected. Run: python manage.py migrate")
        else:
            print("   ✓ All migrations applied")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Database error: {e}")
        return False

def main():
    print("=" * 60)
    print("Enhanced Online Examination System - Setup Verification")
    print("=" * 60)
    
    results = []
    
    # Run all checks
    results.append(check_python_version())
    results.append(check_django())
    results.append(check_required_packages())
    results.append(check_django_settings())
    results.append(check_enhanced_models())
    results.append(check_database())
    
    # Summary
    print("\n" + "=" * 60)
    if all(results):
        print("✓ ALL CHECKS PASSED - System is ready!")
        print("\nNext steps:")
        print("1. Run migrations if needed: python manage.py migrate")
        print("2. Create superuser: python manage.py createsuperuser")
        print("3. Start server: python manage.py runserver")
        print("4. Access at: http://localhost:8000")
    else:
        print("✗ SOME CHECKS FAILED - Please fix the issues above")
        print("\nQuick fix commands:")
        print("1. Install all dependencies:")
        print("   pip install -r requirements_minimal.txt")
        print("2. Or run the installation script:")
        print("   bash install_enhanced.sh")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
