from django.contrib import admin
from .models import SavedSearch
# Register your models here.

@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ("owner", "keyword", "location", "notify_enabled", "created_at")
    list_filter = ("notify_enabled",)
    search_fields = ("keyword", "location")
