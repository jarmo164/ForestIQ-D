"""Regression tests for the versioned API compatibility surface."""

from __future__ import annotations

import yaml

from django.test import SimpleTestCase
from django.urls import resolve


class ApiV1CompatibilityTests(SimpleTestCase):
    def test_versioned_status_route_resolves_to_the_existing_public_view(self):
        legacy = resolve("/api/services/status")
        versioned = resolve("/api/v1/services/status")

        self.assertIs(versioned.func, legacy.func)
        legacy_response = self.client.get("/api/services/status")
        versioned_response = self.client.get("/api/v1/services/status")
        self.assertEqual(versioned_response.status_code, legacy_response.status_code)

    def test_versioned_schema_is_public_and_contains_versioned_status_path(self):
        response = self.client.get("/api/v1/schema/")

        self.assertEqual(response.status_code, 200)
        schema = yaml.safe_load(response.content)
        self.assertEqual(schema["openapi"], "3.0.3")
        self.assertEqual(schema["info"]["version"], "1.0.0")
        self.assertIn("/api/v1/services/status", schema["paths"])
