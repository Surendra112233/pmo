from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.core.validators import MinValueValidator
from master_data.models import Company, Supplier, AssetCategories, Status


def default_from_date():
    return timezone.now().date()


class SoftwareAssignment(models.Model):
    asset_type = models.CharField(max_length=10)
    asset_category = models.CharField(max_length=40)
    asset_sub_category = models.CharField(max_length=40)
    software_name = models.CharField(max_length=40)
    minimum_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    product_key = models.CharField(max_length=50, null=True, blank=True)
    asset_tag = models.CharField(max_length=30)
    company = models.CharField(max_length=50)
    licensed_email = models.EmailField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=60)
    user_name = models.CharField(max_length=40)
    from_date = models.DateField(default=default_from_date)
    to_date = models.DateField(null=True, blank=True)  # READ-ONLY
    notes = models.CharField(max_length=80, null=True, blank=True)
    location = models.CharField(max_length=60)
    image = models.FileField(upload_to="software_images/", null=True, blank=True)
    warranty_start_date = models.DateField(null=True, blank=True)
    warranty_end_date = models.DateField(null=True, blank=True)
    check_in_date = models.DateField(null=True, blank=True)
    byod = models.BooleanField(default=False)
    order_number = models.CharField(max_length=20, null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    supplier = models.CharField(max_length=40, null=True, blank=True)
    purchase_cost = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=20, null=True, blank=True)  # NEW FIELD
    invoice_copy = models.FileField(upload_to="invoices/", null=True, blank=True)
    admin_user_name = models.CharField(max_length=50)
    admin_password = models.CharField(max_length=255)
    last_changed_by = models.CharField(max_length=50, default='system')  # READ-ONLY
    last_changed_datetime = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # ---------------- Additional Software Fields ----------------

    roboxa_asset_id = models.CharField(max_length=100)
    amc_start_date = models.DateField(null=True, blank=True)
    amc_end_date = models.DateField(null=True, blank=True)
    amc_vendor = models.CharField(max_length=100, null=True, blank=True)
    warranty_status = models.CharField(max_length=30, null=True, blank=True)


    class Meta:
        db_table = "software_assignment"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.software_name} - {self.asset_tag}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class SoftwareAssignmentHistory(models.Model):
    assignment = models.ForeignKey(SoftwareAssignment, on_delete=models.CASCADE, related_name="history")
    status = models.CharField(max_length=60)
    user_name = models.CharField(max_length=40)
    from_date = models.DateField(default=default_from_date)
    to_date = models.DateField(null=True, blank=True)  # READ-ONLY
    last_changed_by = models.CharField(max_length=50, default='system')  # READ-ONLY
    last_changed_datetime = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "software_assignment_history"
        ordering = ["-from_date"]

    def __str__(self):
        return f"{self.assignment} - {self.user_name}"
