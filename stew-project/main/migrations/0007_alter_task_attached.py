# Generated by Django 4.2.6 on 2023-10-30 03:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_tasksubmission_is_graded_alter_task_attached'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='attached',
            field=models.FileField(blank=True, null=True, upload_to='main/task_attachments/%m%Y%d%H'),
        ),
    ]