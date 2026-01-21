from django.db import models
from django.contrib.auth.hashers import make_password
from master_data.models import Company, Supplier, AssetCategories, AssetModel
from django.utils import timezone

# ----------------- Default functions for migrations -----------------
def default_from_date():
    return timezone.now().date()

def default_to_date():
    return None  # Keep NULL unless explicitly set

class HardwareAssignment(models.Model):
    # ---------------- General Data ----------------
    asset_type = models.CharField(max_length=10, null=False, blank=False)
    asset_category = models.CharField(max_length=40, null=False, blank=False)
    asset_sub_category = models.CharField(max_length=40, null=False, blank=False)
    asset_name = models.CharField(max_length=40, null=False, blank=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    asset_tag = models.CharField(max_length=30, null=False, blank=False)
    serial_number = models.CharField(max_length=30, null=False, blank=False)
    model = models.ForeignKey(AssetModel, on_delete=models.CASCADE, related_name='hardware_assignments')
    status = models.CharField(max_length=20, null=False, blank=False)
    user_name = models.CharField(max_length=40, null=False, blank=False)
    from_date = models.DateField(default=default_from_date)  # CHANGED: Added default
    to_date = models.DateField(default=default_to_date, null=True, blank=True)  # CHANGED: Added default
    notes = models.CharField(max_length=80, null=True, blank=True)
    location = models.CharField(max_length=60, null=False, blank=False)
    image = models.FileField(upload_to='hardware/images/', null=False, blank=False)
    
    # ---------------- Optional Info ----------------
    warranty_start_date = models.DateField(null=True, blank=True)
    warranty_end_date = models.DateField(null=True, blank=True)
    check_in_date = models.DateField(null=True, blank=True)
    byod = models.BooleanField(default=False)

    # ---------------- Order Info ----------------
    order_number = models.CharField(max_length=20, null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.SET_NULL)
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='INR', null=False, blank=False)  # ADD THIS LINE
    invoice_copy = models.FileField(upload_to='hardware/invoices/', null=True, blank=True)

    # ---------------- Admin Credentials ----------------
    admin_user_name = models.CharField(max_length=50, null=False, blank=False)
    admin_password = models.CharField(max_length=255, null=False, blank=False)

    # ---------------- Current Assignment Details ----------------
    assignment_user_name = models.CharField(max_length=50, null=True, blank=True)
    assignment_status = models.CharField(max_length=50, null=True, blank=True)
    assignment_from_date = models.DateField(null=True, blank=True)
    assignment_to_date = models.DateField(null=True, blank=True)

    # ---------------- Audit Info ----------------
    last_changed_by = models.CharField(max_length=50, null=False, blank=False)
    last_changed_datetime = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ---------------- Additional Hardware Fields ----------------

    roboxa_asset_id = models.CharField(max_length=100, default='TEMP_ASSET')  # mandatory
    configuration_details = models.TextField(blank=True, null=True)  # optional
    transfer_from = models.CharField(max_length=100, blank=True, null=True)  # optional
    transfer_from_date = models.DateField(null=True, blank=True)  # optional
    transfer_to_date = models.DateField(null=True, blank=True)    # optional
    transfer_to = models.CharField(max_length=100, blank=True, null=True)  # optional
    external = models.BooleanField(default=False)  # checkbox
    amc_start_date = models.DateField(null=True, blank=True)
    amc_end_date = models.DateField(null=True, blank=True)
    amc_vendor = models.CharField(max_length=100, null=True, blank=True)
    warranty_status = models.CharField(max_length=30, null=True, blank=True)


    def __str__(self):
        return f"{self.asset_name} assigned to {self.user_name}"

    def save(self, *args, **kwargs):
        
        super().save(*args, **kwargs)


class AssignmentHistory(models.Model):
    """
    Separate model to track complete assignment history
    """
    hardware_assignment = models.ForeignKey(
        HardwareAssignment, 
        on_delete=models.CASCADE, 
        related_name='assignment_history'
    )
    user_name = models.CharField(max_length=50, null=False, blank=False)
    status = models.CharField(max_length=50, null=False, blank=False)
    from_date = models.DateField(default=default_from_date)  # CHANGED: Added default
    to_date = models.DateField(default=default_to_date, null=True, blank=True)  # CHANGED: Added default
    changed_by = models.CharField(max_length=50, null=False, blank=False)
    changed_datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Assignment History"
        verbose_name_plural = "Assignment Histories"
        ordering = ['-from_date', '-changed_datetime']

    def __str__(self):
        return f"{self.hardware_assignment.asset_name} - {self.user_name} ({self.from_date} to {self.to_date})"