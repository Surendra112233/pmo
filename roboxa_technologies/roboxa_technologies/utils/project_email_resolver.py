from pmo.models import Project
from master_data.models import Employee


class ProjectApprovalResolver:

    @staticmethod
    def get_approver_emails(project_code):
        """
        Returns dict with PM, Delivery Head, SBU Head emails
        """

        try:
            project = Project.objects.get(project_code=project_code)
        except Project.DoesNotExist:
            raise ValueError("Invalid project code")

        roles = {
            "project_manager": project.project_manager,
            "delivery_manager": project.delivery_head,
            "sbu_head": project.sbu_head,
        }

        emails = {}

        for role, name in roles.items():
            emp = Employee.objects.filter(name__iexact=name).first()
            if not emp:
                raise ValueError(f"Email not found for {role}: {name}")

            emails[role] = emp.email

        return emails
