import uuid
from io import BytesIO

import qrcode
from django.conf import settings
from django.core.files import File
from django.db import models

from apps.core.models import TimeStampedModel


class Restaurant(TimeStampedModel):
    """Each restaurant is a tenant in the system."""
    owner = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE,
        related_name='owned_restaurants'
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='restaurants/logos/', blank=True, null=True)

    # Contact & Location
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Pakistan')
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True)

    # Business settings
    currency = models.CharField(max_length=3, default='PKR')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    service_charge_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    # Operating hours: {"mon": {"open": "09:00", "close": "23:00"}, ...}
    operating_hours = models.JSONField(default=dict, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    is_manually_closed = models.BooleanField(
        default=False, help_text='Admin can manually close the restaurant'
    )
    closure_reason = models.CharField(
        max_length=500, blank=True, default='',
        help_text='Reason shown to customers when manually closed'
    )

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'is_approved']),
        ]

    def __str__(self):
        return self.name

    @property
    def is_open(self):
        if self.is_manually_closed:
            return False
        from django.utils import timezone
        now = timezone.localtime()
        day = now.strftime('%a').lower()[:3]
        hours = self.operating_hours.get(day)
        if not hours:
            return False
        current_time = now.strftime('%H:%M')
        return hours.get('open', '00:00') <= current_time <= hours.get('close', '23:59')

    @property
    def closure_status(self):
        """Structured closure info for frontend display."""
        if self.is_manually_closed:
            return {
                'is_open': False,
                'reason': self.closure_reason or 'Restaurant is temporarily closed',
                'status': 'manually_closed',
            }
        from django.utils import timezone
        now = timezone.localtime()
        day = now.strftime('%a').lower()[:3]
        hours = self.operating_hours.get(day)
        if not hours:
            return {
                'is_open': False,
                'reason': 'Restaurant is closed today',
                'status': 'closed_today',
            }
        current_time = now.strftime('%H:%M')
        if hours.get('open', '00:00') <= current_time <= hours.get('close', '23:59'):
            return {'is_open': True, 'reason': '', 'status': 'open'}
        return {
            'is_open': False,
            'reason': f"Restaurant is closed. Hours: {hours.get('open')} - {hours.get('close')}",
            'status': 'outside_hours',
        }


class Table(TimeStampedModel):
    """Physical table in a restaurant, each gets a unique QR code."""

    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        OCCUPIED = 'occupied', 'Occupied'
        RESERVED = 'reserved', 'Reserved'
        MAINTENANCE = 'maintenance', 'Maintenance'

    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name='tables'
    )
    number = models.PositiveIntegerField()
    name = models.CharField(max_length=50, blank=True, help_text='Optional label, e.g. "Patio 1"')
    capacity = models.PositiveIntegerField(default=4)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    qr_code = models.ImageField(upload_to='tables/qr_codes/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['restaurant', 'number']
        ordering = ['number']

    def __str__(self):
        return f"Table {self.number} — {self.restaurant.name}"

    def generate_qr_code(self):
        """Generate QR code that links to the customer ordering page."""
        base_url = getattr(settings, 'QR_CODE_BASE_URL', 'http://localhost:8000')
        url = f"{base_url}/r/{self.restaurant.slug}/table/{self.id}/menu"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        filename = f"qr_{self.restaurant.slug}_table_{self.number}.png"
        self.qr_code.save(filename, File(buffer), save=False)


class TableSession(TimeStampedModel):
    """
    A session starts when a customer scans the QR code and ends
    when the bill is paid / table is cleared.
    """
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='sessions')
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    guest_count = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['table', 'is_active']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        return f"Session {str(self.session_id)[:8]} — Table {self.table.number}"

    def close_session(self):
        from django.utils import timezone
        self.is_active = False
        self.ended_at = timezone.now()
        self.table.status = Table.Status.AVAILABLE
        self.table.save(update_fields=['status', 'updated_at'])
        self.save(update_fields=['is_active', 'ended_at', 'updated_at'])
