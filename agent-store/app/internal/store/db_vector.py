# import chromadb
# from chromadb import ClientAPI

# chroma_client: ClientAPI = chromadb.Client()

# # Create or get collection
# collection_name = "taskflow_support_agent"
# try:
#     collection = chroma_client.get_collection(name=collection_name)
# except Exception:
#     collection = chroma_client.create_collection(name=collection_name)

# documents = [
#     # 1) Product Overview
#     """[TaskFlow Product Overview]
# TaskFlow is a SaaS project-management platform for small teams.
# Core modules:
# - Projects: create projects, assign owners, set due dates
# - Tasks: task lists, kanban boards, status (todo / doing / done)
# - Automations: trigger-based rules (e.g., "when task is done, notify channel")
# - Integrations: Slack, Google Calendar, GitHub
# Key differentiators:
# - Lightweight setup (<10 min)
# - Built-in automation templates
# Common user goals:
# - Organize team work
# - Reduce missed deadlines
# - Sync tasks with calendar
# """,

#     # 2) Support Tone & Style Guide
#     """[Support Tone & Style Guide]
# Tone: friendly, concise, confident, no fluff.
# Rules:
# 1) Always acknowledge the user’s issue in one sentence.
# 2) Ask at most ONE clarifying question, unless absolutely necessary.
# 3) Give steps as numbered lists.
# 4) Mention limitations clearly and early (e.g., “This is only on Pro plan”).
# 5) Offer next steps if unresolved.
# Avoid:
# - Blame ("you should have…")
# - Long technical jargon unless user is technical.
# Escalation phrasing:
# “I’m looping in our technical team with the details you provided.”
# """,

#     # 3) Troubleshooting Playbook: Login Issues
#     """[Playbook: Login Issues]
# Symptoms:
# - “Invalid credentials” error
# - Login works in browser but not in mobile
# - MFA code not accepted
# Steps:
# 1) Confirm email address spelling and account exists.
# 2) Ask if password reset works.
# 3) Check if user uses SSO (Google/Microsoft).
# 4) If MFA fails: confirm device time is correct; resend code; try backup codes.
# 5) If mobile login fails: check app version; reinstall; try browser login.
# Escalate if:
# - repeated MFA failures after time sync
# - account locked due to brute-force protection
# Escalation payload:
# - user email
# - timestamp + timezone
# - device OS and app version
# - screenshots if possible
# """,

#     # 4) Billing Policy
#     """[Billing Policy]
# Refunds:
# - Monthly plans: refund within 7 days of purchase if <10 active users.
# - Annual plans: prorated refund within 30 days if <10 active users.
# Billing cycles:
# - Monthly renews same calendar day.
# - Annual renews same date next year.
# Plan changes:
# - Upgrades are immediate; prorate applied.
# - Downgrades take effect at next renewal.
# Disputes:
# - Ask for invoice ID and last 4 digits of payment method.
# Escalate if:
# - chargeback received
# - suspected fraud
# """,

#     # 5) Pricing Cheat Sheet
#     """[Pricing Cheat Sheet — TaskFlow]
# Free:
# - Up to 3 projects
# - 1 automation
# - Basic integrations
# Pro (€12/user/month):
# - Unlimited projects
# - Unlimited automations
# - Slack + GitHub + Calendar integrations
# - Advanced permissions
# Enterprise (custom):
# - SSO/SAML
# - Audit logs
# - Dedicated support
# Upgrade triggers:
# - User hits project limit
# - Needs multiple automations
# - Wants Slack integration beyond basic notifications
# """,

#     # 6) Macro: “Cannot find my project”
#     """[Macro Template: Can't Find Project]
# Hi {name} — I can help with that.
# Quick checks:
# 1) Are you logged into the correct workspace? (top-left workspace switcher)
# 2) Are filters active? Try clearing filters and searching by project name.
# 3) Are you a member of the project? Ask an admin to confirm access.
# If you share:
# - the project name
# - the workspace name
# - approximate last time you accessed it
# …I can narrow it down quickly.
# """,

#     # 7) Escalation Rules
#     """[Escalation Rules]
# Escalate to Engineering if:
# - data loss, corrupted projects, missing tasks
# - integration failures affecting multiple users
# - auth issues that persist after basic steps
# Escalate to Billing if:
# - refunds outside policy requested
# - chargebacks, fraud, invoices missing
# Escalation package must include:
# - user identifier (email)
# - workspace ID
# - reproduction steps
# - expected vs actual behavior
# - timestamps + timezone
# - relevant screenshots/logs
# """,

#     # 8) Known Issues (Example)
#     """[Known Issues — Updated 2025-01-10]
# 1) Slack integration intermittent failures for Slack workspaces with custom enterprise routing.
# Workaround: reconnect Slack integration; if still failing, use webhook fallback.
# 2) Mobile app v2.4.1: push notifications delayed on Android 14.
# Workaround: disable battery optimization for TaskFlow app.
# 3) Calendar sync: events created in Google Calendar may take 3–10 minutes to appear.
# This is expected due to sync window.
# """,
# ]

# metadatas = [
#     {"agent": "support", "type": "product_overview", "topic": "general"},
#     {"agent": "support", "type": "style_guide", "topic": "tone"},
#     {"agent": "support", "type": "playbook", "topic": "login"},
#     {"agent": "support", "type": "policy", "topic": "billing"},
#     {"agent": "support", "type": "pricing", "topic": "plans"},
#     {"agent": "support", "type": "macro", "topic": "projects"},
#     {"agent": "support", "type": "rules", "topic": "escalation"},
#     {"agent": "support", "type": "known_issues", "topic": "status"},
# ]

# ids = [
#     "support_product_overview_v1",
#     "support_tone_guide_v1",
#     "support_login_playbook_v1",
#     "support_billing_policy_v1",
#     "support_pricing_cheatsheet_v1",
#     "support_macro_missing_project_v1",
#     "support_escalation_rules_v1",
#     "support_known_issues_2025_01_10",
# ]

# collection.add(documents=documents, metadatas=metadatas, ids=ids)

# print("✅ Added support-agent documents to Chroma collection:", collection_name)


# app/vectorstore.py
from __future__ import annotations

from typing import Generator, Optional

import chromadb
from chromadb import ClientAPI

# ---- Defaults (override in tests / config) ----
CHROMA_PATH = "./chroma"  # for PersistentClient
USE_PERSISTENT = False

_client: Optional[ClientAPI] = None

def init_chroma(
    *,
    persistent: bool = USE_PERSISTENT,
    path: str = CHROMA_PATH,
    client: Optional[ClientAPI] = None,
) -> ClientAPI:
    """
    Initialize the global Chroma client.

    - If `client` is provided, it becomes the global client (useful for tests).
    - Otherwise creates a new in-memory Client() OR PersistentClient().
    """
    global _client

    if client is not None:
        _client = client
        return _client

    if persistent:
        _client = chromadb.PersistentClient(path=path)
    else:
        _client = chromadb.Client()

    return _client

def set_client(new_client: ClientAPI) -> None:
    """Override the global client (e.g. tests)."""
    global _client
    _client = new_client

def get_client() -> ClientAPI:
    """
    Return the global client. If not initialized, initialize with defaults.
    """
    global _client
    if _client is None:
        _client = init_chroma()
    return _client

def client_dep() -> Generator[ClientAPI, None, None]:
    """
    FastAPI dependency that yields the client.
    Use this if you want the same 'yield style' as DB sessions.
    """
    yield get_client()
