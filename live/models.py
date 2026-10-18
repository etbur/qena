"""
Live stream models.

A Vendor can go live. Viewers join and can:
  - Send chat messages
  - React (❤️ 🔥 👏 😍 🎉)
  - Add products to cart directly from the live stream
  - Ask questions

The host (vendor) can:
  - Pin a product to showcase
  - See live viewer count
  - See chat in real-time
"""
from django.db import models
import uuid


class LiveStream(models.Model):
    STATUS_SCHEDULED = 'scheduled'
    STATUS_LIVE      = 'live'
    STATUS_ENDED     = 'ended'
    STATUS_CHOICES   = [
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_LIVE,      'Live Now'),
        (STATUS_ENDED,     'Ended'),
    ]

    stream_id    = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    vendor       = models.ForeignKey('vendors.Vendor', on_delete=models.CASCADE, related_name='streams')
    title        = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    thumbnail    = models.ImageField(upload_to='live/thumbnails/', blank=True, null=True)
    status       = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_SCHEDULED)

    # Featured product during stream
    pinned_product = models.ForeignKey(
        'store.Product', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='pinned_in_streams'
    )

    # Metrics
    peak_viewers   = models.PositiveIntegerField(default=0)
    total_views    = models.PositiveIntegerField(default=0)
    live_viewers   = models.PositiveIntegerField(default=0)   # current live count
    total_likes    = models.PositiveIntegerField(default=0)
    total_messages = models.PositiveIntegerField(default=0)
    is_paused      = models.BooleanField(default=False)

    # Host WebSocket channel name (for direct signaling)
    host_channel   = models.CharField(max_length=200, blank=True)

    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at   = models.DateTimeField(null=True, blank=True)
    ended_at     = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.vendor.store_name} — {self.title} [{self.status}]'

    @property
    def stream_key(self):
        return str(self.stream_id).replace('-', '')[:16].upper()

    @property
    def channel_name(self):
        return f'live_{self.stream_id}'


class LiveChat(models.Model):
    TYPE_CHAT     = 'chat'
    TYPE_REACTION = 'reaction'
    TYPE_SYSTEM   = 'system'
    TYPE_QUESTION = 'question'
    TYPE_CHOICES  = [
        (TYPE_CHAT,     'Chat'),
        (TYPE_REACTION, 'Reaction'),
        (TYPE_SYSTEM,   'System'),
        (TYPE_QUESTION, 'Question'),
    ]

    stream   = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='messages')
    user     = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=100)   # snapshot (works for anon too)
    msg_type = models.CharField(max_length=12, choices=TYPE_CHOICES, default=TYPE_CHAT)
    text     = models.TextField(max_length=300)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'[{self.stream.title}] {self.username}: {self.text[:40]}'
