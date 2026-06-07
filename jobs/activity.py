"""Helpers for recording job timeline events."""

from .models import JobActivity


def log_job_activity(job, actor, event_type, message):
    return JobActivity.objects.create(
        job=job,
        actor=actor,
        event_type=event_type,
        message=message,
    )
