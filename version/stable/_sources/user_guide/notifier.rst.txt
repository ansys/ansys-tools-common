.. _notifier:

Ansys Notifier
==============

The Ansys Notifier is a tool for sending notifications to various channels, such as email,
Slack, Microsoft Teams, and more. It is built on top of the Apprise library, which provides
a unified interface for sending notifications to multiple services.

To use the Ansys Notifier, you need to first install the optional dependencies.

.. code-block:: bash

    pip install "ansys-tools-common[notifications]"


Once you have the dependencies installed, you can create an instance of the `AnsysNotifier` class
and use it to include it into your code to send notifications. For example:

.. code-block:: python

    from ansys.tools.common.notifications import AnsysNotifier

    notifier = AnsysNotifier()
    notifier.notify("Hello, world!")


Or you can use the convenience function to send a notification without creating an instance:

.. code-block:: python

    from ansys.tools.common.notifications import notify

    notify("Hello, world!")

In both cases, the notification is sent to the native desktop notification service for the
current OS (Windows toast, macOS Notification Center, or Linux D-Bus) unless you specify
channels explicitly.

Notification channels
---------------------

Use :class:`~ansys.tools.common.notifications.NotificationChannel` members to select
well-known channels with IDE auto-complete support.  Channels whose URLs require
credentials or IDs (such as Slack or email) are provided as scheme prefixes that you
concatenate with your specific tokens.

.. list-table:: Built-in channel schemes
   :header-rows: 1
   :widths: 25 30 45

   * - Member
     - URL / prefix
     - Notes
   * - ``NotificationChannel.WINDOWS``
     - ``windows://``
     - Windows 10/11 native toast
   * - ``NotificationChannel.MACOS``
     - ``macosx://``
     - macOS Notification Center
   * - ``NotificationChannel.DBUS``
     - ``dbus://``
     - Linux desktop via D-Bus (GNOME, KDE, …)
   * - ``NotificationChannel.MAILTO``
     - ``mailto://``
     - Gmail with App Password; append ``user:pass@gmail.com``
   * - ``NotificationChannel.MAILTOS``
     - ``mailtos://``
     - Corporate SMTP/TLS; append ``user:pass@smtp.corp.com``
   * - ``NotificationChannel.SLACK``
     - ``slack://``
     - Slack; append ``token/channel``
   * - ``NotificationChannel.MSTEAMS``
     - ``msteams://``
     - Microsoft Teams webhook; append ``A/B/C/D``

.. code-block:: python

    from ansys.tools.common.notifications import AnsysNotifier, NotificationChannel, notify

    # Fixed channels — use the enum member directly
    notifier = AnsysNotifier(channels=[NotificationChannel.WINDOWS])

    # Parametrised channels — concatenate your credentials
    notify(
        "Job done.",
        channels=[
            NotificationChannel.SLACK + "mytoken/mychannel",
            NotificationChannel.MAILTOS + "user:pass@smtp.company.com",
        ],
    )

A plain :class:`str` is always accepted, so existing code using raw URL strings continues
to work unchanged.  For channels not listed above, pass a plain string with any URL
supported by Apprise.  The full list of services is available at
`<https://appriseit.com/services/>`_.

Global configuration
--------------------

Process-wide defaults can be set once, for example at app start-up,
so that every subsequent call to :func:`~ansys.tools.common.notifications.notify`
and :func:`~ansys.tools.common.notifications.notify_on_completion` picks them up
automatically without repeating the same arguments everywhere.

Four settings are available, each controlled by a getter/setter pair:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Setter / Getter
     - Description
   * - ``set_notification_channels`` / ``get_notification_channels``
     - Default channels used when no *channels* argument is passed. ``None``
       restores the auto-detected desktop channel.
   * - ``set_notification_level`` / ``get_notification_level``
     - Default :class:`~ansys.tools.common.notifications.NotificationType` for
       success notifications (initial value: ``INFO``).
   * - ``set_notify_on_failure`` / ``get_notify_on_failure``
     - Whether a failure notification is sent when a decorated function raises
       (initial value: ``True``).
   * - ``set_failure_notification_level`` / ``get_failure_notification_level``
     - Default :class:`~ansys.tools.common.notifications.NotificationType` for
       failure notifications (initial value: ``FAILURE``).

.. code-block:: python

    from ansys.tools.common.notifications import (
        set_notification_channels,
        set_notification_level,
        set_notify_on_failure,
        set_failure_notification_level,
        get_notification_channels,
        get_notification_level,
        NotificationChannel,
        NotificationType,
        notify,
        notify_on_completion,
    )

    # Configure once at start-up
    set_notification_channels([NotificationChannel.SLACK + "mytoken/mychannel"])
    set_notification_level(NotificationType.SUCCESS)
    set_notify_on_failure(True)
    set_failure_notification_level(NotificationType.FAILURE)

    # All subsequent calls use the defaults above — no need to repeat them
    notify("Simulation complete.")


    @notify_on_completion("Solve finished.")
    def solve():
        ...

Per-call arguments always take priority over the global defaults, so individual
calls can still override any setting when needed:

.. code-block:: python

    # Override the global channel for this call only
    notify("Done.", channels=[NotificationChannel.WINDOWS])