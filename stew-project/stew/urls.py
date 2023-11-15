"""
URL configuration for stew project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from main import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    #STEW
    path('', views.home, name='home'),
    path('courses/', views.courses, name='courses'),
    path('createcourse/', views.createcourse, name='createcourse'),
    path('joincourse/', views.joincourse, name='joincourse'),
    path('course/<int:course_pk>/', views.coursehome, name='coursehome'),
    
    path('addteachingassistant/<int:course_pk>/', views.addteachingassistant, name='addteachingassistant'),
    path('removeteachingassistant/<int:course_pk>/', views.removeteachingassistant, name='removeteachingassistant'),
    path('editcourseteamrules/<int:course_pk>/', views.editcourseteamrules, name='editcourseteamrules'),
    
    #Teams
    path('jointeam/', views.jointeam, name='jointeam'),
    path('createteam/<int:course_pk>/<int:team_pk>/', views.createteam, name='createteam'),
    path('team/<int:team_pk>/', views.teamhome, name='teamhome'),
    
    #Meetings
    path('addmeeting/<int:course_pk>/<int:team_pk>/', views.addmeeting, name='addmeeting'),
    path('meetinginfo/<int:meeting_pk>/', views.meetinginfo, name='meetinginfo'),
    path('editmeeting/<int:meeting_pk>/', views.editmeeting, name='editmeeting'),
    
    #Tasks
    path('assigntask/<int:course_pk>/<int:team_pk>/', views.assigntask, name='assigntask'),
    path('viewtask/<int:task_pk>/', views.viewtask, name='viewtask'),
    path('edittask/<int:task_pk>/', views.edittask, name='edittask'),
    path('downloadtaskattachment/<int:task_pk>/', views.downloadtaskattachment, name='downloadtaskattachment'),
    path('addtasksubmission/<int:task_pk>/', views.addtasksubmission, name='addtasksubmission'),
    path('viewtasksubmission/<int:submission_pk>/', views.viewsubmission, name='viewsubmission'),
    path('editsubmission/<int:submission_pk>/', views.editsubmission, name='editsubmission'),
    path('gradesubmission/<int:submission_pk>/', views.gradesubmission, name='gradesubmission'),
    path('downloadsubmissionattachment/<int:submission_pk>/', views.downloadsubmissionattachment, name='downloadsubmissionattachment'),
    path('downloadgradingattachment/<int:submission_pk>/', views.downloadgradingattachment, name='downloadgradingattachment'),
    
    path('commentsubmission/<int:submission_pk>/', views.commentsubmission, name='commentsubmission'),
    path('editcomment/<int:comment_pk>/', views.editcomment, name='editcomment'),
    path('downloadcommentattachment/<int:comment_pk>/', views.downloadcommentattachment, name='downloadcommentattachment'),
    
    #FAQs
    path('faq/', views.faq, name='faq'),
    
    #Account Management
    path('logout/', views.logoutaccount, name='logoutaccount'),
    path('login/', views.loginaccount, name='loginaccount'),
    path('signup/', views.signupaccount, name='signupaccount'),
    path('user/<int:user_pk>/', views.userprofile, name='userprofile'),
    
    path('edituser/<int:user_pk>/', views.edituserprofile, name='edituserprofile'),
    
    path('test/', views.test, name='test')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
