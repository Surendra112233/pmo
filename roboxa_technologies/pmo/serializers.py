from rest_framework import serializers
from .models import Project, ProjectTeam
from django.db.models import Sum,F, Min,Max
from django.db.models.functions import Coalesce
from employee.models import EmployeeTimesheet
import re
from pmo.models import PhaseAllocation,ProjectTeamAllocation
from datetime import timedelta
from master_data.models import ProjectTasks
from employee.models import EmployeeTimesheet,Employee
from pmo.models import PhaseAllocation
from django.db.models import Sum, Value

class ProjectCreateSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    management = serializers.CharField(default="Sudhakara Varma Yarramraju")

    class Meta:
        model = Project
        fields = '__all__'
        
    # def validate_delivery_head(self, value):
    #     if value and not re.match(r'^[A-Za-z ]+$', value):
    #         raise serializers.ValidationError("Delivery head should contain only alphabetic characters and spaces.")
    #     return value
    
    # def validate_sbu_head(self, value):
    #     if value and not re.match(r'^[A-Za-z ]+$', value):
    #         raise serializers.ValidationError("SBU Head should contain only alphabetic characters and spaces.")
    #     return value

    # def validate_management(self, value):
    #     if value and not re.match(r'^[A-Za-z ]+$', value):
    #         raise serializers.ValidationError("Management should contain only alphabetic characters and spaces.")
    #     return value
    def validate_management(self, value):
        # If value is missing or blank, set default
        if not value or value.strip() == "":
            return "Sudhakara Varma Yarramraju"
        if not re.match(r'^[A-Za-z ]+$', value):
            raise serializers.ValidationError("Management should contain only alphabetic characters and spaces.")
        return value



class ProjectListSerializer(serializers.ModelSerializer):
    from_date = serializers.DateField(format='%Y-%m-%d', allow_null=True)
    to_date = serializers.DateField(format='%Y-%m-%d', allow_null=True)
    worked_hours = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = '__all__'

    def get_allocated_hours(self, obj):
        return ProjectTeam.objects.filter(project_code=obj.project_code).aggregate(
            total=Sum('allocated_hours')
        )['total'] or 0

    def validate_client_name(self, value):
        """
        Ensure client_name contains only letters and spaces.
        """
        if not re.match(r'^[A-Za-z ]+$', value):
            raise serializers.ValidationError("Client name should contain only alphabetic characters and spaces.")
        return value

    def validate(self, data):
        """Validate that to_date is greater than from_date."""
        from_date = data.get("from_date")
        to_date = data.get("to_date")

        if from_date and to_date:
            if from_date >= to_date:
                raise serializers.ValidationError("to_date must be greater than from_date, and they cannot be the same.")

        return data
 
    
    def get_worked_hours(self, obj):
        """
        Fetch the total approved worked hours dynamically for each project and format it as 'HH:MM'.
        """

        # Aggregate the total approved worked hours for the project
        total_time = EmployeeTimesheet.objects.filter(
            project_code=obj.project_code,
            status='approved'  # Filter for approved timesheets
        ).aggregate(Sum('worked_hours'))['worked_hours__sum']

        if total_time is None:
            return "00:00"  # Default if no approved hours logged

        if isinstance(total_time, timedelta):
            total_seconds = int(total_time.total_seconds())  # Convert timedelta to seconds
        elif isinstance(total_time, (float, int)):
            total_seconds = int(total_time * 3600)  # Convert float hours to seconds
        else:
            raise ValueError(f"Unexpected data type for worked_hours: {type(total_time)}")

        # Convert total seconds to HH:MM (Handling values greater than 24 hours)
        days, remainder = divmod(total_seconds, 86400)  # Extract days
        hours, remainder = divmod(remainder, 3600)  # Extract hours
        minutes, _ = divmod(remainder, 60)  # Ignore seconds

        # Add extra hours from days (1 day = 24 hours)
        hours += days * 24

        return f"{hours}:{minutes:02d}"



class EditProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'
    
        # extra_kwargs = {
        #     'project_code': {'read_only': True}
        # }
    def validate_client_name(self, value):
        """
        Ensure client_name contains only letters and spaces.
        """
        if not re.match(r'^[A-Za-z ]+$', value):
            raise serializers.ValidationError("Client name should contain only alphabetic characters and spaces.")
        return value
    
    def validate(self, data):
        """Validate that to_date is greater than from_date."""
        from_date = data.get("from_date")
        to_date = data.get("to_date")

        if from_date and to_date:
            if from_date >= to_date:
                raise serializers.ValidationError("to_date must be greater than from_date, and they cannot be the same.")

        return data
    # def validate_delivery_head(self, value):
    #     if value and not re.match(r'^[A-Za-z ]+$', value):
    #         raise serializers.ValidationError("Delivery head should contain only alphabetic characters and spaces.")
    #     return value
    
    # def validate_sbu_head(self, value):
    #     if value and not re.match(r'^[A-Za-z ]+$', value):
    #         raise serializers.ValidationError("SBU Head should contain only alphabetic characters and spaces.")
    #     return value

    # def validate_management(self, value):
    #     if value and not re.match(r'^[A-Za-z ]+$', value):
    #         raise serializers.ValidationError("Management should contain only alphabetic characters and spaces.")
    #     return value
    def validate_management(self, value):
        # Same default logic for updates as well
        if not value or value.strip() == "":
            return "Sudhakara Varma Yarramraju"
        if not re.match(r'^[A-Za-z ]+$', value):
            raise serializers.ValidationError("Management should contain only alphabetic characters and spaces.")
        return value

    

class ProjectTeamSerializer(serializers.ModelSerializer):
    project_code = serializers.CharField(source='project_code.project_code')
    employee_code = serializers.CharField(source='employee_code.employee_code')
    project_role = serializers.IntegerField(source='project_role.id')
    project_role_name = serializers.CharField(source='project_role.project_role')
    task = serializers.IntegerField(source='task.task_code') 
    joining_date = serializers.DateField(source='employee_code.joining_date', format="%Y-%m-%d", read_only=True)
    phase_name = serializers.CharField(source='task.task_group')
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    class Meta:
        model = ProjectTeam
        fields = [
            'id', 'employee_name', 'designation', 'start_date', 'end_date',
            'allocated_hours', 'project_code', 'employee_code',
            'project_role', 'project_role_name', 'joining_date', 'task', 'phase_name', 'created_at', 'updated_at'
        ]

    def validate_allocated_hours(self, value):
        """Ensure allocated_hours do not exceed the project's budgeted_hours."""
        project = self.instance.project if self.instance else self.initial_data.get('project')

        if not project:
            raise serializers.ValidationError("Project is required.")

        # Retrieve project instance if only project ID is provided
        if isinstance(project, int):
            project = Project.objects.get(id=project)

        total_allocated_hours = ProjectTeam.objects.filter(project=project).exclude(id=self.instance.id if self.instance else None).aggregate(total_hours=models.Sum('allocated_hours'))['total_hours'] or 0

        if total_allocated_hours + value > project.budgeted_hours:
            raise serializers.ValidationError(f"Total allocated hours ({total_allocated_hours + value}) exceed the project's budgeted hours ({project.budgeted_hours}).")

        return value
    
    
class ProjectTeamCreateSerializer(serializers.ModelSerializer):
    allocated_hours = serializers.FloatField(required=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = ProjectTeam
        fields = '__all__'

    def validate(self, data):
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        allocated_hours = data.get("allocated_hours")

        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError("end_date must be greater than start_date.")

        if allocated_hours is not None and allocated_hours < 0:
            raise serializers.ValidationError("Allocated hours must be a positive number.")
            

        return data
    
    # def update(self, instance, validated_data):

    #     # Get original employee_code (before update)
    #     original_employee_code = instance.employee_code.employee_code

    #     # Check if employee_code is being changed
    #     new_employee_code = validated_data.get('employee_code', {}).get('employee_code')

    #     # If timesheets exist and employee_code is changing, raise error
    #     if new_employee_code and new_employee_code != original_employee_code:
    #         if EmployeeTimesheet.objects.filter(employee_code=original_employee_code).exists():
    #             raise serializers.ValidationError({
    #                 "error": f"Cannot update employee_code for ProjectTeam id {instance.id}, timesheet entries already exist."
    #             })

    #     # Allow updating start_date, end_date, and allocated_hours
    #     instance.start_date = validated_data.get('start_date', instance.start_date)
    #     instance.end_date = validated_data.get('end_date', instance.end_date)
    #     instance.allocated_hours = validated_data.get('allocated_hours', instance.allocated_hours)

    #     # Update other fields only if timesheets do not exist
    #     if not EmployeeTimesheet.objects.filter(employee_code=original_employee_code).exists():
    #         for attr, value in validated_data.items():
    #             if attr not in ['start_date', 'end_date', 'allocated_hours']:
    #                 setattr(instance, attr, value)

    #     instance.save()
    #     return instance

    # def update(self, instance, validated_data):
    #     new_task = validated_data.get("task", instance.task)
    #     new_employee_name = validated_data.get("employee_name", instance.employee_name)
    #     new_allocated_hours = validated_data.get("allocated_hours", instance.allocated_hours)

    #     timesheet_exists = EmployeeTimesheet.objects.filter(
    #         employee_code=instance.employee_code,
    #         task_description=instance.task
    #     ).exists()

    #     # if timesheet_exists:
    #     #     if new_task != instance.task:
    #     #         raise serializers.ValidationError("Task cannot be changed once a timesheet exists.")
    #     #     if new_employee_name != instance.employee_name:
    #     #         raise serializers.ValidationError("Employee name cannot be changed once a timesheet exists.")

    #     if new_allocated_hours != instance.allocated_hours:
    #         phase_allocation = PhaseAllocation.objects.filter(
    #             task=instance.task, project_code=instance.project_code
    #         ).first()
    #         if phase_allocation:
    #             delta = new_allocated_hours - instance.allocated_hours
    #             phase_allocation.allocated_hours += delta
    #             phase_allocation.save(update_fields=["allocated_hours"])

    #     return super().update(instance, validated_data)

    # def save(self, *args, **kwargs):
    #     instance = super().save(*args, **kwargs)
    #     if not self.instance:  # On create
    #         if instance.task and instance.project_code:
    #             PhaseAllocation.objects.filter(
    #                 task=instance.task, project_code=instance.project_code
    #             ).update(allocated_hours=F("allocated_hours") + instance.allocated_hours)
    #     return instance
    
# class PhaseAllocationSerializer(serializers.ModelSerializer):
#     phase_name = serializers.CharField(source="task.task_group", read_only=True)
#     project_name = serializers.CharField(source="project_code.project_name", read_only=True)

#     def create(self, validated_data):
#         task = validated_data.get("task")
#         project_code = validated_data.get("project_code")

#         total_allocated = ProjectTeam.objects.filter(task=task, project_code=project_code).aggregate(
#             total=Sum('allocated_hours')
#         )['total'] or 0

#         validated_data["allocated_hours"] = total_allocated
#         return super().create(validated_data)


#     def validate_allocated_hours(self, value):
#         if value < 0:
#             raise serializers.ValidationError("Allocated hours must be positive.")
#         if self.instance and value > self.instance.budgeted_hours:
#             raise serializers.ValidationError("Allocated hours cannot exceed budgeted hours.")
#         return value

#     class Meta:
#         model = PhaseAllocation
#         fields = [
#             "id", "task", "phase_name", "project_code", "project_name",
#             "budgeted_hours", "allocated_hours", "worked_hours"
#         ]

class PhaseAllocationSerializer(serializers.ModelSerializer):
    phase_name = serializers.CharField(source="task.task_group", read_only=True)
    project_name = serializers.CharField(source="project_code.project_name", read_only=True)

    class Meta:
        model = PhaseAllocation
        fields = [
            "id", "task", "phase_name", "project_code", "project_name",
            "budgeted_hours", "allocated_hours", "worked_hours","start_date","end_date"
        ]
        def validate(self, attrs):
            start_date = attrs.get("start_date")
            end_date = attrs.get("end_date")
            project_code = attrs.get("project_code")
            task = attrs.get("task")

            if not start_date:
                raise serializers.ValidationError({"start_date": "Start date is required."})
            if not end_date:
                raise serializers.ValidationError({"end_date": "End date is required."})

            if start_date > end_date:
                raise serializers.ValidationError({
                    "end_date": "End date cannot be earlier than start date."
                })
            if not project_code:
                raise serializers.ValidationError({"project_code": "Project code is required."})

            try:
                project = Project.objects.get(project_code=project_code)
            except Project.DoesNotExist:
                raise serializers.ValidationError({
                    "project_code": f"Project '{project_code}' does not exist."
                })
            if start_date < project.from_date:
                raise serializers.ValidationError({
                    "start_date": f"Start date cannot be before project start date ({project.from_date})."
                })

            if end_date > project.to_date:
                raise serializers.ValidationError({
                    "end_date": f"End date cannot be after project end date ({project.to_date})."
                })
        
            phase_name = task.task_group if hasattr(task, "task_group") else None
            if phase_name:
                qs = PhaseAllocation.objects.filter(
                    project_code=project_code,
                    task__task_group=phase_name
                )
                # Exclude current instance in updates
                if self.instance:
                    qs = qs.exclude(id=self.instance.id)
                if qs.exists():
                    raise serializers.ValidationError({
                        "phase_name": f"Phase '{phase_name}' already exists for this project."
                    })
            return attrs

    def compute_allocated_hours(self, task, project_code):
        return ProjectTeam.objects.filter(
            task=task, project_code=project_code
        ).aggregate(total=Sum("allocated_hours"))["total"] or 0

    def compute_worked_hours(self, task, project_code):
        employee_code = self.context.get("employee_code", None)

        filters = {
            "project_code": project_code,
            "task_description": task,
            "status": "approved"
        }

        if employee_code:
            filters["employee_code__employee_code"] = employee_code

        total_time = EmployeeTimesheet.objects.filter(**filters).aggregate(
            total=Sum("worked_hours")
        )["total"]

        if total_time:
            total_seconds = int(total_time.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{hours}:{minutes:02}"
        return "00:00"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["allocated_hours"] = self.compute_allocated_hours(
            instance.task, instance.project_code
        )
        data["worked_hours"] = self.compute_worked_hours(
            instance.task, instance.project_code
        )
    
        return data




class PhaseAllocationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhaseAllocation
        fields = ["task", "project_code", "budgeted_hours","start_date","end_date"]


# class PhaseAllocationSerializer(serializers.ModelSerializer):
#     phase_name = serializers.CharField(source="task.task_group", read_only=True)
#     project_name = serializers.CharField(source="project_code.project_name", read_only=True)
#     worked_hours = serializers.SerializerMethodField()

#     def create(self, validated_data):
#         task = validated_data.get("task")
#         project_code = validated_data.get("project_code")

#         # Fetch allocated_hours from ProjectTeam
#         project_team = ProjectTeam.objects.filter(task=task, project_code=project_code).first()

#         if project_team:
#             validated_data["allocated_hours"] = project_team.allocated_hours  # Correctly assign allocated_hours
#         else:
#             validated_data["allocated_hours"] = 0  # Default if no project team exists

#         # Create PhaseAllocation
#         return super().create(validated_data)

#     def get_worked_hours(self, obj):
#         """
#         Fetch and sum total approved worked hours for this phase (task + project_code).
#         """
#         # Ensure you are filtering with the correct foreign key name
#         total_time = EmployeeTimesheet.objects.filter(
#             project_code=obj.project_code,
#             task_description=obj.task,  # Use task_description instead of task if needed
#             status="approved"
#         ).aggregate(Sum("worked_hours"))["worked_hours__sum"]

#         if total_time is None:
#             return "00:00"

#         if isinstance(total_time, timedelta):
#             total_seconds = int(total_time.total_seconds())  # Convert timedelta to total seconds
#         elif isinstance(total_time, (float, int)):
#             total_seconds = int(total_time * 3600)  # Convert float hours to seconds
#         else:
#             return "00:00"  # Default fallback

#         # Convert total seconds to HH:MM format
#         hours, remainder = divmod(total_seconds, 3600)
#         minutes, _ = divmod(remainder, 60)

#         return f"{hours:02}:{minutes:02}"  # Return HH:MM format

#     def validate_allocated_hours(self, value):
#         """Ensure allocated_hours does not exceed budgeted_hours."""
#         if value < 0:
#             raise serializers.ValidationError("Allocated hours must be a positive number.")
#         if self.instance and value > self.instance.budgeted_hours:
#             raise serializers.ValidationError("Allocated hours cannot exceed budgeted hours.")
#         return value

#     class Meta:
#         model = PhaseAllocation
#         fields = ["id", "task", "phase_name", "project_code", "project_name", "budgeted_hours", "allocated_hours", "worked_hours"]
# class PhaseAllocationUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PhaseAllocation
#         fields = ["task", "project_code", "budgeted_hours"]

class PMODetailSerializer(serializers.Serializer):
    phase = serializers.CharField()
    taskDescription = serializers.CharField()
    workedHours = serializers.CharField()
    remarks = serializers.CharField()
    status = serializers.CharField()


class PMOLogSerializer(serializers.Serializer):
    totalHours = serializers.CharField()
    details = PMODetailSerializer(many=True)


class PMOEmployeeSerializer(serializers.Serializer):
    employeeCode = serializers.CharField()
    employeeName = serializers.CharField()
    log = serializers.DictField(child=PMOLogSerializer())
    total = serializers.CharField()
    average = serializers.CharField()


class ProjectTeamAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectTeamAllocation
        fields = ['employee_code', 'project_code', 'allocation_percent']

    def validate_allocation_percent(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Allocation percent must be between 0 and 100.")
        return value

    def validate(self, data):
        employee = data.get('employee_code')
        project = data.get('project_code')
        new_alloc = data.get('allocation_percent')

        # Get active project codes for this employee from ProjectTeam
        active_project_codes = ProjectTeam.objects.filter(
            employee_code=employee
        ).values_list('project_code', flat=True)

        # Filter allocations only for active project assignments
        qs = ProjectTeamAllocation.objects.filter(
            employee_code=employee,
            project_code__in=active_project_codes
        )

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        total_alloc = qs.aggregate(total=Coalesce(Sum('allocation_percent'), 0))['total']

        if total_alloc + new_alloc > 100:
            raise serializers.ValidationError(
                f"Total allocation percent exceeds 100%. "
                f"Current total from active projects: {total_alloc}%, new allocation: {new_alloc}%."
            )

        return data

class ProjectEmployeeDetailsSerializer(serializers.Serializer):
    employee_code = serializers.CharField(read_only=True)
    employee_name = serializers.CharField(read_only=True)
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    allocation_percent = serializers.SerializerMethodField()
    allocated_hours = serializers.IntegerField(read_only=True)
    worked_hours = serializers.SerializerMethodField()
    pending_hours = serializers.SerializerMethodField()
    balance_hours = serializers.SerializerMethodField()

    def get_start_date(self, obj):
        """Get min start date across ALL phases for this employee in project"""
        employee_code = obj['employee_code']
        project_code = obj['project_code']
        
        # Get the absolute minimum start date across all phases
        phase_dates = ProjectTeam.objects.filter(
            employee_code__employee_code=employee_code,
            project_code__project_code=project_code
        ).aggregate(min_start=Min('start_date'))
        
        return phase_dates['min_start'].strftime('%Y-%m-%d') if phase_dates['min_start'] else None

    def get_end_date(self, obj):
        """Get max end date across ALL phases for this employee in project"""
        employee_code = obj['employee_code']
        project_code = obj['project_code']
        
        # Get the absolute maximum end date across all phases
        phase_dates = ProjectTeam.objects.filter(
            employee_code__employee_code=employee_code,
            project_code__project_code=project_code
        ).aggregate(max_end=Max('end_date'))
        
        return phase_dates['max_end'].strftime('%Y-%m-%d') if phase_dates['max_end'] else None

    def get_allocation_percent(self, obj):
        """Fetch allocation % for this employee in this project."""
        employee_code = obj['employee_code']
        project_code = obj['project_code']

        allocation = ProjectTeamAllocation.objects.filter(
            employee_code__employee_code=employee_code,
            project_code__project_code=project_code
        ).first()
        return allocation.allocation_percent if allocation else 0

    def get_worked_hours(self, obj):
        """Sum all approved worked hours for this employee in this project."""
        employee_code = obj['employee_code']
        project_code = obj['project_code']

        total_time = EmployeeTimesheet.objects.filter(
            employee_code__employee_code=employee_code,
            project_code__project_code=project_code,
            status='approved'
        ).aggregate(Sum('worked_hours'))['worked_hours__sum']

        if not total_time:
            return "00:00"

        if isinstance(total_time, timedelta):
            total_seconds = int(total_time.total_seconds())
        elif isinstance(total_time, (float, int)):
            total_seconds = int(total_time * 3600)
        else:
            return "00:00"

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}:{minutes:02d}"

    def get_pending_hours(self, obj):
        """Calculate not approved hours (total submitted hours - approved hours)"""
        employee_code = obj['employee_code']
        project_code = obj['project_code']

        # Get total submitted hours (all statuses except maybe 'draft' if you have that)
        total_submitted_time = EmployeeTimesheet.objects.filter(
            employee_code__employee_code=employee_code,
            project_code__project_code=project_code
        ).exclude(status='draft').aggregate(Sum('worked_hours'))['worked_hours__sum']

        # Get approved hours (convert from existing method)
        worked_hours_str = self.get_worked_hours(obj)
        
        # Convert "HH:MM" to decimal hours for approved hours
        if worked_hours_str != "00:00":
            hours, minutes = worked_hours_str.split(':')
            approved_hours = int(hours) + (int(minutes) / 60)
        else:
            approved_hours = 0

        # Convert total submitted time to decimal hours
        if total_submitted_time:
            if isinstance(total_submitted_time, timedelta):
                total_seconds = int(total_submitted_time.total_seconds())
                total_submitted_hours = total_seconds / 3600
            elif isinstance(total_submitted_time, (float, int)):
                total_submitted_hours = total_submitted_time
            else:
                total_submitted_hours = 0
        else:
            total_submitted_hours = 0

        # Pending hours = total submitted hours - approved hours
        pending_hours = total_submitted_hours - approved_hours
        
        # Ensure pending hours is not negative
        return max(0, round(pending_hours, 2))
    
    def get_balance_hours(self, obj):
        employee_code = obj['employee_code']
        project_code = obj['project_code']
        allocated_hours = obj.get('allocated_hours', 0) or 0

        # Approved timesheets
        approved_time = EmployeeTimesheet.objects.filter(
            employee_code__employee_code=employee_code,
            project_code__project_code=project_code,
            status='approved'
        ).aggregate(
            total=Coalesce(Sum('worked_hours'), Value(timedelta()))
        )['total']

        # Open timesheets
        open_time = EmployeeTimesheet.objects.filter(
            employee_code__employee_code=employee_code,
            project_code__project_code=project_code,
            status='open'
        ).aggregate(
            total=Coalesce(Sum('worked_hours'), Value(timedelta()))
        )['total']

        # Convert to hours
        approved_hours = approved_time.total_seconds() / 3600 if approved_time else 0
        open_hours = open_time.total_seconds() / 3600 if open_time else 0

        total_worked_hours = approved_hours + open_hours

        # Balance = Allocated − (Approved + Open)
        balance_hours = allocated_hours - total_worked_hours

        return round(balance_hours, 2)