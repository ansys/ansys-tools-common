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
    NotificationFormat,
    NotificationUrgency,
    _desktop_url,
    notify,
)


@pytest.fixture()
def mock_apprise():
    """Patch apprise.Apprise and return a mock instance."""
    ap_instance = MagicMock()
    ap_instance.add.return_value = True
    ap_instance.notify.return_value = True

    with patch("ansys.tools.common.notifications.apprise.Apprise", return_value=ap_instance):
        yield ap_instance


def test_enum_values():
    """Enum members expose the string values expected by apprise."""
    assert NotificationFormat.TEXT == "text"
    assert NotificationFormat.HTML == "html"
    assert NotificationFormat.MARKDOWN == "markdown"
    assert NotificationUrgency.INFO == "info"
    assert NotificationUrgency.SUCCESS == "success"
    assert NotificationUrgency.WARNING == "warning"
    assert NotificationUrgency.FAILURE == "failure"


@pytest.mark.parametrize(
    ("system", "expected"),
    [("Windows", "windows://"), ("Darwin", "macosx://"), ("Linux", "dbus://"), ("FreeBSD", "dbus://")],
)
def test_desktop_url(system, expected):
    """_desktop_url returns the correct apprise scheme for each OS."""
    with patch("platform.system", return_value=system):
        assert _desktop_url() == expected


def test_notifier_defaults(mock_apprise):
    """AnsysNotifier has the expected default title, format and urgency."""
    notifier = AnsysNotifier(channels=["windows://"])
    assert notifier.title == "PyAnsys"
    assert notifier.format is NotificationFormat.TEXT
    assert notifier.urgency is NotificationUrgency.INFO


def test_notifier_auto_detects_desktop_channel(mock_apprise):
    """When no channels are given the OS-appropriate URL is added."""
    with patch("platform.system", return_value="Windows"):
        AnsysNotifier()
    mock_apprise.add.assert_called_once_with("windows://")


def test_notifier_sends_correct_payload(mock_apprise):
    """notify() forwards body, title, format and urgency to apprise."""
    notifier = AnsysNotifier(
        channels=["windows://"],
        title="PyMAPDL",
        format=NotificationFormat.HTML,
        urgency=NotificationUrgency.SUCCESS,
    )
    notifier.notify("Solve complete.")
    kwargs = mock_apprise.notify.call_args.kwargs
    assert kwargs["body"] == "Solve complete."
    assert kwargs["title"] == "PyMAPDL"
    assert kwargs["body_format"] == "html"
    assert kwargs["notify_type"] == "success"


def test_notifier_per_call_overrides(mock_apprise):
    """Per-call title, format and urgency override the instance defaults."""
    notifier = AnsysNotifier(channels=["windows://"])
    notifier.notify("msg", title="Override", format=NotificationFormat.MARKDOWN, urgency=NotificationUrgency.FAILURE)
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
    """title, format and urgency can be changed after construction."""
    notifier = AnsysNotifier(channels=["windows://"])
    notifier.title = "Updated"
    notifier.format = NotificationFormat.MARKDOWN
    notifier.urgency = NotificationUrgency.WARNING
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
