# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Tests for the notifications module."""

from unittest.mock import MagicMock, patch

import pytest

from ansys.tools.common.notifications import (
    AnsysNotifier,
    NotificationChannel,
    NotificationFormat,
    NotificationType,
    _desktop_url,
    notify,
    notify_on_completion,
)


@pytest.fixture()
def mock_apprise():
    """Patch apprise.Apprise and return a mock instance."""
    ap_instance = MagicMock()
    ap_instance.add.return_value = True
    ap_instance.notify.return_value = True

    with patch("ansys.tools.common.notifications.apprise.Apprise", return_value=ap_instance):
        yield ap_instance


@pytest.mark.parametrize(
    ("system", "expected"),
    [
        ("Windows", NotificationChannel.WINDOWS),
        ("Darwin", NotificationChannel.MACOS),
        ("Linux", NotificationChannel.DBUS),
        ("FreeBSD", NotificationChannel.DBUS),
    ],
)
def test_desktop_url(system, expected):
    """_desktop_url returns the correct NotificationChannel for each OS."""
    with patch("platform.system", return_value=system):
        assert _desktop_url() == expected


def test_notifier_defaults(mock_apprise):
    """AnsysNotifier has the expected default title, format and notification_type."""
    notifier = AnsysNotifier(channels=["windows://"])
    assert notifier.title == "PyAnsys"
    assert notifier.format is NotificationFormat.TEXT
    assert notifier.notification_type is NotificationType.INFO


def test_notifier_auto_detects_desktop_channel(mock_apprise):
    """When no channels are given the OS-appropriate URL is added."""
    with patch("platform.system", return_value="Windows"):
        AnsysNotifier()
    mock_apprise.add.assert_called_once_with(NotificationChannel.WINDOWS)


def test_notifier_sends_correct_payload(mock_apprise):
    """notify() forwards body, title, format and notification_type to apprise."""
    notifier = AnsysNotifier(
        channels=["windows://"],
        title="PyMAPDL",
        format=NotificationFormat.HTML,
        notification_type=NotificationType.SUCCESS,
    )
    notifier.notify("Solve complete.")
    kwargs = mock_apprise.notify.call_args.kwargs
    assert kwargs["body"] == "Solve complete."
    assert kwargs["title"] == "PyMAPDL"
    assert kwargs["body_format"] == "html"
    assert kwargs["notify_type"] == "success"


def test_notifier_per_call_overrides(mock_apprise):
    """Per-call title, format and notification_type override the instance defaults."""
    notifier = AnsysNotifier(channels=["windows://"])
    notifier.notify(
        "msg", title="Override", format=NotificationFormat.MARKDOWN, notification_type=NotificationType.FAILURE
    )
    kwargs = mock_apprise.notify.call_args.kwargs
    assert kwargs["title"] == "Override"
    assert kwargs["body_format"] == "markdown"
    assert kwargs["notify_type"] == "failure"


def test_notifier_returns_delivery_status(mock_apprise):
    """notify() propagates the bool returned by apprise."""
    notifier = AnsysNotifier(channels=["windows://"])
    assert notifier.notify("ok") is True
    mock_apprise.notify.return_value = False
    assert notifier.notify("fail") is False


def test_notifier_property_setters(mock_apprise):
    """title, format and notification_type can be changed after construction."""
    notifier = AnsysNotifier(channels=["windows://"])
    notifier.title = "Updated"
    notifier.format = NotificationFormat.MARKDOWN
    notifier.notification_type = NotificationType.WARNING
    notifier.notify("msg")
    kwargs = mock_apprise.notify.call_args.kwargs
    assert kwargs["title"] == "Updated"
    assert kwargs["body_format"] == "markdown"
    assert kwargs["notify_type"] == "warning"


def test_notify_convenience_function(mock_apprise):
    """notify() sends a desktop notification with correct defaults."""
    with patch("platform.system", return_value="Windows"):
        result = notify("Job done.")
    assert result is True
    kwargs = mock_apprise.notify.call_args.kwargs
    assert kwargs["body"] == "Job done."
    assert kwargs["title"] == "PyAnsys"
    assert kwargs["body_format"] == "text"
    assert kwargs["notify_type"] == "info"


def test_notify_on_completion_sends_success_notification(mock_apprise):
    """notify_on_completion sends a success notification when the function returns."""
    with patch("platform.system", return_value="Windows"):

        @notify_on_completion("Done.")
        def job():
            return 42

        result = job()

    assert result == 42
    kwargs = mock_apprise.notify.call_args.kwargs
    assert kwargs["body"] == "Done."
    assert kwargs["notify_type"] == "info"


def test_notify_on_completion_default_message(mock_apprise):
    """notify_on_completion generates a message from the function name when none is given."""
    with patch("platform.system", return_value="Windows"):

        @notify_on_completion()
        def my_solver():
            pass

        my_solver()

    assert mock_apprise.notify.call_args.kwargs["body"] == "my_solver completed."


def test_notify_on_completion_sends_failure_notification(mock_apprise):
    """notify_on_completion sends a failure notification and re-raises the exception."""
    with patch("platform.system", return_value="Windows"):

        @notify_on_completion()
        def bad_job():
            raise ValueError("oops")

        with pytest.raises(ValueError, match="oops"):
            bad_job()

    kwargs = mock_apprise.notify.call_args.kwargs
    assert "bad_job failed" in kwargs["body"]
    assert kwargs["notify_type"] == "failure"


def test_notify_on_completion_no_failure_notification(mock_apprise):
    """notify_on_completion skips the failure notification when notify_on_failure=False."""
    with patch("platform.system", return_value="Windows"):

        @notify_on_completion(notify_on_failure=False)
        def bad_job():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            bad_job()

    mock_apprise.notify.assert_not_called()


def test_notify_on_completion_custom_channels(mock_apprise):
    """notify_on_completion passes custom channels to apprise."""

    @notify_on_completion(channels=["windows://"], notification_type=NotificationType.SUCCESS)
    def job():
        pass

    job()

    mock_apprise.add.assert_called_with("windows://")
    assert mock_apprise.notify.call_args.kwargs["notify_type"] == "success"
