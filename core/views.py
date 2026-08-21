from django.shortcuts import render


def home(request):
    return render(request, "core/home.html")


def search_results(request):
    return render(request, "core/search_results.html")


def event_create(request):
    return render(request, "core/event_form.html")


def event_detail(request, event_id):
    return render(request, "core/event_detail.html")


def review_create(request, event_id):
    return render(request, "core/review_form.html")


def review_detail(request, review_id):
    return render(request, "core/review_detail.html")
