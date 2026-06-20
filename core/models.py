from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    """Custom User model with role-based access"""
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('site_engineer', 'Site Engineer'),
        ('contractor', 'Contractor'),
        ('client', 'Client'),
        ('consultant', 'Consultant'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Set superusers to admin role automatically
        if self.is_superuser:
            self.role = 'admin'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_role_display()}"

    @property
    def display_name(self):
        full = self.get_full_name().strip()
        return full or self.username

    @property
    def initials(self):
        first = (self.first_name or '').strip()
        last = (self.last_name or '').strip()
        if first and last:
            return f"{first[0]}{last[0]}".upper()
        if first:
            return first[0].upper()
        if self.username:
            return self.username[0].upper()
        return '?'


class Project(models.Model):
    """Project model to track construction projects"""
    
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ]
    
    title = models.CharField(max_length=200)
    project_number = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="Unique project number/code")
    description = models.TextField()
    location = models.CharField(max_length=300)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    
    # Assigned users - Extended Team
    site_engineer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='engineer_projects')
    contractor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='contractor_projects', help_text="Assigned contractor")
    consultant = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='consultant_projects')
    client = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='client_projects', help_text="Assigned client")
    
    # Client information
    client_name = models.CharField(max_length=200, blank=True, null=True, help_text="Client/Owner name")
    client_contact = models.CharField(max_length=100, blank=True, null=True, help_text="Client contact person")
    client_email = models.EmailField(blank=True, null=True)
    client_phone = models.CharField(max_length=15, blank=True, null=True)

    # Branding logos (stored in DB for easy rendering in reports/RFI)
    client_logo = models.BinaryField(blank=True, null=True, help_text="Client logo stored as binary data")
    client_logo_name = models.CharField(max_length=255, blank=True, null=True, help_text="Original client logo filename")
    client_logo_type = models.CharField(max_length=50, blank=True, null=True, help_text="Client logo MIME type")
    contractor_logo = models.BinaryField(blank=True, null=True, help_text="Contractor logo stored as binary data")
    contractor_logo_name = models.CharField(max_length=255, blank=True, null=True, help_text="Original contractor logo filename")
    contractor_logo_type = models.CharField(max_length=50, blank=True, null=True, help_text="Contractor logo MIME type")
    
    # Track who created this project (for site engineer ownership)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_projects'
    )
    
    # Project metadata
    budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    contract_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Original contract value")
    total_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Total project area (sq ft/m)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

    @property
    def client_display(self):
        if self.client_name:
            return self.client_name
        if self.client:
            return self.client.display_name
        return "Not assigned"

    @property
    def contractor_display(self):
        if self.contractor:
            return self.contractor.display_name
        return "Not assigned"

    @property
    def consultant_display(self):
        if self.consultant:
            return self.consultant.display_name
        return "Not assigned"
    
    @property
    def progress_percentage(self):
        """Calculate project progress based on completed vs total days"""
        if self.end_date <= timezone.now().date():
            return 100
        
        total_days = (self.end_date - self.start_date).days
        if total_days <= 0:
            return 0
            
        elapsed_days = (timezone.now().date() - self.start_date).days
        if elapsed_days < 0:
            return 0
            
        progress = min((elapsed_days / total_days) * 100, 100)
        return round(progress, 2)


class DailySiteReport(models.Model):
    """Daily site reports submitted by site engineers"""
    
    WEATHER_CHOICES = [
        ('sunny', 'Sunny'),
        ('cloudy', 'Cloudy'),
        ('rainy', 'Rainy'),
        ('windy', 'Windy'),
        ('stormy', 'Stormy'),
    ]
    
    APPROVAL_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='daily_reports')
    site_engineer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_reports')
    date = models.DateField()
    weather = models.CharField(max_length=20, choices=WEATHER_CHOICES)
    work_description = models.TextField()
    issues_remarks = models.TextField(blank=True, null=True)
    
    # Approval workflow
    status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_reports')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['project', 'date']  # One report per project per day
    
    def __str__(self):
        return f"{self.project.title} - {self.date}"


class ReportPhoto(models.Model):
    """Photos attached to daily site reports"""
    
    report = models.ForeignKey(DailySiteReport, on_delete=models.CASCADE, related_name='photos')
    image = models.BinaryField(help_text="Image stored as binary data in database")
    image_name = models.CharField(max_length=255, help_text="Original filename")
    image_type = models.CharField(max_length=50, default='image/jpeg', help_text="MIME type")
    caption = models.CharField(max_length=200, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Photo for {self.report}"


class LaborDetail(models.Model):
    """Labor details for daily reports"""
    
    LABOR_CATEGORIES = [
        ('mason', 'Mason'),
        ('carpenter', 'Carpenter'),
        ('electrician', 'Electrician'),
        ('plumber', 'Plumber'),
        ('painter', 'Painter'),
        ('helper', 'Helper'),
        ('supervisor', 'Supervisor'),
        ('operator', 'Machine Operator'),
        ('welder', 'Welder'),
        ('other', 'Other'),
    ]
    
    report = models.ForeignKey(DailySiteReport, on_delete=models.CASCADE, related_name='labor_details')
    category = models.CharField(max_length=20, choices=LABOR_CATEGORIES)
    count = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    working_hours = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0.5), MaxValueValidator(24)])
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.count} {self.get_category_display()} - {self.working_hours}hrs"
    
    @property
    def total_cost(self):
        if self.hourly_rate:
            return self.count * self.working_hours * self.hourly_rate
        return 0


class MaterialUsage(models.Model):
    """Materials used in daily reports"""
    
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('ton', 'Ton'),
        ('ltr', 'Liter'),
        ('m3', 'Cubic Meter'),
        ('m2', 'Square Meter'),
        ('m', 'Meter'),
        ('pcs', 'Pieces'),
        ('bags', 'Bags'),
        ('rolls', 'Rolls'),
    ]
    
    report = models.ForeignKey(DailySiteReport, on_delete=models.CASCADE, related_name='material_usage')
    material_name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    supplier = models.CharField(max_length=200, blank=True, null=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.material_name} - {self.quantity} {self.unit}"
    
    @property
    def total_cost(self):
        if self.unit_cost:
            return self.quantity * self.unit_cost
        return 0


# --- Independent Daily Report Activity Model ---
class DailyReportActivity(models.Model):
    """Stores activity data independently for each daily report."""
    report = models.ForeignKey('DailySiteReport', on_delete=models.CASCADE, related_name='independent_activities')
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=10)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    description = models.TextField(blank=True, null=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.quantity} {self.unit} ({self.report})"


class TeamMember(models.Model):
    """Simplified team members system"""
    
    # Basic Information
    first_name = models.CharField(max_length=100, help_text="Team member's first name")
    employee_id = models.CharField(max_length=20, unique=True, blank=True, help_text="Auto-generated employee ID (e.g., PB-ST00123)")
    role = models.CharField(max_length=100, blank=True, help_text="Job role or designation")
    cnic = models.CharField(max_length=15, unique=True, help_text="CNIC number (e.g., 12345-1234567-1)")
    contact_info = models.CharField(max_length=15, help_text="Phone/Mobile number")
    address = models.TextField(blank=True, null=True, help_text="Residential address")
    joined_date = models.DateField(default=timezone.now, help_text="Date when team member joined")
    is_active = models.BooleanField(default=True, help_text="Is the team member currently active?")
    
    # Project Assignment
    project = models.ForeignKey(
        'Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_members',
        help_text="Project assigned to this team member"
    )
    
    # Management and Tracking
    added_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='added_team_members',
        help_text="User who added this team member"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['first_name']
    
    def __str__(self):
        return f"{self.first_name} - {self.cnic}"
    
    @property
    def full_name(self):
        return self.first_name


class Worker(models.Model):
    """Workers that can be assigned to projects - managed by site engineers"""
    
    SKILL_LEVELS = [
        ('skilled', 'Skilled Worker'),
        ('unskilled', 'Unskilled Worker'),
        ('supervisor', 'Supervisor'),
        ('technician', 'Technician'),
        ('operator', 'Machine Operator'),
        ('helper', 'Helper'),
    ]
    
    # Basic Information
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    employee_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Work Details
    skill_level = models.CharField(max_length=20, choices=SKILL_LEVELS, default='unskilled')
    designation = models.CharField(max_length=100)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    date_joined = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    # Management
    managed_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='managed_workers',
        limit_choices_to={'role': 'site_engineer'}
    )
    
    # Additional Info
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['first_name', 'last_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id}) - {self.get_skill_level_display()}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class ProjectWorkerAssignment(models.Model):
    """Assignment of workers to specific projects"""
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='worker_assignments')
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='project_assignments')
    assigned_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    # Daily tracking
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Track who assigned this worker
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='worker_assignments_made',
        limit_choices_to={'role': 'site_engineer'}
    )
    
    class Meta:
        unique_together = ['project', 'worker']
        ordering = ['-assigned_date']
    
    def __str__(self):
        return f"{self.worker.full_name} assigned to {self.project.title}"


class Notification(models.Model):
    """Notifications for users"""
    
    NOTIFICATION_TYPES = [
        ('report_submitted', 'Report Submitted'),
        ('report_approved', 'Report Approved'),
        ('report_rejected', 'Report Rejected'),
        ('project_assigned', 'Project Assigned'),
        ('project_updated', 'Project Updated'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    related_report = models.ForeignKey(DailySiteReport, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.recipient} - {self.title}"


class Activity(models.Model):
    """Activities that can be performed on a project"""
    
    UNIT_CHOICES = [
        ('sqft', 'Square Feet'),
        ('sqm', 'Square Meters'),
        ('cuft', 'Cubic Feet'),
        ('cum', 'Cubic Meters'),
        ('lnft', 'Linear Feet'),
        ('lnm', 'Linear Meters'),
        ('pcs', 'Pieces'),
        ('kg', 'Kilogram'),
        ('ton', 'Ton'),
        ('ltr', 'Liter'),
        ('bags', 'Bags'),
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('other', 'Other'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='activities')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    total_quantity = models.DecimalField(max_digits=12, decimal_places=3, blank=True, null=True, help_text="Total planned quantity for this activity")
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Cost per unit (optional)")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_activities')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['project', 'name']  # Unique activity names per project
    
    def __str__(self):
        return f"{self.name} ({self.get_unit_display()}) - {self.project.title}"
    
    @property
    def total_quantity_completed(self):
        """Total quantity of work completed for this activity"""
        return self.activity_work.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
    
    @property
    def total_cost_incurred(self):
        """Total cost incurred for this activity"""
        if self.unit_cost:
            return self.total_quantity_completed * self.unit_cost
        return 0
    
    @property
    def progress_percentage(self):
        """Calculate completion percentage"""
        try:
            if not self.total_quantity or self.total_quantity <= 0:
                return 0
            
            completed = self.total_quantity_completed
            if completed <= 0:
                return 0
                
            # Convert both to float for consistent calculation
            completed_float = float(completed)
            total_float = float(self.total_quantity)
            
            if total_float <= 0:  # Double-check to prevent division by zero
                return 0
                
            progress = min((completed_float / total_float) * 100, 100)
            return round(progress, 2)
        except (TypeError, ValueError, ZeroDivisionError, Exception):
            # Catch any exception to ensure this calculation never breaks the view
            return 0
    
    @property
    def remaining_quantity(self):
        """Calculate remaining quantity to be completed"""
        if not self.total_quantity:
            return 0
        
        remaining = float(self.total_quantity) - self.total_quantity_completed
        return max(remaining, 0)


class ActivityWork(models.Model):
    """Record of work done for a specific activity"""
    
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='activity_work')
    date = models.DateField()
    quantity = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.001)])
    description = models.TextField(blank=True, null=True, help_text="Additional details about this work")
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='recorded_activity_work')
    daily_report = models.ForeignKey(DailySiteReport, on_delete=models.CASCADE, null=True, blank=True, related_name='activity_work')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.activity.name} - {self.quantity} {self.activity.get_unit_display()} on {self.date}"
    
    @property
    def cost_for_work(self):
        """Cost for this specific work entry"""
        if self.activity.unit_cost:
            return self.quantity * self.activity.unit_cost
        return 0


class RFI(models.Model):
    """Request for Inspection / Approval model"""
    
    APPROVAL_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('not_approved', 'Not Approved'),
    ]
    
    # Basic Information
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='rfis')
    rfi_number = models.CharField(max_length=50, unique=True, editable=False)
    
    # Submission Details
    submission_date = models.DateField()
    submission_time = models.TimeField()
    submitted_by_name = models.CharField(max_length=200, help_text="Contractor name")
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_rfis')
    
    # Inspection Details
    inspection_date = models.DateField(null=True, blank=True)
    inspection_time = models.TimeField(null=True, blank=True)
    
    # Receiving Details
    receiving_date = models.DateField(null=True, blank=True)
    receiving_time = models.TimeField(null=True, blank=True)
    received_by_name = models.CharField(max_length=200, blank=True, null=True, help_text="Consultant name")
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_rfis')
    
    # Request Details
    request_description = models.TextField(help_text="Details of the inspection request")
    
    # Inspectors/Reviewers
    site_inspector_name = models.CharField(max_length=200, blank=True, null=True)
    site_inspector_signature = models.CharField(max_length=200, blank=True, null=True)
    
    surveyor_name = models.CharField(max_length=200, blank=True, null=True)
    surveyor_signature = models.CharField(max_length=200, blank=True, null=True)
    
    lab_technician_name = models.CharField(max_length=200, blank=True, null=True)
    lab_technician_signature = models.CharField(max_length=200, blank=True, null=True)
    
    material_engineer_name = models.CharField(max_length=200, blank=True, null=True)
    material_engineer_signature = models.CharField(max_length=200, blank=True, null=True)
    
    are_name = models.CharField(max_length=200, blank=True, null=True, help_text="A.R.E")
    are_signature = models.CharField(max_length=200, blank=True, null=True)
    
    # Approval Status
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default='pending')
    
    # Resident Engineer
    resident_engineer_name = models.CharField(max_length=200, blank=True, null=True)
    resident_engineer_signature = models.CharField(max_length=200, blank=True, null=True)
    
    # Received back to Contractor
    contractor_name = models.CharField(max_length=200, blank=True, null=True)
    contractor_signature = models.CharField(max_length=200, blank=True, null=True)
    
    # Shareable link token for external access
    share_token = models.CharField(max_length=64, unique=True, editable=False)
    access_password = models.CharField(max_length=20, blank=True, null=True, help_text="Password for external access to this RFI")
    
    # Inspector Responses
    site_inspector_response = models.TextField(blank=True, null=True)
    site_inspector_responded_at = models.DateTimeField(null=True, blank=True)
    
    surveyor_response = models.TextField(blank=True, null=True)
    surveyor_responded_at = models.DateTimeField(null=True, blank=True)
    
    lab_technician_response = models.TextField(blank=True, null=True)
    lab_technician_responded_at = models.DateTimeField(null=True, blank=True)
    
    material_engineer_response = models.TextField(blank=True, null=True)
    material_engineer_responded_at = models.DateTimeField(null=True, blank=True)
    
    are_response = models.TextField(blank=True, null=True)
    are_responded_at = models.DateTimeField(null=True, blank=True)
    
    resident_engineer_response = models.TextField(blank=True, null=True)
    resident_engineer_responded_at = models.DateTimeField(null=True, blank=True)

    # Inspector response attachments
    site_inspector_attachment = models.BinaryField(blank=True, null=True, help_text="Site inspector attachment binary")
    site_inspector_attachment_name = models.CharField(max_length=255, blank=True, null=True)
    site_inspector_attachment_type = models.CharField(max_length=50, blank=True, null=True)

    surveyor_attachment = models.BinaryField(blank=True, null=True, help_text="Surveyor attachment binary")
    surveyor_attachment_name = models.CharField(max_length=255, blank=True, null=True)
    surveyor_attachment_type = models.CharField(max_length=50, blank=True, null=True)

    lab_technician_attachment = models.BinaryField(blank=True, null=True, help_text="Lab technician attachment binary")
    lab_technician_attachment_name = models.CharField(max_length=255, blank=True, null=True)
    lab_technician_attachment_type = models.CharField(max_length=50, blank=True, null=True)

    material_engineer_attachment = models.BinaryField(blank=True, null=True, help_text="Material engineer attachment binary")
    material_engineer_attachment_name = models.CharField(max_length=255, blank=True, null=True)
    material_engineer_attachment_type = models.CharField(max_length=50, blank=True, null=True)

    are_attachment = models.BinaryField(blank=True, null=True, help_text="A.R.E attachment binary")
    are_attachment_name = models.CharField(max_length=255, blank=True, null=True)
    are_attachment_type = models.CharField(max_length=50, blank=True, null=True)

    resident_engineer_attachment = models.BinaryField(blank=True, null=True, help_text="Resident engineer attachment binary")
    resident_engineer_attachment_name = models.CharField(max_length=255, blank=True, null=True)
    resident_engineer_attachment_type = models.CharField(max_length=50, blank=True, null=True)
    
    # Inspection Results
    inspection_results = models.TextField(blank=True, null=True)
    attachments = models.BinaryField(blank=True, null=True, help_text="File stored as binary data in database")
    attachment_name = models.CharField(max_length=255, blank=True, null=True, help_text="Original filename")
    attachment_type = models.CharField(max_length=50, blank=True, null=True, help_text="MIME type")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'RFI'
        verbose_name_plural = 'RFIs'
    
    def save(self, *args, **kwargs):
        # Generate RFI number if not exists
        if not self.rfi_number:
            import uuid
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            unique_id = str(uuid.uuid4())[:8].upper()
            self.rfi_number = f"RFI-{date_str}-{unique_id}"
        
        # Generate share token if not exists
        if not self.share_token:
            import secrets
            self.share_token = secrets.token_urlsafe(48)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.rfi_number} - {self.project.title}"
    
    @property
    def shareable_link(self):
        """Generate shareable link for external access"""
        from django.urls import reverse
        from django.conf import settings
        return f"{settings.SITE_URL if hasattr(settings, 'SITE_URL') else ''}{reverse('rfi_view_shared', kwargs={'token': self.share_token})}"

    @property
    def inspector_response_count(self):
        """Count submitted responses across all inspector roles."""
        return sum([
            bool(self.site_inspector_response),
            bool(self.surveyor_response),
            bool(self.lab_technician_response),
            bool(self.material_engineer_response),
            bool(self.are_response),
            bool(self.resident_engineer_response),
        ])

    @property
    def total_inspectors_required(self):
        return 6

    @property
    def all_inspectors_responded(self):
        """True when every required inspector has submitted a response."""
        return self.inspector_response_count >= self.total_inspectors_required

    @property
    def decided_by_display(self):
        if self.received_by:
            return self.received_by.display_name
        if self.received_by_name:
            return self.received_by_name
        return ""


# --- Industry Standard Features ---

class ChangeOrder(models.Model):
    """Track change orders for projects - industry standard practice"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('implemented', 'Implemented'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='change_orders')
    co_number = models.CharField(max_length=50, unique=True, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    reason = models.TextField(help_text="Reason for change order")
    
    # Financial impact
    cost_impact = models.DecimalField(max_digits=12, decimal_places=2, help_text="Cost increase/decrease")
    
    # Schedule impact
    time_impact_days = models.IntegerField(default=0, help_text="Days added to schedule")
    
    # Status and approvals
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='submitted_change_orders')
    submitted_date = models.DateField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_change_orders')
    approved_date = models.DateField(null=True, blank=True)
    
    # Implementation
    implemented_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.co_number:
            import uuid
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            unique_id = str(uuid.uuid4())[:6].upper()
            self.co_number = f"CO-{date_str}-{unique_id}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.co_number} - {self.title}"


class Submittal(models.Model):
    """Track submittals for material/equipment approvals - industry standard"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('approved_with_comments', 'Approved with Comments'),
        ('rejected', 'Rejected'),
        ('resubmit', 'Resubmit Required'),
    ]
    
    SUBMITTAL_TYPES = [
        ('material', 'Material Sample'),
        ('shop_drawing', 'Shop Drawing'),
        ('product_data', 'Product Data'),
        ('design', 'Design'),
        ('method_statement', 'Method Statement'),
        ('other', 'Other'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='submittals')
    submittal_number = models.CharField(max_length=50, unique=True, editable=False)
    title = models.CharField(max_length=200)
    submittal_type = models.CharField(max_length=20, choices=SUBMITTAL_TYPES)
    description = models.TextField()
    specification_section = models.CharField(max_length=100, blank=True, null=True)
    
    # Submission details
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='submitted_submittals')
    submitted_date = models.DateField()
    required_on_site_date = models.DateField(help_text="When material/equipment is needed on site")
    
    # Review and approval
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_submittals')
    reviewed_date = models.DateField(null=True, blank=True)
    review_comments = models.TextField(blank=True, null=True)
    
    # Documents (in a real app, you'd add file upload fields)
    document_path = models.CharField(max_length=500, blank=True, null=True, help_text="Path to submittal documents")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.submittal_number:
            import uuid
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            unique_id = str(uuid.uuid4())[:6].upper()
            self.submittal_number = f"SUB-{date_str}-{unique_id}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.submittal_number} - {self.title}"


class Equipment(models.Model):
    """Track equipment on construction site - industry standard"""
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('in_use', 'In Use'),
        ('maintenance', 'Under Maintenance'),
        ('breakdown', 'Breakdown'),
        ('off_site', 'Off Site'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='equipment')
    equipment_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    equipment_type = models.CharField(max_length=100, help_text="E.g., Excavator, Crane, Mixer, etc.")
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    
    # Status and location
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    location_on_site = models.CharField(max_length=200, blank=True, null=True)
    
    # Dates
    arrival_date = models.DateField()
    planned_departure_date = models.DateField(null=True, blank=True)
    
    # Costs
    daily_rental_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    operator_name = models.CharField(max_length=100, blank=True, null=True)
    operator_phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Maintenance
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    managed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_equipment')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Equipment'
    
    def __str__(self):
        return f"{self.name} ({self.equipment_id})"


class SafetyIncident(models.Model):
    """Track safety incidents - critical for construction industry"""
    
    SEVERITY_CHOICES = [
        ('near_miss', 'Near Miss'),
        ('first_aid', 'First Aid'),
        ('medical_treatment', 'Medical Treatment'),
        ('lost_time', 'Lost Time Injury'),
        ('fatality', 'Fatality'),
    ]
    
    INCIDENT_TYPES = [
        ('fall', 'Fall from Height'),
        ('struck_by', 'Struck By Object'),
        ('caught_between', 'Caught Between'),
        ('electric', 'Electrical'),
        ('equipment', 'Equipment Related'),
        ('chemical', 'Chemical Exposure'),
        ('environmental', 'Environmental'),
        ('other', 'Other'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='safety_incidents')
    incident_number = models.CharField(max_length=50, unique=True, editable=False)
    
    # Incident details
    incident_date = models.DateField()
    incident_time = models.TimeField()
    location = models.CharField(max_length=300, help_text="Location on site")
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    
    # People involved
    person_involved = models.CharField(max_length=200)
    person_role = models.CharField(max_length=100)
    witnesses = models.TextField(blank=True, null=True, help_text="Names of witnesses")
    
    # Description
    description = models.TextField(help_text="Detailed description of the incident")
    immediate_action_taken = models.TextField()
    root_cause = models.TextField(blank=True, null=True)
    corrective_actions = models.TextField(blank=True, null=True)
    
    # Reporting
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_incidents')
    reported_to_authority = models.BooleanField(default=False, help_text="Reported to OSHA or local authority")
    authority_reference = models.CharField(max_length=100, blank=True, null=True)
    
    # Follow-up
    investigation_completed = models.BooleanField(default=False)
    investigation_date = models.DateField(null=True, blank=True)
    investigated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='investigated_incidents')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-incident_date', '-incident_time']
    
    def save(self, *args, **kwargs):
        if not self.incident_number:
            import uuid
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            unique_id = str(uuid.uuid4())[:6].upper()
            self.incident_number = f"INC-{date_str}-{unique_id}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.incident_number} - {self.get_severity_display()}"


class ProjectMilestone(models.Model):
    """Track project milestones - industry standard for project management"""
    
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('delayed', 'Delayed'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    # Dates
    planned_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    completion_percentage = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Dependencies
    dependencies = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='dependent_milestones')
    
    # Financial
    payment_linked = models.BooleanField(default=False, help_text="Payment tied to this milestone")
    payment_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_milestones')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['planned_date']
    
    def __str__(self):
        return f"{self.title} - {self.project.title}"
    
    @property
    def is_delayed(self):
        """Check if milestone is delayed"""
        if self.status == 'completed':
            return False
        return timezone.now().date() > self.planned_date


class ProjectDocument(models.Model):
    """Document management for projects - industry standard"""
    
    DOCUMENT_TYPES = [
        ('contract', 'Contract'),
        ('drawing', 'Drawing'),
        ('specification', 'Specification'),
        ('permit', 'Permit'),
        ('report', 'Report'),
        ('photo', 'Photo'),
        ('invoice', 'Invoice'),
        ('warranty', 'Warranty'),
        ('other', 'Other'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    document_number = models.CharField(max_length=100, blank=True, null=True)
    
    # File info (in real app, use FileField)
    file_path = models.CharField(max_length=500, help_text="Path to document file")
    file_size = models.IntegerField(null=True, blank=True, help_text="File size in bytes")
    
    # Version control
    version = models.CharField(max_length=20, default='1.0')
    is_latest = models.BooleanField(default=True)
    superseded_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='supersedes')
    
    # Upload info
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Access control
    is_confidential = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} v{self.version}"
