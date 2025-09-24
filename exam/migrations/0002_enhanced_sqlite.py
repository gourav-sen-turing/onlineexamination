"""
Migration for Enhanced Question Types - SQLite Compatible
Works with SQLite, MySQL, and PostgreSQL
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0001_initial'),
    ]

    operations = [
        # Add new fields to Course model
        migrations.AddField(
            model_name='course',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='duration_minutes',
            field=models.PositiveIntegerField(default=60),
        ),
        migrations.AddField(
            model_name='course',
            name='pass_percentage',
            field=models.DecimalField(decimal_places=2, default=40.0, max_digits=5),
        ),
        migrations.AddField(
            model_name='course',
            name='randomize_questions',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='course',
            name='show_result_immediately',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='course',
            name='allow_review',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='course',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        
        # Create MCQQuestion model
        migrations.CreateModel(
            name='MCQQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_type', models.CharField(db_index=True, max_length=10, choices=[('MCQ', 'Multiple Choice Question'), ('TF', 'True/False'), ('FB', 'Fill in the Blank'), ('SA', 'Short Answer'), ('MT', 'Matching'), ('DD', 'Drag and Drop'), ('NUM', 'Numerical')])),
                ('question_text', models.TextField(help_text='The main question text')),
                ('marks', models.PositiveIntegerField(default=1)),
                ('explanation', models.TextField(blank=True, help_text='Explanation shown after answering')),
                ('difficulty_level', models.IntegerField(choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Hard')], default=2)),
                ('time_limit_seconds', models.PositiveIntegerField(blank=True, null=True)),
                ('tags', models.JSONField(blank=True, default=list, help_text='Tags for categorizing questions')),
                ('config', models.JSONField(default=dict, help_text='Additional configuration specific to question type')),
                ('times_attempted', models.PositiveIntegerField(default=0)),
                ('times_correct', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('option1', models.CharField(max_length=500)),
                ('option2', models.CharField(max_length=500)),
                ('option3', models.CharField(blank=True, max_length=500)),
                ('option4', models.CharField(blank=True, max_length=500)),
                ('correct_option', models.IntegerField(choices=[(1, 'Option 1'), (2, 'Option 2'), (3, 'Option 3'), (4, 'Option 4')])),
                ('allow_multiple', models.BooleanField(default=False)),
                ('correct_options', models.JSONField(blank=True, default=list, help_text='For multiple correct answers', null=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mcq_questions', to='exam.Course')),
            ],
            options={
                'verbose_name': 'Multiple Choice Question',
                'verbose_name_plural': 'Multiple Choice Questions',
            },
        ),
        
        # Create TrueFalseQuestion model
        migrations.CreateModel(
            name='TrueFalseQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_type', models.CharField(db_index=True, max_length=10, choices=[('MCQ', 'Multiple Choice Question'), ('TF', 'True/False'), ('FB', 'Fill in the Blank'), ('SA', 'Short Answer'), ('MT', 'Matching'), ('DD', 'Drag and Drop'), ('NUM', 'Numerical')])),
                ('question_text', models.TextField(help_text='The main question text')),
                ('marks', models.PositiveIntegerField(default=1)),
                ('explanation', models.TextField(blank=True, help_text='Explanation shown after answering')),
                ('difficulty_level', models.IntegerField(choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Hard')], default=2)),
                ('time_limit_seconds', models.PositiveIntegerField(blank=True, null=True)),
                ('tags', models.JSONField(blank=True, default=list, help_text='Tags for categorizing questions')),
                ('config', models.JSONField(default=dict, help_text='Additional configuration specific to question type')),
                ('times_attempted', models.PositiveIntegerField(default=0)),
                ('times_correct', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('correct_answer', models.BooleanField()),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tf_questions', to='exam.Course')),
            ],
            options={
                'verbose_name': 'True/False Question',
                'verbose_name_plural': 'True/False Questions',
            },
        ),
        
        # Create FillBlankQuestion model
        migrations.CreateModel(
            name='FillBlankQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_type', models.CharField(db_index=True, max_length=10, choices=[('MCQ', 'Multiple Choice Question'), ('TF', 'True/False'), ('FB', 'Fill in the Blank'), ('SA', 'Short Answer'), ('MT', 'Matching'), ('DD', 'Drag and Drop'), ('NUM', 'Numerical')])),
                ('question_text', models.TextField(help_text='The main question text')),
                ('marks', models.PositiveIntegerField(default=1)),
                ('explanation', models.TextField(blank=True, help_text='Explanation shown after answering')),
                ('difficulty_level', models.IntegerField(choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Hard')], default=2)),
                ('time_limit_seconds', models.PositiveIntegerField(blank=True, null=True)),
                ('tags', models.JSONField(blank=True, default=list, help_text='Tags for categorizing questions')),
                ('config', models.JSONField(default=dict, help_text='Additional configuration specific to question type')),
                ('times_attempted', models.PositiveIntegerField(default=0)),
                ('times_correct', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('correct_answers', models.JSONField(default=list, help_text='List of acceptable answers')),
                ('case_sensitive', models.BooleanField(default=False)),
                ('exact_match', models.BooleanField(default=False)),
                ('regex_pattern', models.CharField(blank=True, help_text='Regular expression for answer validation', max_length=500)),
                ('synonyms', models.JSONField(blank=True, default=dict, help_text='Dictionary of synonyms for answers')),
                ('partial_credit', models.BooleanField(default=False)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fb_questions', to='exam.Course')),
            ],
            options={
                'verbose_name': 'Fill in the Blank Question',
                'verbose_name_plural': 'Fill in the Blank Questions',
            },
        ),
        
        # Create ShortAnswerQuestion model
        migrations.CreateModel(
            name='ShortAnswerQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_type', models.CharField(db_index=True, max_length=10, choices=[('MCQ', 'Multiple Choice Question'), ('TF', 'True/False'), ('FB', 'Fill in the Blank'), ('SA', 'Short Answer'), ('MT', 'Matching'), ('DD', 'Drag and Drop'), ('NUM', 'Numerical')])),
                ('question_text', models.TextField(help_text='The main question text')),
                ('marks', models.PositiveIntegerField(default=1)),
                ('explanation', models.TextField(blank=True, help_text='Explanation shown after answering')),
                ('difficulty_level', models.IntegerField(choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Hard')], default=2)),
                ('time_limit_seconds', models.PositiveIntegerField(blank=True, null=True)),
                ('tags', models.JSONField(blank=True, default=list, help_text='Tags for categorizing questions')),
                ('config', models.JSONField(default=dict, help_text='Additional configuration specific to question type')),
                ('times_attempted', models.PositiveIntegerField(default=0)),
                ('times_correct', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('model_answer', models.TextField(help_text='Model answer for reference')),
                ('max_words', models.PositiveIntegerField(default=100)),
                ('keywords', models.JSONField(blank=True, default=list, help_text='Keywords that should be present in the answer')),
                ('keyword_weights', models.JSONField(blank=True, default=dict, help_text='Weights for each keyword for scoring')),
                ('use_ai_grading', models.BooleanField(default=False)),
                ('min_words', models.PositiveIntegerField(default=10)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sa_questions', to='exam.Course')),
            ],
            options={
                'verbose_name': 'Short Answer Question',
                'verbose_name_plural': 'Short Answer Questions',
            },
        ),
        
        # Create MatchingQuestion model
        migrations.CreateModel(
            name='MatchingQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_type', models.CharField(db_index=True, max_length=10, choices=[('MCQ', 'Multiple Choice Question'), ('TF', 'True/False'), ('FB', 'Fill in the Blank'), ('SA', 'Short Answer'), ('MT', 'Matching'), ('DD', 'Drag and Drop'), ('NUM', 'Numerical')])),
                ('question_text', models.TextField(help_text='The main question text')),
                ('marks', models.PositiveIntegerField(default=1)),
                ('explanation', models.TextField(blank=True, help_text='Explanation shown after answering')),
                ('difficulty_level', models.IntegerField(choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Hard')], default=2)),
                ('time_limit_seconds', models.PositiveIntegerField(blank=True, null=True)),
                ('tags', models.JSONField(blank=True, default=list, help_text='Tags for categorizing questions')),
                ('config', models.JSONField(default=dict, help_text='Additional configuration specific to question type')),
                ('times_attempted', models.PositiveIntegerField(default=0)),
                ('times_correct', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('left_items', models.JSONField(default=list, help_text='Items on the left side')),
                ('right_items', models.JSONField(default=list, help_text='Items on the right side')),
                ('correct_pairs', models.JSONField(help_text='Dictionary mapping left items to right items')),
                ('allow_partial_credit', models.BooleanField(default=True)),
                ('shuffle_items', models.BooleanField(default=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mt_questions', to='exam.Course')),
            ],
            options={
                'verbose_name': 'Matching Question',
                'verbose_name_plural': 'Matching Questions',
            },
        ),
        
        # Create DragDropQuestion model
        migrations.CreateModel(
            name='DragDropQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_type', models.CharField(db_index=True, max_length=10, choices=[('MCQ', 'Multiple Choice Question'), ('TF', 'True/False'), ('FB', 'Fill in the Blank'), ('SA', 'Short Answer'), ('MT', 'Matching'), ('DD', 'Drag and Drop'), ('NUM', 'Numerical')])),
                ('question_text', models.TextField(help_text='The main question text')),
                ('marks', models.PositiveIntegerField(default=1)),
                ('explanation', models.TextField(blank=True, help_text='Explanation shown after answering')),
                ('difficulty_level', models.IntegerField(choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Hard')], default=2)),
                ('time_limit_seconds', models.PositiveIntegerField(blank=True, null=True)),
                ('tags', models.JSONField(blank=True, default=list, help_text='Tags for categorizing questions')),
                ('config', models.JSONField(default=dict, help_text='Additional configuration specific to question type')),
                ('times_attempted', models.PositiveIntegerField(default=0)),
                ('times_correct', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('drop_zones', models.JSONField(default=list, help_text='Names of drop zones')),
                ('draggable_items', models.JSONField(default=list, help_text='Items that can be dragged')),
                ('correct_mapping', models.JSONField(help_text='Mapping of drop zones to correct items')),
                ('allow_multiple_per_zone', models.BooleanField(default=False)),
                ('show_zones_labels', models.BooleanField(default=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dd_questions', to='exam.Course')),
            ],
            options={
                'verbose_name': 'Drag and Drop Question',
                'verbose_name_plural': 'Drag and Drop Questions',
            },
        ),
        
        # Create NumericalQuestion model
        migrations.CreateModel(
            name='NumericalQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_type', models.CharField(db_index=True, max_length=10, choices=[('MCQ', 'Multiple Choice Question'), ('TF', 'True/False'), ('FB', 'Fill in the Blank'), ('SA', 'Short Answer'), ('MT', 'Matching'), ('DD', 'Drag and Drop'), ('NUM', 'Numerical')])),
                ('question_text', models.TextField(help_text='The main question text')),
                ('marks', models.PositiveIntegerField(default=1)),
                ('explanation', models.TextField(blank=True, help_text='Explanation shown after answering')),
                ('difficulty_level', models.IntegerField(choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Hard')], default=2)),
                ('time_limit_seconds', models.PositiveIntegerField(blank=True, null=True)),
                ('tags', models.JSONField(blank=True, default=list, help_text='Tags for categorizing questions')),
                ('config', models.JSONField(default=dict, help_text='Additional configuration specific to question type')),
                ('times_attempted', models.PositiveIntegerField(default=0)),
                ('times_correct', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('correct_answer', models.DecimalField(decimal_places=10, max_digits=20)),
                ('tolerance', models.DecimalField(decimal_places=10, default=0, help_text='Acceptable deviation from correct answer', max_digits=20)),
                ('tolerance_type', models.CharField(choices=[('absolute', 'Absolute'), ('percentage', 'Percentage'), ('significant_figures', 'Significant Figures')], default='absolute', max_length=20)),
                ('units', models.CharField(blank=True, max_length=50)),
                ('require_units', models.BooleanField(default=False)),
                ('decimal_places', models.PositiveIntegerField(blank=True, help_text='Required decimal places in answer', null=True)),
                ('scientific_notation', models.BooleanField(default=False)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='num_questions', to='exam.Course')),
            ],
            options={
                'verbose_name': 'Numerical Question',
                'verbose_name_plural': 'Numerical Questions',
            },
        ),
        
        # Update Result model
        migrations.AddField(
            model_name='result',
            name='percentage',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='result',
            name='grade',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='result',
            name='time_taken_seconds',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='result',
            name='question_scores',
            field=models.JSONField(default=list, help_text='List of question-wise scores'),
        ),
        migrations.AddField(
            model_name='result',
            name='answers_data',
            field=models.JSONField(default=dict, help_text='Complete answers data for review'),
        ),
        migrations.AddField(
            model_name='result',
            name='is_passed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='result',
            name='is_reviewed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='result',
            name='review_notes',
            field=models.TextField(blank=True),
        ),
    ]
