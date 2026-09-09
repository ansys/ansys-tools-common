.. _ref_ansys_tools_path:

Ansys pathing tool
==================

The Ansys pathing tool provides a way to identify the path of the local Ansys installation.

How to use
----------

You can use any of the functions available in the
to identify the path of the local Ansys installation.

For example you can use :func:`find_ansys <ansys.tools.common.path.find_ansys>`
to locate the path of the latest Ansys installation available:

.. code:: pycon

   >>> from ansys.tools.common.path import find_ansys
   >>> find_ansys()
   'C:/Program Files/ANSYS Inc/v211/ANSYS/bin/winx64/ansys211.exe', 21.1
