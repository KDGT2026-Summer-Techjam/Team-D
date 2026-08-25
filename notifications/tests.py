from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from events.models import Event, Tag
from notifications.models import Notification
from notifications.services import EventMatchNotifier, NotificationService
from search.services import SavedSearchService

User = get_user_model()


def _make_event(*, organizer, title="イベント", status=Event.Status.PUBLISH,
                 start_offset_days=1, duration_days=1):
    start = timezone.now() + timedelta(days=start_offset_days)
    end = start + timedelta(days=duration_days)
    return Event.objects.create(
        title=title,
        organizer=organizer,
        start_datetime=start,
        end_datetime=end,
        status=status,
    )


class NotificationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user", password="pass12345")
        self.event = _make_event(organizer=self.user)
        self.saved_search = SavedSearchService.create(owner=self.user, keyword="花火")

    def test_duplicate_notification_is_rejected_by_unique_constraint(self):
        Notification.objects.create(
            user=self.user,
            event=self.event,
            saved_search=self.saved_search,
            message="一致しました",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Notification.objects.create(
                    user=self.user,
                    event=self.event,
                    saved_search=self.saved_search,
                    message="重複通知",
                )


class NotificationServiceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass12345")
        self.other = User.objects.create_user(username="other", password="pass12345")
        self.event = _make_event(organizer=self.owner)
        self.saved_search = SavedSearchService.create(owner=self.owner, keyword="花火")

    def test_create_notification_is_idempotent(self):
        first = NotificationService.create_notification(
            user=self.owner,
            event=self.event,
            saved_search=self.saved_search,
            message="一致しました",
        )
        second = NotificationService.create_notification(
            user=self.owner,
            event=self.event,
            saved_search=self.saved_search,
            message="一致しました(2回目)",
        )

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Notification.objects.count(), 1)

    def test_owner_can_mark_as_read(self):
        notification = NotificationService.create_notification(
            user=self.owner,
            event=self.event,
            saved_search=self.saved_search,
            message="一致しました",
        )

        NotificationService.mark_as_read(notification=notification, user=self.owner)

        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_non_owner_cannot_mark_as_read(self):
        notification = NotificationService.create_notification(
            user=self.owner,
            event=self.event,
            saved_search=self.saved_search,
            message="一致しました",
        )

        with self.assertRaises(PermissionError):
            NotificationService.mark_as_read(notification=notification, user=self.other)

        notification.refresh_from_db()
        self.assertFalse(notification.is_read)

    def test_mark_all_as_read(self):
        event2 = _make_event(organizer=self.owner, title="別イベント")
        saved_search2 = SavedSearchService.create(owner=self.owner, keyword="祭り")
        NotificationService.create_notification(
            user=self.owner, event=self.event, saved_search=self.saved_search,
            message="一致1",
        )
        NotificationService.create_notification(
            user=self.owner, event=event2, saved_search=saved_search2, message="一致2",
        )

        updated_count = NotificationService.mark_all_as_read(user=self.owner)

        self.assertEqual(updated_count, 2)
        self.assertEqual(
            Notification.objects.filter(user=self.owner, is_read=False).count(), 0
        )

    def test_unread_count(self):
        NotificationService.create_notification(
            user=self.owner, event=self.event, saved_search=self.saved_search,
            message="一致1",
        )

        self.assertEqual(NotificationService.unread_count(user=self.owner), 1)

    def test_get_notifications_only_returns_own_notifications(self):
        NotificationService.create_notification(
            user=self.owner, event=self.event, saved_search=self.saved_search,
            message="一致1",
        )
        other_saved_search = SavedSearchService.create(owner=self.other, keyword="祭り")
        other_event = _make_event(organizer=self.other, title="他人のイベント")
        NotificationService.create_notification(
            user=self.other, event=other_event, saved_search=other_saved_search,
            message="他人の通知",
        )

        own_notifications = NotificationService.get_notifications(user=self.owner)

        self.assertEqual(own_notifications.count(), 1)
        self.assertEqual(own_notifications.first().user, self.owner)


class EventMatchNotifierTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass12345")

    def test_notify_for_event_creates_notification_for_matching_saved_search(self):
        event = _make_event(organizer=self.owner, title="夏祭り")
        SavedSearchService.create(owner=self.owner, keyword="夏祭り", notify_enabled=True)

        created = EventMatchNotifier.notify_for_event(event)

        self.assertEqual(len(created), 1)
        self.assertEqual(Notification.objects.count(), 1)

    def test_notify_for_event_skips_non_matching_saved_search(self):
        event = _make_event(organizer=self.owner, title="夏祭り")
        SavedSearchService.create(owner=self.owner, keyword="冬フェス", notify_enabled=True)

        created = EventMatchNotifier.notify_for_event(event)

        self.assertEqual(len(created), 0)
        self.assertEqual(Notification.objects.count(), 0)

    def test_notify_for_event_skips_notify_disabled_saved_search(self):
        event = _make_event(organizer=self.owner, title="夏祭り")
        SavedSearchService.create(owner=self.owner, keyword="夏祭り", notify_enabled=False)

        created = EventMatchNotifier.notify_for_event(event)

        self.assertEqual(len(created), 0)
        self.assertEqual(Notification.objects.count(), 0)

    def test_notify_for_event_excludes_draft_and_cancelled_events(self):
        draft_event = _make_event(
            organizer=self.owner, title="夏祭り", status=Event.Status.DRAFT
        )
        SavedSearchService.create(owner=self.owner, keyword="夏祭り", notify_enabled=True)

        created = EventMatchNotifier.notify_for_event(draft_event)

        self.assertEqual(len(created), 0)
        self.assertEqual(Notification.objects.count(), 0)

    def test_notify_for_event_does_not_duplicate_notifications(self):
        event = _make_event(organizer=self.owner, title="夏祭り")
        SavedSearchService.create(owner=self.owner, keyword="夏祭り", notify_enabled=True)

        EventMatchNotifier.notify_for_event(event)
        second_run_created = EventMatchNotifier.notify_for_event(event)

        self.assertEqual(len(second_run_created), 0)
        self.assertEqual(Notification.objects.count(), 1)
