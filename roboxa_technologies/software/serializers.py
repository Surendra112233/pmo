from rest_framework import serializers
from django.utils import timezone
from datetime import datetime
from decimal import Decimal, InvalidOperation
from .models import SoftwareAssignment, SoftwareAssignmentHistory
from master_data.models import Company, Supplier, AssetCategories, Status


def default_from_date():
    return timezone.now().date()


def default_to_date():
    return None  # Keep NULL unless explicitly set


class SoftwareAssignmentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SoftwareAssignmentHistory
        fields = '__all__'


class SoftwareAssignmentSerializer(serializers.ModelSerializer):
    image = serializers.FileField(required=False, allow_null=True)
    invoice_copy = serializers.FileField(required=False, allow_null=True)

    from_date = serializers.DateField(default=default_from_date, required=False)
    to_date = serializers.DateField(default=default_to_date, read_only=True)
    last_changed_by = serializers.CharField(read_only=True)

    # Required fields
    asset_type = serializers.CharField(required=True)
    asset_category = serializers.CharField(required=True)
    asset_sub_category = serializers.CharField(required=True, allow_blank=False)
    software_name = serializers.CharField(required=True)
    minimum_quantity = serializers.IntegerField(required=True)
    asset_tag = serializers.CharField(required=True)
    company = serializers.CharField(required=True)
    status = serializers.CharField(required=True)
    user_name = serializers.CharField(required=True)
    location = serializers.CharField(required=True)
    admin_user_name = serializers.CharField(required=True)
    admin_password = serializers.CharField(required=True)

    # Optional fields
    product_key = serializers.CharField(required=False, allow_blank=True)
    licensed_email = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    purchase_cost = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, allow_null=True)
    warranty_start_date = serializers.DateField(required=False, allow_null=True)
    warranty_end_date = serializers.DateField(required=False, allow_null=True)
    check_in_date = serializers.DateField(required=False, allow_null=True)
    purchase_date = serializers.DateField(required=False, allow_null=True)
    supplier = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    # ---------------- Additional Software Fields ----------------

    roboxa_asset_id = serializers.CharField(required=True, allow_blank=False)
    amc_start_date = serializers.DateField(required=False, allow_null=True)
    amc_end_date = serializers.DateField(required=False, allow_null=True)
    amc_vendor = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    warranty_status = serializers.CharField(required=False, allow_blank=True, allow_null=True)


    class Meta:
        model = SoftwareAssignment
        fields = '__all__'
        read_only_fields = [
            'id', 'last_changed_by', 'last_changed_datetime',
            'created_at', 'updated_at', 'to_date',
            'image_url', 'invoice_url'
        ]

    #  MOVED INSIDE SERIALIZER (THIS IS CRITICAL)
    def validate_image(self, value):
        if not value:
            return value

        allowed_extensions = ['jpg', 'jpeg', 'pdf']
        ext = value.name.split('.')[-1].lower()

        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                "Image must be JPG, JPEG, or PDF."
            )
        return value

    #  ADDED FOR INVOICE FILES
    def validate_invoice_copy(self, value):
        if not value:
            return value

        allowed_extensions = ['jpg', 'jpeg', 'pdf']
        ext = value.name.split('.')[-1].lower()

        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                "Invoice must be JPG, JPEG, or PDF."
            )
        return value

    def _is_update_operation(self):
        request = self.context.get('request')
        return (
            hasattr(self, 'instance') and
            self.instance is not None and
            request and
            request.method in ['PUT', 'PATCH']
        )

    def validate_string_field(self, value, field_name, max_length, mandatory=True):
        if mandatory and not value:
            raise serializers.ValidationError(f"{field_name} is mandatory.")
        if value and len(str(value)) > max_length:
            raise serializers.ValidationError(f"{field_name} cannot exceed {max_length} characters.")
        return str(value).strip() if value else None

    def validate_decimal_field(self, value, field_name):
        if value in (None, ''):
            return None
        try:
            return Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            raise serializers.ValidationError(f"{field_name} must be a valid decimal number.")

    def validate_integer_field(self, value, field_name):
        try:
            return int(value)
        except (ValueError, TypeError):
            raise serializers.ValidationError(f"{field_name} must be an integer.")

    def validate_date_field(self, value, field_name):
        if not value:
            return None
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except Exception:
                raise serializers.ValidationError(f"{field_name} must be in YYYY-MM-DD format.")
        if isinstance(value, datetime):
            return value.date()
        return value

    def validate(self, attrs):
        is_update = self._is_update_operation()

        # ---------------- Date validation ----------------
        if attrs.get('from_date') and attrs.get('to_date') and attrs['from_date'] > attrs['to_date']:
            raise serializers.ValidationError({"to_date": "To Date cannot be earlier than From Date."})

        string_fields = {
            'asset_type': 50, 'asset_category': 50, 'asset_sub_category': 50,
            'software_name': 50, 'product_key': 50, 'asset_tag': 30,
            'licensed_email': 50, 'user_name': 50, 'notes': 200,
            'location': 60, 'order_number': 20,
            'admin_user_name': 50, 'admin_password': 255,
            'status': 50, 'company': 50, 'supplier': 50,
            'roboxa_asset_id': 100, 'amc_vendor': 100, 'warranty_status': 30,
        }

        mandatory_fields = [
            'asset_type', 'asset_category', 'asset_sub_category',
            'software_name', 'minimum_quantity', 'asset_tag',
            'company', 'status', 'user_name', 'location',
            'admin_user_name', 'admin_password', 'from_date', 'image',
            'roboxa_asset_id'
        ]

        for field, max_len in string_fields.items():
            if field in attrs:
                mandatory = (field in mandatory_fields) and not is_update
                attrs[field] = self.validate_string_field(
                    attrs.get(field),
                    field.replace('_', ' ').title(),
                    max_len,
                    mandatory
                )

        # ---------------- Integer/Decimal fields ----------------
        if 'minimum_quantity' in attrs and attrs.get('minimum_quantity') is not None:
            attrs['minimum_quantity'] = self.validate_integer_field(attrs['minimum_quantity'], 'Minimum Quantity')
            if attrs['minimum_quantity'] < 0:
                raise serializers.ValidationError({'minimum_quantity': "Minimum quantity cannot be negative."})

        if 'purchase_cost' in attrs:
            attrs['purchase_cost'] = self.validate_decimal_field(attrs['purchase_cost'], 'Purchase Cost')
            if attrs['purchase_cost'] is not None and attrs['purchase_cost'] < 0:
                raise serializers.ValidationError({'purchase_cost': "Purchase cost cannot be negative."})

        # ---------------- Foreign key validations ----------------
        if attrs.get('status') and not Status.objects.filter(status_name=attrs['status']).exists():
            raise serializers.ValidationError({"status": "Invalid status."})
        if attrs.get('company') and not Company.objects.filter(company=attrs['company']).exists():
            raise serializers.ValidationError({"company": "Invalid company."})
        if attrs.get('supplier') and attrs['supplier'] and not Supplier.objects.filter(supplier=attrs['supplier']).exists():
            raise serializers.ValidationError({"supplier": "Invalid supplier."})

        if attrs.get('asset_type') and attrs.get('asset_category'):
            if not AssetCategories.objects.filter(
                asset_type=attrs['asset_type'],
                asset_category=attrs['asset_category']
            ).exists():
                raise serializers.ValidationError({"asset_category": "Invalid asset category for this asset type."})

        if attrs.get('asset_category') and attrs.get('asset_sub_category'):
            if not AssetCategories.objects.filter(
                asset_category=attrs['asset_category'],
                asset_sub_category=attrs['asset_sub_category']
            ).exists():
                raise serializers.ValidationError({"asset_sub_category": "Invalid asset sub-category for this asset category."})

        # ---------------- History check ----------------
        if is_update and 'from_date' in attrs and attrs.get('from_date'):
            last_history = SoftwareAssignmentHistory.objects.filter(
                assignment=self.instance
            ).order_by('-from_date').first()

            if last_history and last_history.to_date and attrs['from_date'] < last_history.to_date:
                raise serializers.ValidationError({
                    'from_date': f"From date must be on/after last history's to_date ({last_history.to_date.isoformat()})."
                })

        return attrs


class SoftwareAssignmentUpdateSerializer(SoftwareAssignmentSerializer):
    asset_type = serializers.CharField(required=False, allow_blank=True)
    asset_category = serializers.CharField(required=False, allow_blank=True)
    asset_sub_category = serializers.CharField(required=False, allow_blank=True)
    software_name = serializers.CharField(required=False, allow_blank=True)
    minimum_quantity = serializers.IntegerField(required=False)
    asset_tag = serializers.CharField(required=False, allow_blank=True)
    company = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    user_name = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    admin_user_name = serializers.CharField(required=False, allow_blank=True)
    admin_password = serializers.CharField(required=False, allow_blank=True)
    roboxa_asset_id = serializers.CharField(required=False, allow_blank=True)
    amc_vendor = serializers.CharField(required=False, allow_blank=True)
    warranty_status = serializers.CharField(required=False, allow_blank=True)

