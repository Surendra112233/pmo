from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta, datetime, date
from decimal import Decimal, InvalidOperation
import json
from .models import HardwareAssignment, AssignmentHistory
from master_data.models import Company, Supplier, AssetModel, AssetCategories
import re
 
# Add default functions for date fields (EXACT SAME AS SOFTWARE CODE)
def default_from_date():
    return timezone.now().date()
 
def default_to_date():
    return None  # Keep NULL unless explicitly set
 
class HardwareAssignmentSerializer(serializers.ModelSerializer):
    image = serializers.FileField(required=False, allow_null=True)
    invoice_copy = serializers.FileField(required=False, allow_null=True)
    image_url = serializers.SerializerMethodField(read_only=True)
    invoice_url = serializers.SerializerMethodField(read_only=True)
 
    # Update date fields with defaults (EXACT SAME AS SOFTWARE CODE)
    from_date = serializers.DateField(required=True)
    to_date = serializers.DateField(read_only=True)  # CHANGED: Made read_only
    assignment_from_date = serializers.DateField(read_only=True)  # CHANGED: Made read_only
    assignment_to_date = serializers.DateField(read_only=True)  # CHANGED: Made read_only
 
    # Make all fields required by default
    model = serializers.CharField(required=True)
    company = serializers.CharField(required=True)
    asset_category = serializers.CharField(required=True)
    asset_sub_category = serializers.CharField(required=True, allow_blank=False)
    supplier = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    asset_type = serializers.CharField(required=True, max_length=10)
    asset_name = serializers.CharField(required=True, max_length=40)
    asset_tag = serializers.CharField(required=True, max_length=30)
    serial_number = serializers.CharField(required=True, max_length=30)
    status = serializers.CharField(required=True, max_length=20)
    user_name = serializers.CharField(required=True, max_length=40)
    location = serializers.CharField(required=True, max_length=60)
    admin_user_name = serializers.CharField(required=True, max_length=50)
    admin_password = serializers.CharField(required=True, max_length=255)
    last_changed_by = serializers.CharField(read_only=True, max_length=50)  # Made optional
   
    # Add missing fields that are in the model but not explicitly defined
    order_number = serializers.CharField(required=False, max_length=20, allow_null=True, allow_blank=True)
    purchase_cost = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, allow_null=True)
    notes = serializers.CharField(required=False, max_length=80, allow_null=True, allow_blank=True)
    assignment_user_name = serializers.CharField(read_only=True, max_length=50, allow_null=True)
    assignment_status = serializers.CharField(read_only=True, max_length=50, allow_null=True)
    warranty_start_date = serializers.DateField(required=False, allow_null=True)
    warranty_end_date = serializers.DateField(required=False, allow_null=True)
    check_in_date = serializers.DateField(required=False, allow_null=True)
    purchase_date = serializers.DateField(required=False, allow_null=True)
    currency = serializers.CharField(required=False, max_length=3, default='INR')  # ADD THIS LINE
    byod = serializers.BooleanField(required=False, default=False)

    # ----------- Newly Added Hardware Fields -----------

    roboxa_asset_id = serializers.CharField(required=True, max_length=100)
    configuration_details = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    external = serializers.BooleanField(required=False, default=False)

    # ----------- Transfer Fields -----------

    transfer_from = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=100)
    transfer_from_date = serializers.DateField(required=False, allow_null=True)
    transfer_to = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=100)
    transfer_to_date = serializers.DateField(required=False, allow_null=True)

    # ----------- AMC / Warranty Fields -----------

    amc_start_date = serializers.DateField(required=False, allow_null=True)
    amc_end_date = serializers.DateField(required=False, allow_null=True)
    amc_vendor = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=100)
    warranty_status = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=30)

   
 
    class Meta:
        model = HardwareAssignment
        fields = '__all__'
        read_only_fields = [
            'id', 'last_changed_datetime',
            'created_at', 'updated_at', 'image_url', 'invoice_url',
            'to_date', 'assignment_from_date', 'assignment_to_date',
            'last_changed_by', 'assignment_user_name', 'assignment_status'
        ]
 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
       
        # For update operations, make all fields optional
        if self._is_update_operation():
            self.fields['model'].required = False
            self.fields['company'].required = False
            self.fields['asset_category'].required = False
            self.fields['asset_sub_category'].required = False
            self.fields['asset_type'].required = False
            self.fields['asset_name'].required = False
            self.fields['asset_tag'].required = False
            self.fields['serial_number'].required = False
            self.fields['status'].required = False
            self.fields['user_name'].required = False
            self.fields['location'].required = False
            self.fields['admin_user_name'].required = False
            self.fields['admin_password'].required = False
            self.fields['image'].required = False
            self.fields['invoice_copy'].required = False
 
    def _is_update_operation(self):
        """
        Check if this is an update operation
        """
        request = self.context.get('request')
        return (
            hasattr(self, 'instance') and
            self.instance is not None and
            request and
            request.method in ['PUT', 'PATCH']
        )
 
    # ---------------------- VALIDATIONS ----------------------
 
    def validate_string_field(self, value, field_name, max_length, mandatory=True):
        # Convert empty string to None if field is not mandatory
        if value == "" and not mandatory:
            return None
       
        # Check if field is mandatory and has no value
        if mandatory and not value:
            raise serializers.ValidationError(f"{field_name} is mandatory.")
       
        # Check max length if value exists
        if value and len(str(value)) > max_length:
            raise serializers.ValidationError(f"{field_name} cannot exceed {max_length} characters.")
       
        # Return stripped string or None
        return str(value).strip() if value else None
 
    def validate_decimal_field(self, value, field_name):
        if value in (None, ''):
            return None
        try:
            return Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            raise serializers.ValidationError(f"{field_name} must be a valid decimal number.")
 
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
    
    def validate_serial_number(self, value):
        if value != value.strip():
            raise serializers.ValidationError(
                "Serial Number should not end with empty spaces."
            )

        qs = HardwareAssignment.objects.filter(serial_number__iexact=value.strip())

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError("Serial Number already exists.")

        return value.strip()

 
    def validate(self, attrs):
        is_update = self._is_update_operation()
 
        # ---------------- Date validation for from_date and to_date ----------------
        if attrs.get('from_date') and attrs.get('to_date') and attrs['from_date'] > attrs['to_date']:
            raise serializers.ValidationError({"to_date": "To Date cannot be earlier than From Date."})
 
        # ---------------- String field validations ----------------
        field_max_lengths = {
            'asset_type': 50, 'asset_name': 40, 'asset_tag': 30, 'serial_number': 30,
            'status': 50, 'user_name': 40, 'location': 60, 'admin_user_name': 50,
            'admin_password': 255, 'last_changed_by': 50,
            'order_number': 20, 'assignment_user_name': 50,
            'assignment_status': 50, 'notes': 80, 'asset_category': 50, 'roboxa_asset_id': 50,
            'configuration_details': 500, 'transfer_from': 100, 'transfer_to': 100, 'amc_vendor': 100,
            'warranty_status': 30

 
        }
 
        mandatory_fields = [
            'asset_type', 'asset_name', 'asset_tag', 'serial_number',
            'status', 'user_name', 'location', 'admin_user_name',
            'admin_password'
        ]
 
        # For updates, NO fields are mandatory
        # For creates, only mandatory fields are required
        for field, max_len in field_max_lengths.items():
            if field in attrs:
                mandatory = (field in mandatory_fields) and not is_update
                attrs[field] = self.validate_string_field(
                    attrs.get(field), field.replace('_', ' ').title(), max_len, mandatory
                )
 
        # ---------------- Foreign key conversions ----------------
        if 'model' in attrs and attrs['model']:
            try:
                attrs['model'] = AssetModel.objects.get(asset_model_name=attrs['model'])
            except AssetModel.DoesNotExist:
                raise serializers.ValidationError({'model': f"Model '{attrs['model']}' does not exist."})
 
        if 'company' in attrs and attrs['company']:
            try:
                attrs['company'] = Company.objects.get(company=attrs['company'])
            except Company.DoesNotExist:
                raise serializers.ValidationError({'company': f"Company '{attrs['company']}' does not exist."})
 
        # if 'asset_category' in attrs and attrs['asset_category']:
        #     category_qs = AssetCategories.objects.filter(asset_category=attrs['asset_category'])
        #     if category_qs.exists():
        #         attrs['asset_category'] = category_qs.first()
        #     else:
        #         raise serializers.ValidationError({'asset_category': f"Asset Category '{attrs['asset_category']}' does not exist."})
 
        if 'asset_sub_category' in attrs:
            sub_cat = attrs['asset_sub_category']
            if is_update:
                if sub_cat is not None and sub_cat != "":
                    if 'asset_category' in attrs and hasattr(attrs['asset_category'], 'asset_sub_categories'):
                        valid_subs = [sub.asset_sub_category for sub in attrs['asset_category'].asset_sub_categories.all()]
                        if valid_subs and sub_cat not in valid_subs:
                            raise serializers.ValidationError({
                                'asset_sub_category': f"'{sub_cat}' is not a valid sub-category under '{attrs['asset_category']}'."
                            })
            else:
                if not sub_cat:
                    raise serializers.ValidationError({'asset_sub_category': "Asset Sub Category is mandatory."})
                if 'asset_category' in attrs and hasattr(attrs['asset_category'], 'asset_sub_categories'):
                    valid_subs = [sub.asset_sub_category for sub in attrs['asset_category'].asset_sub_categories.all()]
                    if valid_subs and sub_cat not in valid_subs:
                        raise serializers.ValidationError({
                            'asset_sub_category': f"'{sub_cat}' is not a valid sub-category under '{attrs['asset_category']}'."
                        })
 
        if 'supplier' in attrs and attrs['supplier']:
            try:
                attrs['supplier'] = Supplier.objects.get(supplier=attrs['supplier'])
            except Supplier.DoesNotExist:
                raise serializers.ValidationError({'supplier': f"Supplier '{attrs['supplier']}' does not exist."})
        elif 'supplier' in attrs:
            attrs['supplier'] = None
 
        # ---------------- Decimal fields ----------------
        if 'purchase_cost' in attrs:
            attrs['purchase_cost'] = self.validate_decimal_field(attrs.get('purchase_cost'), 'Purchase Cost')
 
        # ---------------- Date fields ----------------
        date_fields = [
            'from_date', 'to_date', 'warranty_start_date', 'warranty_end_date',
            'check_in_date', 'purchase_date', 'assignment_from_date', 'assignment_to_date',
            'transfer_from_date', 'transfer_to_date', 'amc_start_date', 'amc_end_date',
        ]
        for field in date_fields:
            if field in attrs:
                attrs[field] = self.validate_date_field(attrs.get(field), field.replace('_', ' ').title())
 
        # Validate required fields for create operation
        if not is_update:
            required_on_create = [
                'asset_type', 'asset_category', 'asset_sub_category', 'asset_name',
                'asset_tag', 'serial_number', 'company', 'status', 'user_name',
                'location', 'admin_user_name', 'admin_password', 'from_date', 'roboxa_asset_id',
                

            ]
            missing = [f for f in required_on_create if not attrs.get(f)]
            if missing:
                raise serializers.ValidationError({'missing_required_fields': f"Required on create: {', '.join(missing)}"})
 
        return attrs
   
    # Add these validation methods after the existing validate() method:
 
    def validate_image(self, value):
        """Validate that image is either JPG/JPEG or PDF"""
        if value:
            # Get file extension
            ext = value.name.split('.')[-1].lower()
            allowed_extensions = ['jpg', 'jpeg', 'png', 'pdf']
           
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
                )
        return value
   
    def validate_invoice_copy(self, value):
        """Validate that invoice_copy is either JPG/JPEG or PDF"""
        if value:
            # Get file extension
            ext = value.name.split('.')[-1].lower()
            allowed_extensions = ['jpg', 'jpeg', 'png', 'pdf']
           
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
                )
        return value
 
    # ---------------------- URL HELPERS ----------------------
    def get_image_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url) if obj.image and request else None
 
    def get_invoice_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.invoice_copy.url) if obj.invoice_copy and request else None
 
    def create(self, validated_data):
        model_fields = [f.name for f in HardwareAssignment._meta.get_fields()]
        cleaned_data = {k: v for k, v in validated_data.items() if k in model_fields}
        return HardwareAssignment.objects.create(**cleaned_data)
 
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

   
    # ... after your update() method, add these:
 
    def to_representation(self, instance):
        """Convert snake_case to camelCase and add required fields"""
        # Get the default representation
        data = super().to_representation(instance)
       
       
       
        # Convert foreign key objects to string names
        if 'company' in data and hasattr(instance.company, 'company'):
            data['company'] = instance.company.company
       
        if 'model' in data and hasattr(instance.model, 'asset_model_name'):
            data['model'] = instance.model.asset_model_name
       
        if 'supplier' in data and instance.supplier and hasattr(instance.supplier, 'supplier'):
            data['supplier'] = instance.supplier.supplier
       
        # FIX: Get asset_category from data first, then check instance
        data['asset_category'] = instance.asset_category
 
 
       
        # Add assignmentDetails (from assignment_history)
        histories = instance.assignment_history.all().order_by('-from_date')
        data['assignmentDetails'] = [
            {
                "userName": h.user_name,
                "status": h.status,
                "fromDate": h.from_date.strftime("%Y.%m.%d") if h.from_date else None,
                "toDate": h.to_date.strftime("%Y.%m.%d") if h.to_date else None
            }
            for h in histories
        ]
       
        # Add auditTrail
        data['auditTrail'] = {
            "lastChangedBy": data.get('last_changed_by', ''),
            "lastChangedDate": data.get('last_changed_datetime', '')
        }
       
        # Convert snake_case to camelCase for frontend
        field_mapping = {
            'asset_type': 'assetType',
            'asset_category': 'assetCategory',
            'asset_sub_category': 'assetSubCategory',
            'asset_name': 'assetName',
            'asset_tag': 'assetTag',
            'serial_number': 'serialNumber',
            'user_name': 'userName',
            'from_date': 'fromDate',
            'to_date': 'toDate',
            'warranty_start_date': 'warrantyStart',
            'warranty_end_date': 'warrantyEnd',
            'order_number': 'orderNumber',
            'purchase_date': 'purchaseDate',
            'purchase_cost': 'purchaseCost',
            'admin_user_name': 'adminUserName',
            'admin_password': 'adminPassword',
            'check_in_date': 'checkInDate',
            'created_at': 'createdAt',      
            'updated_at': 'updatedAt',
            'roboxa_asset_id': 'roboxaAssetId',
            'configuration_details': 'configurationDetails',
            'external': 'external',
            'transfer_from': 'transferFrom',
            'transfer_from_date': 'transferFromDate',
            'transfer_to': 'transferTo',
            'transfer_to_date': 'transferToDate',
            'amc_start_date': 'amcStartDate',
            'amc_end_date': 'amcEndDate',
            'amc_vendor': 'amcVendor',
            'warranty_status': 'warrantyStatus',
           

        }
       
        # Apply camelCase conversion
        for old_name, new_name in field_mapping.items():
            if old_name in data:
                if old_name != new_name:
                    data[new_name] = data[old_name]
                    del data[old_name]

       
        # Remove unwanted fields that are not in your required output
        fields_to_remove = [
            'image_url', 'invoice_url', 'last_changed_datetime',
            'assignment_user_name', 'assignment_status',
            'assignment_from_date', 'assignment_to_date', 'last_changed_by'
        ]
       
        for field in fields_to_remove:
            if field in data:
                del data[field]
       
        return data
 
 
class HardwareAssignmentUpdateSerializer(HardwareAssignmentSerializer):
    """
    Serializer specifically for update operations - all fields are optional
    """
    # Override all fields to make them optional
    model = serializers.CharField(required=False)
    company = serializers.CharField(required=False)
    asset_category = serializers.CharField(required=False)
    asset_sub_category = serializers.CharField(required=False, allow_blank=True)
    supplier = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    from_date = serializers.DateField(required=False)
    to_date = serializers.DateField(read_only=True)
    asset_type = serializers.CharField(required=False, max_length=10)
    asset_name = serializers.CharField(required=False, max_length=40)
    asset_tag = serializers.CharField(required=False, max_length=30)
    serial_number = serializers.CharField(required=False, max_length=30)
    status = serializers.CharField(required=False, max_length=20)
    user_name = serializers.CharField(required=False, max_length=40)
    location = serializers.CharField(required=False, max_length=60)
    admin_user_name = serializers.CharField(required=False, max_length=50)
    admin_password = serializers.CharField(required=False, max_length=255)
    last_changed_by = serializers.CharField(read_only=True, max_length=50)
    order_number = serializers.CharField(required=False, max_length=20, allow_null=True, allow_blank=True)
    purchase_cost = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, allow_null=True)
    notes = serializers.CharField(required=False, max_length=80, allow_null=True, allow_blank=True)
    assignment_user_name = serializers.CharField(read_only=True, max_length=50, allow_null=True)  # Keep read_only
    assignment_status = serializers.CharField(read_only=True, max_length=50, allow_null=True)  # Keep read_only
    assignment_from_date = serializers.DateField(read_only=True)  # Keep read_only
    assignment_to_date = serializers.DateField(read_only=True)
    warranty_start_date = serializers.DateField(required=False, allow_null=True)
    warranty_end_date = serializers.DateField(required=False, allow_null=True)
    check_in_date = serializers.DateField(required=False, allow_null=True)
    purchase_date = serializers.DateField(required=False, allow_null=True)
    byod = serializers.BooleanField(required=False, default=False)
    roboxa_asset_id = serializers.CharField(required=False)
    configuration_details = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    external = serializers.BooleanField(required=False, default=False)
    transfer_from = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    transfer_from_date = serializers.DateField(required=False)
    transfer_to = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    transfer_to_date = serializers.DateField(required=False)
    amc_start_date = serializers.DateField(required=False, allow_null=True)
    amc_end_date = serializers.DateField(required=False, allow_null=True)
    amc_vendor = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    warranty_status = serializers.CharField(required=False, allow_null=True, allow_blank=True)

   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
 
    def _is_update_operation(self):
        return True
 
    def validate(self, attrs):
        is_update = True
 
        # ---------------- Date validation for from_date and to_date ----------------
        if attrs.get('from_date') and attrs.get('to_date') and attrs['from_date'] > attrs['to_date']:
            raise serializers.ValidationError({"to_date": "To Date cannot be earlier than From Date."})
 
        # ---------------- String field validations ----------------
        field_max_lengths = {
            'asset_type': 50, 'asset_name': 40, 'asset_tag': 30, 'serial_number': 30,
            'status': 50, 'user_name': 40, 'location': 60, 'admin_user_name': 50,
            'admin_password': 255, 'last_changed_by': 50,
            'order_number': 20, 'assignment_user_name': 50,
            'assignment_status': 50, 'notes': 80, 'asset_category': 50
 
        }
 
        # For updates, NO fields are mandatory
        for field, max_len in field_max_lengths.items():
            if field in attrs:
                attrs[field] = self.validate_string_field(
                    attrs.get(field), field.replace('_', ' ').title(), max_len, mandatory=False
                )
 
        # ---------------- Foreign key conversions (only if provided) ----------------
        if 'model' in attrs and attrs['model']:
            try:
                attrs['model'] = AssetModel.objects.get(asset_model_name=attrs['model'])
            except AssetModel.DoesNotExist:
                raise serializers.ValidationError({'model': f"Model '{attrs['model']}' does not exist."})
 
        if 'company' in attrs and attrs['company']:
            try:
                attrs['company'] = Company.objects.get(company=attrs['company'])
            except Company.DoesNotExist:
                raise serializers.ValidationError({'company': f"Company '{attrs['company']}' does not exist."})
 
        # if 'asset_category' in attrs and attrs['asset_category']:
        #     category_qs = AssetCategories.objects.filter(asset_category=attrs['asset_category'])
        #     if category_qs.exists():
        #         attrs['asset_category'] = category_qs.first()
        #     else:
        #         raise serializers.ValidationError({'asset_category': f"Asset Category '{attrs['asset_category']}' does not exist."})
 
        if 'asset_sub_category' in attrs and attrs['asset_sub_category']:
            sub_cat = attrs['asset_sub_category']
            if 'asset_category' in attrs and hasattr(attrs['asset_category'], 'asset_sub_categories'):
                valid_subs = [sub.asset_sub_category for sub in attrs['asset_category'].asset_sub_categories.all()]
                if valid_subs and sub_cat not in valid_subs:
                    raise serializers.ValidationError({
                        'asset_sub_category': f"'{sub_cat}' is not a valid sub-category under '{attrs['asset_category']}'."
                    })
 
        if 'supplier' in attrs and attrs['supplier']:
            try:
                attrs['supplier'] = Supplier.objects.get(supplier=attrs['supplier'])
            except Supplier.DoesNotExist:
                raise serializers.ValidationError({'supplier': f"Supplier '{attrs['supplier']}' does not exist."})
        elif 'supplier' in attrs:
            attrs['supplier'] = None
 
        # ---------------- Decimal fields ----------------
        if 'purchase_cost' in attrs:
            attrs['purchase_cost'] = self.validate_decimal_field(attrs.get('purchase_cost'), 'Purchase Cost')
 
        # ---------------- Date fields ----------------
        date_fields = [
            'from_date', 'to_date', 'warranty_start_date', 'warranty_end_date',
            'check_in_date', 'purchase_date', 'assignment_from_date', 'assignment_to_date'
        ]
        for field in date_fields:
            if field in attrs:
                attrs[field] = self.validate_date_field(attrs.get(field), field.replace('_', ' ').title())
 
        return attrs