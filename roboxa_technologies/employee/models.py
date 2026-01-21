from django.db import models
from master_data.models import Employee
from pmo.models import Project
from master_data.models import ProjectTasks
 
class EmployeeTimesheet(models.Model):
    employee_code = models.ForeignKey(Employee, on_delete=models.CASCADE)
    project_code = models.ForeignKey(Project,on_delete=models.CASCADE)
    employee_name = models.CharField(max_length=80,null=False,blank=False)
    designation = models.CharField(max_length=60,null=False,blank=False)
    month = models.IntegerField()
    year = models.IntegerField()
    date = models.DateField()
    description = models.CharField(max_length=100,null=False,blank=False)
    project_role = models.CharField(max_length=60,null=False,blank=False)
    allocated_hours = models.PositiveIntegerField(null=True,blank=True)
    booked_hours = models.DurationField(null=True,blank=True) 
    task_description = models.ForeignKey(ProjectTasks, on_delete=models.CASCADE)
    new_description = models.CharField(max_length=100,null=True,blank=True)
    worked_hours = models.DurationField()
    remarks = models.CharField(max_length=200, null=True, blank=True)
    status = models.CharField(max_length=10)
    

    @property
    def get_worked_hours(self):
        """Returns worked hours as HH:MM"""
        if self.worked_hours:
            total_seconds = int(self.worked_hours.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{hours:02}:{minutes:02}"
        return "00:00"
    
    def validate_booked_hours(self, value):
        return self.validate_time(value, "booked_hours")  # This line must be indented


    def is_booked_hours_exceed(self):
        """Check if booked hours exceed allocated hours"""
        booked_seconds = self.booked_hours.hour * 3600 + self.booked_hours.minute * 60
        allocated_seconds = self.allocated_hours * 3600
        return booked_seconds > allocated_seconds

    def __str__(self):
        return f"{self.employee_name} - {self.date}"
    