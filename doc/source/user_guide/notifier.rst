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
