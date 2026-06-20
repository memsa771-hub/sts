from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import models as db_models
from django.db.models import Q
from .models import (
    User, Project, DailySiteReport, LaborDetail, MaterialUsage, ReportPhoto, 
    Worker, ProjectWorkerAssignment, Activity, ActivityWork, RFI,
    ChangeOrder, Submittal, Equipment, SafetyIncident, ProjectMilestone, TeamMember
)


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form with additional fields"""
    
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=False)
    designation = forms.CharField(max_length=100, required=False)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone', 
                 'designation', 'role', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            
        # Add placeholders
        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['first_name'].widget.attrs['placeholder'] = 'First Name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Last Name'
        self.fields['email'].widget.attrs['placeholder'] = 'Email Address'
        self.fields['phone'].widget.attrs['placeholder'] = 'Phone Number'
        self.fields['designation'].widget.attrs['placeholder'] = 'Designation/Job Title'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Password'


class ProjectForm(forms.ModelForm):
    """Form for creating/editing projects"""

    client_logo_file = forms.FileField(
        required=False,
        label='Client Logo',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    contractor_logo_file = forms.FileField(
        required=False,
        label='Contractor Logo',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    
    class Meta:
        model = Project
        fields = ['title', 'project_number', 'description', 'location', 'start_date', 'end_date', 
                 'site_engineer', 'contractor', 'consultant', 'client', 'budget', 'contract_value',
                 'total_area', 'client_name', 'client_contact', 'client_email', 'client_phone', 'status']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project Title'}),
            'project_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., PRJ-2026-001'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project Location'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Overall Budget'}),
            'contract_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Contract Value'}),
            'total_area': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Total Area'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'site_engineer': forms.Select(attrs={'class': 'form-select'}),
            'contractor': forms.Select(attrs={'class': 'form-select'}),
            'consultant': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'client_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Client/Owner Name'}),
            'client_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Person'}),
            'client_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'client@example.com'}),
            'client_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 234 567 8900'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter users by role
        self.fields['site_engineer'].queryset = User.objects.filter(role='site_engineer')
        self.fields['contractor'].queryset = User.objects.filter(role='contractor')
        self.fields['consultant'].queryset = User.objects.filter(role='consultant')
        self.fields['client'].queryset = User.objects.filter(role='client')
        
        # Make optional fields
        self.fields['contractor'].required = False
        self.fields['client'].required = False
        self.fields['consultant'].required = False
        self.fields['project_number'].required = False
        self.fields['client_name'].required = False
        self.fields['client_contact'].required = False
        self.fields['client_email'].required = False
        self.fields['client_phone'].required = False
        self.fields['contract_value'].required = False
        self.fields['total_area'].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)

        client_logo_file = self.files.get('client_logo_file')
        if client_logo_file:
            instance.client_logo = client_logo_file.read()
            instance.client_logo_name = client_logo_file.name
            instance.client_logo_type = client_logo_file.content_type

        contractor_logo_file = self.files.get('contractor_logo_file')
        if contractor_logo_file:
            instance.contractor_logo = contractor_logo_file.read()
            instance.contractor_logo_name = contractor_logo_file.name
            instance.contractor_logo_type = contractor_logo_file.content_type

        if commit:
            instance.save()
        return instance


class DailySiteReportForm(forms.ModelForm):
    """Form for creating daily site reports"""
    
    class Meta:
        model = DailySiteReport
        fields = ['date', 'weather', 'work_description', 'issues_remarks']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'weather': forms.Select(attrs={'class': 'form-control'}),
            'work_description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'issues_remarks': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, project=None, **kwargs):
        self.project = project
        super().__init__(*args, **kwargs)
        self.fields['issues_remarks'].required = False
        
    def clean_date(self):
        date = self.cleaned_data['date']
        
        # If we're creating a new report (not updating), check for existing report
        if not self.instance.pk and self.project:
            existing_report = DailySiteReport.objects.filter(project=self.project, date=date).first()
            if existing_report:
                raise forms.ValidationError(
                    f"⚠️ A report for '{self.project.title}' already exists for {date.strftime('%B %d, %Y')}. "
                    f"Each project can have only one report per day. Please choose a different date."
                )
        return date


class LaborDetailForm(forms.ModelForm):
    """Form for labor details in daily reports"""
    
    class Meta:
        model = LaborDetail
        fields = ['category', 'count', 'working_hours', 'hourly_rate']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'count': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'working_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': 0.5, 'max': 24}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hourly_rate'].required = False


class MaterialUsageForm(forms.ModelForm):
    """Form for material usage in daily reports"""
    
    class Meta:
        model = MaterialUsage
        fields = ['material_name', 'quantity', 'unit', 'supplier', 'unit_cost']
        widgets = {
            'material_name': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': 0}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'supplier': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supplier'].required = False
        self.fields['unit_cost'].required = False


class ReportPhotoForm(forms.ModelForm):
    """Form for uploading photos to reports"""
    
    image_file = forms.FileField(
        label='Photo',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        help_text='Upload photo (will be stored in database)'
    )
    
    class Meta:
        model = ReportPhoto
        fields = ['caption']
        widgets = {
            'caption': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Photo caption (optional)'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['caption'].required = False
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if 'image_file' in self.files:
            uploaded_file = self.files['image_file']
            instance.image = uploaded_file.read()
            instance.image_name = uploaded_file.name
            instance.image_type = uploaded_file.content_type
        if commit:
            instance.save()
        return instance


# Formsets for dynamic forms
LaborDetailFormSet = forms.inlineformset_factory(
    DailySiteReport, 
    LaborDetail, 
    form=LaborDetailForm,
    extra=1,
    can_delete=True
)

MaterialUsageFormSet = forms.inlineformset_factory(
    DailySiteReport, 
    MaterialUsage, 
    form=MaterialUsageForm,
    extra=1,
    can_delete=True
)

ReportPhotoFormSet = forms.inlineformset_factory(
    DailySiteReport, 
    ReportPhoto, 
    form=ReportPhotoForm,
    extra=1,
    can_delete=True
)


class WorkerForm(forms.ModelForm):
    """Form for creating/editing workers"""
    
    class Meta:
        model = Worker
        fields = ['first_name', 'last_name', 'employee_id', 'phone', 'address', 
                 'skill_level', 'designation', 'hourly_rate', 'notes']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'skill_level': forms.Select(attrs={'class': 'form-control'}),
            'designation': forms.TextInput(attrs={'class': 'form-control'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ProjectWorkerAssignmentForm(forms.ModelForm):
    """Form for assigning workers to projects"""
    
    class Meta:
        model = ProjectWorkerAssignment
        fields = ['worker', 'assigned_date', 'daily_rate', 'notes']
        widgets = {
            'worker': forms.Select(attrs={'class': 'form-control'}),
            'assigned_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'daily_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        site_engineer = kwargs.pop('site_engineer', None)
        super().__init__(*args, **kwargs)
        
        # Filter workers to only show those managed by the current site engineer
        if site_engineer:
            self.fields['worker'].queryset = Worker.objects.filter(
                managed_by=site_engineer, 
                is_active=True
            )


class ActivityForm(forms.ModelForm):
    """Form for creating/editing activities"""
    
    class Meta:
        model = Activity
        fields = ['name', 'description', 'unit', 'total_quantity', 'unit_cost']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Activity name (e.g., Brickwork, Concrete Pouring)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional description of the activity'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'total_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0', 'placeholder': 'Total planned quantity'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Cost per unit (optional)'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add help text
        self.fields['unit'].help_text = 'Select the unit of measurement for this activity'
        self.fields['total_quantity'].help_text = 'Total planned quantity for this activity (optional)'
        self.fields['unit_cost'].help_text = 'Cost per unit (leave blank if not applicable)'


class ActivityWorkForm(forms.ModelForm):
    """Form for recording work done on an activity"""
    
    class Meta:
        model = ActivityWork
        fields = ['activity', 'date', 'quantity', 'description']
        widgets = {
            'activity': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0.001'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional: Additional details about this work'}),
        }
    
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        # Filter activities to only show active ones for the specific project
        if project:
            self.fields['activity'].queryset = Activity.objects.filter(
                project=project, 
                is_active=True
            )
        
        # Set default date to today
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['date'].initial = timezone.now().date()


class ActivitySelectionForm(forms.Form):
    """Form for selecting multiple activities to include in a daily report"""
    
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        if project:
            activities = Activity.objects.filter(project=project, is_active=True)
            
            for activity in activities:
                # Create a checkbox for each activity
                self.fields[f'activity_{activity.id}'] = forms.BooleanField(
                    required=False,
                    label=f"{activity.name} ({activity.get_unit_display()})",
                    widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
                )
                
                # Create a quantity field for each activity
                self.fields[f'quantity_{activity.id}'] = forms.DecimalField(
                    required=False,
                    max_digits=10,
                    decimal_places=3,
                    min_value=0.001,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'step': '0.001',
                        'placeholder': f'Quantity in {activity.get_unit_display()}',
                        'style': 'display: none;'  # Initially hidden
                    })
                )
    
    def get_selected_activities(self):
        """Return a list of selected activities with their quantities"""
        selected_activities = []
        
        for field_name, value in self.cleaned_data.items():
            if field_name.startswith('activity_') and value:
                activity_id = field_name.split('_')[1]
                quantity_field = f'quantity_{activity_id}'
                quantity = self.cleaned_data.get(quantity_field)
                
                if quantity and quantity > 0:
                    selected_activities.append({
                        'activity_id': int(activity_id),
                        'quantity': quantity
                    })
        
        return selected_activities


class RFIForm(forms.ModelForm):
    """Form for creating/editing RFI (Request for Inspection/Approval)"""
    
    attachment_file = forms.FileField(
        required=False,
        label='Attachment',
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text='Upload attachment (will be stored in database)'
    )
    
    class Meta:
        model = RFI
        fields = [
            'project', 'submission_date', 'submission_time', 'submitted_by_name',
            'inspection_date', 'inspection_time',
            'request_description', 'access_password'
        ]
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'submission_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'submission_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'submitted_by_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your name'}),
            'inspection_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'inspection_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'request_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Describe what needs to be inspected or approved...'}),
            'access_password': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter projects based on user role
        if user:
            if user.role == 'site_engineer':
                self.fields['project'].queryset = Project.objects.filter(
                    db_models.Q(site_engineer=user) | db_models.Q(created_by=user)
                )
            elif user.role == 'consultant':
                self.fields['project'].queryset = Project.objects.filter(consultant=user)
            elif user.role == 'admin':
                self.fields['project'].queryset = Project.objects.all()
            
            # Pre-fill submitted by name
            if not self.instance.pk:
                self.fields['submitted_by_name'].initial = f"{user.first_name} {user.last_name}"
        
        # Set default values
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['submission_date'].initial = timezone.now().date()
            self.fields['submission_time'].initial = timezone.now().time()
            # Generate random password
            import random
            import string
            password = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            self.fields['access_password'].initial = password
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if 'attachment_file' in self.files:
            uploaded_file = self.files['attachment_file']
            instance.attachments = uploaded_file.read()
            instance.attachment_name = uploaded_file.name
            instance.attachment_type = uploaded_file.content_type
        if commit:
            instance.save()
        return instance


class RFIInspectorResponseForm(forms.Form):
    """Form for inspector to respond to RFI via shared link"""
    
    INSPECTOR_CHOICES = [
        ('site_inspector', 'Site Inspector'),
        ('surveyor', 'Surveyor'),
        ('lab_technician', 'Lab Technician'),
        ('material_engineer', 'Material Engineer'),
        ('are', 'A.R.E'),
        ('resident_engineer', 'Resident Engineer'),
    ]
    
    inspector_role = forms.ChoiceField(
        choices=INSPECTOR_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Your Role'
    )
    inspector_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your full name'}),
        label='Your Name'
    )
    inspector_signature = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type your name as signature'}),
        label='Signature'
    )
    response = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Enter your inspection findings, comments, or approval status'}),
        label='Inspection Response/Comments'
    )
    attachment = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        label='Attach Supporting Documents (Optional)'
    )


# --- Industry Standard Feature Forms ---

class TeamMemberForm(forms.ModelForm):
    """Simplified form for adding team members"""
    
    class Meta:
        model = TeamMember
        fields = ['first_name', 'role', 'project', 'cnic', 'contact_info', 'address', 'joined_date', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter first name'
            }),
            'role': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., Site Supervisor, Electrician, etc.'
            }),
            'project': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cnic': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '12345-1234567-1',
                'pattern': '[0-9]{5}-[0-9]{7}-[0-9]{1}',
                'title': 'Format: 12345-1234567-1'
            }),
            'contact_info': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '+92 300 1234567'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Street, city, area details',
                'rows': 3
            }),
            'joined_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'first_name': 'First Name',
            'role': 'Job Role/Designation',
            'project': 'Assign Project',
            'cnic': 'CNIC Number',
            'contact_info': 'Contact Number',
            'address': 'Address',
            'joined_date': 'Joining Date',
            'is_active': 'Active Status',
        }
        help_texts = {
            'role': 'Enter the job role or designation',
            'cnic': 'Enter CNIC in format: 12345-1234567-1',
            'contact_info': 'Mobile or phone number',
            'address': 'Current residential address',
            'is_active': 'Check if the team member is currently active',
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.employee_id:
            # Generate employee ID: PB-ST + 5 random numbers
            import random
            random_num = random.randint(0, 99999)
            instance.employee_id = f"PB-ST{random_num:05d}"
            # Ensure uniqueness
            while TeamMember.objects.filter(employee_id=instance.employee_id).exists():
                random_num = random.randint(0, 99999)
                instance.employee_id = f"PB-ST{random_num:05d}"
        if commit:
            instance.save()
        return instance


class ChangeOrderForm(forms.ModelForm):
    """Form for change orders"""
    
    class Meta:
        model = ChangeOrder
        fields = ['project', 'title', 'description', 'reason', 'cost_impact', 
                 'time_impact_days', 'status', 'notes']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Change Order Title'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'cost_impact': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter negative for cost reduction'}),
            'time_impact_days': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Days added to schedule'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            if user.role == 'site_engineer':
                self.fields['project'].queryset = Project.objects.filter(
                    db_models.Q(site_engineer=user) | db_models.Q(created_by=user)
                )
            elif user.role == 'admin':
                self.fields['project'].queryset = Project.objects.all()
        
        self.fields['notes'].required = False


class SubmittalForm(forms.ModelForm):
    """Form for submittals"""
    
    class Meta:
        model = Submittal
        fields = ['project', 'title', 'submittal_type', 'description', 'specification_section',
                 'submitted_date', 'required_on_site_date', 'status', 'review_comments']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Submittal Title'}),
            'submittal_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'specification_section': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Section 03 30 00'}),
            'submitted_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'required_on_site_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'review_comments': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            if user.role == 'site_engineer':
                self.fields['project'].queryset = Project.objects.filter(
                    db_models.Q(site_engineer=user) | db_models.Q(created_by=user)
                )
            elif user.role == 'consultant':
                self.fields['project'].queryset = Project.objects.filter(consultant=user)
            elif user.role == 'admin':
                self.fields['project'].queryset = Project.objects.all()
        
        self.fields['specification_section'].required = False
        self.fields['review_comments'].required = False


class EquipmentForm(forms.ModelForm):
    """Form for equipment tracking"""
    
    class Meta:
        model = Equipment
        fields = ['project', 'equipment_id', 'name', 'equipment_type', 'manufacturer', 'model',
                 'status', 'location_on_site', 'arrival_date', 'planned_departure_date',
                 'daily_rental_cost', 'operator_name', 'operator_phone', 
                 'last_maintenance_date', 'next_maintenance_date', 'notes']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'equipment_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., EXC-001'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Equipment Name'}),
            'equipment_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Excavator, Crane'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'location_on_site': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location on site'}),
            'arrival_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'planned_departure_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'daily_rental_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'operator_name': forms.TextInput(attrs={'class': 'form-control'}),
            'operator_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'last_maintenance_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'next_maintenance_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            if user.role == 'site_engineer':
                self.fields['project'].queryset = Project.objects.filter(
                    db_models.Q(site_engineer=user) | db_models.Q(created_by=user)
                )
            elif user.role == 'admin':
                self.fields['project'].queryset = Project.objects.all()


class SafetyIncidentForm(forms.ModelForm):
    """Form for safety incidents"""
    
    class Meta:
        model = SafetyIncident
        fields = ['project', 'incident_date', 'incident_time', 'location', 'incident_type', 
                 'severity', 'person_involved', 'person_role', 'witnesses', 'description',
                 'immediate_action_taken', 'root_cause', 'corrective_actions', 
                 'reported_to_authority', 'authority_reference']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'incident_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'incident_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location on site'}),
            'incident_type': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'person_involved': forms.TextInput(attrs={'class': 'form-control'}),
            'person_role': forms.TextInput(attrs={'class': 'form-control'}),
            'witnesses': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'immediate_action_taken': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'root_cause': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'corrective_actions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'reported_to_authority': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'authority_reference': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            if user.role == 'site_engineer':
                self.fields['project'].queryset = Project.objects.filter(
                    db_models.Q(site_engineer=user) | db_models.Q(created_by=user)
                )
            elif user.role == 'admin':
                self.fields['project'].queryset = Project.objects.all()
        
        self.fields['witnesses'].required = False
        self.fields['root_cause'].required = False
        self.fields['corrective_actions'].required = False
        self.fields['authority_reference'].required = False


class ProjectMilestoneForm(forms.ModelForm):
    """Form for project milestones"""
    
    class Meta:
        model = ProjectMilestone
        fields = ['project', 'title', 'description', 'planned_date', 'status', 
                 'completion_percentage', 'payment_linked', 'payment_amount', 'notes']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Milestone Title'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'planned_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'completion_percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
            'payment_linked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'payment_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            if user.role == 'site_engineer':
                self.fields['project'].queryset = Project.objects.filter(
                    db_models.Q(site_engineer=user) | db_models.Q(created_by=user)
                )
            elif user.role == 'admin':
                self.fields['project'].queryset = Project.objects.all()
        
        self.fields['description'].required = False
        self.fields['payment_amount'].required = False
        self.fields['notes'].required = False
