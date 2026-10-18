from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='agents.Deal')
def create_commission_on_deal_close(sender, instance, created, **kwargs):
    """Automatically create an AgentCommission when a deal is closed."""
    from .models import AgentCommission, Deal
    if not created and instance.status == Deal.STATUS_CLOSED:
        # Only create once per deal
        if not AgentCommission.objects.filter(deal=instance).exists():
            rate = instance.agent.commission_rate / 100
            amount = instance.value * rate
            if amount > 0:
                AgentCommission.objects.create(
                    agent=instance.agent,
                    deal=instance,
                    amount=amount,
                    note=f'Commission on deal: {instance.title}',
                )
