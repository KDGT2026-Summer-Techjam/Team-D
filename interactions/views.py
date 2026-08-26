from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from events.services import EventService
from .models import Favorite, Like
from .services import InteractionService


@login_required
@require_POST
def toggle_favorite(request, pk):
    event = get_object_or_404(EventService.get_published_events(), pk=pk)
    try:
        if Favorite.objects.filter(event=event, user=request.user).exists():
            InteractionService.remove_favorite(event=event, user=request.user)
        else:
            InteractionService.add_favorite(event=event, user=request.user)
    except ValidationError:
        pass
    return redirect("events:event_detail", pk=pk)



@login_required
@require_POST
def toggle_like(request, pk):
    event = get_object_or_404(EventService.get_published_events(), pk=pk)
    try:
        if Like.objects.filter(event=event, user=request.user).exists():
            InteractionService.remove_like(event=event, user=request.user)
        else:
            InteractionService.add_like(event=event, user=request.user)
    except ValidationError:
        pass
    return redirect("events:event_detail", pk=pk)


@login_required
@require_POST
def submit_review(request, pk):
    event = get_object_or_404(EventService.get_published_events(), pk=pk)
    rating = request.POST.get("rating")
    comment = request.POST.get("comment", "")

    try:
        InteractionService.submit_review(
            event=event, user=request.user, rating=rating, comment=comment
        )
    except ValidationError:
        pass

    return redirect("events:event_detail", pk=pk)