from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm, ProfileForm
from .models import User


# ─── Helper ──────────────────────────────────────────────────────────────────

def _portal_redirect(user):
    """Return the correct redirect URL for a given user's role."""
    if user.role == User.ROLE_ADMIN or user.is_staff or user.is_superuser:
        return redirect('admin_portal:dashboard')
    elif user.role == User.ROLE_VENDOR:
        if hasattr(user, 'vendor_profile'):
            return redirect('vendors:dashboard')
        return redirect('vendors:setup')
    elif user.role == User.ROLE_AGENT:
        return redirect('agents:dashboard')
    return redirect('store:home')


# ─── Role-based redirect (used by LOGIN_REDIRECT_URL fallback) ───────────────

@login_required
def role_redirect(request):
    """
    Django calls this when LOGIN_REDIRECT_URL is hit.
    We immediately send users to their correct portal.
    """
    return _portal_redirect(request.user)


# ─── Register ────────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return _portal_redirect(request.user)

    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(
            request,
            f'Welcome to Qenagebeya, {user.first_name or user.username}!'
        )
        return _portal_redirect(user)

    return render(request, 'accounts/register.html', {'form': form})


# ─── Login ───────────────────────────────────────────────────────────────────

def login_view(request):
    # Already logged in → go to correct portal
    if request.user.is_authenticated:
        return _portal_redirect(request.user)

    form = LoginForm(data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(
            request,
            f'Welcome back, {user.first_name or user.username}!'
        )

        # If there's a safe ?next= param, use it (e.g. from @login_required)
        next_url = request.GET.get('next', '').strip()
        if next_url and next_url.startswith('/') and 'login' not in next_url:
            return redirect(next_url)

        # Otherwise go to the user's portal
        return _portal_redirect(user)

    return render(request, 'accounts/login.html', {'form': form})


# ─── Logout ──────────────────────────────────────────────────────────────────

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('store:home')


# ─── Profile ─────────────────────────────────────────────────────────────────

@login_required
def profile_view(request):
    form = ProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=request.user
    )
    if form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'form': form})
