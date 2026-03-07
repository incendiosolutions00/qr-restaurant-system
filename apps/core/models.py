from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model with created/updated timestamps."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AuditLog(models.Model):
    """Tracks all important actions across the system."""
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('STATUS_CHANGE', 'Status Change'),
    ]

    user = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True,
        related_name='audit_logs'
    )
    restaurant = models.ForeignKey(
        'tenants.Restaurant', on_delete=models.CASCADE,
        null=True, blank=True, related_name='audit_logs'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['restaurant', '-created_at']),
            models.Index(fields=['model_name', 'object_id']),
        ]

    def __str__(self):
        return f"{self.action} {self.model_name} #{self.object_id} by {self.user}"


class SystemSetting(models.Model):
    """Global system-level configuration (super admin)."""
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField()
    description = models.TextField(blank=True)

    def __str__(self):
        return self.key
