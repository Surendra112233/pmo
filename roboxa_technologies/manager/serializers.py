from rest_framework import serializers
from .models import TimesheetApproval

class TimesheetApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimesheetApproval
        fields = '__all__'
