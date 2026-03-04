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
"""Desktop and multi-channel notification support for PyAnsys libraries.

This module exposes :class:`AnsysNotifier` for persistent use inside PyAnsys
library workflows and the convenience function :func:`notify` for one-shot
script usage.

Install the optional dependency before using this module::

    pip install "ansys-tools-common[notifications]"

Quick start
-----------
>>> from ansys.tools.common.notifications import notify, NotificationType
>>> notify("Simulation complete.")
>>> notify("Solve diverged!", notification_type=NotificationType.FAILURE)
>>> from ansys.tools.common.notifications import NotificationChannel
>>> notify("Job done.", channels=[NotificationChannel.WINDOWS])
"""

from __future__ import annotations

from enum import Enum
import platform

try:
    import apprise
except ImportError:
    raise ImportError(
        "The 'apprise' package is required for notifications. "
        'Install it with: pip install "ansys-tools-common[notifications]"'
    ) from None

__all__ = ["AnsysNotifier", "NotificationChannel", "NotificationFormat", "NotificationType", "notify"]


# TODO: Use StrEnum after dropping Python 3.10 support.
class NotificationChannel(str, Enum):
    """Well-known apprise notification channel URL schemes.

    Each member's value is the scheme prefix of the apprise URL for that
    channel.  Members with self-contained URLs (:attr:`WINDOWS`,
    :attr:`MACOS`, :attr:`DBUS`) can be used directly.  Members that require
    credentials or IDs (:attr:`SLACK`, :attr:`MSTEAMS`, :attr:`MAILTO`,
    :attr:`MAILTOS`) serve as the scheme prefix — concatenate your tokens to
    form the full URL::

        NotificationChannel.SLACK + "token/channel"
        NotificationChannel.MAILTO + "user:pass@gmail.com"

    A plain :class:`str` is always accepted wherever a channel is expected.
    """

    WINDOWS = "windows://"
    """Windows 10/11 native toast notification."""

    MACOS = "macosx://"
    """macOS Notification Center."""

    DBUS = "dbus://"
    """Linux desktop notification via D-Bus (GNOME, KDE, etc.)."""

    MAILTO = "mailto://"
    """Gmail or other IMAP provider. Append ``user:pass@gmail.com``."""

    MAILTOS = "mailtos://"
    """Corporate SMTP with TLS. Append ``user:pass@smtp.corp.com``."""

    SLACK = "slack://"
    """Slack channel. Append ``token/channel``."""

    MSTEAMS = "msteams://"
    """Microsoft Teams incoming webhook. Append ``A/B/C/D``."""


# TODO: Use StrEnum after dropping Python 3.10 support.
class NotificationFormat(str, Enum):
    """Body format of the notification.

    Using a ``str`` enum means the values can be compared directly with the
    string constants used by the ``apprise`` library.
    """

    TEXT = "text"
    """Plain text (default). Compatible with every notification channel."""

    HTML = "html"
    """HTML-formatted body. Rendered by channels that support it (e.g. email,
    Slack). Channels that don't support HTML will fall back to plain text."""

    MARKDOWN = "markdown"
    """Markdown-formatted body. Rendered by channels that support it (e.g.
    Discord, Telegram, Slack). Falls back to plain text elsewhere."""


class NotificationType(str, Enum):
    """notification_type / type of the notification.

    Controls the visual appearance of the notification (colour, icon, sound)
    where the target channel supports it.

    Using a ``str`` enum means the values map directly to ``apprise``
    ``NotifyType`` constants.
    """

    INFO = "info"
    """Informational message (default). Neutral appearance."""

    SUCCESS = "success"
    """Positive outcome. Typically shown in green."""

    WARNING = "warning"
    """Something requires attention. Typically shown in yellow/orange."""

    FAILURE = "failure"
    """An error or critical problem. Typically shown in red."""


def _desktop_url() -> NotificationChannel:
    """Return the apprise desktop notification URL for the current OS.

    Returns
    -------
    NotificationChannel
        :attr:`NotificationChannel.WINDOWS` on Windows,
        :attr:`NotificationChannel.MACOS` on macOS,
        :attr:`NotificationChannel.DBUS` on Linux and other POSIX systems.
    """
    system = platform.system()
    if system == "Windows":
        return NotificationChannel.WINDOWS
    if system == "Darwin":
        return NotificationChannel.MACOS
    return NotificationChannel.DBUS


class AnsysNotifier:
    """Desktop and multi-channel notifier for PyAnsys job-completion events.

    :class:`AnsysNotifier` wraps `apprise <https://github.com/caronc/apprise>`_
    to provide a unified notification API across 100+ channels including native
    desktop toast notifications (Windows, macOS, Linux) and external services
    such as email, Slack, Microsoft Teams, and Telegram.

    Parameters
    ----------
    channels : list[NotificationChannel | str] | None, optional
        List of apprise-compatible channel URLs.  When ``None`` or empty the
        native desktop notification service for the current OS is used
        automatically (Windows toast, macOS Notification Center, Linux D-Bus).

        Use :class:`NotificationChannel` members for the common schemes, or
        pass a plain :class:`str` for any URL supported by apprise::

            NotificationChannel.WINDOWS  # Windows 10/11 toast
            NotificationChannel.DBUS  # Linux (GNOME / KDE)
            NotificationChannel.MACOS  # macOS Notification Center
            NotificationChannel.MAILTO + "user:pass@gmail.com"  # Gmail
            NotificationChannel.MAILTOS + "user:pass@smtp.corp.com"  # SMTP/TLS
            NotificationChannel.SLACK + "token/channel"  # Slack
            NotificationChannel.MSTEAMS + "A/B/C/D"  # MS Teams
            "tgram://bot_token/chat_id"  # Telegram (plain str)

        See https://appriseit.com/ for the full list.
    title : str, optional
        Default notification title, by default ``"PyAnsys"``.
    format : NotificationFormat, optional
        Default body format, by default :attr:`NotificationFormat.TEXT`.
    notification_type : NotificationType, optional
        Default notification_type level, by default :attr:`NotificationType.INFO`.

    Examples
    --------
    Standalone one-liner (desktop notification, auto-detected OS):

    >>> notifier = AnsysNotifier()
    >>> notifier.notify("Simulation complete.")

    Integration inside a PyAnsys library, with a product-specific title and a
    success notification_type:

    >>> from ansys.tools.common.notifications import AnsysNotifier, NotificationType
    >>> _notifier = AnsysNotifier(title="PyMAPDL", notification_type=NotificationType.SUCCESS)
    >>> _notifier.notify("Solve finished in 42 iterations.")

    Multi-channel (desktop + email):

    >>> notifier = AnsysNotifier(
    ...     channels=[NotificationChannel.WINDOWS, NotificationChannel.MAILTOS + "user:pass@smtp.company.com"]
    ... )
    >>> notifier.notify("Job converged.")

    HTML-formatted notification:

    >>> from ansys.tools.common.notifications import NotificationFormat
    >>> notifier = AnsysNotifier(format=NotificationFormat.HTML)
    >>> notifier.notify("<b>Residual:</b> 1.23e-6 &mdash; converged.")
    """

    def __init__(
        self,
        channels: list[NotificationChannel | str] | None = None,
        title: str = "PyAnsys",
        format: NotificationFormat = NotificationFormat.TEXT,  # noqa: A002
        notification_type: NotificationType = NotificationType.INFO,
    ) -> None:
        """Initialize the notifier and register notification channels."""
        self._ap = apprise.Apprise()
        self._title = title
        self._format = NotificationFormat(format)
        self._notification_type = NotificationType(notification_type)

        for url in channels or [_desktop_url()]:
            self.add_channel(url)

    @property
    def title(self) -> str:
        """Default title applied to all notifications from this instance."""
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self._title = value

    @property
    def format(self) -> NotificationFormat:  # noqa: A003
        """Default body format applied to all notifications from this instance."""
        return self._format

    @format.setter
    def format(self, value: NotificationFormat) -> None:  # noqa: A003
        self._format = NotificationFormat(value)

    @property
    def notification_type(self) -> NotificationType:
        """Default notification_type applied to all notifications from this instance."""
        return self._notification_type

    @notification_type.setter
    def notification_type(self, value: NotificationType) -> None:
        self._notification_type = NotificationType(value)

    def add_channel(self, url: str) -> bool:
        """Add a notification channel.

        Parameters
        ----------
        url : str
            An apprise-compatible notification URL.

        Returns
        -------
        bool
            ``True`` if the channel was accepted, ``False`` if the URL was
            invalid or a required backend library is not installed.

        Examples
        --------
        >>> notifier = AnsysNotifier(channels=[])
        >>> notifier.add_channel(NotificationChannel.SLACK + "token/channel")
        True
        """
        return self._ap.add(url)

    def notify(
        self,
        message: str,
        title: str | None = None,
        format: NotificationFormat | None = None,  # noqa: A002
        notification_type: NotificationType | None = None,
    ) -> bool:
        """Send a notification to all registered channels.

        Parameters
        ----------
        message : str
            Body of the notification.
        title : str | None, optional
            Overrides the instance-level :attr:`title` for this call only.
        format : NotificationFormat | None, optional
            Overrides the instance-level :attr:`format` for this call only.
        notification_type : NotificationType | None, optional
            Overrides the instance-level :attr:`notification_type` for this call only.

        Returns
        -------
        bool
            ``True`` if every channel accepted the notification, ``False`` if
            at least one channel failed.

        Examples
        --------
        Basic informational notification:

        >>> notifier.notify("Solve complete.")

        Failure notification with a per-call notification_type override:

        >>> notifier.notify("Divergence detected.", notification_type=NotificationType.FAILURE)

        Success notification with a per-call title override:

        >>> notifier.notify("Converged in 42 steps.", title="MyApp", notification_type=NotificationType.SUCCESS)
        """
        return self._ap.notify(
            title=title if title is not None else self._title,
            body=message,
            body_format=(NotificationFormat(format) if format is not None else self._format).value,
            notify_type=(
                NotificationType(notification_type) if notification_type is not None else self._notification_type
            ).value,
        )


def notify(
    message: str,
    title: str = "PyAnsys",
    channels: list[NotificationChannel | str] | None = None,
    format: NotificationFormat = NotificationFormat.TEXT,  # noqa: A002
    notification_type: NotificationType = NotificationType.INFO,
) -> bool:
    """Send a one-shot notification without creating a persistent notifier.

    This convenience function is intended for simple script usage where a
    persistent :class:`AnsysNotifier` instance is not needed.

    Parameters
    ----------
    message : str
        Body of the notification.
    title : str, optional
        Notification title, by default ``"PyAnsys"``.
    channels : list[NotificationChannel | str] | None, optional
        Apprise channel URLs. When ``None``, the native desktop notification
        service for the current OS is used.
    format : NotificationFormat, optional
        Body format, by default :attr:`NotificationFormat.TEXT`.
    notification_type : NotificationType, optional
        notification_type level, by default :attr:`NotificationType.INFO`.

    Returns
    -------
    bool
        ``True`` if delivered successfully to all channels.

    Examples
    --------
    Minimal usage — sends a desktop notification:

    >>> from ansys.tools.common.notifications import notify
    >>> notify("Simulation complete.")

    Failure notification:

    >>> notify("Solve diverged!", notification_type=NotificationType.FAILURE)

    Multi-channel:

    >>> notify("Job done.", channels=[NotificationChannel.WINDOWS, NotificationChannel.SLACK + "token/channel"])
    """
    return AnsysNotifier(channels=channels, title=title, format=format, notification_type=notification_type).notify(
        message
    )
