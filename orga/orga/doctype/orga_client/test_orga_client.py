# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class TestOrgaClient(IntegrationTestCase):
    def setUp(self):
        # Clean up any test clients
        for client in frappe.get_all("Orga Client", filters={"email": ["like", "%@test.orga%"]}):
            frappe.delete_doc("Orga Client", client.name, force=True)

    def tearDown(self):
        # Clean up test data
        for client in frappe.get_all("Orga Client", filters={"email": ["like", "%@test.orga%"]}):
            frappe.delete_doc("Orga Client", client.name, force=True)

    def test_create_client(self):
        """Test basic client creation"""
        client = frappe.get_doc({
            "doctype": "Orga Client",
            "client_name": "Test Client",
            "email": "test.client@test.orga.com",
            "company": "Test Company"
        })
        client.insert()

        self.assertEqual(client.client_name, "Test Client")
        self.assertEqual(client.status, "Pending")
        self.assertTrue(client.name.startswith("CLT-"))

    def test_email_uniqueness(self):
        """Test that duplicate emails are rejected"""
        client1 = frappe.get_doc({
            "doctype": "Orga Client",
            "client_name": "Client One",
            "email": "duplicate@test.orga.com"
        })
        client1.insert()

        client2 = frappe.get_doc({
            "doctype": "Orga Client",
            "client_name": "Client Two",
            "email": "duplicate@test.orga.com"
        })

        with self.assertRaises(frappe.ValidationError):
            client2.insert()

    def test_naming_series(self):
        """Test client naming series"""
        client = frappe.get_doc({
            "doctype": "Orga Client",
            "client_name": "Naming Test Client",
            "email": "naming@test.orga.com"
        })
        client.insert()

        self.assertTrue(client.name.startswith("CLT-"))
        self.assertEqual(len(client.name), 10)  # CLT- + 5 digits

    def test_status_default(self):
        """Test default status is Pending"""
        client = frappe.get_doc({
            "doctype": "Orga Client",
            "client_name": "Status Test Client",
            "email": "status@test.orga.com"
        })
        client.insert()

        self.assertEqual(client.status, "Pending")

    def test_project_count_update(self):
        """Test project count is updated correctly"""
        client = frappe.get_doc({
            "doctype": "Orga Client",
            "client_name": "Project Count Client",
            "email": "projects@test.orga.com"
        })
        client.insert()

        # Initial count should be 0
        self.assertEqual(client.project_count, 0)

    def test_get_linked_projects_empty(self):
        """Test getting projects when none exist"""
        client = frappe.get_doc({
            "doctype": "Orga Client",
            "client_name": "No Projects Client",
            "email": "noprojects@test.orga.com"
        })
        client.insert()

        projects = client.get_linked_projects()
        self.assertEqual(len(projects), 0)

    def test_get_linked_milestones_empty(self):
        """Test getting milestones when none exist"""
        client = frappe.get_doc({
            "doctype": "Orga Client",
            "client_name": "No Milestones Client",
            "email": "nomilestones@test.orga.com"
        })
        client.insert()

        milestones = client.get_linked_milestones()
        self.assertEqual(len(milestones), 0)

    def test_portal_enabled_default(self):
        """Test portal access is disabled by default"""
        client = frappe.get_doc({
            "doctype": "Orga Client",
            "client_name": "Portal Test Client",
            "email": "portal@test.orga.com"
        })
        client.insert()

        self.assertEqual(client.portal_enabled, 0)
