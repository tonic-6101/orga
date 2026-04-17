# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Tests for orga.orga.api.assignment — Owner + Collaborators picker API."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate, add_days

from orga.orga.api.assignment import set_assignees, search_assignable


def _mk_contact(full_name: str, user: str | None = None) -> str:
    doc = frappe.get_doc({
        "doctype": "Contact",
        "first_name": full_name.split()[0],
        "last_name": " ".join(full_name.split()[1:]) or "Test",
        "full_name": full_name,
        "user": user,
    }).insert(ignore_permissions=True)
    return doc.name


def _mk_user(email: str) -> str:
    if frappe.db.exists("User", email):
        return email
    frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": email.split("@")[0],
        "send_welcome_email": 0,
    }).insert(ignore_permissions=True)
    return email


def _mk_project() -> str:
    return frappe.get_doc({
        "doctype": "Orga Project",
        "project_name": f"AsnProj {frappe.generate_hash(length=6)}",
        "status": "Active",
        "project_type": "Internal",
        "start_date": nowdate(),
        "end_date": add_days(nowdate(), 30),
        "project_manager": "Administrator",
    }).insert().name


def _mk_task(project: str) -> str:
    return frappe.get_doc({
        "doctype": "Orga Task",
        "subject": f"AsnTask {frappe.generate_hash(length=6)}",
        "project": project,
        "status": "Open",
    }).insert().name


class TestSetAssignees(FrappeTestCase):
    def setUp(self):
        self.project = _mk_project()
        self.task = _mk_task(self.project)
        self.internal_user = _mk_user(f"asn-{frappe.generate_hash(length=4)}@test.local")
        self.owner = _mk_contact("Alice Owner", user=self.internal_user)
        self.collab_internal = _mk_contact(
            "Bob Collab",
            user=_mk_user(f"bob-{frappe.generate_hash(length=4)}@test.local"),
        )
        self.collab_external = _mk_contact("Ext Client")  # no user

    def test_sets_owner_and_collaborators(self):
        result = set_assignees(
            task=self.task,
            owner_contact=self.owner,
            collaborator_contacts=[self.collab_internal, self.collab_external],
        )
        self.assertEqual(result["owner_user"], self.internal_user)
        self.assertEqual(
            set(result["collaborators"]),
            {self.collab_internal, self.collab_external},
        )
        self.assertEqual(
            frappe.db.get_value("Orga Task", self.task, "assigned_to"),
            self.internal_user,
        )
        rows = frappe.get_all(
            "Orga Assignment",
            filters={"task": self.task},
            fields=["contact", "resource"],
        )
        self.assertEqual({r["contact"] for r in rows}, {self.collab_internal, self.collab_external})
        # No shadow resource auto-created
        self.assertTrue(all(r["resource"] is None for r in rows))

    def test_idempotent(self):
        set_assignees(self.task, self.owner, [self.collab_internal])
        set_assignees(self.task, self.owner, [self.collab_internal])
        rows = frappe.get_all("Orga Assignment", filters={"task": self.task})
        self.assertEqual(len(rows), 1)

    def test_removes_dropped_collaborators(self):
        set_assignees(self.task, self.owner, [self.collab_internal, self.collab_external])
        set_assignees(self.task, self.owner, [self.collab_internal])
        rows = frappe.get_all(
            "Orga Assignment",
            filters={"task": self.task},
            fields=["contact"],
        )
        self.assertEqual({r["contact"] for r in rows}, {self.collab_internal})

    def test_external_cannot_be_owner(self):
        with self.assertRaises(frappe.ValidationError):
            set_assignees(self.task, self.collab_external, [])

    def test_clear_owner(self):
        set_assignees(self.task, self.owner, [])
        set_assignees(self.task, None, [])
        self.assertIsNone(frappe.db.get_value("Orga Task", self.task, "assigned_to"))

    def test_no_shadow_resource_created(self):
        before = frappe.db.count("Orga Resource")
        set_assignees(self.task, self.owner, [self.collab_external])
        after = frappe.db.count("Orga Resource")
        self.assertEqual(before, after)


class TestSearchAssignable(FrappeTestCase):
    def test_returns_shape(self):
        _mk_contact(f"Searchable {frappe.generate_hash(length=4)}")
        rows = search_assignable(query="", limit=5)
        self.assertIsInstance(rows, list)
        if rows:
            row = rows[0]
            for key in ("contact", "name", "is_internal", "role_label", "resource"):
                self.assertIn(key, row)
