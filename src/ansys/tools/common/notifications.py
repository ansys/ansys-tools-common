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

from collections.abc import Callable
from enum import Enum
import functools
import platform

try:
    import apprise
except ImportError:
    raise ImportError(
        "The 'apprise' package is required for notifications. "
        'Install it with: pip install "ansys-tools-common[notifications]"'
    ) from None

__all__ = [
    "AnsysNotifier",
    "NotificationChannel",
    "NotificationFormat",
    "NotificationType",
    "notify",
    "notify_on_completion",
    "get_notification_channels",
    "get_notification_level",
    "get_notify_on_failure",
    "get_failure_notification_level",
    "set_notification_channels",
    "set_notification_level",
    "set_notify_on_failure",
    "set_failure_notification_level",
]


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
    """Notification type / type of the notification.

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


# ---------------------------------------------------------------------------
# Module-level global configuration
# ---------------------------------------------------------------------------
__default_channels: list[str] | None = None
__default_notification_level: NotificationType = NotificationType.INFO
__default_notify_on_failure: bool = True
__default_failure_notification_level: NotificationType = NotificationType.FAILURE


def get_notification_channels() -> list[str] | None:
    """Return the global default notification channels.

    Returns
    -------
    list[str] | None
        The channels set by :func:`set_notification_channels`, or ``None``
        if no global default is set (desktop channel will be used).
    """
    return __default_channels


def get_notification_level() -> NotificationType:
    """Return the global default notification level.

    Returns
    -------
    NotificationType
        The level set by :func:`set_notification_level`.
    """
    return __default_notification_level


def get_notify_on_failure() -> bool:
    """Return the global default for whether failure notifications are sent.

    Returns
    -------
    bool
        The value set by :func:`set_notify_on_failure`.
    """
    return __default_notify_on_failure


def get_failure_notification_level() -> NotificationType:
    """Return the global default notification level used on failure.

    Returns
    -------
    NotificationType
        The level set by :func:`set_failure_notification_level`.
    """
    return __default_failure_notification_level


def set_notification_channels(channels: list[NotificationChannel | str] | None) -> None:
    """Set the global default notification channels.

    Affects all subsequent calls to :func:`notify` and
    :func:`notify_on_completion` that do not supply an explicit *channels*
    argument. Setting *channels* to ``None`` reverts to the
    automatically detected desktop channel.

    Parameters
    ----------
    channels : list[NotificationChannel | str] | None
        A list of apprise-compatible channel URLs or :class:`NotificationChannel`
        members, or ``None`` to reset to the OS desktop default.

    Examples
    --------
    >>> set_notification_channels([NotificationChannel.SLACK + "token/channel"])
    >>> set_notification_channels(["myfancychannel", "anotherchannel"])
    >>> set_notification_channels(None)  # reset to desktop default
    """
    global __default_channels
    __default_channels = [str(c) for c in channels] if channels is not None else None


def set_notification_level(level: NotificationType | str) -> None:
    """Set the global default notification level.

    Affects all subsequent calls to :func:`notify` and
    :func:`notify_on_completion` that do not supply an explicit
    *notification_type* argument.

    Parameters
    ----------
    level : NotificationType | str
        A :class:`NotificationType` member or its string value
        (``"info"``, ``"success"``, ``"warning"``, ``"failure"``).

    Examples
    --------
    >>> set_notification_level("warning")
    >>> set_notification_level(NotificationType.FAILURE)
    """
    global __default_notification_level
    __default_notification_level = NotificationType(level)


def set_notify_on_failure(enabled: bool) -> None:
    """Set whether a notification is sent globally when a decorated function fails.

    Affects all subsequent calls to :func:`notify_on_completion` that do not
    supply an explicit *notify_on_failure* argument.

    Parameters
    ----------
    enabled : bool
        ``True`` to send a failure notification (default), ``False`` to suppress it.

    Examples
    --------
    >>> set_notify_on_failure(False)
    """
    global __default_notify_on_failure
    __default_notify_on_failure = bool(enabled)


def set_failure_notification_level(level: NotificationType | str) -> None:
    """Set the global default notification level used when a decorated function fails.

    Affects all subsequent calls to :func:`notify_on_completion` that do not
    supply an explicit *failure_notification_type* argument.

    Parameters
    ----------
    level : NotificationType | str
        A :class:`NotificationType` member or its string value
        (``"info"``, ``"success"``, ``"warning"``, ``"failure"``).

    Examples
    --------
    >>> set_failure_notification_level("warning")
    >>> set_failure_notification_level(NotificationType.FAILURE)
    """
    global __default_failure_notification_level
    __default_failure_notification_level = NotificationType(level)


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
    notification_type: NotificationType | None = None,
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
        Apprise channel URLs. When ``None``, the global default set by
        :func:`set_notification_channel` is used; if that is also ``None``,
        the native desktop notification service for the current OS is used.
    format : NotificationFormat, optional
        Body format, by default :attr:`NotificationFormat.TEXT`.
    notification_type : NotificationType | None, optional
        notification_type level.  When ``None``, the global default set by
        :func:`set_notification_level` is used (initially
        :attr:`NotificationType.INFO`).

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
    resolved_channels = channels if channels is not None else __default_channels
    resolved_type = notification_type if notification_type is not None else __default_notification_level
    return AnsysNotifier(
        channels=resolved_channels, title=title, format=format, notification_type=resolved_type
    ).notify(message)


def notify_on_completion(
    message: str | None = None,
    *,
    title: str = "PyAnsys",
    channels: list[NotificationChannel | str] | None = None,
    format: NotificationFormat = NotificationFormat.TEXT,  # noqa: A002
    notification_type: NotificationType | None = None,
    notify_on_failure: bool | None = None,
    failure_notification_type: NotificationType | None = None,
    failure_message: str | None = None,
) -> Callable:
    """Send a notification when the decorated function finishes.

    Wraps a callable so that a notification is dispatched automatically on
    success (and optionally on failure) without any extra code at each call
    site.

    Parameters
    ----------
    message : str | None, optional
        Body of the notification.  When ``None`` a default message is
        built from the wrapped function's name: ``"<func_name> completed."``.
    title : str, optional
        Notification title, by default ``"PyAnsys"``.
    channels : list[NotificationChannel | str] | None, optional
        Apprise channel URLs.  When ``None``, the global default set by
        :func:`set_notification_channel` is used; if that is also ``None``,
        the native desktop notification service for the current OS is used.
    format : NotificationFormat, optional
        Body format, by default :attr:`NotificationFormat.TEXT`.
    notification_type : NotificationType | None, optional
        Notification type used for the notification.  When ``None``, the
        global default set by :func:`set_notification_level` is used
        (initially :attr:`NotificationType.INFO`).
    notify_on_failure : bool | None, optional
        When ``True`` a notification is also sent if the wrapped function
        raises an exception.  The exception is always re-raised.  When
        ``None``, the global default set by :func:`set_notify_on_failure`
        is used (initially ``True``).
    failure_notification_type : NotificationType | None, optional
        Notification type used for the failure notification.  When ``None``,
        the global default set by :func:`set_failure_notification_level` is
        used (initially :attr:`NotificationType.FAILURE`).
    failure_message : str | None, optional
        Body of the failure notification.  When ``None`` a default message is
        built from the wrapped function's name and the exception:
        ``"<func_name> failed: <exception>"``.

    Returns
    -------
    Callable
        A decorator that wraps the target function.

    Examples
    --------
    Send a desktop notification when the function returns:

    >>> from ansys.tools.common.notifications import notify_on_completion
    >>> @notify_on_completion("Simulation complete.")
    ... def run_simulation():
    ...     pass

    Auto-generate the message from the function name:

    >>> @notify_on_completion()
    ... def solve():
    ...     pass

    Custom channels and failure notification:

    >>> @notify_on_completion(
    ...     channels=[NotificationChannel.SLACK + "token/channel"],
    ...     notify_on_failure=True,
    ... )
    ... def long_running_job():
    ...     pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            resolved_type = notification_type if notification_type is not None else __default_notification_level
            resolved_notify_on_failure = (
                notify_on_failure if notify_on_failure is not None else __default_notify_on_failure
            )
            resolved_failure_type = (
                failure_notification_type
                if failure_notification_type is not None
                else __default_failure_notification_level
            )
            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                if resolved_notify_on_failure:
                    failure_msg = failure_message or f"{func.__name__} failed: {exc}"
                    notify(
                        failure_msg,
                        title=title,
                        channels=channels,
                        format=format,
                        notification_type=resolved_failure_type,
                    )
                raise
            success_msg = message or f"{func.__name__} completed."
            notify(success_msg, title=title, channels=channels, format=format, notification_type=resolved_type)
            return result

        return wrapper

    return decorator
