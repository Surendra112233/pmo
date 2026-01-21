from django.db import models
from django.utils import timezone


class ApprovalHistory(models.Model):

    LEVEL_CHOICES = [
        ("PM", "Project Manager"),
        ("DELIVERY", "Delivery Head"),
        ("SBU", "SBU Head"),
    ]

    ACTION_CHOICES = [
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    travel_request = models.ForeignKey(
        "TravelRequest",
        on_delete=models.CASCADE,
        related_name="approval_history"
    )

    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    action_by = models.CharField(max_length=100)
    remarks = models.TextField(blank=True, null=True)

    action_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.travel_request.request_id} - {self.level} - {self.action}"

class TravelRequest(models.Model):
    employee_code = models.CharField(max_length=20)
    employee_name = models.CharField(max_length=100)
    department = models.CharField(max_length=50)

    project_type = models.CharField(max_length=50)
    project_code = models.CharField(max_length=50)
    project_name = models.CharField(max_length=100)
    country = models.CharField(max_length=30)

    project_manager = models.CharField(max_length=100)
    delivery_manager = models.CharField(max_length=100)
    sbu_head = models.CharField(max_length=100)

    request_id = models.AutoField(primary_key=True)  # kept as requested

    travel_location = models.CharField(max_length=50)
    travel_purpose = models.CharField(max_length=50)
    others_specify = models.CharField(max_length=100, blank=True, null=True)

    travel_preferences = models.CharField(max_length=50, blank=True, null=True)
    request_raised_by = models.CharField(max_length=100)
    accommodation_required = models.BooleanField(default=False)

    STATUS_CHOICES = [
       ('Submitted', 'Submitted'),
    ('PM Approved', 'PM Approved'),
    ('Delivery Approved', 'Delivery Approved'),
    ('SBU Approved', 'SBU Approved'),
    ('Rejected', 'Rejected'),

    ]
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Submitted')

    def __str__(self):
        return f"{self.employee_name} - {self.request_id}"

class TravelDetails(models.Model):
    travel_request = models.ForeignKey(
        TravelRequest,
        on_delete=models.CASCADE,
        related_name="travel_details"
    )

    departure_country = models.CharField(max_length=30)
    departure_from = models.CharField(max_length=30)
    departure_date = models.DateField()
    departure_time = models.TimeField()

    arrival_country = models.CharField(max_length=30)
    arrival_to = models.CharField(max_length=30)
    arrival_date = models.DateField()
    arrival_time = models.TimeField()

    MODE_CHOICES = [
        ('Flight', 'Flight'),
        ('Train', 'Train'),
        ('Road', 'Road'),
    ]
    mode = models.CharField(max_length=10, choices=MODE_CHOICES)
    
    PAYMENT_BY_CHOICES = [
        ('Company', 'Company'),
        ('Self', 'Self'),
    ]
    payment_by = models.CharField(
        max_length=10, choices=PAYMENT_BY_CHOICES, blank=True, null=True
    )

class AccommodationDetails(models.Model):
    travel_request = models.ForeignKey(
        TravelRequest,
        on_delete=models.CASCADE,
        related_name="accommodation"
    )

    accommodation_type = models.CharField(max_length=20, blank=True, null=True)
    check_in = models.DateField(blank=True, null=True)
    check_out = models.DateField(blank=True, null=True)
    no_of_days = models.IntegerField(blank=True, null=True)
    city = models.CharField(max_length=30, blank=True, null=True)
    payment_to = models.CharField(max_length=20, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

class PersonalDetails(models.Model):
    travel_request = models.OneToOneField(
        TravelRequest,
        on_delete=models.CASCADE,
        related_name="personaldetails"
    )

    date_of_birth = models.DateField()
    age = models.IntegerField()
    id_document_type = models.CharField(max_length=30)
    id_document_number = models.CharField(max_length=20)

    passport_number = models.CharField(max_length=20, blank=True, null=True)

    mobile = models.CharField(max_length=12)
    alt_mobile = models.CharField(max_length=12, blank=True, null=True)

    email = models.EmailField()
    alt_email = models.EmailField(blank=True, null=True)

    address = models.CharField(max_length=100)
    comments = models.TextField(blank=True, null=True)
