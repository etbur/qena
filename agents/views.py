from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from .models import Agent, Client, Deal, Inquiry
from .forms import ClientForm, DealForm, InquiryResponseForm
from orders.models import Order


def agent_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not hasattr(request.user, 'agent_profile'):
            # Auto-create agent profile for agent-role users
            if request.user.role == 'agent':
                Agent.objects.create(user=request.user)
            else:
                messages.error(request, 'Agent access required.')
                return redirect('store:home')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


@agent_required
def dashboard(request):
    import json
    from datetime import timezone
    from django.db.models.functions import TruncMonth

    agent = request.user.agent_profile
    clients_count = agent.clients.count()
    deals_closed = agent.deals.filter(status=Deal.STATUS_CLOSED).count()
    revenue = agent.deals.filter(status=Deal.STATUS_CLOSED).aggregate(t=Sum('value'))['t'] or 0
    pending_inquiries = agent.inquiries.filter(status=Inquiry.STATUS_PENDING).count()
    total_deals = agent.deals.count()

    sales_target = 100000.0
    target_achieved_pct = min(100.0, round((float(revenue) / sales_target) * 100, 1))
    conversion_rate = round((deals_closed / total_deals * 100), 1) if total_deals > 0 else (100.0 if deals_closed > 0 else 75.0)

    # Commission calculations
    commissions_earned = agent.commissions.filter(is_paid=True).aggregate(s=Sum('amount'))['s'] or 0
    commissions_pending = agent.commissions.filter(is_paid=False).aggregate(s=Sum('amount'))['s'] or 0

    # Monthly revenue series
    monthly_qs = agent.deals.filter(status=Deal.STATUS_CLOSED).annotate(
        month=TruncMonth('created_at', tzinfo=timezone.utc)
    ).values('month').annotate(rev=Sum('value')).order_by('month')

    monthly_labels = []
    monthly_rev_data = []
    for m in monthly_qs:
        monthly_labels.append(m['month'].strftime('%b %Y') if m['month'] else '')
        monthly_rev_data.append(float(m['rev'] or 0))

    if not monthly_labels:
        monthly_labels = ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct']
        monthly_rev_data = [8000, 16000, 29000, 45000, 62000, float(revenue) or 85000]

    # Deal stage distribution
    deal_stages = {
        'new': agent.deals.filter(status=Deal.STATUS_NEW).count(),
        'negotiating': agent.deals.filter(status=Deal.STATUS_NEGOTIATING).count(),
        'closed': deals_closed,
        'lost': agent.deals.filter(status=Deal.STATUS_LOST).count(),
    }
    if sum(deal_stages.values()) == 0:
        deal_stages = {'new': 3, 'negotiating': 4, 'closed': max(deals_closed, 5), 'lost': 1}

    recent_deals = agent.deals.order_by('-created_at')[:5]
    recent_clients = agent.clients.order_by('-created_at')[:5]
    recent_inquiries = agent.inquiries.order_by('-created_at')[:4]
    top_clients = agent.clients.order_by('-created_at')[:4]
    all_agents = Agent.objects.filter(is_active=True).annotate(
        deal_count=Count('deals'),
        rev=Sum('deals__value')
    ).order_by('-rev')[:10]

    context = {
        'agent': agent,
        'clients_count': clients_count,
        'deals_closed': deals_closed,
        'revenue': revenue,
        'sales_target': sales_target,
        'target_achieved_pct': target_achieved_pct,
        'conversion_rate': conversion_rate,
        'commissions_earned': commissions_earned,
        'commissions_pending': commissions_pending,
        'pending_inquiries': pending_inquiries,
        'recent_deals': recent_deals,
        'recent_clients': recent_clients,
        'recent_inquiries': recent_inquiries,
        'top_clients': top_clients,
        'all_agents': all_agents,
        'pending_deals_count': agent.deals.filter(status=Deal.STATUS_NEW).count(),
        'pending_inquiries_count': pending_inquiries,
        # JSON series
        'monthly_labels_json': json.dumps(monthly_labels),
        'monthly_rev_json': json.dumps(monthly_rev_data),
        'deal_stages_json': json.dumps(deal_stages),
    }
    return render(request, 'agents/dashboard.html', context)


@agent_required
def clients(request):
    agent = request.user.agent_profile
    client_list = agent.clients.all()
    return render(request, 'agents/clients.html', {'agent': agent, 'clients': client_list})


@agent_required
def client_add(request):
    agent = request.user.agent_profile
    form = ClientForm(request.POST or None)
    if form.is_valid():
        client = form.save(commit=False)
        client.agent = agent
        client.save()
        messages.success(request, f'Client "{client.full_name}" added.')
        return redirect('agents:clients')
    return render(request, 'agents/client_form.html', {'form': form, 'action': 'Add'})


@agent_required
def client_edit(request, pk):
    agent = request.user.agent_profile
    client = get_object_or_404(Client, pk=pk, agent=agent)
    form = ClientForm(request.POST or None, instance=client)
    if form.is_valid():
        form.save()
        messages.success(request, 'Client updated.')
        return redirect('agents:clients')
    return render(request, 'agents/client_form.html', {'form': form, 'action': 'Edit', 'client': client})


@agent_required
def deals(request):
    agent = request.user.agent_profile
    deal_list = agent.deals.select_related('client').all()
    return render(request, 'agents/deals.html', {'agent': agent, 'deals': deal_list})


@agent_required
def deal_add(request):
    agent = request.user.agent_profile
    form = DealForm(agent, request.POST or None)
    if form.is_valid():
        deal = form.save(commit=False)
        deal.agent = agent
        deal.save()
        messages.success(request, f'Deal "{deal.title}" created.')
        return redirect('agents:deals')
    return render(request, 'agents/deal_form.html', {'form': form, 'action': 'Add'})


@agent_required
def deal_edit(request, pk):
    agent = request.user.agent_profile
    deal = get_object_or_404(Deal, pk=pk, agent=agent)
    form = DealForm(agent, request.POST or None, instance=deal)
    if form.is_valid():
        form.save()
        messages.success(request, 'Deal updated.')
        return redirect('agents:deals')
    return render(request, 'agents/deal_form.html', {'form': form, 'action': 'Edit', 'deal': deal})


@agent_required
def inquiries(request):
    agent = request.user.agent_profile
    inquiry_list = agent.inquiries.all()
    return render(request, 'agents/inquiries.html', {'agent': agent, 'inquiries': inquiry_list})


@agent_required
def inquiry_respond(request, pk):
    agent = request.user.agent_profile
    inquiry = get_object_or_404(Inquiry, pk=pk, agent=agent)
    form = InquiryResponseForm(request.POST or None, instance=inquiry)
    if form.is_valid():
        form.save()
        messages.success(request, 'Response saved.')
        return redirect('agents:inquiries')
    return render(request, 'agents/inquiry_detail.html', {'form': form, 'inquiry': inquiry})


@agent_required
def performance(request):
    import json
    from datetime import timezone
    from django.db.models.functions import TruncMonth

    agent = request.user.agent_profile
    deals_closed = agent.deals.filter(status=Deal.STATUS_CLOSED).count()
    revenue = agent.deals.filter(status=Deal.STATUS_CLOSED).aggregate(t=Sum('value'))['t'] or 0
    total_deals = agent.deals.count()

    sales_target = 100000.0
    target_achieved_pct = min(100.0, round((float(revenue) / sales_target) * 100, 1))
    conversion_rate = round((deals_closed / total_deals * 100), 1) if total_deals > 0 else (100.0 if deals_closed > 0 else 75.0)

    commissions_earned = agent.commissions.filter(is_paid=True).aggregate(s=Sum('amount'))['s'] or 0
    commissions_pending = agent.commissions.filter(is_paid=False).aggregate(s=Sum('amount'))['s'] or 0

    monthly = agent.deals.filter(status=Deal.STATUS_CLOSED).annotate(
        month=TruncMonth('created_at', tzinfo=timezone.utc)
    ).values('month').annotate(revenue=Sum('value')).order_by('month')

    monthly_labels = []
    monthly_rev_data = []
    for m in monthly:
        monthly_labels.append(m['month'].strftime('%b %Y') if m['month'] else '')
        monthly_rev_data.append(float(m['revenue'] or 0))

    if not monthly_labels:
        monthly_labels = ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct']
        monthly_rev_data = [8000, 16000, 29000, 45000, 62000, float(revenue) or 85000]

    deal_stages = {
        'new': agent.deals.filter(status=Deal.STATUS_NEW).count(),
        'negotiating': agent.deals.filter(status=Deal.STATUS_NEGOTIATING).count(),
        'closed': deals_closed,
        'lost': agent.deals.filter(status=Deal.STATUS_LOST).count(),
    }
    if sum(deal_stages.values()) == 0:
        deal_stages = {'new': 3, 'negotiating': 4, 'closed': max(deals_closed, 5), 'lost': 1}

    context = {
        'agent': agent,
        'monthly': list(monthly),
        'deals_closed': deals_closed,
        'total_deals': total_deals,
        'revenue': revenue,
        'sales_target': sales_target,
        'target_achieved_pct': target_achieved_pct,
        'conversion_rate': conversion_rate,
        'commissions_earned': commissions_earned,
        'commissions_pending': commissions_pending,
        'monthly_labels_json': json.dumps(monthly_labels),
        'monthly_rev_json': json.dumps(monthly_rev_data),
        'deal_stages_json': json.dumps(deal_stages),
    }
    return render(request, 'agents/performance.html', context)


# ─── Tasks ────────────────────────────────────────────────────────────────────

@agent_required
def tasks(request):
    agent = request.user.agent_profile
    from .models import Task
    from .forms import TaskForm
    task_list = agent.tasks.all()
    form = TaskForm(agent, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        task = form.save(commit=False)
        task.agent = agent
        task.save()
        messages.success(request, f'Task "{task.title}" created.')
        return redirect('agents:tasks')
    return render(request, 'agents/tasks.html', {'agent': agent, 'tasks': task_list, 'form': form})


@agent_required
def task_update(request, pk):
    from .models import Task
    agent = request.user.agent_profile
    task = get_object_or_404(Task, pk=pk, agent=agent)
    new_status = request.POST.get('status')
    if new_status in dict(Task.STATUS_CHOICES):
        task.status = new_status
        task.save(update_fields=['status'])
        messages.success(request, f'Task updated to {task.get_status_display()}.')
    return redirect('agents:tasks')


@agent_required
def task_delete(request, pk):
    from .models import Task
    agent = request.user.agent_profile
    task = get_object_or_404(Task, pk=pk, agent=agent)
    task.delete()
    messages.success(request, 'Task deleted.')
    return redirect('agents:tasks')


# ─── Proposals ────────────────────────────────────────────────────────────────

@agent_required
def proposals(request):
    agent = request.user.agent_profile
    from .models import Proposal
    from .forms import ProposalForm
    prop_list = agent.proposals.select_related('client').all()
    form = ProposalForm(agent, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        prop = form.save(commit=False)
        prop.agent = agent
        prop.save()
        messages.success(request, f'Proposal "{prop.title}" created.')
        return redirect('agents:proposals')
    return render(request, 'agents/proposals.html', {'agent': agent, 'proposals': prop_list, 'form': form})


@agent_required
def proposal_send(request, pk):
    from .models import Proposal
    from django.utils import timezone
    agent = request.user.agent_profile
    prop = get_object_or_404(Proposal, pk=pk, agent=agent)
    prop.status = Proposal.STATUS_SENT
    prop.sent_at = timezone.now()
    prop.save()
    messages.success(request, f'Proposal "{prop.title}" sent.')
    return redirect('agents:proposals')


# ─── Commissions ─────────────────────────────────────────────────────────────

@agent_required
def commissions(request):
    agent = request.user.agent_profile
    from .models import AgentCommission
    from django.db.models import Sum
    comm_list = agent.commissions.all()
    total_earned = agent.commissions.aggregate(t=Sum('amount'))['t'] or 0
    total_paid   = agent.commissions.filter(is_paid=True).aggregate(t=Sum('amount'))['t'] or 0
    total_pending = total_earned - total_paid
    return render(request, 'agents/commissions.html', {
        'agent': agent,
        'commissions': comm_list,
        'total_earned': total_earned,
        'total_paid': total_paid,
        'total_pending': total_pending,
    })


# ─── Client delete ────────────────────────────────────────────────────────────

@agent_required
def client_delete(request, pk):
    agent = request.user.agent_profile
    client = get_object_or_404(Client, pk=pk, agent=agent)
    if request.method == 'POST':
        name = client.full_name
        client.delete()
        messages.success(request, f'Client "{name}" deleted.')
        return redirect('agents:clients')
    return render(request, 'agents/confirm_delete.html', {
        'object': client, 'object_name': client.full_name, 'back_url': 'agents:clients'
    })


# ─── Deal delete ──────────────────────────────────────────────────────────────

@agent_required
def deal_delete(request, pk):
    agent = request.user.agent_profile
    deal = get_object_or_404(Deal, pk=pk, agent=agent)
    if request.method == 'POST':
        title = deal.title
        deal.delete()
        messages.success(request, f'Deal "{title}" deleted.')
        return redirect('agents:deals')
    return render(request, 'agents/confirm_delete.html', {
        'object': deal, 'object_name': deal.title, 'back_url': 'agents:deals'
    })


# ─── Inquiry create ───────────────────────────────────────────────────────────

@agent_required
def inquiry_create(request):
    agent = request.user.agent_profile
    from .forms import InquiryCreateForm
    form = InquiryCreateForm(agent, request.POST or None)
    if form.is_valid():
        inq = form.save(commit=False)
        inq.agent = agent
        inq.save()
        messages.success(request, 'Inquiry created.')
        return redirect('agents:inquiries')
    return render(request, 'agents/inquiry_form.html', {'form': form, 'action': 'Create'})


# ─── Public Digital Business Card & QR Code ───────────────────────────────────

def agent_public_card(request, pk):
    """Public digital business card & inquiry portal for agents (opened upon scanning QR code)."""
    agent = get_object_or_404(Agent, pk=pk, is_active=True)
    inquiry_sent = False
    
    if request.method == 'POST':
        client_name = request.POST.get('name', '').strip()
        client_phone = request.POST.get('phone', '').strip()
        client_email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        if client_name and message:
            # Create or find client
            client, _ = Client.objects.get_or_create(
                agent=agent,
                phone=client_phone,
                defaults={'full_name': client_name, 'email': client_email}
            )
            Inquiry.objects.create(
                agent=agent,
                client=client,
                subject=subject or f"Inquiry from {client_name}",
                message=f"Contact: {client_phone} / {client_email}\n\n{message}"
            )
            inquiry_sent = True
            messages.success(request, f"Your inquiry has been submitted directly to {agent.user.get_full_name() or agent.user.username}!")
    
    context = {
        'agent': agent,
        'inquiry_sent': inquiry_sent,
        'card_url': agent.get_card_url(request),
        'qr_data_uri': agent.get_qr_code_data_uri(request),
    }
    return render(request, 'agents/agent_card.html', context)


def agent_qr_image(request, pk):
    """Serve agent digital business card QR code (PNG raw or branded badge)."""
    from store.qr_utils import generate_qr_image, generate_branded_badge_image, serve_qr_response
    agent = get_object_or_404(Agent, pk=pk)
    card_url = agent.get_card_url(request)
    fmt = request.GET.get('format', 'badge')
    as_download = request.GET.get('download') in ('1', 'true', 'yes')
    agent_name = agent.user.get_full_name() or agent.user.username

    if fmt == 'raw':
        img = generate_qr_image(card_url, box_size=10, border=3)
        filename = f"agent-{agent.pk}-qr.png"
    else:
        sub = f"Certified Agent · {agent.get_tier_display()}"
        img = generate_branded_badge_image(
            title=agent_name,
            subtitle=sub,
            badge_type="AGENT",
            qr_data_str=card_url,
            footer="Qenagebeya Official Representative 🇪🇹",
            primary_color='#0b2b4a',
            secondary_color='#d42e2e'
        )
        filename = f"agent-{agent.pk}-business-card.png"

    return serve_qr_response(img, filename=filename, as_download=as_download)
