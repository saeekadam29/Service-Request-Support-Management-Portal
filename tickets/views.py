from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import render, redirect, get_object_or_404

from .forms import TicketForm, TicketManageForm, CommentForm, TicketFilterForm
from .models import Ticket, TicketHistory
from .permissions import can_view_ticket, can_edit_ticket_status


def _tickets_for_user(user):
    """Base queryset scoped by role: customers only see their own tickets."""
    qs = Ticket.objects.select_related('category', 'customer', 'assigned_agent')
    if user.profile.is_customer:
        return qs.filter(customer=user)
    if user.profile.is_agent:
        return qs  # agents can browse all tickets, but dashboard highlights their own
    return qs  # admin sees everything


@login_required
def dashboard_view(request):
    profile = request.user.profile
    base_qs = _tickets_for_user(request.user)

    stats = {
        'total': base_qs.count(),
        'open': base_qs.filter(status=Ticket.Status.OPEN).count(),
        'in_progress': base_qs.filter(status=Ticket.Status.IN_PROGRESS).count(),
        'resolved': base_qs.filter(status=Ticket.Status.RESOLVED).count(),
        'closed': base_qs.filter(status=Ticket.Status.CLOSED).count(),
        'critical': base_qs.filter(priority=Ticket.Priority.CRITICAL).exclude(
            status=Ticket.Status.CLOSED).count(),
    }

    if profile.is_agent:
        stats['assigned_to_me'] = Ticket.objects.filter(assigned_agent=request.user).exclude(
            status=Ticket.Status.CLOSED).count()

    recent_tickets = base_qs.order_by('-created_at')[:5]

    category_breakdown = base_qs.values('category__name').annotate(count=Count('id')).order_by('-count')

    return render(request, 'tickets/dashboard.html', {
        'stats': stats,
        'recent_tickets': recent_tickets,
        'category_breakdown': category_breakdown,
    })


@login_required
def ticket_list_view(request):
    profile = request.user.profile
    qs = _tickets_for_user(request.user)

    filter_form = TicketFilterForm(request.GET or None)
    if filter_form.is_valid():
        q = filter_form.cleaned_data.get('q')
        status = filter_form.cleaned_data.get('status')
        priority = filter_form.cleaned_data.get('priority')
        category = filter_form.cleaned_data.get('category')
        assigned_agent = filter_form.cleaned_data.get('assigned_agent')

        if q:
            query = Q(title__icontains=q)
            if q.isdigit():
                query |= Q(id=int(q))
            qs = qs.filter(query)
        if status:
            qs = qs.filter(status=status)
        if priority:
            qs = qs.filter(priority=priority)
        if category:
            qs = qs.filter(category=category)
        if assigned_agent:
            qs = qs.filter(assigned_agent=assigned_agent)

    qs = qs.order_by('-created_at')
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'tickets/ticket_list.html', {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'can_manage': profile.is_admin or profile.is_agent,
    })


@login_required
def ticket_create_view(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.customer = request.user
            ticket.save()
            messages.success(request, f"Ticket #{ticket.id} has been created.")
            return redirect('tickets:ticket_detail', pk=ticket.pk)
    else:
        form = TicketForm()

    return render(request, 'tickets/ticket_form.html', {'form': form, 'is_create': True})


@login_required
def ticket_detail_view(request, pk):
    ticket = get_object_or_404(
        Ticket.objects.select_related('category', 'customer', 'assigned_agent'), pk=pk)

    if not can_view_ticket(request.user, ticket):
        raise PermissionDenied("You do not have permission to view this ticket.")

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.ticket = ticket
            comment.author = request.user
            comment.save()
            TicketHistory.objects.create(
                ticket=ticket, actor=request.user, action=f"{request.user.username} added a comment")
            messages.success(request, "Comment added.")
            return redirect('tickets:ticket_detail', pk=ticket.pk)
    else:
        comment_form = CommentForm()

    return render(request, 'tickets/ticket_detail.html', {
        'ticket': ticket,
        'comments': ticket.comments.select_related('author'),
        'history': ticket.history.select_related('actor'),
        'comment_form': comment_form,
        'can_manage': can_edit_ticket_status(request.user),
    })


@login_required
def ticket_update_view(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    profile = request.user.profile

    is_owner_customer = profile.is_customer and ticket.customer_id == request.user.id
    is_staff_member = profile.is_admin or profile.is_agent

    if not (is_owner_customer or is_staff_member):
        raise PermissionDenied("You do not have permission to edit this ticket.")

    # Customers may only edit title/description/category/priority, and only while still Open.
    if is_owner_customer and not is_staff_member:
        if ticket.status != Ticket.Status.OPEN:
            messages.error(request, "This ticket can no longer be edited by you; it is already in progress.")
            return redirect('tickets:ticket_detail', pk=ticket.pk)

        if request.method == 'POST':
            form = TicketForm(request.POST, instance=ticket)
            if form.is_valid():
                form.save()
                messages.success(request, f"Ticket #{ticket.id} updated.")
                return redirect('tickets:ticket_detail', pk=ticket.pk)
        else:
            form = TicketForm(instance=ticket)
        return render(request, 'tickets/ticket_form.html', {'form': form, 'is_create': False, 'ticket': ticket})

    # Agents/Admins: use the management form (status, priority, assignment, resolution notes)
    if request.method == 'POST':
        # Capture old values BEFORE validating the form: ModelForm.is_valid() calls
        # construct_instance() internally, which already writes the new values onto
        # `ticket` as part of validation - so we must snapshot the old state first.
        old_status = ticket.status
        old_priority = ticket.priority
        old_agent = ticket.assigned_agent_id

        manage_form = TicketManageForm(request.POST, instance=ticket)
        if manage_form.is_valid():
            updated_ticket = manage_form.save()

            if updated_ticket.status != old_status:
                TicketHistory.objects.create(
                    ticket=ticket, actor=request.user,
                    action=f"Status changed from {old_status} to {updated_ticket.status} by {request.user.username}")
            if updated_ticket.priority != old_priority:
                TicketHistory.objects.create(
                    ticket=ticket, actor=request.user,
                    action=f"Priority changed from {old_priority} to {updated_ticket.priority} by {request.user.username}")
            if updated_ticket.assigned_agent_id != old_agent:
                agent_name = updated_ticket.assigned_agent.username if updated_ticket.assigned_agent else "Unassigned"
                TicketHistory.objects.create(
                    ticket=ticket, actor=request.user,
                    action=f"Ticket assigned to {agent_name} by {request.user.username}")

            messages.success(request, f"Ticket #{ticket.id} updated.")
            return redirect('tickets:ticket_detail', pk=ticket.pk)
    else:
        manage_form = TicketManageForm(instance=ticket)

    return render(request, 'tickets/ticket_manage_form.html', {'form': manage_form, 'ticket': ticket})


@login_required
def ticket_delete_view(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    profile = request.user.profile

    is_owner_customer = profile.is_customer and ticket.customer_id == request.user.id
    if not (profile.is_admin or is_owner_customer):
        raise PermissionDenied("You do not have permission to delete this ticket.")

    if request.method == 'POST':
        ticket_id = ticket.id
        ticket.delete()
        messages.success(request, f"Ticket #{ticket_id} was deleted.")
        return redirect('tickets:ticket_list')

    return render(request, 'tickets/ticket_confirm_delete.html', {'ticket': ticket})
