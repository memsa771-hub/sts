from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Project, TeamMember
from datetime import datetime, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates test data: 3 projects, 10 team members, 3 consultants, 3 site engineers, 3 clients'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating test data...')
        
        # Store passwords for reference
        passwords_data = []
        
        # Get admin user (assuming it exists)
        try:
            admin = User.objects.filter(role='admin').first()
            if not admin:
                admin = User.objects.create_superuser(
                    username='admin',
                    email='admin@sitetrack.com',
                    password='admin123',
                    first_name='Admin',
                    last_name='User'
                )
                passwords_data.append(('admin', 'admin', 'admin123', 'admin@sitetrack.com'))
                self.stdout.write(self.style.SUCCESS('Created admin user'))
        except:
            admin = User.objects.first()
        
        # Create 3 Site Engineers
        site_engineers = []
        site_engineer_data = [
            ('eng_ali', 'Ali', 'Khan', 'ali.khan@sitetrack.com', 'site123'),
            ('eng_hamza', 'Hamza', 'Ahmed', 'hamza.ahmed@sitetrack.com', 'site123'),
            ('eng_usman', 'Usman', 'Malik', 'usman.malik@sitetrack.com', 'site123'),
        ]
        
        for username, first_name, last_name, email, password in site_engineer_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'site_engineer'
                }
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created site engineer: {username}'))
            passwords_data.append(('Site Engineer', username, password, email))
            site_engineers.append(user)
        
        # Create 3 Contractors
        contractors = []
        contractor_data = [
            ('contractor_bilal', 'Bilal', 'Construction', 'bilal@contractor.com', 'cont123'),
            ('contractor_ahmad', 'Ahmad', 'Builders', 'ahmad@contractor.com', 'cont123'),
            ('contractor_zain', 'Zain', 'Enterprises', 'zain@contractor.com', 'cont123'),
        ]
        
        for username, first_name, last_name, email, password in contractor_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'contractor'
                }
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created contractor: {username}'))
            passwords_data.append(('Contractor', username, password, email))
            contractors.append(user)
        
        # Create 3 Clients
        clients = []
        client_data = [
            ('client_imran', 'Imran', 'Properties', 'imran@client.com', 'client123'),
            ('client_faisal', 'Faisal', 'Investments', 'faisal@client.com', 'client123'),
            ('client_danish', 'Danish', 'Holdings', 'danish@client.com', 'client123'),
        ]
        
        for username, first_name, last_name, email, password in client_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'client'
                }
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created client: {username}'))
            passwords_data.append(('Client', username, password, email))
            clients.append(user)
        
        # Create 3 Consultants
        consultants = []
        consultant_data = [
            ('consultant_saad', 'Saad', 'Associates', 'saad@consultant.com', 'cons123'),
            ('consultant_kamran', 'Kamran', 'Consulting', 'kamran@consultant.com', 'cons123'),
            ('consultant_waqas', 'Waqas', 'Engineers', 'waqas@consultant.com', 'cons123'),
        ]
        
        for username, first_name, last_name, email, password in consultant_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'consultant'
                }
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created consultant: {username}'))
            passwords_data.append(('Consultant', username, password, email))
            consultants.append(user)
        
        # Create 3 Projects
        projects = []
        project_data = [
            {
                'title': 'Grand Mall Construction',
                'location': 'Islamabad, F-7',
                'description': 'Construction of a 5-story commercial mall with modern facilities and parking',
                'status': 'in_progress',
                'start_date': datetime.now().date() - timedelta(days=60),
                'end_date': datetime.now().date() + timedelta(days=300),
                'budget': 50000000,
            },
            {
                'title': 'Green Valley Housing Society',
                'location': 'Lahore, DHA Phase 8',
                'description': 'Development of residential housing society with 200 plots and infrastructure',
                'status': 'in_progress',
                'start_date': datetime.now().date() - timedelta(days=90),
                'end_date': datetime.now().date() + timedelta(days=450),
                'budget': 75000000,
            },
            {
                'title': 'Business Tower Complex',
                'location': 'Karachi, Clifton',
                'description': '20-story commercial tower with offices, retail spaces and underground parking',
                'status': 'planning',
                'start_date': datetime.now().date() + timedelta(days=30),
                'end_date': datetime.now().date() + timedelta(days=730),
                'budget': 120000000,
            },
        ]
        
        for idx, proj_data in enumerate(project_data):
            project, created = Project.objects.get_or_create(
                title=proj_data['title'],
                defaults={
                    'location': proj_data['location'],
                    'description': proj_data['description'],
                    'status': proj_data['status'],
                    'start_date': proj_data['start_date'],
                    'end_date': proj_data['end_date'],
                    'budget': proj_data['budget'],
                    'site_engineer': site_engineers[idx],
                    'contractor': contractors[idx],
                    'client': clients[idx],
                    'consultant': consultants[idx],
                    'created_by': admin,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created project: {proj_data["title"]}'))
            projects.append(project)
        
        # Create 10 Team Members
        team_member_data = [
            ('Muhammad Asif', 'Site Supervisor', '35403-7593274-1', '0345678543', projects[0]),
            ('Ali Raza', 'Electrician', '42101-8765432-1', '0321456789', projects[0]),
            ('Hassan Sheikh', 'Plumber', '37405-9876543-2', '0333987654', projects[0]),
            ('Imran Farooq', 'Mason', '61101-2345678-9', '0300123456', projects[1]),
            ('Shahid Mahmood', 'Carpenter', '54000-3456789-0', '0312345678', projects[1]),
            ('Naveed Iqbal', 'Steel Fixer', '42301-4567890-1', '0334567890', projects[1]),
            ('Tariq Mehmood', 'Heavy Equipment Operator', '38000-5678901-2', '0345678901', projects[2]),
            ('Kamran Ali', 'Foreman', '54500-6789012-3', '0356789012', projects[2]),
            ('Rizwan Ahmed', 'Safety Officer', '61201-7890123-4', '0367890123', projects[2]),
            ('Adnan Khan', 'Quality Inspector', '42501-8901234-5', '0378901234', projects[0]),
        ]
        
        team_members_created = 0
        for name, role, cnic, contact, project in team_member_data:
            # Generate unique employee ID
            random_num = random.randint(0, 99999)
            emp_id = f"PB-ST{random_num:05d}"
            
            # Ensure uniqueness
            while TeamMember.objects.filter(employee_id=emp_id).exists():
                random_num = random.randint(0, 99999)
                emp_id = f"PB-ST{random_num:05d}"
            
            team_member, created = TeamMember.objects.get_or_create(
                cnic=cnic,
                defaults={
                    'first_name': name,
                    'employee_id': emp_id,
                    'role': role,
                    'contact_info': contact,
                    'joined_date': datetime.now().date() - timedelta(days=random.randint(30, 180)),
                    'is_active': True,
                    'project': project,
                    'added_by': admin,
                }
            )
            if created:
                team_members_created += 1
                self.stdout.write(self.style.SUCCESS(f'Created team member: {name} ({emp_id})'))
        
        # Save passwords to file
        passwords_file = 'test_accounts_passwords.txt'
        with open(passwords_file, 'w', encoding='utf-8') as f:
            f.write('='*80 + '\n')
            f.write('SITE TRACKING SYSTEM - TEST ACCOUNTS\n')
            f.write('Generated on: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\n')
            f.write('='*80 + '\n\n')
            f.write('⚠️  WARNING: This file contains sensitive test credentials.\n')
            f.write('   Keep it secure and delete after testing!\n\n')
            f.write('='*80 + '\n\n')
            
            # Group by role
            roles = {}
            for role, username, password, email in passwords_data:
                if role not in roles:
                    roles[role] = []
                roles[role].append((username, password, email))
            
            for role, accounts in roles.items():
                f.write(f'\n{role.upper()}S:\n')
                f.write('-'*80 + '\n')
                for username, password, email in accounts:
                    f.write(f'  Username: {username}\n')
                    f.write(f'  Password: {password}\n')
                    f.write(f'  Email:    {email}\n')
                    f.write(f'  Login URL: http://127.0.0.1:8000/login/\n')
                    f.write('\n')
            
            f.write('='*80 + '\n')
            f.write('PROJECTS CREATED:\n')
            f.write('-'*80 + '\n')
            for project in projects:
                f.write(f'  • {project.title}\n')
                f.write(f'    Location: {project.location}\n')
                f.write(f'    Status: {project.get_status_display()}\n')
                f.write(f'    Site Engineer: {project.site_engineer.username}\n')
                f.write(f'    Contractor: {project.contractor.username}\n')
                f.write(f'    Client: {project.client.username}\n')
                f.write(f'    Consultant: {project.consultant.username}\n\n')
            
            f.write('='*80 + '\n')
            f.write(f'TEAM MEMBERS CREATED: {team_members_created}\n')
            f.write('-'*80 + '\n')
            for member in TeamMember.objects.all().order_by('employee_id'):
                f.write(f'  • {member.first_name} ({member.employee_id})\n')
                f.write(f'    Role: {member.role}\n')
                f.write(f'    Project: {member.project.title if member.project else "Not Assigned"}\n')
                f.write(f'    CNIC: {member.cnic}\n')
                f.write(f'    Contact: {member.contact_info}\n\n')
            
            f.write('='*80 + '\n')
            f.write('END OF FILE\n')
            f.write('='*80 + '\n')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Test data creation complete!'))
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(site_engineers)} site engineers'))
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(contractors)} contractors'))
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(clients)} clients'))
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(consultants)} consultants'))
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(projects)} projects'))
        self.stdout.write(self.style.SUCCESS(f'✅ Created {team_members_created} team members'))
        self.stdout.write(self.style.SUCCESS(f'\n📝 Passwords saved to: {passwords_file}'))
        self.stdout.write(self.style.WARNING(f'\n⚠️  Keep the passwords file secure!'))
