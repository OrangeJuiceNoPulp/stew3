from django.contrib import admin
from .models import Course, Team, Task, TaskSubmission, Membership, Enrollment

# Register your models here.

admin.site.register(Course)
admin.site.register(Team)
admin.site.register(Task)
admin.site.register(TaskSubmission)
admin.site.register(Membership)
admin.site.register(Enrollment)