import mimetypes
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from users.models import CustomUser
from .forms import CourseForm, TeamForm, MeetingForm, TaskForm, TestForm
from .models import Course, Enrollment, Team, Membership, Meeting, Task, TaskSubmission, SubmissionComment

# Create your views here.

def home(request):
    return render(request, 'main/home.html')

def faq(request):
    return render(request, 'main/faq.html')

@login_required
def courses(request):
    is_teacher = False
    if (request.user.status != 'student'):
        is_teacher = True
    enrolled_courses = Course.objects.filter(students=request.user)
    taught_courses = Course.objects.filter(instructor=request.user)
    
    return render(request, 'main/courses.html', {'is_teacher':is_teacher, 'enrolled_courses':enrolled_courses, 'taught_courses':taught_courses})

@login_required
def logoutaccount(request):
    if request.method == 'POST':
        logout(request)
        return redirect('home')
    
def loginaccount(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'GET':
        return render(request, 'main/loginaccount.html')
    else:
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'main/loginaccount.html', {'error':'Username and password did not match'})
        else:
            login(request, user)
            return redirect('courses')

def signupaccount(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'GET':
        return render(request, 'main/signupaccount.html')
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user_status = 'student'
                if (request.POST['my_role'] == 'instructor'):
                    user_status = 'teacher'
                
                user = CustomUser.objects.create_user(
                    request.POST['username'], 
                    password=request.POST['password1'], 
                    email=request.POST['email'],
                    first_name=request.POST['first_name'],
                    last_name=request.POST['last_name'],
                    status=user_status)
                user.save()
                login(request, user)
                return redirect('courses')
            except IntegrityError:
                return render(request, 'main/signupaccount.html', {'error':'That username has already been taken. Please choose a new username.'})
                
        else:
            # The passwords did not match
            return render(request, 'main/signupaccount.html', {'error':'Passwords did not match'})
        
@login_required
def createcourse(request):
    if request.method == 'GET':
        return render(request, 'main/createcourse.html', {'form':CourseForm()})
    else:
        try:
            form = CourseForm(request.POST)
            new_course = form.save(commit=False)
            new_course.instructor = request.user
            
            try:
                if (request.POST['students_can_make_teams']):
                    new_course.students_can_make_teams = True
                else:
                    new_course.students_can_make_teams = False
            except:
                new_course.students_can_make_teams = False 
            
            new_course.save()
            return redirect('courses')
        except ValueError:
            if (len(request.POST['join_code']) <= 100 and len(request.POST['name']) <= 100):
                return render(request, 'main/createcourse.html', {'form':CourseForm(), 'error':'That Course Code is taken. Please choose another.'})
            else:
                return render(request, 'main/createcourse.html', {'form':CourseForm(), 'error':'Bad data entered. Please try again.'})

@login_required
def coursehome(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)
    #Need the .all because the ManyToMany is not iterable
    
    tas = CustomUser.objects.filter(courses=course, enrollment__enrolled_as_ta=True)
    
    tasks = Task.objects.filter(course=course, task_level=None).order_by('due_date')
    
    completed_meetings = request.GET.get('display_completed_meetings')
    
    if (completed_meetings == 'True'):
        completed_meetings = True
        meetings = Meeting.objects.filter(meeting_course=course, meeting_team=None).order_by('meeting_time')
    else:
        completed_meetings = False
        meetings = Meeting.objects.filter(meeting_course=course, meeting_team=None, is_complete=False).order_by('meeting_time')
    
    # if (course.students.filter(pk=request.user.id)):
    #     print('User is a student')
    # else:
    #     print('User is not a student')
        
    # if (course.instructor.id == request.user.id):
    #     print('User is the instructor')
    # else:
    #     print('User is not the instructor')
    
    students = CustomUser.objects.filter(courses=course, enrollment__enrolled_as_ta=False).order_by('last_name')
    
    if (course.instructor.id == request.user.id):
        teams = Team.objects.filter(course=course, parent_team=None)
        if request.method == 'GET':
            return render(request, 'main/coursehome.html', {'course':course, 'tas':tas, 'students':students, 'teams':teams, 'meetings':meetings, 'completed_meetings':completed_meetings, 'tasks':tasks})
    elif (course.students.filter(pk=request.user.id)):
        teams = Team.objects.filter(course=course, parent_team=None, members=request.user)
        if request.method == 'GET':
            return render(request, 'main/coursehome.html', {'course':course, 'tas':tas, 'students':students, 'teams':teams, 'meetings':meetings, 'completed_meetings':completed_meetings, 'tasks':tasks})
    elif (request.user.status == 'admin'):
        teams = Team.objects.filter(course=course, parent_team=None)
        if request.method == 'GET':
            return render(request, 'main/coursehome.html', {'course':course, 'tas':tas, 'students':students, 'teams':teams, 'meetings':meetings, 'completed_meetings':completed_meetings, 'tasks':tasks})
    else:
        return redirect('courses')
        
    

@login_required
def userprofile(request, user_pk):
    userprofile = get_object_or_404(CustomUser, pk=user_pk)
    
    if request.method == 'GET':
        return render(request, 'main/userprofile.html', {'userprofile':userprofile})
    
@login_required
def joincourse(request):
    if request.method == 'GET':
        return render(request, 'main/joincourse.html')
    else:
        try:
            course = get_object_or_404(Course, join_code=request.POST['join_code'])
            
            try:
                #Check if the student is already in the course
                enrollment = get_object_or_404(Enrollment, course=course, student=request.user)
            except:
                #otherwise make new enrollment
                enroll = Enrollment(course=course, student=request.user)
                enroll.save()
        
            return redirect('courses')
        except:
            return render(request, 'main/joincourse.html', {'error':'That Course cannot be found.'})

@login_required  
def jointeam(request):
    if request.method == 'GET':
        return render(request, 'main/jointeam.html')
    else:
        try:
            team = get_object_or_404(Team, join_code=request.POST['join_code'])
            if (team.parent_team != None):
                if (team.parent_team.members.filter(pk=request.user.id)):
                    try:
                        #Check if the student is already in the team
                        membership = get_object_or_404(Membership, team=team, student=request.user)
                    except:
                        #otherwise make new membership
                        member = Membership(team=team, student=request.user)
                        member.save()
                    return redirect('teamhome', team.id)
                else:
                    return render(request, 'main/jointeam.html', {'error':'You do not belong to that team\'s parent team.'})
            else:
                if (team.course.students.filter(pk=request.user.id)):
                    try:
                        #Check if the student is already in the team
                        membership = get_object_or_404(Membership, team=team, student=request.user)
                    except:
                        #otherwise make new membership
                        member = Membership(team=team, student=request.user)
                        member.save()
                    return redirect('teamhome', team.id)
                else:
                    return render(request, 'main/jointeam.html', {'error':'You do not belong to that team\'s course.'})
        except:
            return render(request, 'main/jointeam.html', {'error':'That Team cannot be found.'})
        

@login_required
def teamhome(request, team_pk):
    team = get_object_or_404(Team, pk=team_pk)
    
    completed_meetings = request.GET.get('display_completed_meetings')
    
    tasks = Task.objects.filter(course=team.course, task_level=team).order_by('due_date')
    
    if (completed_meetings == 'True'):
        completed_meetings = True
        meetings = Meeting.objects.filter(meeting_course=team.course, meeting_team=team).order_by('meeting_time')
    else:
        completed_meetings = False
        meetings = Meeting.objects.filter(meeting_course=team.course, meeting_team=team, is_complete=False).order_by('meeting_time')
    
    if (team.course.instructor.id == request.user.id):
        subteams = Team.objects.filter(course=team.course, parent_team=team)
        if request.method == 'GET':
            return render(request, 'main/teamhome.html', {'team':team, 'subteams':subteams, 'meetings':meetings, 'completed_meetings':completed_meetings, 'tasks':tasks})
    elif (team.members.filter(pk=request.user.id)):
        subteams = Team.objects.filter(course=team.course, parent_team=team, members=request.user)
        if request.method == 'GET':
            return render(request, 'main/teamhome.html', {'team':team, 'subteams':subteams, 'meetings':meetings, 'completed_meetings':completed_meetings, 'tasks':tasks})
    elif (request.user.status == 'admin'):
        subteams = Team.objects.filter(course=team.course, parent_team=team)
        if request.method == 'GET':
            return render(request, 'main/teamhome.html', {'team':team, 'subteams':subteams, 'meetings':meetings, 'completed_meetings':completed_meetings, 'tasks':tasks})
    else:
        return redirect('courses')
    
    
@login_required
def createteam(request, course_pk, team_pk):
    try:
        team = get_object_or_404(Team, pk=team_pk)
    except:
        team = None
        
    try:
        course = get_object_or_404(Course, pk=course_pk)
    except:
        return redirect('home')
    
    if (team != None):
        if (team.course.id != course.id):
            return redirect('home')
    
        if (not team.members.filter(pk=request.user.id)):
            return redirect('home')
    #If the user is not the instructor and students cannot make teams
    elif (request.user != course.instructor and not course.students_can_make_teams):
        return redirect('home')
    
    
    if request.method == 'GET':
        return render(request, 'main/createteam.html', {'form':TeamForm()})
    else:
        try:
            form = TeamForm(request.POST)
            new_team = form.save(commit=False)
            new_team.course = course
            
            new_team.parent_team = team
            new_team.save()
            
            member = Membership(team=new_team, student=request.user)
            member.save()
            
            return redirect('teamhome', new_team.id)
        except ValueError:
            if (len(request.POST['join_code']) <= 100 and len(request.POST['name']) <= 100):
                return render(request, 'main/createteam.html', {'form':TeamForm(), 'error':'That Team Code is taken. Please choose another.'})
            else:
                return render(request, 'main/createteam.html', {'form':TeamForm(), 'error':'Bad data entered. Please try again.'})

@login_required          
def addmeeting(request, course_pk, team_pk):
    try:
        team = get_object_or_404(Team, pk=team_pk)
    except:
        team = None
        
    try:
        course = get_object_or_404(Course, pk=course_pk)
    except:
        return redirect('home')
    
    if (team != None):
        if (team.course.id != course.id):
            return redirect('home')
    
        if (not team.members.filter(pk=request.user.id)) and (course.instructor.id != request.user.id):
            return redirect('home')
    
    
    if request.method == 'GET':
        return render(request, 'main/addmeeting.html', {'time':timezone.now()})
    else:
        try:
            form = MeetingForm(request.POST)
            new_meeting = form.save(commit=False)
            
            new_meeting.meeting_team = team
            new_meeting.meeting_host = request.user
            new_meeting.meeting_course = course
            
            new_meeting.save()
            
            if (team != None):
                return redirect('teamhome', team_pk)
            else:
                return redirect('coursehome', course_pk)
            
        except ValueError:
            return render(request, 'main/addmeeting.html', {'time':timezone.now(), 'error':'Bad data entered. Please try again.'})
        
@login_required
def meetinginfo(request, meeting_pk):
    meeting = get_object_or_404(Meeting, pk=meeting_pk)
    if (meeting.meeting_course.instructor.id == request.user.id):
        return render(request, 'main/meetinginfo.html', {'meeting':meeting})
    elif (meeting.meeting_team == None):
        if (meeting.meeting_course.students.filter(pk=request.user.id)):
            return render(request, 'main/meetinginfo.html', {'meeting':meeting})
        else:
            return redirect('home')
    elif (meeting.meeting_team.members.filter(pk=request.user.id)):
        return render(request, 'main/meetinginfo.html', {'meeting':meeting})
    else:
        return redirect('home')
    
@login_required
def editmeeting(request, meeting_pk):
    meeting = get_object_or_404(Meeting, pk=meeting_pk)
    
    if request.method == 'GET':
        if (meeting.meeting_host.id ==  request.user.id):
            return render(request, 'main/editmeeting.html', {'meeting':meeting})
        else:
            return redirect('home')
    else:
        if (meeting.meeting_host.id == request.user.id):
            try:
                meeting.meeting_time = request.POST['meeting_time']
                meeting.memo = request.POST['memo']
                meeting.link = request.POST['meeting_time']
                meeting.is_complete = request.POST['is_complete']
                meeting.save()
                return redirect('meetinginfo', meeting_pk)
            except ValueError:  
                return render(request, 'main/editmeeting.html', {'meeting':meeting, 'error':'Bad data entered. Please try again.'})
        else:
            return redirect('home')
        
@login_required
def assigntask(request, course_pk, team_pk):
    try:
        team = get_object_or_404(Team, pk=team_pk)
    except:
        team = None
        
    try:
        course = get_object_or_404(Course, pk=course_pk)
    except:
        return redirect('home')
    
    if (team != None):
        if (team.course.id != course.id):
            return redirect('home')
    
        if (not team.members.filter(pk=request.user.id)) and (course.instructor.id != request.user.id):
            return redirect('home')
    else:
        if (course.instructor.id != request.user.id):
            return redirect('home')
    
    
    if request.method == 'GET':
        return render(request, 'main/assigntask.html', {'time':timezone.now(), 'form':TaskForm()})
    else:
        try:
            form = TaskForm(request.POST, request.FILES)
            new_task = form.save(commit=False)
            
            new_task.task_level = team
            new_task.assigned_date = timezone.now()
            new_task.course = course
            
            new_task.save()
            
            if (team != None):
                return redirect('teamhome', team_pk)
            else:
                return redirect('coursehome', course_pk)
            
        except ValueError:
            return render(request, 'main/assigntask.html', {'time':timezone.now(), 'form':TaskForm(), 'error':'Bad data entered. Please try again.'})
        
        
@login_required
def viewtask(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if (task.course.instructor.id == request.user.id):
        submissions = TaskSubmission.objects.filter(task=task)
        return render(request, 'main/viewtask.html', {'task':task, 'submissions':submissions})
    elif (task.task_level == None):
        if (task.course.students.filter(pk=request.user.id)):
            enrollment = get_object_or_404(Enrollment, course=task.course, student=request.user)
            if (enrollment.enrolled_as_ta):
                submissions = TaskSubmission.objects.filter(task=task)
            else:
                #teams = Team.objects.filter(course=task.course, parent_team=None, members=request.user.id)
                submissions = TaskSubmission.objects.filter(task=task, team__members=request.user).union(TaskSubmission.objects.filter(task=task, submitter=request.user))
            return render(request, 'main/viewtask.html', {'task':task, 'submissions':submissions})
        else:
            return redirect('home')
    elif (task.task_level.members.filter(pk=request.user.id)):
        #teams = Team.objects.filter(course=task.course, parent_team=task.task_level, members=request.user.id)
        submissions = TaskSubmission.objects.filter(task=task)
        return render(request, 'main/viewtask.html', {'task':task, 'submissions':submissions})
    else:
        return redirect('home')
    
@login_required
def downloadtaskattachment(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if (task.course.instructor.id == request.user.id):
        file_path = task.attached.url
        filename = task.attached.url
        
        file = task.attached
        mime_type, blank = mimetypes.guess_type(file_path)
        response = HttpResponse(file, content_type=mime_type)
        response['Content-Disposition'] = "attachment; filename=%s" % filename
        return response
    elif (task.task_level == None):
        if (task.course.students.filter(pk=request.user.id)):
            file_path = task.attached.url
            filename = task.attached.url
            
            file = task.attached
            mime_type, blank = mimetypes.guess_type(file_path)
            response = HttpResponse(file, content_type=mime_type)
            response['Content-Disposition'] = "attachment; filename=%s" % filename
            return response
        else:
            return redirect('home')
    elif (task.task_level.members.filter(pk=request.user.id)):
        file_path = task.attached.url
        filename = task.attached.url
        
        file = task.attached
        mime_type, blank = mimetypes.guess_type(file_path)
        response = HttpResponse(file, content_type=mime_type)
        response['Content-Disposition'] = "attachment; filename=%s" % filename
        return response
    else:
        return redirect('home')
    
@login_required
def edittask(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    
    if request.method == 'GET':
        if (task.course.instructor.id == request.user.id):
            return render(request, 'main/edittask.html', {'task':task})
        elif (task.task_level != None):
            if (task.task_level.members.filter(pk=request.user.id)):
                return render(request, 'main/edittask.html', {'task':task})
            else:
                return redirect('home')
        else:
            return redirect('home')
    else:
        if (task.course.instructor.id == request.user.id):
            try:
                task.name = request.POST['name']
                task.description = request.POST['description']
                if (request.FILES):
                        task.attached = request.FILES['attached']
                task.due_date = request.POST['due_date']
                if (request.POST['is_team_task'] == "True"):
                    task.is_team_task = True
                else:
                    task.is_team_task = False
                task.save()
                return redirect('viewtask', task_pk)
            except ValueError:  
                return render(request, 'main/edittask.html', {'task':task, 'error':'Bad data entered. Please try again.'})
        elif (task.task_level != None):
            if (task.task_level.members.filter(pk=request.user.id)):
                try:
                    task.name = request.POST['name']
                    task.description = request.POST['description']
                    if (request.FILES):
                        task.attached = request.FILES['attached']
                    task.due_date = request.POST['due_date']
                    if (request.POST['is_team_task'] == "True"):
                        task.is_team_task = True
                    else:
                        task.is_team_task = False
                    task.save()
                    return redirect('viewtask', task_pk)
                except ValueError:  
                    return render(request, 'main/edittask.html', {'task':task, 'error':'Bad data entered. Please try again.'})
            else:
                return redirect('home')
        else:
            return redirect('home')
        
@login_required       
def addtasksubmission(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if request.method == 'GET':
        if (task.course.instructor.id == request.user.id):
            if (task.task_level == None):
                teams = Team.objects.filter(course=task.course, parent_team=None)
            else:
                teams = Team.objects.filter(course=task.course, parent_team=task.task_level)
            
            if (task.is_team_task):
                return render(request, 'main/addtasksubmission.html', {'task':task, 'teams':teams})
            else:
                return render(request, 'main/addtasksubmission.html', {'task':task})
        elif (task.task_level == None):
            if (task.course.students.filter(pk=request.user.id)):
                teams = Team.objects.filter(course=task.course, parent_team=None, members=request.user.id)
                if (task.is_team_task):
                    return render(request, 'main/addtasksubmission.html', {'task':task, 'teams':teams})
                else:
                    return render(request, 'main/addtasksubmission.html', {'task':task})
            else:
                return redirect('home')
        elif (task.task_level.members.filter(pk=request.user.id)):
            teams = Team.objects.filter(course=task.course, parent_team=task.task_level, members=request.user.id)
            if (task.is_team_task):
                return render(request, 'main/addtasksubmission.html', {'task':task, 'teams':teams})
            else:
                return render(request, 'main/addtasksubmission.html', {'task':task})
        else:
            return redirect('home')
    else:
        try:
            if (request.POST['team'] != '0'):
                team = get_object_or_404(Team, pk=request.POST['team'])
            else:
                team = None
            
            submission = TaskSubmission.objects.create(task=task, description=request.POST['description'], team=team, submitter=request.user)
            
            if (request.FILES):
                submission.attached = request.FILES['attached']
            submission.save()
            
            return redirect('viewtask', task.id)
            
        except ValueError:
            if (task.course.instructor.id == request.user.id):
                if (task.task_level == None):
                    teams = Team.objects.filter(course=task.course, parent_team=None)
                else:
                    teams = Team.objects.filter(course=task.course, parent_team=task.task_level)
                
                if (task.is_team_task):
                    return render(request, 'main/addtasksubmission.html', {'task':task, 'teams':teams, 'error':'Bad data'})
                else:
                    return render(request, 'main/addtasksubmission.html', {'task':task, 'error':'Bad data'})
            elif (task.task_level == None):
                if (task.course.students.filter(pk=request.user.id)):
                    teams = Team.objects.filter(course=task.course, parent_team=None, members=request.user.id)
                    if (task.is_team_task):
                        return render(request, 'main/addtasksubmission.html', {'task':task, 'teams':teams, 'error':'Bad data'})
                    else:
                        return render(request, 'main/addtasksubmission.html', {'task':task, 'error':'Bad data'})
                else:
                    return redirect('home')
            elif (task.task_level.members.filter(pk=request.user.id)):
                teams = Team.objects.filter(course=task.course, parent_team=task.task_level, members=request.user.id)
                if (task.is_team_task):
                    return render(request, 'main/addtasksubmission.html', {'task':task, 'teams':teams, 'error':'Bad data'})
                else:
                    return render(request, 'main/addtasksubmission.html', {'task':task, 'error':'Bad data'})
            else:
                return redirect('home')
            
@login_required     
def viewsubmission(request, submission_pk):
    submission = get_object_or_404(TaskSubmission, pk=submission_pk)
    
    if (submission.task.task_level == None):
        if (submission.task.course.instructor.id == request.user.id):
            comments = SubmissionComment.objects.filter(submission=submission).order_by('posted')
            return render(request, 'main/viewsubmission.html', {'submission':submission, 'comments':comments, 'can_grade':True})
        else:
            if (submission.task.course.students.filter(pk=request.user.id)):
                enrollment = get_object_or_404(Enrollment, course=submission.task.course, student=request.user)
                if (enrollment.enrolled_as_ta):
                    comments = SubmissionComment.objects.filter(submission=submission).order_by('posted')
                    return render(request, 'main/viewsubmission.html', {'submission':submission, 'comments':comments, 'can_grade':True})
                else:
                    if (submission.submitter == request.user) or (submission.team.members.contains(request.user)):
                        comments = SubmissionComment.objects.filter(submission=submission).order_by('posted')
                        return render(request, 'main/viewsubmission.html', {'submission':submission, 'comments':comments})
                    else:
                        return redirect('home')
    else:
        if (submission.task.course.instructor.id == request.user.id):
            comments = SubmissionComment.objects.filter(submission=submission).order_by('posted')
            return render(request, 'main/viewsubmission.html', {'submission':submission, 'comments':comments})
        elif (submission.task.task_level.members.filter(pk=request.user.id)):
            comments = SubmissionComment.objects.filter(submission=submission).order_by('posted')
            return render(request, 'main/viewsubmission.html', {'submission':submission, 'comments':comments})
        else:
            return redirect('home')
       
            
@login_required    
def downloadsubmissionattachment(request, submission_pk):
    submission = get_object_or_404(TaskSubmission, pk=submission_pk)
    if (submission.task.course.instructor == request.user):
        file_path = submission.attached.url
        filename = submission.attached.url
        
        file = submission.attached
        mime_type, blank = mimetypes.guess_type(file_path)
        response = HttpResponse(file, content_type=mime_type)
        response['Content-Disposition'] = "attachment; filename=%s" % filename
        return response
    elif (submission.task.task_level == None):
        if (submission.team.members.contains(request.user)):
            file_path = submission.attached.url
            filename = submission.attached.url
            
            file = submission.attached
            mime_type, blank = mimetypes.guess_type(file_path)
            response = HttpResponse(file, content_type=mime_type)
            response['Content-Disposition'] = "attachment; filename=%s" % filename
            return response
        elif (submission.task.course.students.filter(pk=request.user.id, enrollment__enrolled_as_ta=True)):
            file_path = submission.attached.url
            filename = submission.attached.url
            
            file = submission.attached
            mime_type, blank = mimetypes.guess_type(file_path)
            response = HttpResponse(file, content_type=mime_type)
            response['Content-Disposition'] = "attachment; filename=%s" % filename
            return response
        else:
            return redirect('home')
    elif (submission.task.task_level.members.contains(request.user)):
        file_path = submission.attached.url
        filename = submission.attached.url
        
        file = submission.attached
        mime_type, blank = mimetypes.guess_type(file_path)
        response = HttpResponse(file, content_type=mime_type)
        response['Content-Disposition'] = "attachment; filename=%s" % filename
        return response
    else:
        return redirect('home')

@login_required    
def downloadgradingattachment(request, submission_pk):
    submission = get_object_or_404(TaskSubmission, pk=submission_pk)
    if (submission.task.course.instructor == request.user):
        file_path = submission.grading_attached.url
        filename = submission.grading_attached.url
        
        file = submission.grading_attached
        mime_type, blank = mimetypes.guess_type(file_path)
        response = HttpResponse(file, content_type=mime_type)
        response['Content-Disposition'] = "attachment; filename=%s" % filename
        return response
    elif (submission.task.task_level == None):
        if (submission.team.members.contains(request.user)):
            file_path = submission.grading_attached.url
            filename = submission.grading_attached.url
            
            file = submission.grading_attached
            mime_type, blank = mimetypes.guess_type(file_path)
            response = HttpResponse(file, content_type=mime_type)
            response['Content-Disposition'] = "attachment; filename=%s" % filename
            return response
        elif (submission.task.course.students.filter(pk=request.user.id, enrollment__enrolled_as_ta=True)):
            file_path = submission.grading_attached.url
            filename = submission.grading_attached.url
            
            file = submission.grading_attached
            mime_type, blank = mimetypes.guess_type(file_path)
            response = HttpResponse(file, content_type=mime_type)
            response['Content-Disposition'] = "attachment; filename=%s" % filename
            return response
        else:
            return redirect('home')
    elif (submission.task.task_level.members.contains(request.user)):
        file_path = submission.grading_attached.url
        filename = submission.grading_attached.url
        
        file = submission.grading_attached
        mime_type, blank = mimetypes.guess_type(file_path)
        response = HttpResponse(file, content_type=mime_type)
        response['Content-Disposition'] = "attachment; filename=%s" % filename
        return response
    else:
        return redirect('home')
    
def test(request):
    return render(request, 'main/test.html', {'form':TestForm()})

@login_required   
def gradesubmission(request, submission_pk):
    submission = get_object_or_404(TaskSubmission, pk=submission_pk)
    if (submission.task.course.instructor == request.user):
        if request.method == 'GET':
            return render(request, 'main/gradesubmission.html', {'submission':submission})
        else:
            try:
                submission.grade = request.POST['grade']
                submission.grading_comments = request.POST['grading_comments']
                if (request.FILES):
                        submission.grading_attached = request.FILES['grading_attached']
                submission.grader = request.user
                try:
                    if (request.POST['grade_visible']):
                        submission.grade_visible = True
                    else:
                        submission.grade_visible = False
                except:
                    submission.grade_visible = False
                    
                submission.is_graded = True
                submission.save()
                return redirect('viewsubmission', submission_pk)
            except ValueError:  
                return render(request, 'main/gradesubmission.html', {'submission':submission,'error':'Bad data entered. Please try again.'})
            
    elif (submission.task.task_level == None):
        if (submission.task.course.students.filter(pk=request.user.id, enrollment__enrolled_as_ta=True)):
            if request.method == 'GET':
                return render(request, 'main/gradesubmission.html', {'submission':submission})
            else:
                try:
                    submission.grade = request.POST['grade']
                    submission.grading_comments = request.POST['grading_comments']
                    if (request.FILES):
                            submission.grading_attached = request.FILES['grading_attached']
                    submission.grader = request.user
                    try:
                        if (request.POST['grade_visible']):
                            submission.grade_visible = True
                        else:
                            submission.grade_visible = False
                    except:
                        submission.grade_visible = False
                    
                    submission.is_graded = True
                    submission.save()
                    return redirect('viewsubmission', submission_pk)
                except ValueError:  
                    return render(request, 'main/gradesubmission.html', {'submission':submission,'error':'Bad data entered. Please try again.'})
        else:
            return redirect('home')
    else:
        return redirect('home')
    
@login_required
def editsubmission(request, submission_pk):
    submission = get_object_or_404(TaskSubmission, pk=submission_pk)
    if (not submission.is_graded):
        if (submission.submitter == request.user):
            if request.method == 'GET':
                return render(request, 'main/editsubmission.html', {'submission':submission})
            else:
                try:
                    submission.submitter = request.user
                    submission.submission_time = timezone.now()
                    submission.description = request.POST['description']
                    if (request.FILES):
                            submission.attached = request.FILES['attached']
                        
                    submission.save()
                    return redirect('viewsubmission', submission_pk)
                except ValueError:  
                    return render(request, 'main/editsubmission.html', {'submission':submission,'error':'Bad data entered. Please try again.'})
                
        elif (submission.team != None):
            if (submission.task.task_level.members.filter(pk=request.user.id)):
                if request.method == 'GET':
                    return render(request, 'main/editsubmission.html', {'submission':submission})
                else:
                    try:
                        submission.submitter = request.user
                        submission.submission_time = timezone.now()
                        submission.description = request.POST['description']
                        if (request.FILES):
                                submission.attached = request.FILES['attached']
                            
                        submission.save()
                        return redirect('viewsubmission', submission_pk)
                    except ValueError:  
                        return render(request, 'main/editsubmission.html', {'submission':submission,'error':'Bad data entered. Please try again.'})
            
    else:
        return redirect('home')
    
    
@login_required     
def commentsubmission(request, submission_pk):
    submission = get_object_or_404(TaskSubmission, pk=submission_pk)
    
    if (submission.task.task_level == None):
        if (submission.task.course.instructor.id == request.user.id):
            
            if request.method == 'GET':
                return render(request, 'main/commentsubmission.html', {'submission':submission})
            else:
                try:
                    comment = SubmissionComment.objects.create(submission=submission, commenter=request.user, content=request.POST['content'])
                
                    if (request.FILES):
                        comment.attached = request.FILES['attached']
                    
                    try:
                        if (request.POST['visible']):
                            comment.visible = True
                        else:
                            comment.visible = False
                    except:
                        comment.visible = False    
                    
                    comment.save()
                    return redirect('viewsubmission', submission_pk)
                except ValueError: 
                    return render(request, 'main/commentsubmission.html', {'submission':submission,'error':'Bad data entered. Please try again.'})

        else:
            if (submission.task.course.students.filter(pk=request.user.id)):
                enrollment = get_object_or_404(Enrollment, course=submission.task.course, student=request.user)
                if (enrollment.enrolled_as_ta):
                    if request.method == 'GET':
                        return render(request, 'main/commentsubmission.html', {'submission':submission})
                    else:
                        try:
                            comment = SubmissionComment.objects.create(submission=submission, commenter=request.user, content=request.POST['content'])
                        
                            if (request.FILES):
                                comment.attached = request.FILES['attached']
                            
                            try:
                                if (request.POST['visible']):
                                    comment.visible = True
                                else:
                                    comment.visible = False
                            except:
                                comment.visible = False      
                            
                            comment.save()
                            return redirect('viewsubmission', submission_pk)
                        except ValueError: 
                            return render(request, 'main/commentsubmission.html', {'submission':submission,'error':'Bad data entered. Please try again.'})
                
                
                else:
                    if (submission.submitter == request.user) or (submission.team.members.contains(request.user)):
                        if request.method == 'GET':
                            return render(request, 'main/commentsubmission.html', {'submission':submission})
                        else:
                            try:
                                comment = SubmissionComment.objects.create(submission=submission, commenter=request.user, content=request.POST['content'])
                            
                                if (request.FILES):
                                    comment.attached = request.FILES['attached']
                                    
                                try:
                                    if (request.POST['visible']):
                                        comment.visible = True
                                    else:
                                        comment.visible = False
                                except:
                                    comment.visible = False  
                                    
                                comment.save()
                                return redirect('viewsubmission', submission_pk)
                            except ValueError: 
                                return render(request, 'main/commentsubmission.html', {'submission':submission,'error':'Bad data entered. Please try again.'})
                    
                    else:
                        return redirect('home')
    else:
        if (submission.task.course.instructor.id == request.user.id):
            if request.method == 'GET':
                return render(request, 'main/commentsubmission.html', {'submission':submission})
            else:
                try:
                    comment = SubmissionComment.objects.create(submission=submission, commenter=request.user, content=request.POST['content'])
                
                    if (request.FILES):
                        comment.attached = request.FILES['attached']
                    
                    try:
                        if (request.POST['visible']):
                            comment.visible = True
                        else:
                            comment.visible = False
                    except:
                        comment.visible = False      
                    
                    comment.save()
                    return redirect('viewsubmission', submission_pk)
                except ValueError: 
                    return render(request, 'main/commentsubmission.html', {'submission':submission,'error':'Bad data entered. Please try again.'})
                
        elif (submission.task.task_level.members.filter(pk=request.user.id)):
            if request.method == 'GET':
                return render(request, 'main/commentsubmission.html', {'submission':submission})
            else:
                try:
                    comment = SubmissionComment.objects.create(submission=submission, commenter=request.user, content=request.POST['content'])
                
                    if (request.FILES):
                        comment.attached = request.FILES['attached']
                        
                    try:
                        if (request.POST['visible']):
                            comment.visible = True
                        else:
                            comment.visible = False
                    except:
                        comment.visible = False  
                    
                    comment.save()
                    return redirect('viewsubmission', submission_pk)
                except ValueError: 
                    return render(request, 'main/commentsubmission.html', {'submission':submission,'error':'Bad data entered. Please try again.'})
        
        else:
            return redirect('home')
        
@login_required 
def editcomment(request, comment_pk):
    comment = get_object_or_404(SubmissionComment, pk=comment_pk)
    
    if (comment.commenter == request.user):
        if request.method == 'GET':
            return render(request, 'main/editcomment.html', {'comment':comment})
        else:
            try:
                if (request.FILES):
                    comment.attached = request.FILES['attached']
                    
                try:
                    if (request.POST['visible']):
                        comment.visible = True
                    else:
                        comment.visible = False
                except:
                    comment.visible = False    
                    
                comment.modified = timezone.now()
                    
                comment.save()
                return redirect('viewsubmission', comment.submission.id)
            except ValueError: 
                return render(request, 'main/editcomment.html', {'comment':comment,'error':'Bad data entered. Please try again.'})
            
    else:
        return redirect('home')

        
@login_required 
def downloadcommentattachment(request, comment_pk):
    comment = get_object_or_404(SubmissionComment, pk=comment_pk)
    
    if (comment.submission.task.task_level == None):
        if (comment.submission.task.course.instructor.id == request.user.id):
            file_path = comment.attached.url
            filename = comment.attached.url
            
            file = comment.attached
            mime_type, blank = mimetypes.guess_type(file_path)
            response = HttpResponse(file, content_type=mime_type)
            response['Content-Disposition'] = "attachment; filename=%s" % filename
            return response
        else:
            if (comment.submission.task.course.students.filter(pk=request.user.id)):
                enrollment = get_object_or_404(Enrollment, course=comment.submission.task.course, student=request.user)
                if (enrollment.enrolled_as_ta):
                    file_path = comment.attached.url
                    filename = comment.attached.url
                    
                    file = comment.attached
                    mime_type, blank = mimetypes.guess_type(file_path)
                    response = HttpResponse(file, content_type=mime_type)
                    response['Content-Disposition'] = "attachment; filename=%s" % filename
                    return response
                else:
                    if (comment.submission.submitter == request.user) or (comment.submission.team.members.contains(request.user)):
                        file_path = comment.attached.url
                        filename = comment.attached.url
                        
                        file = comment.attached
                        mime_type, blank = mimetypes.guess_type(file_path)
                        response = HttpResponse(file, content_type=mime_type)
                        response['Content-Disposition'] = "attachment; filename=%s" % filename
                        return response
                    else:
                        return redirect('home')
    else:
        if (comment.submission.task.course.instructor.id == request.user.id):
            file_path = comment.attached.url
            filename = comment.attached.url
            
            file = comment.attached
            mime_type, blank = mimetypes.guess_type(file_path)
            response = HttpResponse(file, content_type=mime_type)
            response['Content-Disposition'] = "attachment; filename=%s" % filename
            return response
        elif (comment.submission.task.task_level.members.filter(pk=request.user.id)):
            file_path = comment.attached.url
            filename = comment.attached.url
            
            file = comment.attached
            mime_type, blank = mimetypes.guess_type(file_path)
            response = HttpResponse(file, content_type=mime_type)
            response['Content-Disposition'] = "attachment; filename=%s" % filename
            return response
        else:
            return redirect('home')
        
@login_required      
def addteachingassistant(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)
    if (request.user == course.instructor):
        if request.method == 'GET':
            students = CustomUser.objects.filter(courses=course, enrollment__enrolled_as_ta=False).order_by('last_name')
            return render(request, 'main/addteachingassistant.html', {'students':students})
        else:
            try:
                student = get_object_or_404(CustomUser, pk=int(request.POST['student_id']))
                enrollment = get_object_or_404(Enrollment, course=course, student=student)
            
                enrollment.enrolled_as_ta = True
                enrollment.save()
                
                return redirect('coursehome', course_pk)
            except:
                students = CustomUser.objects.filter(courses=course, enrollment__enrolled_as_ta=False).order_by('last_name')
                return render(request, 'main/addteachingassistant.html', {'students':students, 'error':'Could not find the specified student. Please try again.'})
            
    else:
        return redirect('home')
    
@login_required
def removeteachingassistant(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)
    if (request.user == course.instructor):
        if request.method == 'GET':
            tas = CustomUser.objects.filter(courses=course, enrollment__enrolled_as_ta=True).order_by('last_name')
            return render(request, 'main/removeteachingassistant.html', {'tas':tas})
        else:
            try:
                student = get_object_or_404(CustomUser, pk=request.POST['student_id'])
                enrollment = get_object_or_404(Enrollment, course=course, student=student)
            
                enrollment.enrolled_as_ta = False
                enrollment.save()
                
                return redirect('coursehome', course_pk)
            except:
                tas = CustomUser.objects.filter(courses=course, enrollment__enrolled_as_ta=True).order_by('last_name')
                return render(request, 'main/removeteachingassistant.html', {'tas':tas, 'error':'Could not find the specified student. Please try again.'})
            
    else:
        return redirect('home')
    

@login_required
def editcourseteamrules(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)
    if (request.user == course.instructor):
        if request.method == 'GET':
            return render(request, 'main/editcourseteamrules.html', {'course':course})
        else:
            try:
                try:
                    if (request.POST['students_can_make_teams']):
                        course.students_can_make_teams = True
                    else:
                        course.students_can_make_teams = False
                except:
                    course.students_can_make_teams = False 
                
                course.save()
                
                return redirect('coursehome', course_pk)
            except:
                return render(request, 'main/editcourseteamrules.html', {'error':'Something went wrong.'})
            
    else:
        return redirect('home')
    

@login_required
def edituserprofile(request, user_pk):
    userprofile = get_object_or_404(CustomUser, pk=user_pk)
    
    if (userprofile == request.user):
        if request.method == 'GET':
            return render(request, 'main/edituserprofile.html', {'userprofile':userprofile})
        else:
            
            try:
                if (request.FILES):
                    userprofile.profile_picture = request.FILES['profile_picture']
                    
                userprofile.description = request.POST['description']
                    
                userprofile.save()
                return redirect('userprofile', user_pk)
            except:
                return render(request, 'main/edituserprofile.html', {'userprofile':userprofile, 'error':'Bad data entered. Please try again.'})
        
    else:
        return redirect('home')
    
    
