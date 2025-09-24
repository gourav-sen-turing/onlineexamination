#!/bin/bash

# Enhanced Online Examination System - Installation Script
# Compatible with Python 3.8+ (including 3.12) and Django 3.2

echo "=========================================="
echo "Enhanced Online Examination System Setup"
echo "=========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check Python version
print_status "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
echo "Found Python $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Django 3.2 (LTS version)
print_status "Installing Django 3.2 LTS..."
pip install "Django>=3.2,<3.3"

# Install required dependencies
print_status "Installing required dependencies..."

# Core dependencies
pip install Pillow>=8.4.0
pip install pytz>=2021.3
pip install python-dateutil>=2.8.2

# Install widget_tweaks (fixing the missing module error)
print_status "Installing django-widget-tweaks..."
pip install django-widget-tweaks>=1.4.8

# Install crispy forms
print_status "Installing django-crispy-forms..."
pip install django-crispy-forms>=1.12.0

# Install packages for enhanced question types
print_status "Installing packages for enhanced question features..."
pip install python-Levenshtein>=0.12.2
pip install fuzzywuzzy>=0.18.0
pip install python-Levenshtein-wheels  # Alternative if python-Levenshtein fails

# Install numpy for numerical operations
print_status "Installing numpy for numerical questions..."
pip install numpy>=1.21.4

# Optional but recommended packages
print_status "Installing optional packages..."
pip install django-extensions>=3.1.3 2>/dev/null || print_warning "django-extensions installation failed (optional)"
pip install ipython>=7.29.0 2>/dev/null || print_warning "ipython installation failed (optional)"

# Display installed packages
print_status "Installed packages:"
pip list | grep -E "Django|widget|crispy|Pillow|numpy|Levenshtein"

# Backup existing settings if they exist
if [ -f "onlinexam/settings.py" ]; then
    print_status "Backing up existing settings.py..."
    cp onlinexam/settings.py onlinexam/settings_backup_$(date +%Y%m%d_%H%M%S).py
fi

# Use the fixed settings file
print_status "Applying fixed settings..."
if [ -f "onlinexam/settings_fixed.py" ]; then
    cp onlinexam/settings_fixed.py onlinexam/settings.py
    print_status "Settings updated successfully"
else
    print_warning "Fixed settings file not found, please update settings.py manually"
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p static
mkdir -p media
mkdir -p media/profile_pic/Student
mkdir -p media/profile_pic/Teacher
mkdir -p staticfiles
mkdir -p templates/exam/enhanced

# Check if migrations directory exists
if [ ! -d "exam/migrations" ]; then
    mkdir -p exam/migrations
    touch exam/migrations/__init__.py
fi

# Run migrations
print_status "Running database migrations..."
python manage.py makemigrations exam --noinput
python manage.py makemigrations student --noinput
python manage.py makemigrations teacher --noinput
python manage.py migrate --noinput

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser prompt
echo ""
print_warning "Do you want to create a superuser account? (y/n)"
read -r create_super

if [ "$create_super" = "y" ] || [ "$create_super" = "Y" ]; then
    python manage.py createsuperuser
fi

# Test Django configuration
print_status "Testing Django configuration..."
python manage.py check

# Test imports
print_status "Testing enhanced models import..."
python -c "from exam.models_enhanced import *; print('Enhanced models imported successfully')" 2>/dev/null || print_warning "Enhanced models not found"

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
print_status "To start the development server, run:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""
print_status "Access the application at:"
echo "  http://localhost:8000"
echo ""
print_status "Admin panel:"
echo "  http://localhost:8000/admin"
echo ""

# Display troubleshooting info if needed
if [ -f "debug.log" ]; then
    print_warning "Check debug.log for any errors"
fi

# Deactivate virtual environment
deactivate 2>/dev/null || true
