from django.db import models
from master_data.models import Employee, ProjectRoles, ProjectTasks
from django.core.validators import MaxValueValidator,MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from datetime import timedelta
from decimal import Decimal

class Project(models.Model):
    project_code = models.CharField(max_length=10, unique=True, primary_key=True, null=False, blank=False)
    project_description = models.CharField(max_length=100, null=False, blank=False)
    project_type = models.CharField(max_length=30, null=False, blank=False)
    project_category = models.CharField(max_length=10, null=False, blank=False)
    project_status = models.CharField(max_length=10, null=False, blank=False)
    project_manager = models.CharField(max_length=80, null=False, blank=False)
    hr = models.CharField(max_length=80, null=True,blank=True)
    delivery_head = models.CharField(max_length=80, null=True, blank=True)
    sbu_head = models.CharField(max_length=80, null=True, blank=True)
    contracting_company = models.CharField(max_length=50, null=True, blank=True)
    management = models.CharField(max_length=100, default='Sudhakara Varma Yarramraju', editable=False)
    from_date = models.DateField()
    to_date = models.DateField()
    client_name = models.CharField(max_length=100, null=False, blank=False)
    project_region = models.CharField(max_length=60, null=False, blank=False)
    project_country = models.CharField(max_length=60, null=False, blank=False)
    delivery_model = models.CharField(max_length=20, null=False, blank=False)
    budgeted_hours = models.BigIntegerField(validators=[MaxValueValidator(9999999999)], null=False, blank=False)
    allocated_hours = models.BigIntegerField(validators=[MaxValueValidator(9999999999)], null=True, blank=True)
    # allocated_budgeted_hours = models.BigIntegerField(null=False, blank=False,default=0,validators=[MinValueValidator(0),MaxValueValidator(9999999999)])
    allocated_budgeted_hours = models.DecimalField(
    max_digits=12,
    decimal_places=2,
    null=False,
    blank=False,
    default=Decimal("0.00"),
    validators=[
        MinValueValidator(Decimal("0.00")),
        MaxValueValidator(Decimal("9999999999.99"))
    ]
)
    allocated_budgeted_percentage = models.IntegerField(null=True,blank=True)
    worked_hours = models.CharField(max_length=10, default="00:00")    
    notes = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(default=now, editable=False)  # Auto-set at creation
    updated_at = models.DateTimeField(auto_now=True)  # Auto-update on save

    def save(self, *args, **kwargs):
        """Ensure worked_hours is always stored in 'HH:MM' format."""
        if isinstance(self.worked_hours, timedelta):
            total_minutes = int(self.worked_hours.total_seconds() // 60)
            hours, minutes = divmod(total_minutes, 60)
            self.worked_hours = f"{hours:02}:{minutes:02}"  # Convert timedelta to HH:MM
        elif isinstance(self.worked_hours, str) and ":" in self.worked_hours:
            self.worked_hours = self.worked_hours[:5]  # Trim existing string to HH:MM

        # Set default for management if null or blank
        if not self.management:
            self.management = "Sudhakara Varma Yarramraju"
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.project_description

class ProjectTeam(models.Model):
    project_code = models.ForeignKey(Project, on_delete=models.CASCADE)
    employee_code = models.ForeignKey(Employee, on_delete=models.CASCADE)
    employee_name = models.CharField(max_length=80, null=False, blank=False)
    designation = models.CharField(max_length=60, null=False, blank=False)
    project_role = models.ForeignKey(ProjectRoles, on_delete=models.CASCADE)
    start_date = models.DateField() 
    end_date = models.DateField()   
    task = models.ForeignKey(ProjectTasks, on_delete=models.CASCADE)
    allocated_hours = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=now, editable=False)  # Auto-set at creation
    updated_at = models.DateTimeField(auto_now=True)  # Auto-update on save

    def __str__(self):
        return f"{self.project_code} - {self.employee_name}"
    

class PhaseAllocation(models.Model):
    task = models.ForeignKey(ProjectTasks, to_field="task_code",on_delete=models.CASCADE) 
    project_code = models.ForeignKey(Project, on_delete=models.CASCADE)
    budgeted_hours = models.BigIntegerField()
    allocated_hours = models.PositiveIntegerField(default=0)  # Updated from ProjectTeam
    # worked_hours = models.DurationField(default="00:00")  # From EmployeeTimesheet
    worked_hours = models.CharField(max_length=10, default="00:00")
    start_date = models.DateField(null=True, blank=True) 
    end_date = models.DateField(null=True, blank=True)  
    
    def clean(self):
        """Ensure total task-wise budgeted_hours does not exceed project's budgeted_hours."""
        total_task_hours = (
            PhaseAllocation.objects.filter(project_code=self.project_code)
            .exclude(pk=self.pk)  # Exclude current instance (for updates)
            .aggregate(total=models.Sum("budgeted_hours"))["total"] or 0
        )

        if total_task_hours + self.budgeted_hours > self.project_code.budgeted_hours:
            raise ValidationError(
                f"Total budgeted hours ({total_task_hours + self.budgeted_hours}) "
                f"exceed project budgeted hours ({self.project_code.budgeted_hours})."
            )

    def save(self, *args, **kwargs):
        """Run validation before saving."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.task.task_group} - {self.project_code}"
    

class ProjectTeamAllocation(models.Model):
    employee_code = models.ForeignKey(Employee, on_delete=models.CASCADE)
    project_code = models.ForeignKey(Project, on_delete=models.CASCADE)
    allocation_percent = models.FloatField(default=0)
    allocation_start_date = models.DateField(null=True, blank=True)
    allocation_end_date = models.DateField(null=True, blank=True)


    class Meta:
        unique_together = ('employee_code', 'project_code')

    def __str__(self):
        return f"{self.employee_code.employee_code} - {self.project_code.project_code} : {self.allocation_percent}%"
    
class ProjectTeamAllocationHistory(models.Model):
    allocation = models.ForeignKey(ProjectTeamAllocation, on_delete=models.CASCADE, related_name="history")
    allocation_percent = models.FloatField()
    allocation_start_date = models.DateField()
    allocation_end_date = models.DateField()
    updated_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=50, null=True)

class PhaseTeamAllocation(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    task = models.ForeignKey(ProjectTasks, on_delete=models.CASCADE)

    allocation_percent = models.FloatField(default=0)
    allocation_start_date = models.DateField(null=True, blank=True)
    allocation_end_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('employee', 'project', 'task')

    def __str__(self):
        return f"{self.employee.employee_code} - {self.project.project_code} - {self.task.task_code}"
    

class PhaseTeamAllocationHistory(models.Model):
    allocation = models.ForeignKey(
        PhaseTeamAllocation,
        on_delete=models.CASCADE,
        related_name="history"
    )
    allocation_percent = models.FloatField()
    allocation_start_date = models.DateField()
    allocation_end_date = models.DateField()
    updated_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=50, null=True)

