"""Targeted replacements for legacy routes while keeping URL compatibility."""

from django.urls import path

from . import account, portfolio

urlpatterns = [
    path("services/account", account.account_profile),
    path("services/metsis-portfolio/status", portfolio.portfolio_status),
    path("services/metsis-portfolio/sync", portfolio.portfolio_sync),
]
