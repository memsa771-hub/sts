from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse, Http404
from django.core.paginator import Paginator
from django.forms import forms
from django.template.loader import render_to_string


def home_view(request):
    """Landing page view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


from .models import (
    User, Project, DailySiteReport, TeamMember, Activity, ActivityWork, 
    Notification, ReportPhoto, Worker, ProjectWorkerAssignment, LaborDetail, MaterialUsage, RFI
)
from .forms import (
    CustomUserCreationForm, ProjectForm, DailySiteReportForm, LaborDetailForm, 
    MaterialUsageForm, WorkerForm, ProjectWorkerAssignmentForm, ActivityForm, 
    ActivityWorkForm, ActivitySelectionForm, RFIForm, TeamMemberForm, RFIInspectorResponseForm
)
import json


def login_view(request):
    """Custom login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/login.html')


def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to Site Tracking System, {user.first_name}!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'auth/register.html', {'form': form})


def logout_view(request):
    """Custom logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def dashboard(request):
    """Main dashboard view"""
    user = request.user
    
    # Get user's projects based on role
    if user.role == 'admin':
        projects = Project.objects.all()  # Admin can see all projects
    elif user.role == 'site_engineer':
        projects = Project.objects.filter(site_engineer=user)
    elif user.role == 'consultant':
        projects = Project.objects.filter(consultant=user)
    elif user.role == 'contractor':
        projects = Project.objects.filter(contractor=user)
    elif user.role == 'client':
        projects = Project.objects.filter(client=user)
    elif user.role == 'viewer':
        projects = Project.objects.filter(viewer=user)
    else:
        projects = Project.objects.none()
    
    # Dashboard statistics
    total_projects = projects.count()
    ongoing_projects = projects.filter(status='ongoing').count()
    completed_projects = projects.filter(status='completed').count()
    
    # Recent notifications
    notifications = Notification.objects.filter(recipient=user, is_read=False)[:5]
    
    # Recent reports (for site engineers and consultants)
    recent_reports = []
    if user.role in ['site_engineer', 'consultant']:
        if user.role == 'site_engineer':
            recent_reports = DailySiteReport.objects.filter(site_engineer=user)[:5]
        else:
            recent_reports = DailySiteReport.objects.filter(
                project__consultant=user
            )[:5]
    
    # Upcoming bookings (next 24 hours) - similar to the hotel dashboard
    upcoming_reports = 0
    if user.role == 'site_engineer':
        tomorrow = timezone.now().date() + timezone.timedelta(days=1)
        upcoming_reports = projects.filter(
            status='ongoing',
            end_date__gte=tomorrow
        ).count()
    
    context = {
        'total_projects': total_projects,
        'ongoing_projects': ongoing_projects,
        'completed_projects': completed_projects,
        'upcoming_reports': upcoming_reports,
        'projects': projects[:6],  # Recent projects for dashboard
        'notifications': notifications,
        'recent_reports': recent_reports,
        'user': user,
    }
    
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def projects_list(request):
    """List all projects"""
    user = request.user
    
    # Filter projects based on user role
    if user.role == 'admin':
        projects = Project.objects.all()
    elif user.role == 'site_engineer':
        projects = Project.objects.filter(site_engineer=user)
    elif user.role == 'consultant':
        projects = Project.objects.filter(consultant=user)
    elif user.role == 'contractor':
        projects = Project.objects.filter(contractor=user)
    elif user.role == 'client':
        projects = Project.objects.filter(client=user)
    elif user.role == 'viewer':
        projects = Project.objects.filter(viewer=user)
    else:
        projects = Project.objects.none()
    
    # Search and filter
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    if search_query:
        projects = projects.filter(
            Q(title__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    if status_filter:
        projects = projects.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(projects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Project.STATUS_CHOICES,
    }
    
    return render(request, 'projects/projects_list.html', context)


@login_required
def project_detail(request, project_id):
    """Project detail view with tabs"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user has access to this project
    user_has_access = (
        request.user == project.site_engineer or
        request.user == project.consultant or
        request.user == project.contractor or
        request.user == project.client or
        request.user.role == 'admin'
    )
    
    if not user_has_access:
        messages.error(request, 'You do not have access to this project.')
        return redirect('projects_list')
    
    # Get project reports
    reports = DailySiteReport.objects.filter(project=project)
    
    # Get team members assigned to this project
    team_members = TeamMember.objects.filter(project=project, is_active=True)
    
    # Get active tab from URL parameter
    active_tab = request.GET.get('tab', 'overview')
    
    # Determine if user can edit (site engineer or admin only)
    can_edit = (request.user == project.site_engineer or request.user.role == 'admin')
    
    context = {
        'project': project,
        'reports': reports,
        'team_members': team_members,
        'active_tab': active_tab,
        'can_edit': can_edit,
    }
    
    return render(request, 'projects/project_detail.html', context)


@login_required
def create_project(request):
    """Create new project - Admin and Site Engineers can create projects"""
    if request.user.role not in ['admin', 'site_engineer']:
        messages.error(request, 'Only admins and site engineers can create projects.')
        return redirect('projects_list')
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            # Auto-assign the creating site engineer
            if request.user.role == 'site_engineer':
                project.site_engineer = request.user
            project.save()
            messages.success(request, f'Project "{project.title}" created successfully!')
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm()
    
    return render(request, 'projects/create_project.html', {'form': form})


@login_required
def daily_reports_list(request):
    """List daily reports"""
    user = request.user
    
    if user.role == 'site_engineer':
        reports = DailySiteReport.objects.filter(site_engineer=user)
    elif user.role == 'consultant':
        reports = DailySiteReport.objects.filter(project__consultant=user)
    elif user.role == 'contractor':
        reports = DailySiteReport.objects.filter(project__contractor=user)
    elif user.role == 'client':
        reports = DailySiteReport.objects.filter(project__client=user)
    elif user.role == 'admin':
        reports = DailySiteReport.objects.all()
    elif user.role == 'viewer':
        reports = DailySiteReport.objects.filter(
            project__viewer=user,
            status='approved'
        )
    else:
        reports = DailySiteReport.objects.none()
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        reports = reports.filter(status=status_filter)
    
    # Filter by date
    date_filter = request.GET.get('date', '')
    if date_filter:
        try:
            from datetime import datetime
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            reports = reports.filter(date=filter_date)
        except ValueError:
            # Invalid date format, ignore the filter
            pass
    
    # Filter by date range (from and to dates)
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if date_from:
        try:
            from datetime import datetime
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            reports = reports.filter(date__gte=from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            from datetime import datetime
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            reports = reports.filter(date__lte=to_date)
        except ValueError:
            pass
    
    # Order by date (newest first)
    reports = reports.order_by('-date', '-created_at')
    
    # Pagination
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Quick filter dates
    from datetime import date, timedelta
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # This week (Monday to Sunday)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # This month
    month_start = today.replace(day=1)
    import calendar
    last_day = calendar.monthrange(today.year, today.month)[1]
    month_end = today.replace(day=last_day)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'date_from': date_from,
        'date_to': date_to,
        'status_choices': DailySiteReport.APPROVAL_STATUS,
        # Quick filter dates
        'today': today.strftime('%Y-%m-%d'),
        'yesterday': yesterday.strftime('%Y-%m-%d'),
        'week_start': week_start.strftime('%Y-%m-%d'),
        'week_end': week_end.strftime('%Y-%m-%d'),
        'month_start': month_start.strftime('%Y-%m-%d'),
        'month_end': month_end.strftime('%Y-%m-%d'),
    }
    
    return render(request, 'reports/daily_reports_list.html', context)


@login_required
def view_daily_report(request, report_id):
    """View individual daily site report"""
    report = get_object_or_404(DailySiteReport, id=report_id)
    
    # Permission check
    user = request.user
    if user.role == 'site_engineer' and report.site_engineer != user:
        messages.error(request, 'You can only view your own reports.')
        return redirect('daily_reports_list')
    elif user.role == 'consultant' and report.project.consultant != user:
        messages.error(request, 'You can only view reports from your projects.')
        return redirect('daily_reports_list')
    elif user.role == 'contractor' and report.project.contractor != user:
        messages.error(request, 'You can only view reports from your projects.')
        return redirect('daily_reports_list')
    elif user.role == 'client' and report.project.client != user:
        messages.error(request, 'You can only view reports from your projects.')
        return redirect('daily_reports_list')
    elif user.role == 'viewer' and (report.project.viewer != user or report.status != 'approved'):
        messages.error(request, 'You can only view approved reports from your assigned projects.')
        return redirect('daily_reports_list')
    elif user.role not in ['admin', 'site_engineer', 'consultant', 'contractor', 'client', 'viewer']:
        messages.error(request, 'You do not have permission to view reports.')
        return redirect('daily_reports_list')
    
    # Get activity work associated with this report (new format)
    activity_works = report.activity_work.select_related('activity').all()
    
    # Get independent activities (old format for backward compatibility)
    # Handle case where table might not exist yet
    independent_activities = []
    try:
        from core.models import DailyReportActivity
        independent_activities = DailyReportActivity.objects.filter(report=report).all()
    except Exception:
        # Table doesn't exist yet, will be empty list
        independent_activities = []
    
    # Pre-calculate percentages for activities if needed
    for work in activity_works:
        try:
            if not hasattr(work.activity, 'progress_percentage'):
                if work.activity.total_quantity and float(work.activity.total_quantity) > 0:
                    try:
                        completed = float(work.activity.total_quantity_completed)
                        total = float(work.activity.total_quantity)
                        work.activity.progress_percentage = min(round((completed / total) * 100, 2), 100)
                    except (TypeError, ValueError, ZeroDivisionError):
                        work.activity.progress_percentage = 0
                else:
                    work.activity.progress_percentage = 0
        except Exception:
            # Ensure we don't break the view if any calculation fails
            work.activity.progress_percentage = 0
    
    # Get photos associated with this report, ordered by upload time (newest first)
    photos = report.photos.all().order_by('-uploaded_at')
    
    # Prepare labor and material data
    labor_details = report.labor_details.all()
    material_usage = report.material_usage.all()
    
    context = {
        'report': report,
        'project': report.project,
        'activity_works': activity_works,
        'independent_activities': independent_activities,
        'photos': photos,
        'labor_details': labor_details,
        'material_usage': material_usage,
    }
    
    return render(request, 'reports/view_daily_report.html', context)


@login_required
def create_daily_report(request, project_id):
    """Create daily site report - Site Engineer only"""
    project = get_object_or_404(Project, id=project_id)
    
    if request.user.role != 'site_engineer' or request.user != project.site_engineer:
        messages.error(request, 'Only the assigned site engineer can create reports.')
        return redirect('project_detail', project_id=project.id)
    
    # Handle selected activities from activities page
    selected_activities_ids = request.POST.getlist('selected_activities') if request.method == 'POST' else None
    if selected_activities_ids:
        # Store selected activities in session for the form
        selected_activities = Activity.objects.filter(id__in=selected_activities_ids, project=project)
        request.session['report_selected_activities'] = [
            {
                'id': activity.id,
                'name': activity.name,
                'unit': activity.unit,
                'unit_display': activity.get_unit_display(),
                'total_quantity': float(activity.total_quantity) if activity.total_quantity else 0
            }
            for activity in selected_activities
        ]
        request.session['report_project_id'] = project_id
    
    # Check for selected activities from session
    selected_activities_data = None
    if ('report_selected_activities' in request.session and 
        request.session.get('report_project_id') == project_id):
        selected_activities_data = request.session.get('report_selected_activities')
        print(f"DEBUG: Session data: {selected_activities_data}")  # Debug line
    
    # Also check for old session data format and clear it
    if 'selected_activities' in request.session:
        print(f"DEBUG: Found old session data, clearing it")
        del request.session['selected_activities']
    if 'selected_activities_project' in request.session:
        del request.session['selected_activities_project']
    
    if request.method == 'POST' and 'submit_report' in request.POST:
        form = DailySiteReportForm(request.POST, request.FILES, project=project)
        if form.is_valid():
            # Check if a report already exists for this project and date
            report_date = form.cleaned_data['date']
            existing_report = DailySiteReport.objects.filter(
                project=project,
                date=report_date
            ).first()
            
            if existing_report:
                # Report already exists, show an error message
                messages.error(
                    request, 
                    f"⚠️ A report for '{project.title}' already exists on {report_date.strftime('%B %d, %Y')}. "
                    f"Each project can have only one report per day. Please choose a different date or edit the existing report."
                )
                # Stay on the form page with the entered data
                return render(request, 'reports/create_daily_report.html', {
                    'form': form,
                    'project': project,
                    'selected_activities': selected_activities_details if 'selected_activities_details' in locals() else [],
                    'from_activities': bool(selected_activities_data),
                    'date_collision': True,
                    'existing_report': existing_report,
                })
                
            # No existing report, proceed with creation
            report = form.save(commit=False)
            report.project = project
            report.site_engineer = request.user
            report.save()
            
            # Process activity entries if activities were selected
            if selected_activities_data:
                for activity_data in selected_activities_data:
                    completed_field = f"activity_completed_{activity_data['id']}"
                    remarks_field = f"activity_remarks_{activity_data['id']}"
                    completed_quantity = request.POST.get(completed_field, 0)
                    remarks = request.POST.get(remarks_field, '')
                    
                    try:
                        completed_qty = float(completed_quantity) if completed_quantity else 0
                    except (ValueError, TypeError):
                        completed_qty = 0
                    
                    try:
                        # Get the Activity object
                        activity = Activity.objects.get(id=activity_data['id'], project=project)
                        
                        # Handle the activity photo FIRST (even if no quantity entered)
                        # Check for photo upload - try multiple field name formats
                        activity_picture_field = f"activity_picture_{activity_data['id']}"
                        photo_uploaded = False
                        activity_photo = None
                        
                        # Check if file exists in request.FILES
                        if activity_picture_field in request.FILES:
                            activity_photo = request.FILES.get(activity_picture_field)
                        # Also check all files to see if any match the pattern
                        elif request.FILES:
                            for key in request.FILES.keys():
                                if key.startswith('activity_picture_') and key.endswith(str(activity_data['id'])):
                                    activity_photo = request.FILES.get(key)
                                    break
                        
                        if activity_photo and activity_photo.size > 0:
                            try:
                                photo_uploaded = True
                                # Format quantity for caption (use 0 if no quantity entered)
                                if completed_qty > 0:
                                    if completed_qty == int(completed_qty):
                                        qty_str = str(int(completed_qty))
                                    else:
                                        qty_str = f"{completed_qty:.3f}".rstrip('0').rstrip('.')
                                else:
                                    qty_str = "0"
                                
                                ReportPhoto.objects.create(
                                    report=report,
                                    image=activity_photo.read(),
                                    image_name=activity_photo.name,
                                    image_type=activity_photo.content_type,
                                    caption=f"Photo for {activity_data['name']}: {qty_str} {activity_data['unit_display']}"
                                )
                            except Exception as photo_error:
                                print(f"Error saving photo for activity {activity_data['name']}: {str(photo_error)}")
                                import traceback
                                traceback.print_exc()
                        
                        # Create ActivityWork entry only if quantity > 0
                        if completed_qty > 0:
                            # Format description to match November 28 reports: "Daily work: 23 Square Feet - dsas"
                            # Show whole numbers without decimals, decimals with 3 places
                            if completed_qty == int(completed_qty):
                                quantity_str = str(int(completed_qty))
                            else:
                                quantity_str = f"{completed_qty:.3f}".rstrip('0').rstrip('.')
                            
                            description = f"Daily work: {quantity_str} {activity_data['unit_display']}"
                            if remarks:
                                description += f" - {remarks}"
                            
                            ActivityWork.objects.create(
                                activity=activity,
                                date=report_date,
                                quantity=completed_qty,
                                description=description,
                                recorded_by=request.user,
                                daily_report=report
                            )
                            
                            # Also create DailyReportActivity for backward compatibility
                            from core.models import DailyReportActivity
                            cost = None
                            if activity.unit_cost:
                                try:
                                    cost = completed_qty * float(activity.unit_cost)
                                except Exception:
                                    cost = None
                            
                            DailyReportActivity.objects.create(
                                report=report,
                                name=activity_data['name'],
                                unit=activity_data['unit'],
                                quantity=completed_qty,
                                description=description,
                                cost=cost
                            )
                    except Exception as e:
                        import traceback
                        print(f"Error processing activity {activity_data.get('id', 'unknown')}: {str(e)}")
                        traceback.print_exc()
                        continue
                
                # Clear the session data
                if 'report_selected_activities' in request.session:
                    del request.session['report_selected_activities']
                if 'report_project_id' in request.session:
                    del request.session['report_project_id']
            
            # Create notification for consultant
            if project.consultant:
                Notification.objects.create(
                    recipient=project.consultant,
                    sender=request.user,
                    notification_type='report_submitted',
                    title=f'New Report Submitted - {project.title}',
                    message=f'{request.user.first_name} {request.user.last_name} submitted a daily report for {report.date}',
                    related_project=project,
                    related_report=report
                )
            
            messages.success(request, 'Daily report submitted successfully!')
            return redirect('project_detail', project_id=project.id)
    else:
        form = DailySiteReportForm(project=project)
        
        # Pre-fill work description if activities were selected
        if selected_activities_data:
            activities_text = []
            for activity_data in selected_activities_data:
                try:
                    activity = Activity.objects.get(
                        id=activity_data['id'], 
                        project=project
                    )
                    # Use total_quantity from activity_data or calculate a default
                    total_qty = activity_data.get('total_quantity', 0)
                    activities_text.append(
                        f"- {activity.name}: Total {total_qty} {activity.get_unit_display()}"
                    )
                except Activity.DoesNotExist:
                    continue
            
            if activities_text:
                pre_filled_description = "Activities completed today:\n" + "\n".join(activities_text)
                form.fields['work_description'].initial = pre_filled_description
    
    # Get recent reports for this project (last 10 reports)
    recent_reports = DailySiteReport.objects.filter(project=project).order_by('-date')[:10]
    
    # Get selected activities details for display
    selected_activities_details = []
    if selected_activities_data:
        for activity_data in selected_activities_data:
            try:
                activity = Activity.objects.get(
                    id=activity_data['id'], 
                    project=project
                )
                # Create object with activity attribute that template expects
                selected_activities_details.append({
                    'activity': activity,
                    'total_quantity': activity_data.get('total_quantity', 0),
                    'unit_display': activity_data.get('unit_display', activity.get_unit_display())
                })
            except Activity.DoesNotExist:
                continue
    
    return render(request, 'reports/create_daily_report.html', {
        'form': form,
        'project': project,
        'selected_activities': selected_activities_details,
        'from_activities': bool(selected_activities_data),
        'recent_reports': recent_reports,
    })


@login_required
def team_members_list(request):
    """List all team members"""
    user = request.user
    
    # All users can see all team members
    team_members = TeamMember.objects.all()
    
    # Search filter
    search_query = request.GET.get('search', '')
    if search_query:
        team_members = team_members.filter(
            Q(first_name__icontains=search_query) |
            Q(cnic__icontains=search_query) |
            Q(contact_info__icontains=search_query)
        )
    
    # Filter by active status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        team_members = team_members.filter(is_active=True)
    elif status_filter == 'inactive':
        team_members = team_members.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(team_members, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'team_members': team_members,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'team/team_members_list.html', context)


@login_required
def create_team_member(request):
    """Create a new team member"""
    if request.user.role not in ['admin', 'site_engineer']:
        messages.error(request, 'You do not have permission to add team members.')
        return redirect('team_members_list')
    
    if request.method == 'POST':
        form = TeamMemberForm(request.POST)
        if form.is_valid():
            team_member = form.save(commit=False)
            team_member.added_by = request.user
            team_member.save()
            messages.success(request, f'Team member {team_member.full_name} added successfully!')
            return redirect('team_members_list')
    else:
        form = TeamMemberForm()
    
    context = {'form': form}
    return render(request, 'team/create_team_member.html', context)


@login_required
def edit_team_member(request, member_id):
    """Edit team member details"""
    member = get_object_or_404(TeamMember, id=member_id)
    
    if request.user.role not in ['admin', 'site_engineer']:
        messages.error(request, 'You do not have permission to edit team members.')
        return redirect('team_members_list')
    
    if request.method == 'POST':
        form = TeamMemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f'Team member {member.first_name} updated successfully!')
            return redirect('team_members_list')
    else:
        form = TeamMemberForm(instance=member)
    
    context = {'form': form, 'member': member}
    return render(request, 'team/edit_team_member.html', context)


@login_required
def view_team_member(request, member_id):
    """View team member details"""
    member = get_object_or_404(TeamMember, id=member_id)
    
    context = {
        'member': member
    }
    return render(request, 'team/view_team_member.html', context)


@login_required
def delete_team_member(request, member_id):
    """Delete/deactivate team member"""
    member = get_object_or_404(TeamMember, id=member_id)
    
    if request.user.role not in ['admin', 'site_engineer']:
        messages.error(request, 'You do not have permission to delete team members.')
        return redirect('team_members_list')
    
    if request.method == 'POST':
        member_name = member.full_name
        member.is_active = False
        member.end_date = timezone.now().date()
        member.save()
        messages.success(request, f'Team member {member_name} has been deactivated.')
        return redirect('team_members_list')
    
    context = {'member': member}
    return render(request, 'team/delete_team_member.html', context)


@login_required
def notifications_list(request):
    """List user notifications"""
    notifications = Notification.objects.filter(recipient=request.user)
    
    # Mark as read when viewing
    unread_notifications = notifications.filter(is_read=False)
    unread_notifications.update(is_read=True)
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'notifications/notifications_list.html', {'page_obj': page_obj})


@login_required
def approve_report(request, report_id):
    """Approve daily report - Consultant and Admin only"""
    report = get_object_or_404(DailySiteReport, id=report_id)
    
    # Check permissions - only consultant assigned to project or admin can approve
    if request.user.role == 'consultant':
        if request.user != report.project.consultant:
            messages.error(request, 'Only the project consultant can approve reports.')
            return redirect('daily_reports_list')
    elif request.user.role != 'admin':
        messages.error(request, 'Only consultants and admins can approve reports.')
        return redirect('daily_reports_list')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            report.status = 'approved'
            report.approved_by = request.user
            report.approved_at = timezone.now()
            report.save()
            
            # Create notification for site engineer
            Notification.objects.create(
                recipient=report.site_engineer,
                sender=request.user,
                notification_type='report_approved',
                title=f'Report Approved - {report.project.title}',
                message=f'Your daily report for {report.date} has been approved.',
                related_project=report.project,
                related_report=report
            )
            
            messages.success(request, 'Report approved successfully!')
            
        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', '')
            report.status = 'rejected'
            report.rejection_reason = rejection_reason
            report.save()
            
            # Create notification for site engineer
            Notification.objects.create(
                recipient=report.site_engineer,
                sender=request.user,
                notification_type='report_rejected',
                title=f'Report Rejected - {report.project.title}',
                message=f'Your daily report for {report.date} has been rejected. Reason: {rejection_reason}',
                related_project=report.project,
                related_report=report
            )
            
            messages.info(request, 'Report rejected.')
    
    return redirect('daily_reports_list')


@login_required
def delete_daily_report(request, report_id):
    """Delete a daily site report - site engineer (own reports) or admin"""
    report = get_object_or_404(DailySiteReport, id=report_id)

    is_owner = request.user == report.site_engineer
    is_admin = request.user.role == 'admin'

    if not (is_owner or is_admin):
        messages.error(request, 'You do not have permission to delete this report.')
        return redirect('daily_reports_list')

    if request.method == 'POST':
        project_title = report.project.title
        report_date = report.date
        report.delete()
        messages.success(request, f'Daily report for {project_title} on {report_date} has been deleted.')
        return redirect('daily_reports_list')

    context = {'report': report}
    return render(request, 'reports/confirm_delete_report.html', context)


def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and user.role == 'admin'


@user_passes_test(is_admin)
def user_management(request):
    """User management interface for admins only"""
    users = User.objects.all().order_by('date_joined')
    
    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'users': page_obj,
        'role_filter': role_filter,
        'search_query': search_query,
        'role_choices': User.ROLE_CHOICES,
    }
    
    return render(request, 'users/user_management.html', context)


@user_passes_test(is_admin)
def create_user(request):
    """Create new user (admin only)"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('user_management')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/create_user.html', {'form': form})


@user_passes_test(is_admin)
def edit_user(request, user_id):
    """Edit user details (admin only)"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Update user fields
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.phone = request.POST.get('phone', '')
        user.designation = request.POST.get('designation', '')
        user.role = request.POST.get('role', user.role)
        user.is_active = request.POST.get('is_active') == 'on'
        user.save()
        
        messages.success(request, f'User {user.username} updated successfully!')
        return redirect('user_management')
    
    context = {
        'user_obj': user,  # Rename to avoid conflict with request.user
        'role_choices': User.ROLE_CHOICES,
    }
    
    return render(request, 'users/edit_user.html', context)


@user_passes_test(is_admin)
def delete_user(request, user_id):
    """Delete user (admin only)"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        if user.is_superuser:
            messages.error(request, 'Cannot delete superuser!')
        elif user == request.user:
            messages.error(request, 'Cannot delete yourself!')
        else:
            username = user.username
            user.delete()
            messages.success(request, f'User {username} deleted successfully!')
        
        return redirect('user_management')
    
    return render(request, 'users/delete_user.html', {'user_obj': user})


# Worker Management Views

@login_required
def select_project_workers(request):
    """Select a project to manage its workers"""
    user = request.user
    
    # Get user's projects based on role
    if user.role == 'admin':
        projects = Project.objects.all()
    elif user.role == 'site_engineer':
        projects = Project.objects.filter(site_engineer=user)
    else:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Annotate projects with active worker count
    from django.db.models import Count
    projects = projects.annotate(
        active_workers_count=Count('worker_assignments', filter=Q(worker_assignments__is_active=True))
    )
    
    context = {
        'projects': projects,
    }
    
    return render(request, 'workers/select_project_workers.html', context)


@login_required
def workers_list_all(request):
    """List all workers across all projects"""
    user = request.user
    
    if user.role == 'site_engineer':
        workers = Worker.objects.filter(managed_by=user, is_active=True)
    elif user.role == 'admin':
        workers = Worker.objects.filter(is_active=True)
    else:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        workers = workers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(employee_id__icontains=search_query) |
            Q(designation__icontains=search_query)
        )
    
    # Filter by skill level
    skill_filter = request.GET.get('skill_level', '')
    if skill_filter:
        workers = workers.filter(skill_level=skill_filter)
    
    # Order by skill level and name for grouping
    workers = workers.order_by('skill_level', 'first_name', 'last_name')
    
    context = {
        'workers': workers,
        'search_query': search_query,
        'skill_filter': skill_filter,
        'skill_choices': Worker.SKILL_LEVELS,
        'project': None,  # All workers view
        'view_mode': 'all',
    }
    
    return render(request, 'workers/workers_list.html', context)


@login_required
def workers_list_project(request, project_id):
    """List workers assigned to a specific project"""
    user = request.user
    project = get_object_or_404(Project, id=project_id)
    
    # Check permission
    if user.role == 'site_engineer' and project.site_engineer != user:
        messages.error(request, 'You can only view workers for your own projects.')
        return redirect('select_project_workers')
    elif user.role in ['consultant', 'contractor', 'client']:
        # Allow read-only access for consultant, contractor, client assigned to this project
        if not (project.consultant == user or project.contractor == user or project.client == user):
            messages.error(request, 'You can only view workers for your assigned projects.')
            return redirect('select_project_workers')
    elif user.role not in ['site_engineer', 'admin', 'consultant', 'contractor', 'client']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get workers assigned to this project
    assignments = ProjectWorkerAssignment.objects.filter(
        project=project,
        is_active=True
    ).select_related('worker')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        assignments = assignments.filter(
            Q(worker__first_name__icontains=search_query) |
            Q(worker__last_name__icontains=search_query) |
            Q(worker__employee_id__icontains=search_query) |
            Q(worker__designation__icontains=search_query)
        )
    
    # Filter by skill level
    skill_filter = request.GET.get('skill_level', '')
    if skill_filter:
        assignments = assignments.filter(worker__skill_level=skill_filter)
    
    # Order by skill level and name for grouping
    assignments = assignments.order_by('worker__skill_level', 'worker__first_name', 'worker__last_name')
    
    # Extract workers and attach assignment_id as an attribute
    workers = []
    for assignment in assignments:
        worker = assignment.worker
        worker.assignment_id = assignment.id  # Add assignment_id as attribute
        workers.append(worker)
    
    context = {
        'workers': workers,
        'search_query': search_query,
        'skill_filter': skill_filter,
        'skill_choices': Worker.SKILL_LEVELS,
        'project': project,
        'view_mode': 'project',
        'can_edit': user.role in ['site_engineer', 'admin'] and (project.site_engineer == user or user.role == 'admin'),
    }
    
    return render(request, 'workers/workers_list.html', context)


@login_required
def create_worker(request):
    """Create new worker (site engineers only)"""
    if request.user.role not in ['site_engineer', 'admin']:
        messages.error(request, 'Only site engineers can create workers.')
        return redirect('workers_list_all')
    
    if request.method == 'POST':
        form = WorkerForm(request.POST)
        if form.is_valid():
            worker = form.save(commit=False)
            worker.managed_by = request.user
            worker.save()
            messages.success(request, f'Worker {worker.full_name} created successfully!')
            return redirect('workers_list_all')
    else:
        form = WorkerForm()
    
    return render(request, 'workers/create_worker.html', {'form': form})


@login_required
def edit_worker(request, worker_id):
    """Edit worker details"""
    worker = get_object_or_404(Worker, id=worker_id)
    
    # Check permission
    if request.user.role == 'site_engineer' and worker.managed_by != request.user:
        messages.error(request, 'You can only edit workers you manage.')
        return redirect('workers_list_all')
    elif request.user.role not in ['site_engineer', 'admin']:
        messages.error(request, 'Access denied.')
        return redirect('workers_list_all')
    
    if request.method == 'POST':
        form = WorkerForm(request.POST, instance=worker)
        if form.is_valid():
            form.save()
            messages.success(request, f'Worker {worker.full_name} updated successfully!')
            return redirect('workers_list_all')
    else:
        form = WorkerForm(instance=worker)
    
    return render(request, 'workers/edit_worker.html', {'form': form, 'worker': worker})


@login_required
def assign_workers_to_project(request, project_id):
    """Assign workers to a project"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check permission
    if request.user.role == 'site_engineer' and project.site_engineer != request.user:
        messages.error(request, 'You can only manage workers for your own projects.')
        return redirect('project_detail', project_id=project.id)
    elif request.user.role not in ['site_engineer', 'admin']:
        messages.error(request, 'Access denied.')
        return redirect('project_detail', project_id=project.id)
    
    # Get currently assigned workers
    assigned_workers = ProjectWorkerAssignment.objects.filter(
        project=project, 
        is_active=True
    ).select_related('worker')
    
    if request.method == 'POST':
        form = ProjectWorkerAssignmentForm(request.POST, site_engineer=request.user)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.project = project
            assignment.assigned_by = request.user
            assignment.save()
            messages.success(request, f'Worker {assignment.worker.full_name} assigned to project!')
            return redirect('assign_workers_to_project', project_id=project.id)
    else:
        form = ProjectWorkerAssignmentForm(site_engineer=request.user)
    
    context = {
        'project': project,
        'form': form,
        'assigned_workers': assigned_workers,
    }
    
    return render(request, 'workers/assign_workers.html', context)


@login_required
def remove_worker_from_project(request, assignment_id):
    """Remove worker from project"""
    assignment = get_object_or_404(ProjectWorkerAssignment, id=assignment_id)
    
    # Check permission
    if request.user.role == 'site_engineer' and assignment.project.site_engineer != request.user:
        messages.error(request, 'You can only manage workers for your own projects.')
        return redirect('project_detail', project_id=assignment.project.id)
    elif request.user.role not in ['site_engineer', 'admin']:
        messages.error(request, 'Access denied.')
        return redirect('project_detail', project_id=assignment.project.id)
    
    if request.method == 'POST':
        project_id = assignment.project.id
        worker_name = assignment.worker.full_name
        assignment.is_active = False
        assignment.save()
        messages.success(request, f'Worker {worker_name} removed from project!')
        return redirect('assign_workers_to_project', project_id=project_id)
    
    return render(request, 'workers/remove_worker.html', {'assignment': assignment})


@login_required
def activities_overview(request):
    """Overview of all activities across projects the user has access to"""
    user_projects = []
    
    # Get projects based on user role
    if request.user.role == 'admin':
        user_projects = Project.objects.all()
    else:
        user_projects = Project.objects.filter(
            Q(created_by=request.user) |
            Q(site_engineer=request.user) |
            Q(consultant=request.user) |
            Q(viewer=request.user)
        ).distinct()
    
    # Get activities for these projects
    activities_by_project = []
    total_activities = 0
    
    for project in user_projects.order_by('-created_at'):
        activities = Activity.objects.filter(project=project, is_active=True).order_by('created_at')
        if activities.exists():
            total_activities += activities.count()
            activities_by_project.append({
                'project': project,
                'activities': activities,
                'activities_count': activities.count()
            })
    
    context = {
        'activities_by_project': activities_by_project,
        'total_projects': len(activities_by_project),
        'total_activities': total_activities,
    }
    
    return redirect('projects_list')


@login_required
def activities_list(request, project_id=None):
    """List activities with project selection"""
    if project_id:
        # Direct access to project activities
        project = get_object_or_404(Project, id=project_id)
        
        # Check permissions - only relevant users can view activities
        if not (request.user == project.created_by or 
                request.user == project.site_engineer or 
                request.user == project.consultant or
                request.user == project.contractor or
                request.user == project.client or
                request.user.role == 'admin'):
            messages.error(request, 'You do not have permission to view this project\'s activities.')
            return redirect('projects_list')
        
        activities = Activity.objects.filter(project=project, is_active=True).order_by('created_at')
        
        # Get activity work statistics for each activity
        for activity in activities:
            activity.total_completed = activity.total_quantity_completed
            activity.work_entries_count = activity.activity_work.count()
        
        context = {
            'project': project,
            'activities': activities,
            'can_edit': request.user == project.created_by or request.user == project.site_engineer or request.user.role == 'admin'
        }
        
        return render(request, 'activities/activities_list.html', context)
    else:
        # Project selection view
        user_projects = Project.objects.filter(
            Q(created_by=request.user) | 
            Q(site_engineer=request.user) |
            Q(consultant=request.user) |
            Q(contractor=request.user) |
            Q(client=request.user)
        ).distinct().order_by('-created_at')
        
        return render(request, 'activities/select_project.html', {
            'projects': user_projects
        })


@login_required
def create_activity(request, project_id):
    """Create a new activity for a project"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check permissions - only site engineers, project creators, and admins can create activities
    if not (request.user == project.created_by or 
            request.user == project.site_engineer or 
            request.user.role == 'admin'):
        messages.error(request, 'You do not have permission to create activities for this project.')
        return redirect('activities_list', project_id=project_id)
    
    if request.method == 'POST':
        form = ActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.project = project
            activity.created_by = request.user
            try:
                activity.save()
                messages.success(request, f'Activity "{activity.name}" created successfully!')
                return redirect('activities_list', project_id=project_id)
            except Exception as e:
                if 'UNIQUE constraint failed' in str(e) or 'unique_together' in str(e):
                    messages.error(request, f'An activity with the name "{activity.name}" already exists for this project.')
                else:
                    messages.error(request, 'An error occurred while creating the activity. Please try again.')
    else:
        # GET request - redirect to activities list where the form is now located
        return redirect('activities_list', project_id=project_id)
    
    # This should not be reached, but just in case
    return redirect('activities_list', project_id=project_id)


@login_required
def create_activity_quick(request, project_id):
    """Quick activity creation via AJAX"""
    if request.method == 'POST':
        project = get_object_or_404(Project, id=project_id)
        
        # Check permissions
        if not (request.user == project.created_by or 
                request.user == project.site_engineer or 
                request.user.role == 'admin'):
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        
        activity_name = request.POST.get('activity_name', '').strip()
        total_quantity = request.POST.get('total_quantity', '')
        unit = request.POST.get('unit', 'pcs')
        
        if not activity_name:
            return JsonResponse({'success': False, 'error': 'Activity name is required'})
        
        if not unit:
            return JsonResponse({'success': False, 'error': 'Unit is required'})
        
        try:
            # Convert total_quantity to float if provided
            quantity_value = None
            if total_quantity and total_quantity.strip():
                try:
                    quantity_value = float(total_quantity)
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Invalid quantity value'})
            
            activity = Activity.objects.create(
                project=project,
                name=activity_name,
                unit=unit,
                total_quantity=quantity_value,
                created_by=request.user
            )
            return JsonResponse({'success': True, 'activity_id': activity.id})
        except Exception as e:
            if 'UNIQUE constraint failed' in str(e) or 'unique_together' in str(e):
                return JsonResponse({'success': False, 'error': f'Activity "{activity_name}" already exists'})
            else:
                return JsonResponse({'success': False, 'error': 'Failed to create activity'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def edit_activity(request, activity_id):
    """Get activity data for editing"""
    activity = get_object_or_404(Activity, id=activity_id)
    
    # Check permissions
    if not (request.user == activity.project.created_by or 
            request.user == activity.project.site_engineer or 
            request.user.role == 'admin'):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    return JsonResponse({
        'success': True,
        'activity': {
            'id': activity.id,
            'name': activity.name,
            'unit': activity.unit,
            'total_quantity': float(activity.total_quantity) if activity.total_quantity else None,
            'unit_cost': float(activity.unit_cost) if activity.unit_cost else None,
        }
    })


@login_required
def update_activity(request, activity_id):
    """Update activity via AJAX"""
    if request.method == 'POST':
        activity = get_object_or_404(Activity, id=activity_id)
        
        # Check permissions
        if not (request.user == activity.project.created_by or 
                request.user == activity.project.site_engineer or 
                request.user.role == 'admin'):
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        
        try:
            activity_name = request.POST.get('activity_name', '').strip()
            unit = request.POST.get('unit', 'pcs')
            total_quantity = request.POST.get('total_quantity', '').strip()
            unit_cost = request.POST.get('unit_cost', '').strip()
            
            if not activity_name:
                return JsonResponse({'success': False, 'error': 'Activity name is required'})
            
            activity.name = activity_name
            activity.unit = unit
            
            if total_quantity:
                try:
                    activity.total_quantity = float(total_quantity)
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Invalid total quantity value'})
            else:
                activity.total_quantity = None
            
            if unit_cost:
                try:
                    activity.unit_cost = float(unit_cost)
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Invalid unit cost value'})
            else:
                activity.unit_cost = None
            
            activity.save()
            return JsonResponse({'success': True})
        except Exception as e:
            if 'UNIQUE constraint failed' in str(e) or 'unique_together' in str(e):
                return JsonResponse({'success': False, 'error': f'Activity "{activity.name}" already exists'})
            else:
                return JsonResponse({'success': False, 'error': 'Failed to update activity'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def delete_activity(request, activity_id):
    """Delete activity via AJAX"""
    if request.method == 'POST':
        activity = get_object_or_404(Activity, id=activity_id)
        
        # Check permissions
        if not (request.user == activity.project.created_by or 
                request.user == activity.project.site_engineer or 
                request.user.role == 'admin'):
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        
        try:
            activity_name = activity.name
            activity.delete()
            return JsonResponse({'success': True, 'message': f'Activity "{activity_name}" deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'Failed to delete activity'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def update_activity_progress(request, activity_id):
    """Update activity completed quantity via AJAX"""
    if request.method == 'POST':
        activity = get_object_or_404(Activity, id=activity_id)
        
        # Check permissions
        if not (request.user == activity.project.created_by or 
                request.user == activity.project.site_engineer or 
                request.user.role == 'admin'):
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        
        try:
            import json
            data = json.loads(request.body)
            completed_quantity = float(data.get('completed_quantity', 0))
            
            # For now, we'll create/update an ActivityWork entry for today
            from django.utils import timezone
            today = timezone.now().date()
            
            # Get or create today's work entry
            activity_work, created = ActivityWork.objects.get_or_create(
                activity=activity,
                date=today,
                recorded_by=request.user,
                defaults={
                    'quantity': completed_quantity,
                    'description': f'Progress update: {completed_quantity} {activity.get_unit_display()}'
                }
            )
            
            if not created:
                # Update existing entry
                activity_work.quantity = completed_quantity
                activity_work.description = f'Progress update: {completed_quantity} {activity.get_unit_display()}'
                activity_work.save()
            
            return JsonResponse({'success': True})
            
        except (ValueError, json.JSONDecodeError) as e:
            return JsonResponse({'success': False, 'error': 'Invalid data format'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'Failed to update progress'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def create_activity_work(request, project_id, activity_id=None):
    """Record work done on an activity"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check permissions - only site engineers, project creators, and admins can record activity work
    if not (request.user == project.created_by or 
            request.user == project.site_engineer or 
            request.user.role == 'admin'):
        messages.error(request, 'You do not have permission to record work for this project.')
        return redirect('activities_list', project_id=project_id)
    
    if request.method == 'POST':
        form = ActivityWorkForm(request.POST, project=project)
        if form.is_valid():
            activity_work = form.save(commit=False)
            activity_work.recorded_by = request.user
            activity_work.save()
            messages.success(request, f'Work recorded for "{activity_work.activity.name}" successfully!')
            return redirect('activities_list', project_id=project_id)
    else:
        form = ActivityWorkForm(project=project)
        
        # If activity_id is provided, pre-select that activity
        if activity_id:
            try:
                activity = Activity.objects.get(id=activity_id, project=project)
                form.fields['activity'].initial = activity
            except Activity.DoesNotExist:
                pass
    
    # Simplified: redirect to activities list instead of separate work creation form
    return redirect('activities_list', project_id=project_id)


@login_required
def select_activities_for_report(request, project_id):
    """Select activities to include in a daily report"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check permissions - only site engineers, project creators, and admins can create reports
    if not (request.user == project.created_by or 
            request.user == project.site_engineer or 
            request.user.role == 'admin'):
        messages.error(request, 'You do not have permission to create reports for this project.')
        return redirect('activities_list', project_id=project_id)
    
    activities = Activity.objects.filter(project=project, is_active=True).order_by('created_at')
    
    if request.method == 'POST':
        selected_activities = []
        
        for activity in activities:
            activity_selected = request.POST.get(f'activity_{activity.id}')
            quantity = request.POST.get(f'quantity_{activity.id}')
            
            if activity_selected and quantity:
                try:
                    quantity_float = float(quantity)
                    if quantity_float > 0:
                        selected_activities.append({
                            'activity_id': activity.id,
                            'quantity': quantity_float
                        })
                except ValueError:
                    continue
        
        if not selected_activities:
            messages.warning(request, 'Please select at least one activity with a valid quantity.')
        else:
            # Store selected activities in session for the daily report form
            request.session['selected_activities'] = selected_activities
            request.session['selected_activities_project'] = project_id
            
            # Redirect to create daily report page
            return redirect('create_daily_report', project_id=project_id)
    
    # Simplified: redirect to daily report creation directly
    return redirect('create_daily_report', project_id=project_id)


@login_required
def print_report_view(request, report_id):
    """Print-friendly HTML view for daily report"""
    report = get_object_or_404(DailySiteReport, id=report_id)
    
    # Permission check - similar to view_daily_report
    user = request.user
    if user.role == 'site_engineer' and report.site_engineer != user:
        messages.error(request, 'You can only view your own reports.')
        return redirect('daily_reports_list')
    elif user.role == 'consultant' and report.project.consultant != user:
        messages.error(request, 'You can only view reports from your projects.')
        return redirect('daily_reports_list')
    elif user.role == 'contractor' and report.project.contractor != user:
        messages.error(request, 'You can only view reports from your projects.')
        return redirect('daily_reports_list')
    elif user.role == 'client' and report.project.client != user:
        messages.error(request, 'You can only view reports from your projects.')
        return redirect('daily_reports_list')
    elif user.role == 'viewer' and (report.project.viewer != user or report.status != 'approved'):
        messages.error(request, 'You can only view approved reports from your assigned projects.')
        return redirect('daily_reports_list')
    elif user.role not in ['admin', 'site_engineer', 'consultant', 'contractor', 'client', 'viewer']:
        messages.error(request, 'You do not have permission to view reports.')
        return redirect('daily_reports_list')
    
    # Get activity work associated with this report (new format)
    activity_works = report.activity_work.select_related('activity').all()
    
    # Get independent activities (old format for backward compatibility)
    # Handle case where table might not exist yet
    independent_activities = []
    try:
        from core.models import DailyReportActivity
        independent_activities = DailyReportActivity.objects.filter(report=report).all()
    except Exception:
        # Table doesn't exist yet, will be empty list
        independent_activities = []
    
    # Pre-calculate percentages for activities if needed
    for work in activity_works:
        try:
            if not hasattr(work.activity, 'progress_percentage'):
                if work.activity.total_quantity and float(work.activity.total_quantity) > 0:
                    try:
                        completed = float(work.activity.total_quantity_completed)
                        total = float(work.activity.total_quantity)
                        work.activity.progress_percentage = min(round((completed / total) * 100, 2), 100)
                    except (TypeError, ValueError, ZeroDivisionError):
                        work.activity.progress_percentage = 0
                else:
                    work.activity.progress_percentage = 0
        except Exception:
            # Ensure we don't break the view if any calculation fails
            work.activity.progress_percentage = 0
    
    # Get photos associated with this report, ordered by upload time (newest first)
    photos = report.photos.all().order_by('-uploaded_at')
    
    # Prepare labor and material data
    labor_details = report.labor_details.all()
    material_usage = report.material_usage.all()
    
    context = {
        'report': report,
        'project': report.project,
        'activity_works': activity_works,
        'independent_activities': independent_activities,
        'photos': photos,
        'labor_details': labor_details,
        'material_usage': material_usage,
    }
    
    return render(request, 'reports/report_print_view.html', context)


@login_required
def activity_work_history(request, project_id, activity_id):
    """View work history for a specific activity"""
    project = get_object_or_404(Project, id=project_id)
    activity = get_object_or_404(Activity, id=activity_id, project=project)    # Check permissions
    if not (request.user == project.created_by or 
            request.user == project.site_engineer or 
            request.user == project.consultant or
            request.user == project.contractor or
            request.user == project.client or
            request.user.role == 'admin'):
        messages.error(request, 'You do not have permission to view this activity.')
        return redirect('activities_list', project_id=project_id)
    
    work_entries = ActivityWork.objects.filter(activity=activity).order_by('-date', '-created_at')
    
    # Pagination
    paginator = Paginator(work_entries, 10)  # Show 10 entries per page
    page_number = request.GET.get('page')
    work_entries = paginator.get_page(page_number)
    
    # Simplified: redirect to activities list instead of separate history page
    return redirect('activities_list', project_id=project_id)


# ===========================
# RFI (Request for Inspection/Approval) Views
# ===========================

@login_required
def rfi_list(request):
    """List all RFIs"""
    # Filter RFIs based on user role
    if request.user.role == 'site_engineer':
        rfis = RFI.objects.filter(
            Q(project__site_engineer=request.user) | Q(submitted_by=request.user)
        )
    elif request.user.role == 'consultant':
        rfis = RFI.objects.filter(project__consultant=request.user)
    elif request.user.role == 'contractor':
        rfis = RFI.objects.filter(project__contractor=request.user)
    elif request.user.role == 'client':
        rfis = RFI.objects.filter(project__client=request.user)
    elif request.user.role == 'admin':
        rfis = RFI.objects.all()
    else:
        rfis = RFI.objects.filter(
            Q(project__site_engineer=request.user) | 
            Q(project__consultant=request.user) |
            Q(project__contractor=request.user) |
            Q(project__client=request.user) |
            Q(submitted_by=request.user)
        )
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        rfis = rfis.filter(
            Q(rfi_number__icontains=search_query) |
            Q(project__title__icontains=search_query) |
            Q(request_description__icontains=search_query)
        )
    
    # Filter by project
    project_id = request.GET.get('project')
    if project_id:
        rfis = rfis.filter(project_id=project_id)
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        rfis = rfis.filter(approval_status=status)
    
    rfis = rfis.select_related('project', 'submitted_by').order_by('-created_at')
    
    # Categorize RFIs by status
    all_rfis = rfis
    pending_rfis = rfis.filter(approval_status='pending')
    approved_rfis = rfis.filter(approval_status='approved')
    disapproved_rfis = rfis.filter(approval_status='not_approved')
    
    # Pagination
    paginator = Paginator(rfis, 15)
    page_number = request.GET.get('page')
    rfis_page = paginator.get_page(page_number)
    
    # Get projects for filter dropdown
    if request.user.role == 'site_engineer':
        projects = Project.objects.filter(
            Q(site_engineer=request.user) | Q(created_by=request.user)
        )
    elif request.user.role == 'consultant':
        projects = Project.objects.filter(consultant=request.user)
    elif request.user.role == 'admin':
        projects = Project.objects.all()
    else:
        projects = Project.objects.filter(
            Q(site_engineer=request.user) | Q(consultant=request.user)
        )
    
    context = {
        'rfis': rfis_page,
        'pending_count': pending_rfis.count(),
        'approved_count': approved_rfis.count(),
        'disapproved_count': disapproved_rfis.count(),
        'projects': projects,
        'search_query': search_query,
        'selected_project': project_id,
        'selected_status': status,
    }
    
    return render(request, 'rfi/rfi_list.html', context)


@login_required
def rfi_create(request):
    """Create a new RFI - Site Engineers and Admins only"""
    # Permission check - only site engineers and admins can create RFIs
    if request.user.role not in ['site_engineer', 'admin']:
        messages.error(request, 'Only site engineers and admins can create RFIs.')
        return redirect('rfi_list')
    
    if request.method == 'POST':
        form = RFIForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            rfi = form.save(commit=False)
            rfi.submitted_by = request.user
            
            # Set default status to pending (Site Engineer will approve/disapprove later)
            rfi.approval_status = 'pending'
            
            rfi.save()
            
            # Create notification for consultant if assigned
            if rfi.project.consultant:
                Notification.objects.create(
                    recipient=rfi.project.consultant,
                    sender=request.user,
                    notification_type='project_updated',
                    title='New RFI Submitted',
                    message=f'A new RFI ({rfi.rfi_number}) has been submitted for project "{rfi.project.title}". Share with inspectors.',
                    related_project=rfi.project
                )
            
            messages.success(request, f'RFI {rfi.rfi_number} created successfully! Share the link and password (Access Password: {rfi.access_password}) with inspectors.')
            return redirect('rfi_detail', rfi_id=rfi.id)
    else:
        form = RFIForm(user=request.user)
    
    context = {
        'form': form,
        'page_title': 'Create Request for Inspection',
    }
    
    return render(request, 'rfi/rfi_form_simple.html', context)


@login_required
def rfi_detail(request, rfi_id):
    """View RFI details"""
    rfi = get_object_or_404(RFI, id=rfi_id)
    
    # Check permissions
    if not (request.user == rfi.submitted_by or 
            request.user == rfi.project.site_engineer or 
            request.user == rfi.project.consultant or
            request.user == rfi.project.contractor or
            request.user == rfi.project.client or
            request.user.role == 'admin' or
            request.user.role == 'site_engineer'):
        messages.error(request, 'You do not have permission to view this RFI.')
        return redirect('rfi_list')
    
    context = {
        'rfi': rfi,
    }
    
    return render(request, 'rfi/rfi_detail_new.html', context)


@login_required
def rfi_edit(request, rfi_id):
    """Edit an existing RFI"""
    rfi = get_object_or_404(RFI, id=rfi_id)
    
    # Check permissions - only submitter (if site engineer), project site engineer, or admin can edit
    if not (request.user == rfi.submitted_by or 
            request.user == rfi.project.site_engineer or 
            request.user.role == 'admin'):
        messages.error(request, 'You do not have permission to edit this RFI.')
        return redirect('rfi_detail', rfi_id=rfi.id)
    
    if request.method == 'POST':
        form = RFIForm(request.POST, request.FILES, instance=rfi, user=request.user)
        if form.is_valid():
            rfi = form.save(commit=False)
            rfi.save()
            messages.success(request, f'RFI {rfi.rfi_number} updated successfully!')
            return redirect('rfi_detail', rfi_id=rfi.id)
    else:
        form = RFIForm(instance=rfi, user=request.user)
    
    context = {
        'form': form,
        'rfi': rfi,
        'page_title': f'Edit RFI {rfi.rfi_number}',
    }
    
    return render(request, 'rfi/rfi_form_simple.html', context)


@login_required
def rfi_delete(request, rfi_id):
    """Delete an RFI"""
    rfi = get_object_or_404(RFI, id=rfi_id)
    
    # Check permissions - only submitter or admin can delete
    if not (request.user == rfi.submitted_by or request.user.role == 'admin'):
        messages.error(request, 'You do not have permission to delete this RFI.')
        return redirect('rfi_detail', rfi_id=rfi.id)
    
    if request.method == 'POST':
        rfi_number = rfi.rfi_number
        rfi.delete()
        messages.success(request, f'RFI {rfi_number} has been deleted.')
        return redirect('rfi_list')
    
    context = {
        'rfi': rfi,
    }
    
    return render(request, 'rfi/rfi_confirm_delete.html', context)


def rfi_view_shared(request, token):
    """View and respond to RFI via shareable link - no login required"""
    rfi = get_object_or_404(RFI, share_token=token)
    
    # Check if password is required
    if rfi.access_password:
        # Check if password was provided in session
        session_key = f'rfi_access_{token}'
        if not request.session.get(session_key):
            # Password authentication required
            if request.method == 'POST':
                password = request.POST.get('password')
                if password == rfi.access_password:
                    request.session[session_key] = True
                    messages.success(request, 'Access granted. You can now view and respond to the RFI.')
                else:
                    messages.error(request, 'Incorrect password. Please try again.')
                    return render(request, 'rfi/rfi_password.html', {'rfi': rfi, 'token': token})
            else:
                return render(request, 'rfi/rfi_password.html', {'rfi': rfi, 'token': token})
    
    # Handle inspector response submission
    if request.method == 'POST' and 'submit_response' in request.POST:
        from .forms import RFIInspectorResponseForm
        form = RFIInspectorResponseForm(request.POST, request.FILES)
        if form.is_valid():
            inspector_role = form.cleaned_data['inspector_role']
            inspector_name = form.cleaned_data['inspector_name']
            inspector_signature = form.cleaned_data['inspector_signature']
            response = form.cleaned_data['response']
            
            # Update RFI based on inspector role
            if inspector_role == 'site_inspector':
                rfi.site_inspector_name = inspector_name
                rfi.site_inspector_signature = inspector_signature
                rfi.site_inspector_response = response
                rfi.site_inspector_responded_at = timezone.now()
            elif inspector_role == 'surveyor':
                rfi.surveyor_name = inspector_name
                rfi.surveyor_signature = inspector_signature
                rfi.surveyor_response = response
                rfi.surveyor_responded_at = timezone.now()
            elif inspector_role == 'lab_technician':
                rfi.lab_technician_name = inspector_name
                rfi.lab_technician_signature = inspector_signature
                rfi.lab_technician_response = response
                rfi.lab_technician_responded_at = timezone.now()
            elif inspector_role == 'material_engineer':
                rfi.material_engineer_name = inspector_name
                rfi.material_engineer_signature = inspector_signature
                rfi.material_engineer_response = response
                rfi.material_engineer_responded_at = timezone.now()
            elif inspector_role == 'are':
                rfi.are_name = inspector_name
                rfi.are_signature = inspector_signature
                rfi.are_response = response
                rfi.are_responded_at = timezone.now()
            elif inspector_role == 'resident_engineer':
                rfi.resident_engineer_name = inspector_name
                rfi.resident_engineer_signature = inspector_signature
                rfi.resident_engineer_response = response
                rfi.resident_engineer_responded_at = timezone.now()
            
            # Handle attachment if provided
            if form.cleaned_data.get('attachment'):
                uploaded_file = form.cleaned_data['attachment']
                file_bytes = uploaded_file.read()

                if inspector_role == 'site_inspector':
                    rfi.site_inspector_attachment = file_bytes
                    rfi.site_inspector_attachment_name = uploaded_file.name
                    rfi.site_inspector_attachment_type = uploaded_file.content_type
                elif inspector_role == 'surveyor':
                    rfi.surveyor_attachment = file_bytes
                    rfi.surveyor_attachment_name = uploaded_file.name
                    rfi.surveyor_attachment_type = uploaded_file.content_type
                elif inspector_role == 'lab_technician':
                    rfi.lab_technician_attachment = file_bytes
                    rfi.lab_technician_attachment_name = uploaded_file.name
                    rfi.lab_technician_attachment_type = uploaded_file.content_type
                elif inspector_role == 'material_engineer':
                    rfi.material_engineer_attachment = file_bytes
                    rfi.material_engineer_attachment_name = uploaded_file.name
                    rfi.material_engineer_attachment_type = uploaded_file.content_type
                elif inspector_role == 'are':
                    rfi.are_attachment = file_bytes
                    rfi.are_attachment_name = uploaded_file.name
                    rfi.are_attachment_type = uploaded_file.content_type
                elif inspector_role == 'resident_engineer':
                    rfi.resident_engineer_attachment = file_bytes
                    rfi.resident_engineer_attachment_name = uploaded_file.name
                    rfi.resident_engineer_attachment_type = uploaded_file.content_type
            
            rfi.save()
            
            messages.success(request, 'Your response has been submitted successfully. Thank you!')
            return redirect('rfi_view_shared', token=token)
    else:
        from .forms import RFIInspectorResponseForm
        form = RFIInspectorResponseForm()
    
    context = {
        'rfi': rfi,
        'form': form,
        'is_shared_view': True,
    }
    
    return render(request, 'rfi/rfi_shared_view.html', context)


@login_required
def rfi_update_status(request, rfi_id):
    """Update RFI approval status"""
    rfi = get_object_or_404(RFI, id=rfi_id)
    
    is_site_engineer = request.user == rfi.project.site_engineer
    is_consultant = request.user == rfi.project.consultant
    is_admin = request.user.role == 'admin'

    # Check permissions - site engineer, consultant, or admin can update status
    if not (is_site_engineer or is_consultant or is_admin):
        messages.error(request, 'You do not have permission to update RFI status.')
        return redirect('rfi_detail', rfi_id=rfi.id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in ['pending', 'approved', 'not_approved']:
            # Final approval/disapproval requires all inspector responses
            if status in ['approved', 'not_approved'] and not rfi.all_inspectors_responded:
                messages.error(
                    request,
                    f'All {rfi.total_inspectors_required} inspectors must submit their responses before this RFI can be approved or disapproved.'
                )
                return redirect('rfi_detail', rfi_id=rfi.id)

            rfi.approval_status = status
            
            # Update received by if consultant is approving
            if is_consultant and not rfi.received_by:
                rfi.received_by = request.user
                if not rfi.received_by_name:
                    rfi.received_by_name = f"{request.user.first_name} {request.user.last_name}"
            
            rfi.save()
            
            # Create notification for submitter
            if rfi.submitted_by:
                Notification.objects.create(
                    recipient=rfi.submitted_by,
                    sender=request.user,
                    notification_type='report_approved' if status == 'approved' else 'report_rejected',
                    title=f'RFI {status.replace("_", " ").title()}',
                    message=f'RFI {rfi.rfi_number} has been {status.replace("_", " ")}.',
                    related_project=rfi.project
                )
            
            messages.success(request, f'RFI status updated to {status.replace("_", " ").title()}.')
        else:
            messages.error(request, 'Invalid status.')
    
    return redirect('rfi_detail', rfi_id=rfi.id)


@login_required
def serve_report_photo(request, photo_id):
    """Serve photo from database"""
    photo = get_object_or_404(ReportPhoto, id=photo_id)
    return HttpResponse(photo.image, content_type=photo.image_type)


@login_required
def serve_rfi_attachment(request, rfi_id):
    """Serve RFI attachment from database"""
    rfi = get_object_or_404(RFI, id=rfi_id)

    role = request.GET.get('role')
    if role:
        role_map = {
            'site_inspector': ('site_inspector_attachment', 'site_inspector_attachment_type'),
            'surveyor': ('surveyor_attachment', 'surveyor_attachment_type'),
            'lab_technician': ('lab_technician_attachment', 'lab_technician_attachment_type'),
            'material_engineer': ('material_engineer_attachment', 'material_engineer_attachment_type'),
            'are': ('are_attachment', 'are_attachment_type'),
            'resident_engineer': ('resident_engineer_attachment', 'resident_engineer_attachment_type'),
        }
        fields = role_map.get(role)
        if not fields:
            raise Http404('Invalid attachment role')

        attachment_data = getattr(rfi, fields[0])
        attachment_type = getattr(rfi, fields[1]) or 'application/octet-stream'
        if attachment_data:
            return HttpResponse(attachment_data, content_type=attachment_type)
        return HttpResponse("No attachment found", status=404)

    if rfi.attachments:
        return HttpResponse(rfi.attachments, content_type=(rfi.attachment_type or 'application/octet-stream'))
    return HttpResponse("No attachment found", status=404)


def serve_rfi_shared_attachment(request, token):
    """Serve RFI attachments in shared-token flow for external inspectors."""
    rfi = get_object_or_404(RFI, share_token=token)

    # If password is enabled, shared attachment access requires passed session auth.
    if rfi.access_password and not request.session.get(f'rfi_access_{token}'):
        return HttpResponse("Unauthorized", status=401)

    role = request.GET.get('role')
    if role:
        role_map = {
            'site_inspector': ('site_inspector_attachment', 'site_inspector_attachment_type'),
            'surveyor': ('surveyor_attachment', 'surveyor_attachment_type'),
            'lab_technician': ('lab_technician_attachment', 'lab_technician_attachment_type'),
            'material_engineer': ('material_engineer_attachment', 'material_engineer_attachment_type'),
            'are': ('are_attachment', 'are_attachment_type'),
            'resident_engineer': ('resident_engineer_attachment', 'resident_engineer_attachment_type'),
        }
        fields = role_map.get(role)
        if not fields:
            raise Http404('Invalid attachment role')

        attachment_data = getattr(rfi, fields[0])
        attachment_type = getattr(rfi, fields[1]) or 'application/octet-stream'
        if attachment_data:
            return HttpResponse(attachment_data, content_type=attachment_type)
        return HttpResponse("No attachment found", status=404)

    if rfi.attachments:
        return HttpResponse(rfi.attachments, content_type=(rfi.attachment_type or 'application/octet-stream'))
    return HttpResponse("No attachment found", status=404)


def serve_project_logo_shared(request, token, logo_type):
    """Serve project logos in shared-token flow for external inspectors."""
    rfi = get_object_or_404(RFI, share_token=token)

    # If password is enabled, shared logo access requires passed session auth.
    if rfi.access_password and not request.session.get(f'rfi_access_{token}'):
        return HttpResponse("Unauthorized", status=401)

    project = rfi.project
    if logo_type == 'client' and project.client_logo:
        return HttpResponse(project.client_logo, content_type=(project.client_logo_type or 'image/png'))
    if logo_type == 'contractor' and project.contractor_logo:
        return HttpResponse(project.contractor_logo, content_type=(project.contractor_logo_type or 'image/png'))
    return HttpResponse("No logo found", status=404)


@login_required
def serve_project_logo(request, project_id, logo_type):
    """Serve project logos from DB for report/RFI pages."""
    project = get_object_or_404(Project, id=project_id)

    # Allow only users with project visibility.
    if not (
        request.user.role == 'admin' or
        request.user == project.site_engineer or
        request.user == project.consultant or
        request.user == project.contractor or
        request.user == project.client
    ):
        return HttpResponse("Forbidden", status=403)

    if logo_type == 'client' and project.client_logo:
        return HttpResponse(project.client_logo, content_type=(project.client_logo_type or 'image/png'))
    if logo_type == 'contractor' and project.contractor_logo:
        return HttpResponse(project.contractor_logo, content_type=(project.contractor_logo_type or 'image/png'))
    return HttpResponse("No logo found", status=404)


@login_required
def rfi_print_view(request, rfi_id):
    """Clean print view for RFI with tabular responses and attachments."""
    rfi = get_object_or_404(RFI, id=rfi_id)

    if not (request.user == rfi.submitted_by or
            request.user == rfi.project.site_engineer or
            request.user == rfi.project.consultant or
            request.user == rfi.project.contractor or
            request.user == rfi.project.client or
            request.user.role == 'admin' or
            request.user.role == 'site_engineer'):
        messages.error(request, 'You do not have permission to view this RFI.')
        return redirect('rfi_list')

    inspector_rows = [
        {
            'role': 'Site Inspector',
            'name': rfi.site_inspector_name,
            'signature': rfi.site_inspector_signature,
            'response': rfi.site_inspector_response,
            'responded_at': rfi.site_inspector_responded_at,
            'attachment_role': 'site_inspector',
            'has_attachment': bool(rfi.site_inspector_attachment),
            'attachment_type': rfi.site_inspector_attachment_type or '',
        },
        {
            'role': 'Surveyor',
            'name': rfi.surveyor_name,
            'signature': rfi.surveyor_signature,
            'response': rfi.surveyor_response,
            'responded_at': rfi.surveyor_responded_at,
            'attachment_role': 'surveyor',
            'has_attachment': bool(rfi.surveyor_attachment),
            'attachment_type': rfi.surveyor_attachment_type or '',
        },
        {
            'role': 'Lab Technician',
            'name': rfi.lab_technician_name,
            'signature': rfi.lab_technician_signature,
            'response': rfi.lab_technician_response,
            'responded_at': rfi.lab_technician_responded_at,
            'attachment_role': 'lab_technician',
            'has_attachment': bool(rfi.lab_technician_attachment),
            'attachment_type': rfi.lab_technician_attachment_type or '',
        },
        {
            'role': 'Material Engineer',
            'name': rfi.material_engineer_name,
            'signature': rfi.material_engineer_signature,
            'response': rfi.material_engineer_response,
            'responded_at': rfi.material_engineer_responded_at,
            'attachment_role': 'material_engineer',
            'has_attachment': bool(rfi.material_engineer_attachment),
            'attachment_type': rfi.material_engineer_attachment_type or '',
        },
        {
            'role': 'A.R.E',
            'name': rfi.are_name,
            'signature': rfi.are_signature,
            'response': rfi.are_response,
            'responded_at': rfi.are_responded_at,
            'attachment_role': 'are',
            'has_attachment': bool(rfi.are_attachment),
            'attachment_type': rfi.are_attachment_type or '',
        },
        {
            'role': 'Resident Engineer',
            'name': rfi.resident_engineer_name,
            'signature': rfi.resident_engineer_signature,
            'response': rfi.resident_engineer_response,
            'responded_at': rfi.resident_engineer_responded_at,
            'attachment_role': 'resident_engineer',
            'has_attachment': bool(rfi.resident_engineer_attachment),
            'attachment_type': rfi.resident_engineer_attachment_type or '',
        },
    ]

    context = {
        'rfi': rfi,
        'inspector_rows': inspector_rows,
    }
    return render(request, 'rfi/rfi_print_view.html', context)
