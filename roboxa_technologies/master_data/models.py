from django.db import models
from django.utils.timezone import now
from django.db.models import Q,  UniqueConstraint

class ProjectTasks(models.Model):
    task_code = models.AutoField(primary_key=True)
    project_type = models.CharField(max_length=30,null=False, blank=False)
    task_group = models.CharField(max_length=40,null=False, blank=False)
    description = models.CharField(max_length=100,null=False, blank=False) 
    created_at = models.DateTimeField(default=now, editable=False)  # Auto-set at creation
    updated_at = models.DateTimeField(auto_now=True)  # Auto-update on save

    def __str__(self):
        return f"{self.task_code} - {self.description}"


class Employee(models.Model):
    employee_code = models.CharField(max_length=10, unique=True, primary_key=True,null=False, blank=False)
    name = models.CharField(max_length=80,null=False, blank=False)
    designation = models.CharField(max_length=60,null=False, blank=False)
    country = models.CharField(max_length=60, null=False,blank=False)
    band_grade = models.CharField(max_length=4, null=False, blank=False)
    joining_date = models.DateField(null=False, blank=False)
    manager = models.CharField(max_length=80, null=True, blank=True)
    status = models.CharField(max_length=10,null=False,blank=False)
    created_at = models.DateTimeField(default=now, editable=False)  # Auto-set at creation
    updated_at = models.DateTimeField(auto_now=True)  # Auto-update on save
    relieving_date = models.DateField(null=True, blank=True)
    email = models.CharField(max_length=50,null=True,blank=True)
    mobile = models.CharField(max_length=15, null=True, blank=True) 
    primary_skill = models.JSONField(default=list) 
    secondary_skill = models.JSONField(default=list) 
    department=models.CharField(max_length=50, null=True, blank=True)
    contractor=models.CharField(max_length=20, null=True, blank=True)
    project_specific_hire=models.CharField(max_length=20, null=True, blank=True)
    # skill=models.CharField(max_length=50, null=True, blank=True)


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['email'],
                condition=~Q(email__isnull=True) & ~Q(email=''),
                name='unique_non_empty_email'
            )
        ]

    def save(self, *args, **kwargs):
        # Normalize email (for case-insensitive uniqueness)
        if self.email:
            self.email = self.email.strip().lower()
        else:
            self.email = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProjectRoles(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-generated ID field
    project_role = models.CharField(max_length=80, unique=True, null=False, blank=False)
    created_at = models.DateTimeField(default=now, editable=False)  # Auto-set at creation
    updated_at = models.DateTimeField(auto_now=True)  # Auto-update on save

    def __str__(self):
        return self.project_role



class AssetCategories(models.Model):

    asset_id = models.CharField(max_length=10, unique=True, editable=False)  
    asset_type = models.CharField(max_length=10, null=False, blank=False)  # Hardware / Software
    asset_category = models.CharField(max_length=40, null=False, blank=False)
    asset_sub_category = models.CharField(max_length=40, null=False, blank=False)
    created_at = models.DateTimeField(default=now, editable=False)  # Auto-set at creation
    updated_at = models.DateTimeField(auto_now=True)  # Auto-update on save

    
    class Meta:
        db_table = 'master_data_assetcategory'




class AssetModel(models.Model):
    asset_model_id = models.CharField(max_length=10, unique=True, editable=False)  # AM1, AM2...
    asset_model_code = models.CharField(max_length=15, null=False, blank=False)  # Mandatory, manual
    asset_model_name = models.CharField(max_length=40, null=False, blank=False)  # Mandatory
    created_at = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.asset_model_id} - {self.asset_model_name}"


class Status(models.Model):
    status_id = models.CharField(max_length=10, unique=True, editable=False)  # ST1, ST2...
    status_code = models.CharField(max_length=15, null=False, blank=False)     # Mandatory
    status_name = models.CharField(max_length=60, null=False, blank=False)    # Mandatory
    created_at = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.status_id} - {self.status_name}"
    
class Company(models.Model):
    id = models.AutoField(primary_key=True)
    company=models.CharField(max_length=50,null=False,blank=True)
    address=models.CharField(max_length=80,null=False,blank=True)
    country= models.CharField(null=False,blank=True)
    geo_region=models.CharField(null=False,blank=True)
    location_name = models.JSONField(default=list, blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at= models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company


class Supplier(models.Model):
    id = models.AutoField(primary_key=True) 
    supplier= models.CharField(max_length=40,null=False,blank=True)
    address=models.CharField(max_length=80,null=False,blank=True)
    country=models.CharField(null=False,blank=True)
    geo_region=models.CharField(null=False,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at= models.DateTimeField(auto_now=True)
    
    def __str__(self):
    
        return self.supplier




