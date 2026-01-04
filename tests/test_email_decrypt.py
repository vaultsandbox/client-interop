"""Tests for email decryption across all SDKs."""

import time
import pytest

from helpers import send_test_email, send_email_with_attachment, send_html_email
from conftest import save_export


class TestEmailDecryption:
    """Test that all SDKs can decrypt emails from the server."""

    def test_decrypt_plain_text(self, creator_sdk, keep_inboxes):
        """Test decryption of a plain text email."""
        export_data = creator_sdk.create_inbox()
        email_address = export_data["emailAddress"]

        if keep_inboxes:
            filepath = save_export(export_data, f"plain_text_{creator_sdk.sdk}")
            print(f"\n  Saved export: {filepath}")
            print(f"  Email address: {email_address}")

        try:
            subject = f"Plain text test - {creator_sdk.sdk}"
            body = "This is a plain text email body."
            send_test_email(email_address, subject, body)

            time.sleep(2)

            result = creator_sdk.read_emails(export_data)

            assert len(result["emails"]) >= 1
            email = result["emails"][0]
            assert email["subject"] == subject
            assert body in email["text"]

        finally:
            if not keep_inboxes:
                creator_sdk.cleanup(email_address)

    def test_decrypt_with_attachment(self, creator_sdk, keep_inboxes):
        """Test decryption of emails with attachments."""
        export_data = creator_sdk.create_inbox()
        email_address = export_data["emailAddress"]

        if keep_inboxes:
            filepath = save_export(export_data, f"attachment_{creator_sdk.sdk}")
            print(f"\n  Saved export: {filepath}")
            print(f"  Email address: {email_address}")

        try:
            subject = f"Attachment test - {creator_sdk.sdk}"
            body = "This email has an attachment."
            attachment_content = b"Hello, this is attachment content!"
            attachment_name = "test.txt"

            send_email_with_attachment(
                email_address,
                subject,
                body,
                attachment_name,
                attachment_content,
                "text/plain",
            )

            time.sleep(2)

            result = creator_sdk.read_emails(export_data)

            assert len(result["emails"]) >= 1
            email = result["emails"][0]
            assert email["subject"] == subject
            assert "attachments" in email
            assert len(email["attachments"]) >= 1

            attachment = email["attachments"][0]
            assert attachment["filename"] == attachment_name

        finally:
            if not keep_inboxes:
                creator_sdk.cleanup(email_address)

    def test_decrypt_html_email(self, creator_sdk, keep_inboxes):
        """Test decryption of HTML emails."""
        export_data = creator_sdk.create_inbox()
        email_address = export_data["emailAddress"]

        if keep_inboxes:
            filepath = save_export(export_data, f"html_{creator_sdk.sdk}")
            print(f"\n  Saved export: {filepath}")
            print(f"  Email address: {email_address}")

        try:
            subject = f"HTML test - {creator_sdk.sdk}"
            html_body = "<html><body><h1>Hello</h1><p>This is HTML</p></body></html>"
            text_body = "Hello\nThis is HTML"

            send_html_email(email_address, subject, html_body, text_body)

            time.sleep(2)

            result = creator_sdk.read_emails(export_data)

            assert len(result["emails"]) >= 1
            email = result["emails"][0]
            assert email["subject"] == subject
            # Should have either html or text content
            assert email.get("html") or email.get("text")

        finally:
            if not keep_inboxes:
                creator_sdk.cleanup(email_address)

    def test_decrypt_unicode_content(self, creator_sdk, keep_inboxes):
        """Test decryption of emails with unicode content."""
        export_data = creator_sdk.create_inbox()
        email_address = export_data["emailAddress"]

        if keep_inboxes:
            filepath = save_export(export_data, f"unicode_{creator_sdk.sdk}")
            print(f"\n  Saved export: {filepath}")
            print(f"  Email address: {email_address}")

        try:
            subject = f"Unicode test - {creator_sdk.sdk} - 日本語"
            body = "Unicode content: 你好世界 🌍 émojis работает"

            send_test_email(email_address, subject, body)

            time.sleep(2)

            result = creator_sdk.read_emails(export_data)

            assert len(result["emails"]) >= 1
            email = result["emails"][0]
            assert "日本語" in email["subject"]
            assert "你好世界" in email["text"]

        finally:
            if not keep_inboxes:
                creator_sdk.cleanup(email_address)

    def test_decrypt_multiple_emails(self, creator_sdk, keep_inboxes):
        """Test reading multiple emails from an inbox."""
        export_data = creator_sdk.create_inbox()
        email_address = export_data["emailAddress"]

        if keep_inboxes:
            filepath = save_export(export_data, f"multiple_{creator_sdk.sdk}")
            print(f"\n  Saved export: {filepath}")
            print(f"  Email address: {email_address}")

        try:
            # Send multiple emails
            for i in range(3):
                send_test_email(
                    email_address,
                    f"Multi-email test {i + 1}",
                    f"Body of email {i + 1}",
                )

            time.sleep(3)

            result = creator_sdk.read_emails(export_data)

            assert len(result["emails"]) >= 3, "Should have at least 3 emails"

        finally:
            if not keep_inboxes:
                creator_sdk.cleanup(email_address)
