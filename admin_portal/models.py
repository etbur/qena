from django.db import models


class AuditLog(models.Model):
    ACTION_CREATE  = 'create'
    ACTION_UPDATE  = 'update'
    ACTION_DELETE  = 'delete'
    ACTION_APPROVE = 'approve'
    ACTION_SUSPEND = 'suspend'
    ACTION_LOGIN   = 'login'
    ACTION_OTHER   = 'other'
    ACTION_CHOICES = [
        (ACTION_CREATE,  'Created'),
        (ACTION_UPDATE,  'Updated'),
        (ACTION_DELETE,  'Deleted'),
        (ACTION_APPROVE, 'Approved'),
        (ACTION_SUSPEND, 'Suspended'),
        (ACTION_LOGIN,   'Logged In'),
        (ACTION_OTHER,   'Other'),
    ]

    actor       = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                    null=True, related_name='audit_logs')
    action      = models.CharField(max_length=20, choices=ACTION_CHOICES, default=ACTION_OTHER)
    description = models.TextField()
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.actor} – {self.get_action_display()} – {self.created_at:%Y-%m-%d %H:%M}'


class Dispute(models.Model):
    STATUS_OPEN     = 'open'
    STATUS_RESOLVED = 'resolved'
    STATUS_CLOSED   = 'closed'
    STATUS_CHOICES  = [
        (STATUS_OPEN,     'Open'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_CLOSED,   'Closed'),
    ]

    order       = models.ForeignKey('orders.Order', on_delete=models.CASCADE,
                                    related_name='disputes')
    raised_by   = models.ForeignKey('accounts.User', on_delete=models.CASCADE,
                                    related_name='disputes')
    subject     = models.CharField(max_length=300)
    description = models.TextField()
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    resolved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='resolved_disputes')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Dispute #{self.pk} – {self.subject}'
