from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with role-based access for multi-tenant system."""

    class Role(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'Super Admin'
        RESTAURANT_OWNER = 'restaurant_owner', 'Restaurant Owner'
        MANAGER = 'manager', 'Manager'
        STAFF = 'staff', 'Staff'
        KITCHEN = 'kitchen', 'Kitchen Staff'
        CUSTOMER = 'customer', 'Customer'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    restaurant = models.ForeignKey(
        'tenants.Restaurant', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='staff_members'
    )
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['restaurant', 'role']),
        ]

    def __str__(self):
        name = self.get_full_name() or self.username
        return f"{name} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        # Auto-set role for Django superusers
        if self.is_superuser and self.role != self.Role.SUPER_ADMIN:
            self.role = self.Role.SUPER_ADMIN
        super().save(*args, **kwargs)

    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN or self.is_superuser

    @property
    def is_restaurant_owner(self):
        return self.role == self.Role.RESTAURANT_OWNER

    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER

    @property
    def is_kitchen_staff(self):
        return self.role == self.Role.KITCHEN

    @property
    def is_restaurant_member(self):
        """Owner, manager, staff, or kitchen — anyone tied to a restaurant."""
        return self.role in [
            self.Role.RESTAURANT_OWNER,
            self.Role.MANAGER,
            self.Role.STAFF,
            self.Role.KITCHEN,
        ]
