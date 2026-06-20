from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Project, DailySiteReport, TeamMember, LaborDetail, MaterialUsage, Notification
from django.utils import timezone
from datetime import date, timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for Site Tracking System application'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample data...'))
        
        # Create users
        self.create_users()
        
        # Create projects
        self.create_projects()
        
        # Create daily reports
        self.create_daily_reports()
        
        # Create team members
        self.create_team_members()
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
    
    def create_users(self):
        # Create admin
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'John',
                'last_name': 'Smith',
                'email': 'admin@sitetrackingsystem.com',
                'role': 'admin',
                'designation': 'System Administrator',
                'phone': '+1-555-0101',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(f'Created admin user: {admin.username}')
        
        # Create site engineers
        engineers = [
            {'username': 'engineer1', 'first_name': 'Mike', 'last_name': 'Johnson', 'email': 'mike@sitetrackingsystem.com'},
            {'username': 'engineer2', 'first_name': 'Sarah', 'last_name': 'Williams', 'email': 'sarah@sitetrackingsystem.com'},
            {'username': 'engineer3', 'first_name': 'David', 'last_name': 'Brown', 'email': 'david@sitetrackingsystem.com'},
        ]
        
        for eng_data in engineers:
            user, created = User.objects.get_or_create(
                username=eng_data['username'],
                defaults={
                    'first_name': eng_data['first_name'],
                    'last_name': eng_data['last_name'],
                    'email': eng_data['email'],
                    'role': 'site_engineer',
                    'designation': 'Site Engineer',
                    'phone': f'+1-555-{random.randint(1000, 9999)}'
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created site engineer: {user.username}')
        
        # Create project managers
        managers = [
            {'username': 'manager1', 'first_name': 'Emily', 'last_name': 'Davis', 'email': 'emily@sitetrackingsystem.com'},
            {'username': 'manager2', 'first_name': 'Robert', 'last_name': 'Miller', 'email': 'robert@sitetrackingsystem.com'},
        ]
        
        for mgr_data in managers:
            user, created = User.objects.get_or_create(
                username=mgr_data['username'],
                defaults={
                    'first_name': mgr_data['first_name'],
                    'last_name': mgr_data['last_name'],
                    'email': mgr_data['email'],
                    'role': 'project_manager',
                    'designation': 'Project Manager',
                    'phone': f'+1-555-{random.randint(1000, 9999)}'
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created project manager: {user.username}')
        
        # Create clients
        clients = [
            {'username': 'client1', 'first_name': 'James', 'last_name': 'Wilson', 'email': 'james@client.com'},
            {'username': 'client2', 'first_name': 'Lisa', 'last_name': 'Anderson', 'email': 'lisa@client.com'},
        ]
        
        for client_data in clients:
            user, created = User.objects.get_or_create(
                username=client_data['username'],
                defaults={
                    'first_name': client_data['first_name'],
                    'last_name': client_data['last_name'],
                    'email': client_data['email'],
                    'role': 'client',
                    'designation': 'Client Representative',
                    'phone': f'+1-555-{random.randint(1000, 9999)}'
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created client: {user.username}')
    
    def create_projects(self):
        admin = User.objects.get(username='admin')
        engineers = User.objects.filter(role='site_engineer')
        managers = User.objects.filter(role='project_manager')
        clients = User.objects.filter(role='client')
        
        projects_data = [
            {
                'title': 'Nestopia Hotel Skardu',
                'description': 'A luxury hotel construction project in the beautiful Skardu valley featuring modern amenities and traditional architecture.',
                'location': 'Skardu, Gilgit-Baltistan, Pakistan',
                'start_date': date.today() - timedelta(days=30),
                'end_date': date.today() + timedelta(days=120),
                'status': 'ongoing',
                'budget': 2500000.00
            },
            {
                'title': 'Downtown Office Complex',
                'description': 'A modern 15-story office building with state-of-the-art facilities and sustainable design features.',
                'location': '123 Business District, New York, NY',
                'start_date': date.today() - timedelta(days=60),
                'end_date': date.today() + timedelta(days=180),
                'status': 'ongoing',
                'budget': 15000000.00
            },
            {
                'title': 'Residential Tower A',
                'description': 'A 25-story residential tower with luxury apartments and commercial spaces on the ground floor.',
                'location': '456 Residential Ave, Los Angeles, CA',
                'start_date': date.today() - timedelta(days=90),
                'end_date': date.today() + timedelta(days=90),
                'status': 'ongoing',
                'budget': 8500000.00
            },
            {
                'title': 'Shopping Mall Renovation',
                'description': 'Complete renovation of existing shopping mall including new facades, interior design, and system upgrades.',
                'location': '789 Commerce St, Chicago, IL',
                'start_date': date.today() - timedelta(days=120),
                'end_date': date.today() - timedelta(days=10),
                'status': 'completed',
                'budget': 3200000.00
            }
        ]
        
        for i, project_data in enumerate(projects_data):
            project, created = Project.objects.get_or_create(
                title=project_data['title'],
                defaults={
                    'description': project_data['description'],
                    'location': project_data['location'],
                    'start_date': project_data['start_date'],
                    'end_date': project_data['end_date'],
                    'status': project_data['status'],
                    'budget': project_data['budget'],
                    'admin': admin,
                    'site_engineer': engineers[i % len(engineers)],
                    'project_manager': managers[i % len(managers)],
                    'client': clients[i % len(clients)]
                }
            )
            if created:
                self.stdout.write(f'Created project: {project.title}')
    
    def create_daily_reports(self):
        projects = Project.objects.filter(status='ongoing')
        weather_choices = ['sunny', 'cloudy', 'rainy', 'windy']
        
        for project in projects:
            # Create reports for the last 10 days
            for i in range(10):
                report_date = date.today() - timedelta(days=i)
                if report_date >= project.start_date:
                    report, created = DailySiteReport.objects.get_or_create(
                        project=project,
                        date=report_date,
                        defaults={
                            'site_engineer': project.site_engineer,
                            'weather': random.choice(weather_choices),
                            'work_description': f'Construction work progress for {report_date}. Foundation work completed, starting with structural framework. All safety protocols followed.',
                            'status': random.choice(['pending', 'approved', 'approved']),  # More approved than pending
                            'issues_remarks': 'Minor delays due to material delivery' if random.random() > 0.7 else ''
                        }
                    )
                    
                    if created and report.status == 'approved':
                        report.approved_by = project.project_manager
                        report.approved_at = timezone.now()
                        report.save()
                        
                        # Create labor details
                        labor_categories = ['mason', 'carpenter', 'electrician', 'helper']
                        for category in random.sample(labor_categories, 2):
                            LaborDetail.objects.create(
                                report=report,
                                category=category,
                                count=random.randint(3, 12),
                                working_hours=random.uniform(6.0, 10.0),
                                hourly_rate=random.uniform(15.0, 35.0)
                            )
                        
                        # Create material usage
                        materials = [
                            {'name': 'Cement', 'unit': 'bags'},
                            {'name': 'Steel Rebar', 'unit': 'kg'},
                            {'name': 'Concrete Blocks', 'unit': 'pcs'},
                            {'name': 'Sand', 'unit': 'm3'}
                        ]
                        for material in random.sample(materials, 2):
                            MaterialUsage.objects.create(
                                report=report,
                                material_name=material['name'],
                                quantity=random.uniform(10.0, 100.0),
                                unit=material['unit'],
                                supplier=f'{material["name"]} Supply Co.',
                                unit_cost=random.uniform(5.0, 50.0)
                            )
                        
                        self.stdout.write(f'Created daily report for {project.title} on {report_date}')
    
    def create_team_members(self):
        projects = Project.objects.all()
        all_users = User.objects.exclude(role='admin')
        
        for project in projects:
            # Add some team members to each project
            project_users = [project.site_engineer, project.project_manager, project.client]
            additional_users = random.sample(list(all_users.exclude(id__in=[u.id for u in project_users])), 2)
            
            for user in project_users + additional_users:
                team_member, created = TeamMember.objects.get_or_create(
                    project=project,
                    user=user,
                    defaults={
                        'joined_date': project.start_date + timedelta(days=random.randint(0, 10))
                    }
                )
                if created:
                    self.stdout.write(f'Added {user.username} to {project.title} team')
    
    def create_notifications(self):
        # Create some sample notifications
        users = User.objects.all()
        projects = Project.objects.all()
        
        for project in projects[:2]:  # Only for first 2 projects
            # Report submission notification
            Notification.objects.create(
                recipient=project.project_manager,
                sender=project.site_engineer,
                notification_type='report_submitted',
                title=f'New Report Submitted - {project.title}',
                message=f'{project.site_engineer.first_name} submitted a daily report for review.',
                related_project=project
            )
            
            # Report approval notification
            Notification.objects.create(
                recipient=project.site_engineer,
                sender=project.project_manager,
                notification_type='report_approved',
                title=f'Report Approved - {project.title}',
                message=f'Your daily report has been approved by {project.project_manager.first_name}.',
                related_project=project
            )