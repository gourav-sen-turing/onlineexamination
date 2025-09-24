"""
Migration for Polymorphic Questions - SQLite Compatible
NO PostgreSQL dependencies
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0001_initial'),
        ('student', '0001_initial'),
    ]

    operations = [
        # Create CourseExtended for additional fields
        migrations.CreateModel(
            name='CourseExtended',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(blank=True, null=True)),
                ('duration_minutes', models.PositiveIntegerField(default=60)),
                ('pass_percentage', models.DecimalField(decimal_places=2, default=40.0, max_digits=5)),
                ('randomize_questions', models.BooleanField(default=False)),
                ('show_result_immediately', models.BooleanField(default=True)),
                ('allow_review', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='extended', to='exam.course')),
            ],
            options={
                'db_table': 'exam_course_extended',
            },
        ),
        
        # Create single PolymorphicQuestion model for all question types
        migrations.CreateModel(
            name='PolymorphicQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_type', models.CharField(
                    choices=[
                        ('MCQ', 'Multiple Choice Question'),
                        ('TF', 'True/False'),
                        ('FB', 'Fill in the Blank'),
                        ('SA', 'Short Answer'),
                        ('MT', 'Matching'),
                        ('DD', 'Drag and Drop'),
                        ('NUM', 'Numerical')
                    ],
                    db_index=True,
                    max_length=10
                )),
                ('question_text', models.TextField()),
                ('marks', models.PositiveIntegerField(default=1)),
                ('explanation', models.TextField(blank=True)),
                ('difficulty_level', models.IntegerField(
                    choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Hard')],
                    default=2
                )),
                ('question_data', models.TextField(default='{}')),  # JSON stored as text for SQLite
                ('times_attempted', models.PositiveIntegerField(default=0)),
                ('times_correct', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='poly_questions', to='exam.course')),
            ],
            options={
                'db_table': 'exam_polymorphic_question',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create ResultExtended for polymorphic questions
        migrations.CreateModel(
            name='ResultExtended',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('marks', models.PositiveIntegerField(default=0)),
                ('percentage', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('grade', models.CharField(blank=True, max_length=10)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('time_taken_seconds', models.PositiveIntegerField(blank=True, null=True)),
                ('question_scores', models.TextField(default='[]')),  # JSON as text
                ('answers_data', models.TextField(default='{}')),  # JSON as text
                ('is_passed', models.BooleanField(default=False)),
                ('is_reviewed', models.BooleanField(default=False)),
                ('review_notes', models.TextField(blank=True)),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exam.course')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='student.student')),
            ],
            options={
                'db_table': 'exam_result_extended',
                'ordering': ['-date'],
            },
        ),
        
        # Add indexes for performance
        migrations.AddIndex(
            model_name='polymorphicquestion',
            index=models.Index(fields=['question_type', 'course'], name='poly_q_type_course_idx'),
        ),
        migrations.AddIndex(
            model_name='polymorphicquestion',
            index=models.Index(fields=['is_active'], name='poly_q_active_idx'),
        ),
        migrations.AddIndex(
            model_name='resultextended',
            index=models.Index(fields=['student', 'exam'], name='result_ext_student_exam_idx'),
        ),
    ]
