"""
Data Migration to convert existing MCQ questions to new structure
Ensures backward compatibility with existing data
"""
from django.db import migrations


def migrate_existing_questions(apps, schema_editor):
    """Convert existing Question model data to MCQQuestion"""
    Question = apps.get_model('exam', 'Question')
    MCQQuestion = apps.get_model('exam', 'MCQQuestion')
    
    for old_question in Question.objects.all():
        # Map old answer choices to correct_option number
        answer_mapping = {
            'Option1': 1,
            'Option2': 2,
            'Option3': 3,
            'Option4': 4,
        }
        
        correct_option = answer_mapping.get(old_question.answer, 1)
        
        # Create new MCQQuestion from old Question
        MCQQuestion.objects.create(
            course=old_question.course,
            question_text=old_question.question,
            marks=old_question.marks,
            option1=old_question.option1,
            option2=old_question.option2,
            option3=old_question.option3 if old_question.option3 else '',
            option4=old_question.option4 if old_question.option4 else '',
            correct_option=correct_option,
            allow_multiple=False,
            question_type='MCQ',
            difficulty_level=2,  # Default to medium
            is_active=True
        )


def reverse_migration(apps, schema_editor):
    """Reverse the migration if needed"""
    MCQQuestion = apps.get_model('exam', 'MCQQuestion')
    Question = apps.get_model('exam', 'Question')
    
    for mcq in MCQQuestion.objects.all():
        # Map correct_option number back to old format
        option_mapping = {
            1: 'Option1',
            2: 'Option2',
            3: 'Option3',
            4: 'Option4',
        }
        
        answer = option_mapping.get(mcq.correct_option, 'Option1')
        
        Question.objects.create(
            course=mcq.course,
            question=mcq.question_text,
            marks=mcq.marks,
            option1=mcq.option1,
            option2=mcq.option2,
            option3=mcq.option3,
            option4=mcq.option4,
            answer=answer
        )


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0002_enhanced_question_types'),
    ]

    operations = [
        migrations.RunPython(migrate_existing_questions, reverse_migration),
    ]
