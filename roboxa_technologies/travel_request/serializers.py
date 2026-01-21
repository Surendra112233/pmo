from rest_framework import serializers
from .models import (
    TravelRequest,
    TravelDetails,
    AccommodationDetails,
    PersonalDetails
)
from travel_request.utils.exceptions import TravelRequestException
from django.db import transaction


# =================================================
# Travel Details Serializer
# =================================================
class TravelDetailsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    departure_date = serializers.DateField(
        format="%d-%m-%Y", input_formats=["%d-%m-%Y"]
    )
    arrival_date = serializers.DateField(
        format="%d-%m-%Y", input_formats=["%d-%m-%Y"]
    )
    departure_time = serializers.TimeField(
        format="%H:%M:%S", input_formats=["%H:%M:%S"]
    )
    arrival_time = serializers.TimeField(
        format="%H:%M:%S", input_formats=["%H:%M:%S"]
    )

    class Meta:
        model = TravelDetails
        fields = "__all__"
        read_only_fields = ("travel_request",)


# =================================================
# Accommodation Details Serializer
# =================================================
class AccommodationDetailsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    check_in = serializers.DateField(
        format="%d-%m-%Y", input_formats=["%d-%m-%Y"]
    )
    check_out = serializers.DateField(
        format="%d-%m-%Y", input_formats=["%d-%m-%Y"]
    )

    class Meta:
        model = AccommodationDetails
        fields = "__all__"
        read_only_fields = ("travel_request",)


# =================================================
# Personal Details Serializer
# =================================================
class PersonalDetailsSerializer(serializers.ModelSerializer):
    date_of_birth = serializers.DateField(
        format="%d-%m-%Y", input_formats=["%d-%m-%Y"]
    )

    class Meta:
        model = PersonalDetails
        fields = "__all__"
        read_only_fields = ("travel_request",)


# =================================================
# Travel Request Serializer (MAIN)
# =================================================
class TravelRequestSerializer(serializers.ModelSerializer):
    travel_details = TravelDetailsSerializer(many=True, required=False)
    accommodation = AccommodationDetailsSerializer(many=True, required=False)
    personal_details = PersonalDetailsSerializer(
        source="personaldetails",
        required=False
    )

    is_edit = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TravelRequest
        fields = "__all__"

    # -------------------------------------------------
    # Computed Field
    # -------------------------------------------------
    def get_is_edit(self, obj):
        return obj.status == "Rejected"

    # -------------------------------------------------
    # Validation (SINGLE SOURCE OF TRUTH)
    # -------------------------------------------------
    def validate(self, attrs):
        instance = self.instance

        # ❌ Block edit after approvals
        if instance and instance.status in [
            "PM Approved",
            "Delivery Approved",
            "SBU Approved"
        ]:
            raise TravelRequestException(
                "This request is already approved and cannot be edited."
            )

        accommodation_required = attrs.get(
            "accommodation_required",
            getattr(instance, "accommodation_required", False)
        )

        accommodation = attrs.get("accommodation")

        if not accommodation_required and accommodation:
            raise TravelRequestException(
                "Accommodation details are not allowed."
            )

        if accommodation_required and not accommodation and not instance:
            raise TravelRequestException(
                "Accommodation details are required."
            )

        return attrs

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------
    @transaction.atomic
    def create(self, validated_data):
        travel_details_data = validated_data.pop("travel_details", [])
        accommodation_data = validated_data.pop("accommodation", [])
        personal_data = validated_data.pop("personaldetails", None)

        travel_request = TravelRequest.objects.create(**validated_data)

        for td in travel_details_data:
            TravelDetails.objects.create(
                travel_request=travel_request, **td
            )

        if travel_request.accommodation_required:
            for acc in accommodation_data:
                AccommodationDetails.objects.create(
                    travel_request=travel_request, **acc
                )

        if personal_data:
            PersonalDetails.objects.create(
                travel_request=travel_request, **personal_data
            )

        return travel_request

    # -------------------------------------------------
    # UPDATE
    # -------------------------------------------------
    @transaction.atomic
    def update(self, instance, validated_data):
        travel_details_data = validated_data.pop("travel_details", None)
        accommodation_data = validated_data.pop("accommodation", None)
        personal_data = validated_data.pop("personaldetails", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.status = "Submitted"
        instance.save()

        # -------- Travel Details --------
        if travel_details_data is not None:
            for td in travel_details_data:
                td_id = td.pop("id", None)
                if not td_id:
                    raise TravelRequestException(
                        "travel_details.id is required for update."
                    )

                td_instance = instance.travel_details.filter(id=td_id).first()
                if not td_instance:
                    raise TravelRequestException(
                        "Invalid travel details ID."
                    )

                for k, v in td.items():
                    setattr(td_instance, k, v)
                td_instance.save()

        # -------- Accommodation --------
        if accommodation_data is not None:
            if not instance.accommodation_required:
                instance.accommodation.all().delete()
            else:
                for acc in accommodation_data:
                    acc_id = acc.pop("id", None)
                    if acc_id:
                        acc_instance = instance.accommodation.filter(id=acc_id).first()
                        if not acc_instance:
                            raise TravelRequestException(
                                "Invalid accommodation ID."
                            )
                        for k, v in acc.items():
                            setattr(acc_instance, k, v)
                        acc_instance.save()
                    else:
                        AccommodationDetails.objects.create(
                            travel_request=instance, **acc
                        )

        # -------- Personal Details --------
        if personal_data:
            PersonalDetails.objects.update_or_create(
                travel_request=instance,
                defaults=personal_data
            )

        return instance
