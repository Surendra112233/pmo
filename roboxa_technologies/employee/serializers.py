
from rest_framework import serializers
from .models import EmployeeTimesheet, ProjectTasks
from pmo.models import ProjectTeam
from manager.models import TimesheetApproval
from datetime import timedelta
from datetime import datetime


class EmployeeTimesheetSerializer(serializers.ModelSerializer):
    task_description = serializers.PrimaryKeyRelatedField(queryset=ProjectTasks.objects.all())
    worked_hours = serializers.CharField(required=True)  # Expect HH:MM format
    comments = serializers.SerializerMethodField()
    project_manager = serializers.CharField(source='project_code.project_manager', read_only=True)

    # booked_hours = serializers.CharField(required=False, allow_null=True)

    #  Convert `worked_hours`

    # def validate(self, data):
    #     employee = data.get("employee_code") or self.instance.employee_code
    #     date = data.get("date") or self.instance.date
    #     new_worked_hours = data.get("worked_hours")

    #     #  Convert worked_hours safely
    #     def convert_to_seconds(value):
    #         if isinstance(value, timedelta):
    #             return int(value.total_seconds())  # Convert timedelta to seconds
    #         elif isinstance(value, str):
    #             try:
    #                 hours, minutes = map(int, value.split(":"))
    #                 return (hours * 3600) + (minutes * 60)
    #             except ValueError:
    #                 raise serializers.ValidationError({"worked_hours": "Invalid time format. Use HH:MM."})
    #         return 0

    #     new_worked_seconds = convert_to_seconds(new_worked_hours)

    #     #  Get all existing timesheets for this employee on this date
    #     existing_entries = EmployeeTimesheet.objects.filter(employee_code=employee, date=date).exclude(id=self.instance.id if self.instance else None)

    #     total_existing_seconds = sum(convert_to_seconds(entry.worked_hours) for entry in existing_entries)

    #     #  Calculate new total hours if this update is applied
    #     total_seconds = total_existing_seconds + new_worked_seconds

    #     if total_seconds > 28800:  # 8 hours max
    #         raise serializers.ValidationError({
    #             "worked_hours": f"Total worked hours exceed 8 hours ({total_seconds / 3600:.2f} hrs)."
    #         })

    #     return data
    # def validate(self, data):
    #     employee = data.get("employee_code") or self.instance.employee_code
    #     date = data.get("date") or self.instance.date
    #     new_worked_hours = data.get("worked_hours")

    #     # Convert worked_hours safely
    #     def convert_to_seconds(value):
    #         if isinstance(value, timedelta):
    #             return int(value.total_seconds())  # Convert timedelta to seconds
    #         elif isinstance(value, str):
    #             try:
    #                 hours, minutes = map(int, value.split(":"))
    #                 return (hours * 3600) + (minutes * 60)
    #             except ValueError:
    #                 raise serializers.ValidationError({"worked_hours": "Invalid time format. Use HH:MM."})
    #         return 0

    #     new_worked_seconds = convert_to_seconds(new_worked_hours)

    #     # Get all existing APPROVED or PENDING timesheets (IGNORE rejected ones)
    #     existing_entries = EmployeeTimesheet.objects.filter(
    #         employee_code=employee,
    #         date=date
    #     ).exclude(status="rejected")  # Ignore rejected entries

    #     # Calculate total worked hours for this employee on the given date
    #     total_existing_seconds = sum(convert_to_seconds(entry.worked_hours) for entry in existing_entries)

    #     #  If updating an existing entry, subtract the old worked_hours first
    #     if self.instance:
    #         old_worked_seconds = convert_to_seconds(self.instance.worked_hours)
    #         total_seconds = (total_existing_seconds - old_worked_seconds) + new_worked_seconds
    #     else:
    #         total_seconds = total_existing_seconds + new_worked_seconds

    #     #  Validate that total does not exceed 8 hours (28,800 seconds)
    #     if total_seconds > 28800:
    #         raise serializers.ValidationError({
    #             "worked_hours": f"Total worked hours exceed 8 hours ({total_seconds / 3600:.2f} hrs)."
    #         })
        
        
    #     return data
    def validate(self, data):
        employee = data.get("employee_code") or self.instance.employee_code
        date = data.get("date") or self.instance.date
        new_worked_hours = data.get("worked_hours")
        task = data.get("task_description") or self.instance.task_description
        project = data.get("project_code") or self.instance.project_code

        # Convert worked_hours safely
        def convert_to_seconds(value):
            if isinstance(value, timedelta):
                return int(value.total_seconds())
            elif isinstance(value, str):
                try:
                    hours, minutes = map(int, value.split(":"))
                    return (hours * 3600) + (minutes * 60)
                except ValueError:
                    raise serializers.ValidationError({"worked_hours": "Invalid time format. Use HH:MM."})
            return 0

        new_worked_seconds = convert_to_seconds(new_worked_hours)

        # 1. Validate daily worked hours do not exceed 8 hours
        existing_entries = EmployeeTimesheet.objects.filter(
            employee_code=employee,
            date=date
        ).exclude(status="rejected")

        total_existing_seconds = sum(convert_to_seconds(entry.worked_hours) for entry in existing_entries)

        if self.instance:
            old_worked_seconds = convert_to_seconds(self.instance.worked_hours)
            total_seconds = (total_existing_seconds - old_worked_seconds) + new_worked_seconds
        else:
            total_seconds = total_existing_seconds + new_worked_seconds

        if total_seconds > 28800:
            raise serializers.ValidationError({
                "worked_hours": f"Total worked hours exceed 8 hours ({total_seconds / 3600:.2f} hrs)."
            })

        # 2. Validate cumulative worked hours do not exceed allocated_hours from ProjectTeam
        from pmo.models import ProjectTeam  # Import inside function if circular import

        try:
            project_team = ProjectTeam.objects.get(
                employee_code=employee,
                project_code=project,
                task=task
            )
        except ProjectTeam.DoesNotExist:
            raise serializers.ValidationError("Employee is not assigned to this task in the project team.")

        allocated_seconds = project_team.allocated_hours * 3600

        # Get all approved or pending timesheets for that employee-task-project
        total_project_task_seconds = sum(
            convert_to_seconds(entry.worked_hours)
            for entry in EmployeeTimesheet.objects.filter(
                employee_code=employee,
                project_code=project,
                task_description=task
            ).exclude(status="rejected")
        )

        if self.instance:
            old_worked_seconds = convert_to_seconds(self.instance.worked_hours)
            total_project_task_seconds = (total_project_task_seconds - old_worked_seconds) + new_worked_seconds
        else:
            total_project_task_seconds += new_worked_seconds

        if total_project_task_seconds > allocated_seconds:
            raise serializers.ValidationError({
                "worked_hours": f"Total worked hours for this phase ({total_project_task_seconds / 3600:.2f} hrs) exceed allocated hours ({project_team.allocated_hours} hrs)."
            })

        return data

    
    def validate_date(self, value):
        """
        Ensure the timesheet entry date is within (or on) the employee's project assignment period.
        """
        # Use self.initial_data carefully, as it's a list when `many=True`
        if isinstance(self.initial_data, list):  
            request_data = self.initial_data[0]  # Get the first entry safely
        else:
            request_data = self.initial_data  

        employee_code = request_data.get("employee_code")
        project_code = request_data.get("project_code")
        task_description = request_data.get("task_description")

        if not employee_code or not project_code:
            raise serializers.ValidationError("Employee code and project code are required.")

        # Fetch the correct project team entry including the task
        project_team_entry = ProjectTeam.objects.filter(
            employee_code=employee_code,
            project_code=project_code,
            task=task_description  # Now filtering by the specific task
        ).first()

        if not project_team_entry:
            raise serializers.ValidationError("No project assignment found for the given employee, project, and phase.")

        # Convert value to date if it's a string
        if isinstance(value, str):
            value = datetime.strptime(value, "%Y-%m-%d").date()

        # Validate the timesheet date against the specific task's start and end dates
        if not (project_team_entry.start_date <= value <= project_team_entry.end_date):
            raise serializers.ValidationError(
                f"Timesheet date must be between {project_team_entry.start_date} and {project_team_entry.end_date}."
            )

        return value

    class Meta:
        model = EmployeeTimesheet
        exclude = ['designation', 'allocated_hours', 'booked_hours']  # Remove these fields from API request/response
    
    def get_comments(self, obj):
        """Fetch the latest approval/rejection comment for the specific timesheet entry."""
        latest_approval = TimesheetApproval.objects.filter(
            employee_code=obj.employee_code,
            id=obj.id,  # Ensure it matches the correct timesheet entry
            status__in=["approved", "rejected"]  # Consider both approved & rejected statuses
        ).order_by('-date').first()

        return latest_approval.comments if latest_approval else None


    def create(self, validated_data):
        """Ensure booked_hours defaults to worked_hours if not provided"""
        validated_data.pop('allocated_hours', None)  # Remove if exists
        validated_data.pop('booked_hours', None)  # Remove if exists

        return super().create(validated_data)

    def validate_time(self, value, field_name):
        """Convert 'HH:MM' or 'HH:MM:SS' format to timedelta."""
        if not value:
            return None
        try:
            parts = list(map(int, value.split(":")))
            if len(parts) == 2:
                hours, minutes = parts
                seconds = 0
            elif len(parts) == 3:
                hours, minutes, seconds = parts
            else:
                raise ValueError
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
        except ValueError:
            raise serializers.ValidationError(f"Invalid {field_name} format. Use 'HH:MM' or 'HH:MM:SS'.")

    def validate_worked_hours(self, value):
        return self.validate_time(value, "worked_hours")

    # def validate_booked_hours(self, value):
    #     return self.validate_time(value, "booked_hours")

    # def create(self, validated_data):
    #     if 'booked_hours' not in validated_data or validated_data['booked_hours'] is None:
    #         validated_data['booked_hours'] = validated_data.get('worked_hours', timedelta())
    #     return super().create(validated_data)

    def to_representation(self, instance):
        """Convert timedelta fields back to 'HH:MM' format for response"""
        def format_time(value):
            if isinstance(value, timedelta):
                total_seconds = int(value.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                return f"{hours:02}:{minutes:02}"
            return "00:00"

        data = super().to_representation(instance)
        data["worked_hours"] = format_time(instance.worked_hours)
        
        # Remove booked_hours if it appears in response
        data.pop("booked_hours", None)
        
        return data


class DisplayTimesheetSerializer(serializers.ModelSerializer):
    project = serializers.CharField(source='project_code')
    month_year = serializers.SerializerMethodField()
    task = serializers.SerializerMethodField()
    worked_hours = serializers.CharField(source='get_worked_hours')

    class Meta:
        model = EmployeeTimesheet
        fields = ['project', 'month_year', 'date', 'task', 'worked_hours', 'status']

    def get_month_year(self, obj):
        return f"{obj.month}/{obj.year}"

    def get_task(self, obj):
        """Return task descriptions as a comma-separated string instead of a list."""
        return ", ".join(task.description for task in obj.task_description.all()) if obj.task_description.exists() else ""
    
class ProjectHoursSerializer(serializers.ModelSerializer):
    phase_name = serializers.CharField(source="task_description.task_group")  # Assuming task_group is in ProjectTasks
    allocated_hours = serializers.IntegerField()
    worked_hours = serializers.SerializerMethodField()
    balanced_hours = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeTimesheet
        fields = ["phase_name", "allocated_hours", "worked_hours", "balanced_hours"]

    def get_worked_hours(self, obj):
        """Convert worked_hours from timedelta to HH:MM format"""
        if obj.worked_hours:
            total_seconds = int(obj.worked_hours.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{hours:02}:{minutes:02}"
        return "00:00"

    def get_balanced_hours(self, obj):
        """Calculate remaining hours"""
        worked_hours = obj.worked_hours.total_seconds() / 3600 if obj.worked_hours else 0
        return obj.allocated_hours - worked_hours