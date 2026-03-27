from django.http import QueryDict
from django.test import TestCase

from agent_app.analytics.query_filter import build_filtered_query_params


class AnalyticsQueryFilterTests(TestCase):
    def test_keeps_only_allowlisted_params(self):
        raw = QueryDict("utm_source=google&campaign=spring&secret=abc")
        out = build_filtered_query_params(
            raw,
            allowlist=["utm_source", "campaign"],
            denylist=["secret"],
        )
        self.assertEqual(out, {"utm_source": "google", "campaign": "spring"})

    def test_denylist_wins_over_allowlist(self):
        raw = QueryDict("token=abc")
        out = build_filtered_query_params(raw, allowlist=["token"], denylist=["token"])
        self.assertEqual(out, {})

    def test_multiple_values_are_retained_as_list(self):
        raw = QueryDict("tag=a&tag=b")
        out = build_filtered_query_params(raw, allowlist=["tag"], denylist=[])
        self.assertEqual(out, {"tag": ["a", "b"]})
