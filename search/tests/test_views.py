from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from search.models import SavedSearch

User = get_user_model()


class SearchResultsPostDispatchTests(TestCase):
    #POST側の共通ディスパッチ(認証・action判定)の振る舞いを検証する。
    def setUp(self):
        self.url = reverse("search:search_results")
        self.owner = User.objects.create_user(email="owner@example.com", password="pass12345")

    def test_anonymous_post_is_forbidden(self):
        response = self.client.post(self.url, {"action": "create", "keyword": "花火"})

        self.assertEqual(response.status_code, 403)
        self.assertFalse(SavedSearch.objects.exists())

    def test_unknown_action_is_bad_request(self):
        self.client.force_login(self.owner)

        response = self.client.post(self.url, {"action": "bogus"})

        self.assertEqual(response.status_code, 400)

    def test_missing_action_is_bad_request(self):
        self.client.force_login(self.owner)

        response = self.client.post(self.url, {"keyword": "花火"})

        self.assertEqual(response.status_code, 400)
        self.assertFalse(SavedSearch.objects.exists())


class SavedSearchOwnershipTests(TestCase):
    #他人のSavedSearchに対するupdate/deleteが404になり、実データも変更されないことを検証する。
    def setUp(self):
        self.url = reverse("search:search_results")
        self.owner = User.objects.create_user(email="owner@example.com", password="pass12345")
        self.other = User.objects.create_user(email="other@example.com", password="pass12345")
        self.saved_search = SavedSearch.objects.create(
            owner=self.owner, keyword="花火", location="東京"
        )

    def test_update_others_saved_search_returns_404_and_does_not_change_data(self):
        self.client.force_login(self.other)

        response = self.client.post(
            self.url,
            {"action": "update", "pk": self.saved_search.pk, "keyword": "乗っ取り"},
        )

        self.assertEqual(response.status_code, 404)
        self.saved_search.refresh_from_db()
        self.assertEqual(self.saved_search.keyword, "花火")

    def test_delete_others_saved_search_returns_404_and_does_not_delete(self):
        self.client.force_login(self.other)

        response = self.client.post(
            self.url, {"action": "delete", "pk": self.saved_search.pk}
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(SavedSearch.objects.filter(pk=self.saved_search.pk).exists())

    def test_owner_can_update_own_saved_search(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            self.url,
            {"action": "update", "pk": self.saved_search.pk, "keyword": "夏祭り"},
        )

        self.assertEqual(response.status_code, 302)
        self.saved_search.refresh_from_db()
        self.assertEqual(self.saved_search.keyword, "夏祭り")

    def test_owner_can_delete_own_saved_search(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            self.url, {"action": "delete", "pk": self.saved_search.pk}
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(SavedSearch.objects.filter(pk=self.saved_search.pk).exists())


class SavedSearchInvalidPkTests(TestCase):
    #非数値のpkが渡された場合に500にならず400を返すことを検証する(修正2の回帰テスト)。
    def setUp(self):
        self.url = reverse("search:search_results")
        self.owner = User.objects.create_user(email="owner@example.com", password="pass12345")
        self.client.force_login(self.owner)

    def test_update_with_non_numeric_pk_is_bad_request(self):
        response = self.client.post(
            self.url, {"action": "update", "pk": "abc", "keyword": "花火"}
        )

        self.assertEqual(response.status_code, 400)

    def test_delete_with_non_numeric_pk_is_bad_request(self):
        response = self.client.post(self.url, {"action": "delete", "pk": "abc"})

        self.assertEqual(response.status_code, 400)

    def test_update_with_missing_pk_is_bad_request(self):
        response = self.client.post(
            self.url, {"action": "update", "keyword": "花火"}
        )

        self.assertEqual(response.status_code, 400)


class SavedSearchPartialUpdateTests(TestCase):
    #未送信フィールドが既存値を消してしまわないことを検証する(修正1の回帰テスト)。
    def setUp(self):
        self.url = reverse("search:search_results")
        self.owner = User.objects.create_user(email="owner@example.com", password="pass12345")
        self.client.force_login(self.owner)
        self.saved_search = SavedSearch.objects.create(
            owner=self.owner,
            keyword="花火",
            location="東京",
            period_from="2026-01-01",
            period_to="2026-01-31",
            age_min=3,
            age_max=10,
        )

    def test_updating_only_keyword_keeps_other_fields(self):
        response = self.client.post(
            self.url,
            {"action": "update", "pk": self.saved_search.pk, "keyword": "夏祭り"},
        )

        self.assertEqual(response.status_code, 302)
        self.saved_search.refresh_from_db()
        self.assertEqual(self.saved_search.keyword, "夏祭り")
        self.assertEqual(self.saved_search.location, "東京")
        self.assertEqual(str(self.saved_search.period_from), "2026-01-01")
        self.assertEqual(str(self.saved_search.period_to), "2026-01-31")
        self.assertEqual(self.saved_search.age_min, 3)
        self.assertEqual(self.saved_search.age_max, 10)

    def test_explicitly_clearing_a_field_with_empty_string_still_works(self):
        #period_fromキー自体は送信し、値を空にした場合は明示的なクリアとして扱われる
        response = self.client.post(
            self.url,
            {
                "action": "update",
                "pk": self.saved_search.pk,
                "period_from": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.saved_search.refresh_from_db()
        self.assertIsNone(self.saved_search.period_from)
        # period_toは未送信のため維持される
        self.assertEqual(str(self.saved_search.period_to), "2026-01-31")


class SavedSearchNotifyEnabledDefaultTests(TestCase):
    #notify_enabledを送信しないcreateでモデルのdefault=Trueが維持されることを検証する(修正4の回帰テスト)。
    def setUp(self):
        self.url = reverse("search:search_results")
        self.owner = User.objects.create_user(email="owner@example.com", password="pass12345")
        self.client.force_login(self.owner)

    def test_create_without_notify_enabled_defaults_to_true(self):
        response = self.client.post(self.url, {"action": "create", "keyword": "花火"})

        self.assertEqual(response.status_code, 302)
        saved_search = SavedSearch.objects.get(owner=self.owner, keyword="花火")
        self.assertTrue(saved_search.notify_enabled)

    def test_create_with_notify_enabled_off_value_is_false(self):
        response = self.client.post(
            self.url,
            {"action": "create", "keyword": "夏祭り", "notify_enabled": "false"},
        )

        self.assertEqual(response.status_code, 302)
        saved_search = SavedSearch.objects.get(owner=self.owner, keyword="夏祭り")
        self.assertFalse(saved_search.notify_enabled)

    def test_create_with_notify_enabled_on_value_is_true(self):
        response = self.client.post(
            self.url,
            {"action": "create", "keyword": "花見", "notify_enabled": "on"},
        )

        self.assertEqual(response.status_code, 302)
        saved_search = SavedSearch.objects.get(owner=self.owner, keyword="花見")
        self.assertTrue(saved_search.notify_enabled)

    def test_update_without_notify_enabled_keeps_existing_value(self):
        saved_search = SavedSearch.objects.create(
            owner=self.owner, keyword="花火", notify_enabled=False
        )

        response = self.client.post(
            self.url,
            {"action": "update", "pk": saved_search.pk, "keyword": "花火2"},
        )

        self.assertEqual(response.status_code, 302)
        saved_search.refresh_from_db()
        self.assertFalse(saved_search.notify_enabled)
