from django.contrib import admin

# Register your models here.

# Polymorphic Question Admin
try:
    from exam.admin_poly import *
except ImportError:
    pass  # Polymorphic admin not available yet

# Polymorphic Question Admin
try:
    from exam.admin_poly import *
except ImportError:
    pass  # Polymorphic admin not available yet
