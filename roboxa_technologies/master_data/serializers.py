from rest_framework import serializers
from .models import ProjectTasks,Employee,ProjectRoles
from .models import AssetCategories, AssetModel, Status, Company, Supplier
import re
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from rest_framework.validators import UniqueValidator


class ProjectTasksSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectTasks
        fields = ['task_code','project_type', 'task_group', 'description', 'created_at', 'updated_at']  # Exclude task_code

    def validate_description(self, value):
        value = value.strip()
        # Allow alphanumeric, space, &, /, -
        if not re.fullmatch(r'^[A-Za-z0-9 &/\-]+$', value):
            raise serializers.ValidationError(
                "Description must contain only alphanumeric characters, spaces, and the symbols &, /, -."
            )
        return value

    def validate_task_group(self, value):
        value = value.strip()
        # Allow alphanumeric, space, &, /, -
        if not re.fullmatch(r'^[A-Za-z0-9 &/\-]+$', value):
            raise serializers.ValidationError(
                "Task group must contain only alphanumeric characters, spaces, and the symbols &, /, -."
            )
        return value


class EmployeeSerializer(serializers.ModelSerializer):
    contractor = serializers.BooleanField(required=False, default=False)
    project_specific_hire = serializers.BooleanField(required=False, default=False)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    email = serializers.EmailField(
    required=False,
    allow_blank=True,
    validators=[
        UniqueValidator(
            queryset=Employee.objects.all(),
            message="Email already exists."
        )
    ]
)

    def to_internal_value(self, data):
        # Clean empty string -> None before any validation
        if data.get('relieving_date', '') == '':
            data['relieving_date'] = None

        # --- Handle boolean fields for contractor & project_specific_hire ---
        for field in ['contractor', 'project_specific_hire']:
            val = data.get(field)

            if val in [None, "", "null"]:
                data[field] = False
            elif isinstance(val, bool):
                data[field] = val
            elif isinstance(val, str):
                data[field] = val.strip().lower() == "true"
            else:
                data[field] = bool(val)

        return super().to_internal_value(data)


    class Meta:
        model = Employee
        fields = '__all__'  #  includes created_at and updated_at

    def validate(self, data):
        # Ensure relieving_date is provided if status is 'inactive'
        status = data.get('status', '').lower()
        relieving_date = data.get('relieving_date')

        if status == 'inactive' and not relieving_date:
            raise serializers.ValidationError({
                "relieving_date": "Relieving date is required when status is 'inactive'."
            })

        # --- Validating primary_skill (mandatory) ---
        if not data.get('primary_skill'):
            raise serializers.ValidationError({
                "primary_skill": "Primary skill is required."
            })

        # --- Validating department (mandatory) ---
        department = data.get('department', '').strip()
        if not department:
            raise serializers.ValidationError({
                "department": "Department is required."
            })

        return data
    
    def validate_name(self, value):
        """
        Ensure the name contains only alphabetic characters and spaces.
        """
        if not re.fullmatch(r'^[A-Za-z ]+$', value.strip()):
            raise serializers.ValidationError("The name must contain only alphabetic characters and spaces.")

        return value
    
    def validate_mobile(self, value):
        if not re.fullmatch(r'[+\-\d\s]+', value):
            raise serializers.ValidationError("Mobile number can only contain digits, '+', '-', or spaces.")
        digits_only = re.sub(r'\D', '', value)
        if len(digits_only) < 10:
            raise serializers.ValidationError("Mobile number must contain at least 10 digits.")
        return value
    
    def validate_designation(self, value):
        value = value.strip()
        if not re.fullmatch(r'^[A-Za-z0-9 ]+$', value):
            raise serializers.ValidationError("designation must contain only alphanumeric characters and spaces.")
        return value
    
    def validate_manager(self, value):
        """
        Ensure the manager name contains only alphabetic characters and spaces.
        Allow an empty string.
        """
        if value.strip() == "":  # Allow empty string
            return value

        if not re.fullmatch(r'^[A-Za-z ]+$', value.strip()):
            raise serializers.ValidationError("The manager's name must contain only alphabetic characters and spaces.")

        return value


    def validate_employee_code(self, value):
            """
            Ensure that the userId starts with 'RBX'.
            """
            if not value.startswith('RBX'):
                raise serializers.ValidationError("The employee_code must start with the prefix 'RBX'.")
            return value
    
    def validate_designation(self, value):
        value = value.strip()
        # Allow letters, numbers, spaces, dash (-), slash (/), and ampersand (&)
        if not re.fullmatch(r'^[A-Za-z0-9\s\-/&]+$', value):
            raise serializers.ValidationError(
                "Designation must contain only letters, numbers, spaces, and special characters (-, /, &)."
            )
        return value
    
    def update(self, instance, validated_data):
        old_status = instance.status
        old_relieving_date = instance.relieving_date

        # Proceed with default update
        updated_instance = super().update(instance, validated_data)

        # Trigger email if status changed to 'inactive' and relieving_date provided and newly added
        if (
            validated_data.get('status', old_status).lower() == 'inactive' and
            validated_data.get('relieving_date') and
            (str(old_relieving_date) != str(validated_data['relieving_date']))
        ):

            subject = 'PMO Tool Access Removed – Employee Offboarding Update'
            from_email = 'pmo-admin@roboxaservices.com'
            to = ['pmo-admin@roboxaservices.com','HR@roboxaservices.com','valentina.p@roboxaservices.com']

            html_content = f"""
            Hello <strong>Team</strong>,<br><br>

            This is to inform you that access to the <strong>PMO</strong> application has been removed for the following employee as a part of the <strong>offboarding</strong> process:<br><br>

            Employee Name: <strong>{updated_instance.name}</strong><br>
            Employee Code: <strong>{updated_instance.employee_code}</strong><br>
            Last Working Day: <strong>{updated_instance.relieving_date.strftime('%d-%m-%Y')}</strong><br><br>

            The employee has no longer access to the PMO application.<br><br>
            Please let me know if any further action is required from our side or if additional details are needed.<br><br>


            Regards,<br>
            <strong>PMO ROBOXA</strong>
            """ 

            # Create and send the email
            msg = EmailMultiAlternatives(subject, '', from_email, to)
            msg.attach_alternative(html_content, "text/html")
            msg.send()

        return updated_instance


class ProjectRolesSerializer(serializers.ModelSerializer):
    # project_role = serializers.CharField(write_only=True)
    class Meta:
        model = ProjectRoles
        fields = ['id', 'project_role', 'created_at', 'updated_at']

    def validate_project_role(self, value):
        value = value.strip()
        # Allow letters, numbers, spaces, dash (-), slash (/), and ampersand (&)
        if not re.fullmatch(r'^[A-Za-z0-9\s\-/&]+$', value):
            raise serializers.ValidationError(
                "The project role must contain only letters, numbers, spaces, and special characters (-, /, &)."
            )
        return value


class EmployeeSummaryRequestSerializer(serializers.Serializer):
    month = serializers.IntegerField()
    year = serializers.IntegerField()
    employee_code = serializers.ListField(child=serializers.CharField(), required=False,
allow_empty=True
    )
    country = serializers.CharField(required=False, allow_blank=True)

    def validate_employee_code(self, value):
    # value is now a list of strings
    # Strip each string and remove empty strings
        cleaned_list = [v.strip() for v in value if v.strip()]
        return cleaned_list


    def validate_country(self, value):
        if value.strip() == "":
            return ""
        return value

class ProjectUtilizationSerializer(serializers.Serializer):
    allocated_budgeted_hours = serializers.IntegerField()
    worked_hours = serializers.CharField()
    Utilization = serializers.CharField()



class AssetCategoriesSerializer(serializers.ModelSerializer):
    asset_category = serializers.CharField(trim_whitespace=False)
    asset_sub_category = serializers.CharField(trim_whitespace=False)

    class Meta:
        model = AssetCategories
        fields = [
            'asset_id',
            'asset_type',
            'asset_category',
            'asset_sub_category',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['asset_id', 'created_at', 'updated_at']

    def validate(self, attrs):
        asset_category = attrs.get('asset_category')
        asset_sub_category = attrs.get('asset_sub_category')

        # Leading / trailing space validation
        if asset_category != asset_category.strip():
            raise serializers.ValidationError(
                "Asset category should not end with empty spaces."
            )

        if asset_sub_category != asset_sub_category.strip():
            raise serializers.ValidationError(
                "Asset sub category should not end with empty spaces."
            )

        # Duplicate check
        qs = AssetCategories.objects.filter(
            asset_category__iexact=asset_category.strip(),
            asset_sub_category__iexact=asset_sub_category.strip()
        )

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError(
                "This sub-category already exists for the given asset category."
            )

        return attrs

    def create(self, validated_data):
        last_asset = AssetCategories.objects.order_by('-id').first()
        if last_asset and last_asset.asset_id.startswith("AC"):
            last_num = int(last_asset.asset_id.replace("AC", ""))
            validated_data['asset_id'] = f"AC{last_num + 1}"
        else:
            validated_data['asset_id'] = "AC1"


        return AssetCategories.objects.create(**validated_data)


class AssetModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = AssetModel
        fields = [
            'asset_model_id',
            'asset_model_code',
            'asset_model_name',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['asset_model_id', 'created_at', 'updated_at']

    def validate(self, attrs):
        code = attrs.get('asset_model_code')
        name = attrs.get('asset_model_name')

        # ---- Trim validation ----
        if code and code != code.strip():
            raise serializers.ValidationError(
                "Asset model code should not end with empty spaces."
            )

        if name and name != name.strip():
            raise serializers.ValidationError(
                "Asset model name should not end with empty spaces."
            )

        # ---- Code uniqueness ----
        if code:
            code_qs = AssetModel.objects.filter(
                asset_model_code__iexact=code.strip()
            )

            if self.instance:
                code_qs = code_qs.exclude(id=self.instance.id)

            if code_qs.exists():
                raise serializers.ValidationError(
                    "Asset model code already exists."
                )
        if name:
            name_qs = AssetModel.objects.filter(
                asset_model_name__iexact=name.strip()
            )

            if self.instance:
                name_qs = name_qs.exclude(id=self.instance.id)

            if name_qs.exists():
                raise serializers.ValidationError(
                    "Asset model name already exists."
                )

        return attrs

    def create(self, validated_data):
        last_asset = AssetModel.objects.order_by('-id').first()
        if last_asset and last_asset.asset_model_id.startswith("AM"):
            last_num = int(last_asset.asset_model_id.replace("AM", ""))
            validated_data['asset_model_id'] = f"AM{last_num + 1}"
        else:
            validated_data['asset_model_id'] = "AM1"

        return super().create(validated_data)


class StatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = Status
        fields = [
            'status_id',
            'status_code',
            'status_name',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['status_id', 'created_at', 'updated_at']

    def validate_status_code(self, value):
        if value != value.strip():
            raise serializers.ValidationError(
                "Status code should not end with empty spaces."
            )

        qs = Status.objects.filter(status_code__iexact=value.strip())

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError(
                "Status code already exists."
            )

        return value

    def validate_status_name(self, value):
        if value != value.strip():
            raise serializers.ValidationError(
                "status should not end with empty spaces."
            )

        qs = Status.objects.filter(status_name__iexact=value.strip())

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError(
                "Status name already exists."
            )

        return value

    def create(self, validated_data):
        last_status = Status.objects.order_by('-id').first()
        if last_status and last_status.status_id.startswith("ST"):
            last_num = int(last_status.status_id.replace("ST", ""))
            validated_data['status_id'] = f"ST{last_num + 1}"
        else:
            validated_data['status_id'] = "ST1"

        return super().create(validated_data)

class CompanySerializer(serializers.ModelSerializer):
    company = serializers.CharField(trim_whitespace=False)
    address = serializers.CharField(trim_whitespace=False)
    geo_region = serializers.CharField(trim_whitespace=False)
    country = serializers.CharField(trim_whitespace=False)

    class Meta:
        model = Company
        fields = [
            'id',
            'company',
            'address',
            'country',
            'geo_region',
            'location_name',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_company(self, value):
        if not value.strip():
            raise serializers.ValidationError("Company name cannot be empty")
        if len(value) > 50:
            raise serializers.ValidationError("Company name too long (max 50 chars)")
        return value

    def validate_address(self, value):
        if not value.strip():
            raise serializers.ValidationError("Address cannot be empty")
        if len(value) > 80:
            raise serializers.ValidationError("Address too long (max 80 chars)")
        return value

    def validate_location_name(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("location_name must be a list of strings")

        for item in value:
            if not isinstance(item, str):
                raise serializers.ValidationError("All location names must be strings")
            if item != item.strip():
                raise serializers.ValidationError(
                    "Location should not end with empty spaces."
                )
        return value

    def validate(self, attrs):
        company = attrs.get('company')
        address = attrs.get('address')
        geo_region = attrs.get('geo_region')
        country = attrs.get('country')

        if company != company.strip():
            raise serializers.ValidationError(
                "Company should not end with empty spaces."
            )

        if address != address.strip():
            raise serializers.ValidationError(
                "Address should not end with empty spaces"
            )

        if geo_region and geo_region != geo_region.strip():
            raise serializers.ValidationError(
                "Geo region should not end with empty spaces."
            )

        if country and country != country.strip():
            raise serializers.ValidationError(
                "Country should not end with empty spaces."
            )

        return attrs

    def update(self, instance, validated_data):
        for field in self.Meta.fields:
            if field in validated_data and validated_data[field] in ["", None, "string"]:
                validated_data.pop(field)
        return super().update(instance, validated_data)

class SupplierSerializer(serializers.ModelSerializer):
    supplier = serializers.CharField(required=True, trim_whitespace=False)
    address = serializers.CharField(trim_whitespace=False)
    geo_region = serializers.CharField(trim_whitespace=False)
    country = serializers.CharField(trim_whitespace=False)

    class Meta:
        model = Supplier
        fields = [
            'id',
            'supplier',
            'address',
            'country',
            'geo_region',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_supplier(self, value):
        if not value.strip():
            raise serializers.ValidationError("Supplier name is required")
        if len(value) > 40:
            raise serializers.ValidationError("Supplier name too long (max 40 chars)")
        return value

    def validate(self, attrs):
        supplier = attrs.get('supplier')
        address = attrs.get('address')
        geo_region = attrs.get('geo_region')
        country = attrs.get('country')

        if supplier != supplier.strip():
            raise serializers.ValidationError(
                "Supplier should not end with empty spaces."
            )

        if address != address.strip():
            raise serializers.ValidationError(
                "Address should not end with empty spaces."
            )

        if geo_region and geo_region != geo_region.strip():
            raise serializers.ValidationError(
                "Geo region should not end with empty spaces."
            )

        if country and country != country.strip():
            raise serializers.ValidationError(
                "Country should not end with empty spaces."
            )

        return attrs

    def update(self, instance, validated_data):
        for field in self.Meta.fields:
            if field in validated_data and validated_data[field] in ["", None, "string"]:
                validated_data.pop(field)
        return super().update(instance, validated_data)
