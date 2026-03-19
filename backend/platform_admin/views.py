from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from core.decorators import owner_required
from .services import CloudAPIClient
import logging

logger = logging.getLogger(__name__)


def _get_client():
    return CloudAPIClient()


@login_required
@owner_required
def dashboard(request):
    try:
        client = _get_client()
        licenses = client.list_licenses()
        total = len(licenses)
        active = sum(1 for lic in licenses if lic.get('is_active'))
        expired = sum(1 for lic in licenses if not lic.get('is_active'))
        trials = sum(1 for lic in licenses if lic.get('plan') == 'TRIAL')
    except Exception as e:
        logger.error("Cloud API error: %s", e)
        licenses, total, active, expired, trials = [], 0, 0, 0, 0
        messages.warning(request, _("Could not connect to Cloud API."))

    return render(request, 'platform_admin/dashboard.html', {
        'licenses': licenses,
        'total': total,
        'active': active,
        'expired': expired,
        'trials': trials,
        'active_portal_tab': 'dashboard',
    })


@login_required
@owner_required
def license_list(request):
    try:
        client = _get_client()
        plan_filter = request.GET.get('plan', '')
        active_filter = request.GET.get('is_active', '')
        search = request.GET.get('search', '')

        kwargs = {}
        if plan_filter:
            kwargs['plan'] = plan_filter
        if active_filter:
            kwargs['is_active'] = active_filter == 'true'
        if search:
            kwargs['search'] = search

        licenses = client.list_licenses(**kwargs)
    except Exception as e:
        logger.error("Cloud API error: %s", e)
        licenses = []
        messages.warning(request, _("Could not connect to Cloud API."))

    return render(request, 'platform_admin/license_list.html', {
        'licenses': licenses,
        'plan_filter': plan_filter if 'plan_filter' in dir() else '',
        'active_filter': active_filter if 'active_filter' in dir() else '',
        'search': search if 'search' in dir() else '',
        'active_portal_tab': 'licenses',
    })


@login_required
@owner_required
def license_detail(request, hw_id):
    try:
        client = _get_client()
        license_data = client.get_license(hw_id)
    except Exception as e:
        logger.error("Cloud API error: %s", e)
        messages.error(request, _("License not found or Cloud API unavailable."))
        return redirect('platform_license_list')

    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'update':
                update_data = {}
                for field in ['plan', 'notes', 'expiration_date', 'client_name', 'client_email']:
                    val = request.POST.get(field, '').strip()
                    if val:
                        update_data[field] = val
                if update_data:
                    client.update_license(hw_id, update_data)
                    messages.success(request, _("License updated successfully."))
                    return redirect('platform_license_detail', hw_id=hw_id)
        except Exception as e:
            logger.error("Cloud API error: %s", e)
            messages.error(request, _("Error updating license."))

    return render(request, 'platform_admin/license_detail.html', {
        'license': license_data,
        'active_portal_tab': 'licenses',
    })


@login_required
@owner_required
def license_create(request):
    if request.method == 'POST':
        try:
            client = _get_client()
            data = {
                'hw_id': request.POST.get('hw_id', '').strip(),
                'client_name': request.POST.get('client_name', '').strip(),
                'client_email': request.POST.get('client_email', '').strip(),
                'company_name': request.POST.get('company_name', '').strip(),
                'company_email': request.POST.get('company_email', '').strip(),
                'company_tax_id': request.POST.get('company_tax_id', '').strip(),
                'plan': request.POST.get('plan', 'MONTHLY'),
                'expiration_date': request.POST.get('expiration_date', ''),
            }
            # Remove empty strings
            data = {k: v for k, v in data.items() if v}
            client.create_license(data)
            messages.success(request, _("License created successfully."))
            return redirect('platform_license_list')
        except Exception as e:
            logger.error("Cloud API error: %s", e)
            messages.error(request, _("Error creating license."))

    return render(request, 'platform_admin/license_create.html', {
        'active_portal_tab': 'create',
    })


@login_required
@owner_required
def license_revoke(request, hw_id):
    if request.method == 'POST':
        try:
            client = _get_client()
            client.revoke_license(hw_id)
            messages.success(request, _("License revoked successfully."))
        except Exception as e:
            logger.error("Cloud API error: %s", e)
            messages.error(request, _("Error revoking license."))
    return redirect('platform_license_detail', hw_id=hw_id)


@login_required
@owner_required
def license_transfer(request):
    if request.method == 'POST':
        try:
            client = _get_client()
            old_hw_id = request.POST.get('old_hw_id', '').strip()
            new_hw_id = request.POST.get('new_hw_id', '').strip()
            client.transfer_license(old_hw_id, new_hw_id)
            messages.success(request, _("License transferred successfully."))
            return redirect('platform_license_list')
        except Exception as e:
            logger.error("Cloud API error: %s", e)
            messages.error(request, _("Error transferring license."))
    return render(request, 'platform_admin/license_transfer.html', {
        'active_portal_tab': 'transfer',
    })


@login_required
@owner_required
def force_password_reset(request, hw_id):
    if request.method == 'POST':
        try:
            client = _get_client()
            client.create_pending_action(hw_id, 'FORCE_PASSWORD_RESET')
            messages.success(request, _("Password reset action queued for this node."))
        except Exception as e:
            logger.error("Cloud API error: %s", e)
            messages.error(request, _("Error creating password reset action."))
    return redirect('platform_license_detail', hw_id=hw_id)
