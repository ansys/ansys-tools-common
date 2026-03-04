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

"""
.. _ref_notifications:

Job-completion notifications
-----------------------------

This example shows how to send desktop notifications from a PyAnsys workflow
using :class:`~ansys.tools.common.notifications.AnsysNotifier` and the
convenience function :func:`~ansys.tools.common.notifications.notify`.

Notifications are delivered as native desktop toasts on Windows, macOS, and
Linux with no extra configuration required.

.. note::

    Install the optional dependency before running this example::

        pip install "ansys-tools-common[notifications]"

"""

# Library integration pattern
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# PyAnsys libraries embed :class:`~ansys.tools.common.notifications.AnsysNotifier`
# inside their solver or session class and expose it as a public attribute so
# that users can configure it freely.

import time

from ansys.tools.common.notifications import AnsysNotifier, NotificationChannel, NotificationType


class Solver:
    """Minimal example of a PyAnsys library solver class with notification support."""

    def __init__(self, name: str = "MySolver"):
        self.name = name
        self.notifier = AnsysNotifier(title=name)

    def solve(self, iterations: int = 5) -> dict:
        """Run a fake solve loop and notify on completion."""
        residual = 1.0
        for _ in range(iterations):
            time.sleep(0.05)
            residual /= 10.0
        results = {"iterations": iterations, "residual": residual, "status": "converged"}
        self.notifier.notify(
            f"Converged in {results['iterations']} iterations. Residual: {results['residual']:.2e}",
            notification_type=NotificationType.SUCCESS,
        )
        return results



# Instantiate the solver
# ~~~~~~~~~~~~~~~~~~~~~~
# Instantiate the solver. By default it will send a desktop notification on
# whatever OS the user is running.

solver = Solver("PyFluent")
results = solver.solve(iterations=3)
print(results)



# Users can reconfigure the notifier on the object at any time — for example
# to add an extra channel such as email or Microsoft Teams. Check available services
# at https://appriseit.com/services/

# solver.notifier.add_channel(NotificationChannel.MAILTOS + "user:pass@smtp.company.com")
# solver.notifier.add_channel(NotificationChannel.MSTEAMS + "{team}/{tokenA}/{tokenB}/{tokenC}/")


# Convenience function
# ~~~~~~~~~~~~~~~~~~~~
#
# For one-off notifications in user scripts, use the module-level
# :func:`~ansys.tools.common.notifications.notify` function.  It requires no
# setup and auto-detects the OS.

from ansys.tools.common.notifications import notify

notify("Simulation complete.")


# Pass a custom
# ~~~~~~~~~~~~~
#
# Pass a custom title or notification_type level when needed.

notify("Solve diverged — check boundary conditions.", notification_type=NotificationType.FAILURE)
