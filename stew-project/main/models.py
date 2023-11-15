from django.db import models
from django.utils import timezone
from users.models import CustomUser


# Create your models here.

class Course(models.Model):
    
    name = models.CharField(max_length=100)
    
    join_code = models.CharField(max_length=100, unique=True)
    
    instructor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="taught_courses")
    
    students = models.ManyToManyField(CustomUser, verbose_name=("Students"), related_name="courses", through="Enrollment")
    
    students_can_make_teams = models.BooleanField(default=False)
    
class Enrollment(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="enrollment")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollment")
    enrolled_as_ta = models.BooleanField(default=False)
    
class Team(models.Model):
    name = models.CharField(max_length=100)
    
    join_code = models.CharField(max_length=100, unique=True)
    
    members = models.ManyToManyField(CustomUser, verbose_name=("Members"), blank=True, related_name="teams", through='Membership')
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="teams")
    
    parent_team = models.ForeignKey('self', on_delete=models.CASCADE, related_name="subteams", null=True, blank=True)
    
class Membership(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="membership")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="membership")
    
class Task(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=5000, blank=True)
    
    attached = models.FileField(upload_to='main/task_attachments/%Y%m%d', null=True, blank=True)
    
    due_date = models.DateTimeField("Due Date", default=timezone.now, null=True, blank=True)
    assigned_date = models.DateTimeField("Assigned", default=timezone.now)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="all_tasks")
    
    #This team is the parent team of the teams which would make a submission for the task
    #If null, then it is a course level task
    task_level = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="task_level", null=True)
    
    is_team_task = models.BooleanField(default=False)
    
class TaskSubmission(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="task_submissions")
    
    description = models.TextField(max_length=5000, blank=True)
    
    attached = models.FileField(upload_to='main/task_submissions/%Y%m%d', null=True, blank=True)
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="submitted_tasks", null=True, blank=True)
    
    submitter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="submitted_task")
    
    submission_time = models.DateTimeField("Submitted", default=timezone.now)
    
    grade = models.FloatField(null=True, blank=True)
    
    grading_comments = models.TextField(max_length=5000, blank=True)
    
    grading_attached = models.FileField(upload_to='main/task_grading/%Y%m%d', null=True, blank=True)
    
    grader = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="graded_tasks", null=True, blank=True)
    
    grade_visible = models.BooleanField(null=True, blank=True, default=True)
    
    is_graded = models.BooleanField(null=True, blank=True, default=False)
    
    
class Meeting(models.Model):
    link = models.URLField(max_length=300)
    memo = models.TextField(max_length=500, blank=True)
    meeting_time = models.DateTimeField("Meeting Time", default=timezone.now)
    is_complete = models.BooleanField(default=False)
    meeting_course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="meetings")
    meeting_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="meetings", null=True, blank=True)
    meeting_host = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="hosted_meetings")
    
class SubmissionComment(models.Model):
    submission = models.ForeignKey(TaskSubmission, on_delete=models.CASCADE, related_name="submission_comments")
    commenter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="comments")
    posted = models.DateTimeField("Posted", default=timezone.now)
    modified = models.DateTimeField("Modified", default=timezone.now)
    content = models.TextField(max_length=5000, blank=True)
    visible = models.BooleanField(null=True, blank=True, default=True)
    
    attached = models.FileField(upload_to='main/task_comments/%Y%m%d', null=True, blank=True)