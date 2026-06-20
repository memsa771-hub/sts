from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Project, DailySiteReport, ReportPhoto, 
    LaborDetail, MaterialUsage, TeamMember, Notification,
    Worker, ProjectWorkerAssignment, RFI, Activity, ActivityWork,
    ChangeOrder, Submittal, Equipment, SafetyIncident, ProjectMilestone, ProjectDocument
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom User Admin"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'designation', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'designation')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'address', 'designation')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'address', 'designation')
        }),
    )


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'project_number', 'location', 'status', 'start_date', 'end_date', 'site_engineer', 'contractor', 'consultant')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('title', 'project_number', 'location', 'description', 'client_name')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Project Info', {
            'fields': ('title', 'project_number', 'description', 'location', 'status')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
        ('Team Assignment', {
            'fields': ('site_engineer', 'contractor', 'consultant', 'client')
        }),
        ('Client Information', {
            'fields': ('client_name', 'client_contact', 'client_email', 'client_phone')
        }),
        ('Financial', {
            'fields': ('budget', 'contract_value', 'total_area')
        }),
    )


class ReportPhotoInline(admin.TabularInline):
    model = ReportPhoto
    extra = 1


class LaborDetailInline(admin.TabularInline):
    model = LaborDetail
    extra = 1


class MaterialUsageInline(admin.TabularInline):
    model = MaterialUsage
    extra = 1


@admin.register(DailySiteReport)
class DailySiteReportAdmin(admin.ModelAdmin):
    list_display = ('project', 'date', 'site_engineer', 'weather', 'status', 'approved_by', 'created_at')
    list_filter = ('status', 'weather', 'date', 'project__status')
    search_fields = ('project__title', 'site_engineer__username', 'work_description')
    date_hierarchy = 'date'
    
    inlines = [LaborDetailInline, MaterialUsageInline, ReportPhotoInline]
    
    fieldsets = (
        ('Report Info', {
            'fields': ('project', 'site_engineer', 'date', 'weather')
        }),
        ('Work Details', {
            'fields': ('work_description', 'issues_remarks')
        }),
        ('Approval', {
            'fields': ('status', 'approved_by', 'approved_at', 'rejection_reason')
        }),
    )
    
    readonly_fields = ('approved_at',)


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'cnic', 'contact_info', 'joined_date', 'is_active')
    list_filter = ('is_active', 'joined_date')
    search_fields = ('first_name', 'cnic', 'contact_info')
    date_hierarchy = 'joined_date'
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'cnic', 'contact_info')
        }),
        ('Employment Details', {
            'fields': ('joined_date', 'is_active')
        }),
        ('Management', {
            'fields': ('added_by',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')
    date_hierarchy = 'created_at'
    
    readonly_fields = ('created_at',)


@admin.register(LaborDetail)
class LaborDetailAdmin(admin.ModelAdmin):
    list_display = ('report', 'category', 'count', 'working_hours', 'hourly_rate', 'total_cost')
    list_filter = ('category',)
    search_fields = ('report__project__title', 'category')


@admin.register(MaterialUsage)
class MaterialUsageAdmin(admin.ModelAdmin):
    list_display = ('report', 'material_name', 'quantity', 'unit', 'supplier', 'unit_cost', 'total_cost')
    list_filter = ('unit',)
    search_fields = ('report__project__title', 'material_name', 'supplier')


@admin.register(ReportPhoto)
class ReportPhotoAdmin(admin.ModelAdmin):
    list_display = ('report', 'caption', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('report__project__title', 'caption')


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'first_name', 'last_name', 'skill_level', 'designation', 'hourly_rate', 'managed_by', 'is_active')
    list_filter = ('skill_level', 'is_active', 'managed_by')
    search_fields = ('first_name', 'last_name', 'employee_id', 'designation')
    fieldsets = (
        ('Basic Information', {
            'fields': ('first_name', 'last_name', 'employee_id', 'phone', 'address')
        }),
        ('Work Details', {
            'fields': ('skill_level', 'designation', 'hourly_rate', 'date_joined', 'is_active')
        }),
        ('Management', {
            'fields': ('managed_by', 'notes')
        }),
    )


@admin.register(ProjectWorkerAssignment)
class ProjectWorkerAssignmentAdmin(admin.ModelAdmin):
    list_display = ('worker', 'project', 'assigned_date', 'end_date', 'is_active', 'assigned_by')
    list_filter = ('is_active', 'assigned_date', 'assigned_by')
    search_fields = ('worker__first_name', 'worker__last_name', 'project__title')
    date_hierarchy = 'assigned_date'


@admin.register(RFI)
class RFIAdmin(admin.ModelAdmin):
    list_display = ('rfi_number', 'project', 'submission_date', 'submitted_by', 'approval_status', 'has_responses', 'created_at')
    list_filter = ('approval_status', 'submission_date', 'created_at')
    search_fields = ('rfi_number', 'project__title', 'request_description', 'submitted_by_name')
    date_hierarchy = 'submission_date'
    
    def has_responses(self, obj):
        responses = sum([
            bool(obj.site_inspector_response),
            bool(obj.surveyor_response),
            bool(obj.lab_technician_response),
            bool(obj.material_engineer_response),
            bool(obj.are_response),
            bool(obj.resident_engineer_response),
        ])
        return f"{responses}/6"
    has_responses.short_description = 'Responses'
    
    fieldsets = (
        ('RFI Information', {
            'fields': ('rfi_number', 'project', 'share_token', 'access_password')
        }),
        ('Submission Details', {
            'fields': ('submission_date', 'submission_time', 'submitted_by_name', 'submitted_by')
        }),
        ('Inspection Details', {
            'fields': ('inspection_date', 'inspection_time', 'inspection_results', 'attachments')
        }),
        ('Receiving Details', {
            'fields': ('receiving_date', 'receiving_time', 'received_by_name', 'received_by')
        }),
        ('Request', {
            'fields': ('request_description',)
        }),
        ('Site Inspector', {
            'fields': ('site_inspector_name', 'site_inspector_signature', 'site_inspector_response', 'site_inspector_responded_at')
        }),
        ('Surveyor', {
            'fields': ('surveyor_name', 'surveyor_signature', 'surveyor_response', 'surveyor_responded_at')
        }),
        ('Lab Technician', {
            'fields': ('lab_technician_name', 'lab_technician_signature', 'lab_technician_response', 'lab_technician_responded_at')
        }),
        ('Material Engineer', {
            'fields': ('material_engineer_name', 'material_engineer_signature', 'material_engineer_response', 'material_engineer_responded_at')
        }),
        ('A.R.E', {
            'fields': ('are_name', 'are_signature', 'are_response', 'are_responded_at')
        }),
        ('Resident Engineer', {
            'fields': ('resident_engineer_name', 'resident_engineer_signature', 'resident_engineer_response', 'resident_engineer_responded_at')
        }),
        ('Approval', {
            'fields': ('approval_status',)
        }),
        ('Contractor', {
            'fields': ('contractor_name', 'contractor_signature')
        }),
    )
    
    readonly_fields = ('rfi_number', 'share_token', 'created_at', 'site_inspector_responded_at', 
                      'surveyor_responded_at', 'lab_technician_responded_at', 
                      'material_engineer_responded_at', 'are_responded_at', 'resident_engineer_responded_at')



# --- Industry Standard Feature Admin Classes ---

@admin.register(ChangeOrder)
class ChangeOrderAdmin(admin.ModelAdmin):
    list_display = ('co_number', 'title', 'project', 'status', 'cost_impact', 'time_impact_days', 'submitted_date')
    list_filter = ('status', 'submitted_date')
    search_fields = ('co_number', 'title', 'description', 'project__title')
    date_hierarchy = 'submitted_date'
    readonly_fields = ('co_number',)


@admin.register(Submittal)
class SubmittalAdmin(admin.ModelAdmin):
    list_display = ('submittal_number', 'title', 'project', 'submittal_type', 'status', 'submitted_date', 'required_on_site_date')
    list_filter = ('status', 'submittal_type', 'submitted_date')
    search_fields = ('submittal_number', 'title', 'project__title')
    date_hierarchy = 'submitted_date'
    readonly_fields = ('submittal_number',)


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('equipment_id', 'name', 'equipment_type', 'project', 'status', 'arrival_date', 'daily_rental_cost')
    list_filter = ('status', 'equipment_type', 'arrival_date')
    search_fields = ('equipment_id', 'name', 'equipment_type', 'project__title')
    date_hierarchy = 'arrival_date'


@admin.register(SafetyIncident)
class SafetyIncidentAdmin(admin.ModelAdmin):
    list_display = ('incident_number', 'project', 'severity', 'incident_type', 'incident_date', 'investigation_completed')
    list_filter = ('severity', 'incident_type', 'investigation_completed', 'reported_to_authority', 'incident_date')
    search_fields = ('incident_number', 'person_involved', 'project__title', 'description')
    date_hierarchy = 'incident_date'
    readonly_fields = ('incident_number',)
    
    fieldsets = (
        ('Incident Details', {
            'fields': ('incident_number', 'project', 'incident_date', 'incident_time', 'location', 'incident_type', 'severity')
        }),
        ('People Involved', {
            'fields': ('person_involved', 'person_role', 'witnesses')
        }),
        ('Description', {
            'fields': ('description', 'immediate_action_taken', 'root_cause', 'corrective_actions')
        }),
        ('Reporting', {
            'fields': ('reported_by', 'reported_to_authority', 'authority_reference')
        }),
        ('Investigation', {
            'fields': ('investigation_completed', 'investigation_date', 'investigated_by')
        }),
    )


@admin.register(ProjectMilestone)
class ProjectMilestoneAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'planned_date', 'actual_date', 'status', 'completion_percentage', 'payment_linked')
    list_filter = ('status', 'payment_linked', 'planned_date')
    search_fields = ('title', 'project__title', 'description')
    date_hierarchy = 'planned_date'


@admin.register(ProjectDocument)
class ProjectDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'document_type', 'project', 'version', 'is_latest', 'uploaded_by', 'uploaded_at')
    list_filter = ('document_type', 'is_latest', 'is_confidential', 'uploaded_at')
    search_fields = ('title', 'document_number', 'project__title')
    date_hierarchy = 'uploaded_at'
    readonly_fields = ('uploaded_at',)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'unit', 'total_quantity', 'is_active', 'progress_percentage')
    list_filter = ('is_active', 'unit', 'created_at')
    search_fields = ('name', 'description', 'project__title')


@admin.register(ActivityWork)
class ActivityWorkAdmin(admin.ModelAdmin):
    list_display = ('activity', 'date', 'quantity', 'recorded_by', 'daily_report')
    list_filter = ('date', 'activity__project')
    search_fields = ('activity__name', 'description')
    date_hierarchy = 'date'
