.. _ref_ansys_tools_path:

Ansys path tool
===============

Use the Ansys path tool to find the path of the latest local Ansys installation. Importing this tool and then call the :func:`find_ansys <ansys.tools.common.path.find_ansys>` function to return the installation path:

.. code:: pycon

   >>> from ansys.tools.common.path import find_ansys
   >>> find_ansys()
   'C:/Program Files/ANSYS Inc/v211/ANSYS/bin/winx64/ansys211.exe', 21.1
