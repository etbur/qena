from django.urls import path
from . import views

app_name = 'agents'

urlpatterns = [
    path('dashboard/',                          views.dashboard,         name='dashboard'),
    # Clients
    path('clients/',                            views.clients,           name='clients'),
    path('clients/add/',                        views.client_add,        name='client_add'),
    path('clients/<int:pk>/edit/',              views.client_edit,       name='client_edit'),
    path('clients/<int:pk>/delete/',            views.client_delete,     name='client_delete'),
    # Deals
    path('deals/',                              views.deals,             name='deals'),
    path('deals/add/',                          views.deal_add,          name='deal_add'),
    path('deals/<int:pk>/edit/',                views.deal_edit,         name='deal_edit'),
    path('deals/<int:pk>/delete/',              views.deal_delete,       name='deal_delete'),
    # Inquiries
    path('inquiries/',                          views.inquiries,         name='inquiries'),
    path('inquiries/create/',                   views.inquiry_create,    name='inquiry_create'),
    path('inquiries/<int:pk>/respond/',         views.inquiry_respond,   name='inquiry_respond'),
    # Tasks
    path('tasks/',                              views.tasks,             name='tasks'),
    path('tasks/<int:pk>/update/',              views.task_update,       name='task_update'),
    path('tasks/<int:pk>/delete/',              views.task_delete,       name='task_delete'),
    # Proposals
    path('proposals/',                          views.proposals,         name='proposals'),
    path('proposals/<int:pk>/send/',            views.proposal_send,     name='proposal_send'),
    # Commissions
    path('commissions/',                        views.commissions,       name='commissions'),
    # Performance
    path('performance/',                        views.performance,       name='performance'),
    # Public digital card & QR code
    path('card/<int:pk>/',                      views.agent_public_card, name='agent_card'),
    path('qr/<int:pk>/',                        views.agent_qr_image,    name='agent_qr'),
]
