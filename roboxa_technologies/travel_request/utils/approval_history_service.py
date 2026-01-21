# travel_request/utils/approval_history_service.py

from travel_request.models import ApprovalHistory


def log_approval_action(travel_request, level, action, action_by, remarks=None):
    ApprovalHistory.objects.create(
        travel_request=travel_request,
        level=level,
        action=action,
        action_by=action_by,
        remarks=remarks
    )
