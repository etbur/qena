from .models import Agent, Deal, Inquiry


def agent_badges(request):
    """Inject sidebar badge counts for agent portal pages."""
    counts = {'pending_deals_count': 0, 'pending_inquiries_count': 0}
    user = getattr(request, 'user', None)
    if user and user.is_authenticated and hasattr(user, 'agent_profile'):
        agent = user.agent_profile
        counts['pending_deals_count'] = agent.deals.filter(status=Deal.STATUS_NEW).count()
        counts['pending_inquiries_count'] = agent.inquiries.filter(status=Inquiry.STATUS_PENDING).count()
    return counts
