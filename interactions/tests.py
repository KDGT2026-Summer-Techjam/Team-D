from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from events.models import Event
from .models import Favorite, Like, Rating
from .services import InteractionService

User = get_user_model()


class InteractionServiceTests(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(email="organizer@example.com", password="pass")
        self.user = User.objects.create_user(email="user1@example.com", password="pass")
        self.other_user = User.objects.create_user(email="user2@example.com", password="pass")

        self.finished_event = Event.objects.create(
            title="終了済みイベント",
            organizer=self.organizer,
            start_datetime=timezone.now() - timedelta(days=2),
            end_datetime=timezone.now() - timedelta(days=1),
            status=Event.Status.PUBLISH,
        )

        self.upcoming_event = Event.objects.create(
            title="開催前イベント",
            organizer=self.organizer,
            start_datetime=timezone.now() + timedelta(days=1),
            end_datetime=timezone.now() + timedelta(days=2),
            status=Event.Status.PUBLISH,
        )


    def test_add_favorite_success(self):
        InteractionService.add_favorite(event=self.finished_event, user=self.user)
        self.assertTrue(
            Favorite.objects.filter(event=self.finished_event, user=self.user).exists()
        )

    def test_add_favorite_duplicate_raises_error(self):
        InteractionService.add_favorite(event=self.finished_event, user=self.user)
        with self.assertRaises(ValidationError):
            InteractionService.add_favorite(event=self.finished_event, user=self.user)

    def test_remove_favorite_success(self):
        InteractionService.add_favorite(event=self.finished_event, user=self.user)
        InteractionService.remove_favorite(event=self.finished_event, user=self.user)
        self.assertFalse(
            Favorite.objects.filter(event=self.finished_event, user=self.user).exists()
        )

    def test_remove_favorite_not_registered_raises_error(self):
        with self.assertRaises(ValidationError):
            InteractionService.remove_favorite(event=self.finished_event, user=self.user)


    def test_add_like_duplicate_raises_error(self):
        InteractionService.add_like(event=self.finished_event, user=self.user)
        with self.assertRaises(ValidationError):
            InteractionService.add_like(event=self.finished_event, user=self.user)


    def test_submit_review_before_event_finished_raises_error(self):
        """開催前(終了前)のイベントには評価・レビューできないこと"""
        with self.assertRaises(ValidationError):
            InteractionService.submit_review(
                event=self.upcoming_event, user=self.user, rating=5
            )

    def test_submit_review_after_event_finished_success(self):
        review = InteractionService.submit_review(
            event=self.finished_event, user=self.user, rating=5
        )
        self.assertEqual(review.rating, 5)

    def test_submit_review_rating_out_of_range_raises_error(self):
        with self.assertRaises(ValidationError):
            InteractionService.submit_review(
                event=self.finished_event, user=self.user, rating=6
            )

    def test_submit_review_rating_zero_is_allowed(self):
        review = InteractionService.submit_review(
            event=self.finished_event, user=self.user, rating=0
        )
        self.assertEqual(review.rating, 0)

    def test_submit_review_duplicate_raises_error(self):
        InteractionService.submit_review(event=self.finished_event, user=self.user, rating=3)
        with self.assertRaises(ValidationError):
            InteractionService.submit_review(
                event=self.finished_event, user=self.user, rating=4
            )

    def test_update_review_by_owner_success(self):
        review = InteractionService.submit_review(
            event=self.finished_event, user=self.user, rating=3
        )
        updated = InteractionService.update_review(review=review, user=self.user, rating=5)
        self.assertEqual(updated.rating, 5)

    def test_update_review_by_other_user_raises_error(self):
        """他人のレビューは編集できないこと"""
        review = InteractionService.submit_review(
            event=self.finished_event, user=self.user, rating=3
        )
        with self.assertRaises(PermissionError):
            InteractionService.update_review(review=review, user=self.other_user, rating=5)

    def test_delete_review_by_other_user_raises_error(self):
        review = InteractionService.submit_review(
            event=self.finished_event, user=self.user, rating=3
        )
        with self.assertRaises(PermissionError):
            InteractionService.delete_review(review=review, user=self.other_user)


    def test_get_event_stats_calculates_correctly(self):
        InteractionService.submit_review(event=self.finished_event, user=self.user, rating=4)
        InteractionService.submit_review(
            event=self.finished_event, user=self.other_user, rating=2
        )
        InteractionService.add_favorite(event=self.finished_event, user=self.user)

        stats = InteractionService.get_event_stats(self.finished_event)

        self.assertEqual(stats["review_count"], 2)
        self.assertEqual(stats["average_rating"], 3.0)  # (4+2)/2
        self.assertEqual(stats["favorite_count"], 1)
