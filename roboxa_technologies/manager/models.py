from django.db import models
from master_data.models import Employee
from pmo.models import Project

class TimesheetApproval(models.Model):
    project_code = models.ForeignKey(Project, on_delete=models.CASCADE)
    employee_code = models.ForeignKey(Employee, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, null=False, blank=False)
    month = models.IntegerField()
    year = models.IntegerField()
    budgeted_hours = models.PositiveIntegerField()
    allocated_hours = models.PositiveIntegerField()
    worked_hours = models.PositiveIntegerField()
    employee_name = models.CharField(max_length=80)
    date = models.DateField() 
    description = models.CharField(max_length=100)
    project_role = models.CharField(max_length=60)
    booked_hours = models.PositiveIntegerField()
    task_description = models.CharField(max_length=100)
    remarks = models.CharField(max_length=200)
    comments = models.CharField(max_length=50)

    def __str__(self):
        return f"Timesheet Approval for {self.employee_name} on ({self.month} {self.year})"
    
    def is_booked_hours_exceed(self):
        """
        Check if the booked hours exceed the allocated hours.
        Returns a boolean indicating the condition.
        """
        return self.booked_hours > self.allocated_hours

