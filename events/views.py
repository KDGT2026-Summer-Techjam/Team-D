from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import Event
from interactions.models import EventView, Favorite, Like, Rating
from interactions.services import InteractionService
from .services import EventService


EVENT_SORT_FIELDS = {
    "start_asc": ("start_datetime", "pk"),
    "start_desc": ("-start_datetime", "pk"),
    "newest": ("-created_at", "pk"),
}


def event_list(request):
    selected_sort = request.GET.get("sort", "start_asc")
    if selected_sort not in EVENT_SORT_FIELDS:
        selected_sort = "start_asc"

    events = (
        EventService.get_published_events()
        .select_related("organizer")
        .prefetch_related("tags")
        .order_by(*EVENT_SORT_FIELDS[selected_sort])
    )
    return render(
        request,
        "events/event_list.html",
        {"events": events, "selected_sort": selected_sort},
    )


def event_detail(request, pk):
    event = get_object_or_404(
        EventService.get_published_events()
        .select_related("organizer")
        .prefetch_related("tags", "ratings__user"),
        pk=pk,
    )
    stats = InteractionService.get_event_stats(event)

    is_favorited = False
    is_liked = False
    user_rating = None
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(event=event, user=request.user).exists()
        is_liked = Like.objects.filter(event=event, user=request.user).exists()
        user_rating = Rating.objects.filter(event=event, user=request.user).first()
        InteractionService.record_view(event=event, user=request.user)

    context = {
        "event": event,
        "stats": stats,
        "is_favorited": is_favorited,
        "is_liked": is_liked,
        "ratings": event.ratings.select_related("user"),
        "user_rating": user_rating,
        "rating_choices": range(5, -1, -1),
    }
    return render(request, "events/event_detail.html", context)

@login_required
def my_favorites(request):
    events = (
        EventService.get_published_events()
        .filter(favorites__user=request.user)
        .select_related("organizer")
        .prefetch_related("tags")
        .order_by("start_datetime")
    )
    return render(request, "events/my_favorites.html", {"events": events})

@login_required
def my_view_history(request):
    views = (
        EventView.objects.filter(
            user=request.user,
            event__status=Event.Status.PUBLISH,
        )
        .select_related("event", "event__organizer")
        .prefetch_related("event__tags")
        .order_by("-viewed_at")
    )
    return render(request, "events/my_view_history.html", {"views": views})
