"""Tests for cross-SDK inbox export/import functionality."""

import json
import time
import pytest

from helpers import send_test_email
from conftest import save_export


class TestExportImport:
    """Test that exports from SDK-A can be imported by SDK-B."""

    def test_cross_sdk_import(self, creator_sdk, importer_sdk, keep_inboxes, request):
        """
        Test that an inbox created by one SDK can be imported and used by another.

        1. Create inbox with creator SDK
        2. Send test email to the inbox
        3. Import inbox with importer SDK
        4. Read and decrypt emails
        5. Verify email content matches
        """
        # 1. Create inbox with creator SDK
        export_data = creator_sdk.create_inbox()
        email_address = export_data["emailAddress"]

        # Save export if --keep-inboxes flag is set
        if keep_inboxes:
            filepath = save_export(export_data, f"cross_sdk_{creator_sdk.sdk}_to_{importer_sdk.sdk}")
            print(f"\n  Saved export: {filepath}")
            print(f"  Email address: {email_address}")

        try:
            # 2. Send test email
            subject = f"Interop test {creator_sdk.sdk} -> {importer_sdk.sdk}"
            body = "Test body content for interoperability test"
            send_test_email(email_address, subject, body)

            # 3. Wait for email processing
            time.sleep(2)

            # 4. Import and read with importer SDK
            result = importer_sdk.read_emails(export_data)

            # 5. Verify email content
            assert "emails" in result, "Response should contain 'emails' key"
            assert len(result["emails"]) >= 1, "Should have at least one email"

            email = result["emails"][0]
            assert email["subject"] == subject, f"Subject mismatch: {email['subject']}"
            assert body in email["text"], f"Body not found in email text"

        finally:
            # Cleanup (skip if --keep-inboxes)
            if not keep_inboxes:
                creator_sdk.cleanup(email_address)

    def test_export_format_consistency(self, creator_sdk, keep_inboxes):
        """Test that export data contains required fields."""
        export_data = creator_sdk.create_inbox()
        email_address = export_data.get("emailAddress")

        if keep_inboxes:
            filepath = save_export(export_data, f"format_{creator_sdk.sdk}")
            print(f"\n  Saved export: {filepath}")
            print(f"  Email address: {email_address}")

        try:
            # Verify required fields in export
            assert "emailAddress" in export_data, "Export must contain emailAddress"
            assert "@" in export_data["emailAddress"], "emailAddress must be valid"

            # The export should contain encrypted key material
            # (specific field names depend on the spec)

        finally:
            if email_address and not keep_inboxes:
                creator_sdk.cleanup(email_address)

    def test_import_idempotency(self, creator_sdk, importer_sdk, keep_inboxes):
        """Test that importing the same inbox multiple times works."""
        export_data = creator_sdk.create_inbox()
        email_address = export_data["emailAddress"]

        if keep_inboxes:
            filepath = save_export(export_data, f"idempotency_{creator_sdk.sdk}_to_{importer_sdk.sdk}")
            print(f"\n  Saved export: {filepath}")
            print(f"  Email address: {email_address}")

        try:
            # Import twice - should not fail
            result1 = importer_sdk.import_inbox(export_data)
            result2 = importer_sdk.import_inbox(export_data)

            assert result1.get("success") or "emailAddress" in result1
            assert result2.get("success") or "emailAddress" in result2

        finally:
            if not keep_inboxes:
                creator_sdk.cleanup(email_address)
