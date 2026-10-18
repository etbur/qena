from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CUSTOMER = 'customer'
    ROLE_VENDOR = 'vendor'
    ROLE_AGENT = 'agent'
    ROLE_ADMIN = 'admin'

    ROLE_CHOICES = [
        (ROLE_CUSTOMER, 'Customer'),
        (ROLE_VENDOR, 'Vendor'),
        (ROLE_AGENT, 'Agent'),
        (ROLE_ADMIN, 'Admin'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='UAE')

    @property
    def is_vendor(self):
        return self.role == self.ROLE_VENDOR

    @property
    def is_agent(self):
        return self.role == self.ROLE_AGENT

    @property
    def is_customer(self):
        return self.role == self.ROLE_CUSTOMER

    @property
    def is_admin_user(self):
        return self.role == self.ROLE_ADMIN or self.is_staff

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'
