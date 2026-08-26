from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from interactions.models import Favorite, Like
from interactions.services import InteractionService
from .models import Event
from .services import EventService


def event_list(request):
    events = EventService.get_published_events()
    return render(request, "events/event_list.html", {"events": events})


def event_detail(request, pk):
    event = get_object_or_404(EventService.get_published_events(), pk=pk)

    if request.user.is_authenticated:
        InteractionService.record_view(event=event, user=request.user)

    stats = InteractionService.get_event_stats(event)

    is_favorited = False
    is_liked = False
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(event=event, user=request.user).exists()
        is_liked = Like.objects.filter(event=event, user=request.user).exists()

    context = {
        "event": event,
        "stats": stats,
        "is_favorited": is_favorited,
        "is_liked": is_liked,
    }
    return render(request, "events/event_detail.html", context)


@login_required
def my_favorites(request):
    events = Event.objects.filter(favorites__user=request.user)
    return render(request, "events/my_favorites.html", {"events": events})


@login_required
def my_view_history(request):
    from interactions.models import EventView
    views = EventView.objects.filter(user=request.user).select_related("event")
    return render(request, "events/my_view_history.html", {"views": views})