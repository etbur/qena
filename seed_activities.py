"""
Seed sample tasks, proposals, commissions, vendor payouts and disputes
so every dashboard shows real data.
Run:  python seed_activities.py
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qenagebeya.settings')
django.setup()

from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

from agents.models import Agent, Client, Deal, Task, Proposal, AgentCommission, Inquiry
from vendors.models import Vendor, VendorPayout
from orders.models import Order
from admin_portal.models import AuditLog, Dispute
from accounts.models import User

print("Seeding activity data…")

# ── Agent tasks ───────────────────────────────────────────────────────────────
for agent in Agent.objects.all():
    clients = list(agent.clients.all())
    tasks_data = [
        (f'Follow up with {clients[0].full_name if clients else "client"}',
         Task.PRIORITY_HIGH, Task.STATUS_TODO, date.today() + timedelta(days=1)),
        ('Prepare monthly report', Task.PRIORITY_MEDIUM, Task.STATUS_IN_PROGRESS,
         date.today() + timedelta(days=3)),
        ('Submit commission invoice', Task.PRIORITY_LOW, Task.STATUS_TODO,
         date.today() + timedelta(days=7)),
    ]
    for title, priority, status, due in tasks_data:
        Task.objects.get_or_create(
            agent=agent, title=title,
            defaults={'priority': priority, 'status': status, 'due_date': due,
                      'client': clients[0] if clients else None}
        )

print(f"  {Task.objects.count()} tasks")

# ── Proposals ─────────────────────────────────────────────────────────────────
for agent in Agent.objects.all():
    clients = list(agent.clients.all())
    if clients:
        Proposal.objects.get_or_create(
            agent=agent, client=clients[0],
            title=f'Bulk Purchase Proposal for {clients[0].full_name}',
            defaults={
                'content': 'We propose a bulk purchase arrangement with 15% discount on orders above ETB 50,000.',
                'value': Decimal('50000'),
                'status': Proposal.STATUS_SENT,
                'sent_at': timezone.now(),
            }
        )
        if len(clients) > 1:
            Proposal.objects.get_or_create(
                agent=agent, client=clients[1],
                title=f'Service Agreement — {clients[1].full_name}',
                defaults={
                    'content': 'Annual service agreement covering all product categories.',
                    'value': Decimal('25000'),
                    'status': Proposal.STATUS_ACCEPTED,
                }
            )

print(f"  {Proposal.objects.count()} proposals")

# ── Agent commissions (from closed deals) ────────────────────────────────────
for deal in Deal.objects.filter(status=Deal.STATUS_CLOSED):
    if not AgentCommission.objects.filter(deal=deal).exists():
        rate   = deal.agent.commission_rate / 100
        amount = deal.value * rate
        AgentCommission.objects.create(
            agent=deal.agent, deal=deal, amount=amount,
            note=f'Auto commission on: {deal.title}',
            is_paid=False,
        )

# Mark one per agent as paid
for agent in Agent.objects.all():
    comm = agent.commissions.first()
    if comm:
        comm.is_paid  = True
        comm.paid_at  = timezone.now()
        comm.save()

print(f"  {AgentCommission.objects.count()} commissions")

# ── Vendor payouts ────────────────────────────────────────────────────────────
for vendor in Vendor.objects.filter(status=Vendor.STATUS_APPROVED):
    # Give each vendor some balance first
    vendor.balance = vendor.total_sales * Decimal('0.85')
    vendor.save(update_fields=['balance'])

    VendorPayout.objects.get_or_create(
        vendor=vendor,
        status=VendorPayout.STATUS_PENDING,
        defaults={'amount': min(vendor.balance * Decimal('0.5'), Decimal('50000'))}
    )

print(f"  {VendorPayout.objects.count()} payout requests")

# ── Disputes ──────────────────────────────────────────────────────────────────
orders = list(Order.objects.all()[:3])
customers = list(User.objects.filter(role='customer')[:3])
dispute_data = [
    ('Item not received', 'Order was not delivered within the promised time.',  Dispute.STATUS_OPEN),
    ('Wrong item sent',   'Received a completely different product.',           Dispute.STATUS_OPEN),
    ('Defective product', 'Product stopped working after 2 days of use.',      Dispute.STATUS_RESOLVED),
]
for i, (subject, desc, status) in enumerate(dispute_data):
    if i < len(orders) and i < len(customers):
        Dispute.objects.get_or_create(
            order=orders[i],
            raised_by=customers[i % len(customers)],
            subject=subject,
            defaults={'description': desc, 'status': status}
        )

print(f"  {Dispute.objects.count()} disputes")

# ── More audit logs ───────────────────────────────────────────────────────────
admin = User.objects.filter(username='admin').first()
extra_logs = [
    (AuditLog.ACTION_APPROVE, 'Approved vendor payout #1'),
    (AuditLog.ACTION_UPDATE,  'Updated order QN-001 to Delivered'),
    (AuditLog.ACTION_APPROVE, 'Approved vendor: Mariam Home Decor'),
    (AuditLog.ACTION_OTHER,   'Platform settings reviewed'),
    (AuditLog.ACTION_UPDATE,  'Resolved dispute #1: Item not received'),
]
if admin:
    for action, desc in extra_logs:
        AuditLog.objects.create(actor=admin, action=action,
                                description=desc, ip_address='127.0.0.1')

print(f"  {AuditLog.objects.count()} audit logs")

# ── Inquiries for agents ──────────────────────────────────────────────────────
for agent in Agent.objects.all():
    clients = list(agent.clients.all())
    if clients:
        Inquiry.objects.get_or_create(
            agent=agent,
            subject=f'Pricing inquiry from {clients[0].full_name}',
            defaults={
                'client': clients[0],
                'message': 'Can you provide a custom pricing for bulk orders of Ethiopian coffee?',
                'status': Inquiry.STATUS_PENDING,
            }
        )

print(f"  {Inquiry.objects.count()} inquiries")

print("\n✅ Activity data seeded successfully!")
print(f"   Tasks:       {Task.objects.count()}")
print(f"   Proposals:   {Proposal.objects.count()}")
print(f"   Commissions: {AgentCommission.objects.count()}")
print(f"   Payouts:     {VendorPayout.objects.count()}")
print(f"   Disputes:    {Dispute.objects.count()}")
print(f"   Audit logs:  {AuditLog.objects.count()}")
print(f"   Inquiries:   {Inquiry.objects.count()}")
