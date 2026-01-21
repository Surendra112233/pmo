from django.contrib import admin
from django.utils.html import format_html
from .models import SoftwareAssignment, SoftwareAssignmentHistory

@admin.register(SoftwareAssignment)
class SoftwareAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        "id", "software_name", "asset_tag", "asset_type",
        "asset_category", "asset_sub_category", "company", "status",
        "user_name", "from_date", "to_date", "last_changed_by", "created_at"
    ]
    list_filter = ["asset_type", "status", "company", "from_date", "to_date"]
    search_fields = ["software_name", "asset_tag", "user_name", "company", "status"]
    readonly_fields = ["id", "last_changed_datetime", "created_at", "updated_at", "get_image_url", "get_invoice_url"]
    ordering = ["-created_at"]

    def get_image_url(self, obj):
        if obj.image:
            return format_html(f"<a href='{obj.image.url}' target='_blank'>View Image</a>")
        return "No Image"
    get_image_url.short_description = "Image URL"

    def get_invoice_url(self, obj):
        if obj.invoice_copy:
            return format_html(f"<a href='{obj.invoice_copy.url}' target='_blank'>View Invoice</a>")
        return "No Invoice"
    get_invoice_url.short_description = "Invoice URL"


@admin.register(SoftwareAssignmentHistory)
class SoftwareAssignmentHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "id", "assignment", "status", "user_name",
        "from_date", "to_date", "last_changed_by", "created_at"
    ]
    list_filter = ["status", "from_date", "to_date"]
    search_fields = ["assignment__software_name", "user_name", "status"]
    readonly_fields = ["id", "last_changed_datetime", "created_at", "updated_at"]
    ordering = ["-from_date"]
