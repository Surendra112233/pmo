# roboxa_technologies/utils/email_utils.py

from django.core.mail import send_mail
from django.conf import settings


def send_approval_mail(subject, message, recipients):
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=False
    )
