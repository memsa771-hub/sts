from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home_view, name='home'),  # Landing page
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Projects
    path('projects/', views.projects_list, name='projects_list'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('projects/create/', views.create_project, name='create_project'),
    
    # Daily Reports
    path('reports/', views.daily_reports_list, name='daily_reports_list'),
    path('reports/<int:report_id>/', views.view_daily_report, name='view_daily_report'),
    path('reports/<int:report_id>/print/', views.print_report_view, name='print_report_view'),
    path('projects/<int:project_id>/reports/create/', views.create_daily_report, name='create_daily_report'),
    path('reports/<int:report_id>/approve/', views.approve_report, name='approve_report'),
    path('reports/<int:report_id>/delete/', views.delete_daily_report, name='delete_daily_report'),
    
    # Team Members (Unified System)
    path('team/', views.team_members_list, name='team_members_list'),
    path('team/create/', views.create_team_member, name='create_team_member'),
    path('team/<int:member_id>/', views.view_team_member, name='view_team_member'),
    path('team/<int:member_id>/edit/', views.edit_team_member, name='edit_team_member'),
    path('team/<int:member_id>/delete/', views.delete_team_member, name='delete_team_member'),
    
    # Notifications
    path('notifications/', views.notifications_list, name='notifications_list'),
    
    # User Management (Admin only)
    path('admin/users/', views.user_management, name='user_management'),
    path('admin/users/create/', views.create_user, name='create_user'),
    path('admin/users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('admin/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    
    # Worker Management (Site Engineers)
    path('workers/', views.select_project_workers, name='select_project_workers'),
    path('workers/all/', views.workers_list_all, name='workers_list_all'),
    path('workers/project/<int:project_id>/', views.workers_list_project, name='workers_list_project'),
    path('workers/create/', views.create_worker, name='create_worker'),
    path('workers/<int:worker_id>/edit/', views.edit_worker, name='edit_worker'),
    path('projects/<int:project_id>/assign-workers/', views.assign_workers_to_project, name='assign_workers_to_project'),
    path('assignments/<int:assignment_id>/remove/', views.remove_worker_from_project, name='remove_worker_from_project'),
    
    # Activities Management (Simplified)
    path('activities/', views.activities_list, name='activities_overview'),  # Project selection
    path('projects/<int:project_id>/activities/', views.activities_list, name='activities_list'),
    path('projects/<int:project_id>/activities/quick-create/', views.create_activity_quick, name='create_activity_quick'),
    path('activities/import/', views.import_activities, name='import_activities'),
    path('activities/import/template/', views.download_activity_import_template, name='download_activity_import_template'),
    path('activities/<int:activity_id>/edit/', views.edit_activity, name='edit_activity'),
    path('activities/<int:activity_id>/update/', views.update_activity, name='update_activity'),
    path('activities/<int:activity_id>/delete/', views.delete_activity, name='delete_activity'),
    path('activities/<int:activity_id>/update-progress/', views.update_activity_progress, name='update_activity_progress'),
    
    # RFI (Request for Inspection/Approval)
    path('rfi/', views.rfi_list, name='rfi_list'),
    path('rfi/create/', views.rfi_create, name='rfi_create'),
    path('rfi/<int:rfi_id>/', views.rfi_detail, name='rfi_detail'),
    path('rfi/<int:rfi_id>/print/', views.rfi_print_view, name='rfi_print_view'),
    path('rfi/<int:rfi_id>/edit/', views.rfi_edit, name='rfi_edit'),
    path('rfi/<int:rfi_id>/delete/', views.rfi_delete, name='rfi_delete'),
    path('rfi/<int:rfi_id>/update-status/', views.rfi_update_status, name='rfi_update_status'),
    path('rfi/shared/<str:token>/', views.rfi_view_shared, name='rfi_view_shared'),
    path('rfi/shared/<str:token>/attachment/', views.serve_rfi_shared_attachment, name='serve_rfi_shared_attachment'),
    path('rfi/shared/<str:token>/logo/<str:logo_type>/', views.serve_project_logo_shared, name='serve_project_logo_shared'),
    
    # Media serving from database
    path('media/photo/<int:photo_id>/', views.serve_report_photo, name='serve_report_photo'),
    path('media/rfi/<int:rfi_id>/attachment/', views.serve_rfi_attachment, name='serve_rfi_attachment'),
    path('media/project/<int:project_id>/logo/<str:logo_type>/', views.serve_project_logo, name='serve_project_logo'),
]