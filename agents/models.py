from django.db import models


class Agent(models.Model):
    TIER_JUNIOR = 'junior'
    TIER_SENIOR = 'senior'
    TIER_LEAD = 'lead'
    TIER_CHOICES = [
        (TIER_JUNIOR, 'Junior Agent'),
        (TIER_SENIOR, 'Senior Agent'),
        (TIER_LEAD, 'Lead Agent'),
    ]

    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='agent_profile')
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default=TIER_JUNIOR)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} ({self.get_tier_display()})'

    @property
    def total_deals(self):
        return self.deals.filter(status=Deal.STATUS_CLOSED).count()

    @property
    def total_revenue(self):
        from django.db.models import Sum
        result = self.deals.filter(status=Deal.STATUS_CLOSED).aggregate(total=Sum('value'))
        return result['total'] or 0

    @property
    def total_commission(self):
        from django.db.models import Sum
        result = self.commissions.aggregate(total=Sum('amount'))
        return result['total'] or 0

    def get_card_url(self, request=None):
        from django.urls import reverse
        from store.qr_utils import get_base_url
        base = get_base_url(request)
        return f"{base}{reverse('agents:agent_card', kwargs={'pk': self.pk})}"

    def get_qr_code_data_uri(self, request=None):
        from store.qr_utils import generate_qr_data_uri
        return generate_qr_data_uri(self.get_card_url(request))

    @property
    def qr_code_data_uri(self):
        return self.get_qr_code_data_uri()

    def get_qr_url(self):
        from django.urls import reverse
        return reverse('agents:agent_qr', kwargs={'pk': self.pk})

    def get_qr_download_url(self):
        from django.urls import reverse
        return f"{reverse('agents:agent_qr', kwargs={'pk': self.pk})}?download=1"

    def get_qr_badge_download_url(self):
        from django.urls import reverse
        return f"{reverse('agents:agent_qr', kwargs={'pk': self.pk})}?format=badge&download=1"


class Client(models.Model):
    TIER_STANDARD = 'standard'
    TIER_SILVER = 'silver'
    TIER_GOLD = 'gold'
    TIER_PLATINUM = 'platinum'
    TIER_CHOICES = [
        (TIER_STANDARD, 'Standard'),
        (TIER_SILVER, 'Silver'),
        (TIER_GOLD, 'Gold'),
        (TIER_PLATINUM, 'Platinum'),
    ]

    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='clients')
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='client_profile', null=True, blank=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    company = models.CharField(max_length=200, blank=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default=TIER_STANDARD)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.full_name


class Deal(models.Model):
    STATUS_NEW = 'new'
    STATUS_NEGOTIATING = 'negotiating'
    STATUS_CLOSED = 'closed'
    STATUS_LOST = 'lost'
    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_NEGOTIATING, 'Negotiating'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_LOST, 'Lost'),
    ]

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='deals')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='deals')
    title = models.CharField(max_length=300)
    value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} – {self.client.full_name}'


class Inquiry(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='inquiries')
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=300)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Inquiries'
        ordering = ['-created_at']

    def __str__(self):
        return self.subject


class Task(models.Model):
    PRIORITY_LOW    = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH   = 'high'
    PRIORITY_CHOICES = [
        (PRIORITY_LOW,    'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH,   'High'),
    ]
    STATUS_TODO       = 'todo'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_DONE       = 'done'
    STATUS_CHOICES = [
        (STATUS_TODO,       'To Do'),
        (STATUS_IN_PROGRESS,'In Progress'),
        (STATUS_DONE,       'Done'),
    ]

    agent    = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='tasks')
    client   = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    title    = models.CharField(max_length=300)
    notes    = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    status   = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_TODO)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date', '-priority']

    def __str__(self):
        return self.title


class Proposal(models.Model):
    STATUS_DRAFT    = 'draft'
    STATUS_SENT     = 'sent'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_DRAFT,    'Draft'),
        (STATUS_SENT,     'Sent'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    agent   = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='proposals')
    client  = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='proposals')
    title   = models.CharField(max_length=300)
    content = models.TextField()
    value   = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status  = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} → {self.client.full_name}'


class AgentCommission(models.Model):
    agent  = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='commissions')
    deal   = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='commissions', null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    note   = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.agent} – ETB {self.amount}'
