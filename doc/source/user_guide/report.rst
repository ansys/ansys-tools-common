.. _ref_report:

Ansys report tool
=================

Use the Ansys report tool to generate detailed reports. This tool includes the main :class:`Report <ansys.tools.common.report.Report>` class, which extends ``scooby.Report`` and customizes it to display Ansys libraries and
environment variables in a standardized format.

To use the tool, import it:

.. code:: python

    import ansys.tools.report as pyansys_report

Here is an example of how to use the tool to display Ansys variables and libraries:

.. code:: python

    # Define my_ansys_libs and my_ansys_vars with the required format (see API Reference)
    # Instantiate a Report object
    rep = report.Report(ansys_libs=my_ansys_libs, ansys_vars=my_ansys_vars)

    # Print the report
    rep

The typical output of a report looks like this:

.. code-block:: text

    >>> -------------------------------------------------------------------------------
    >>> PyAnsys Software and Environment Report
    >>> -------------------------------------------------------------------------------
    >>> Date: Wed Nov 30 14:54:58 2022 Romance Standard Time
    >>>
    >>>                                OS : Windows
    >>>                            CPU(s) : 16
    >>>                           Machine : AMD64
    >>>                      Architecture : 64bit
    >>>                       Environment : Python
    >>>                        GPU Vendor : Intel
    >>>                      GPU Renderer : Intel(R) UHD Graphics
    >>>                       GPU Version : 4.5.0 - Build 30.0.100.9955
    >>>
    >>> Python 3.10.4 (tags/v3.10.4:9d38120, Mar 23 2022, 23:13:41) [MSC v.1929 64 bit (AMD64)]
    >>>
    >>>                  ansys-mapdl-core : X.Y.Z
    >>>                    ansys-dpf-core : X.Y.Z
    >>>                    ansys-dpf-post : X.Y.Z
    >>>                    ansys-dpf-gate : X.Y.Z
    >>>                 ansys-fluent-core : X.Y.Z
    >>>                            pyaedt : X.Y.Z
    >>> ansys-platform-instancemanagement : X.Y.Z
    >>>       ansys-grantami-bomanalytics : X.Y.Z
    >>>              ansys-openapi-common : X.Y.Z
    >>>                ansys-mapdl-reader : X.Y.Z
    >>>        ansys-fluent-visualization : X.Y.Z
    >>>           ansys-fluent-parametric : X.Y.Z
    >>>                ansys-sphinx-theme : X.Y.Z
    >>>                    ansys-seascape : X.Y.Z
    >>>              pyansys-tools-report : X.Y.Z
    >>>          pyansys-tools-versioning : X.Y.Z
    >>>                        matplotlib : X.Y.Z
    >>>                             numpy : X.Y.Z
    >>>                           pyvista : X.Y.Z
    >>>                      platformdirs : X.Y.Z
    >>>                              tqdm : X.Y.Z
    >>>                            pyiges : X.Y.Z
    >>>                             scipy : X.Y.Z
    >>>                              grpc : X.Y.Z
    >>>                   google.protobuf : X.Y.Z
    >>>
    >>>
    >>> -------------------------------------------------------------------------------
    >>> Ansys Environment Report
    >>> -------------------------------------------------------------------------------
    >>>
    >>>
    >>> Ansys Installation
    >>> ******************
    >>> Version   Location
    >>> ------------------
    >>> MyLib1       v1.2
    >>> MyLib2       v1.3
    >>>
    >>>
    >>> Ansys Environment Variables
    >>> ***************************
    >>> MYVAR_1                        VAL_1
    >>> MYVAR_2                        VAL_2

By default, the ``Report`` class searches for a predefined set of environment variables. The following strings are searched in the available environment variables, and any matches are included in the report:

* ``AWP_ROOT``
* ``ANS``
* ``MAPDL``
* ``FLUENT``
* ``AEDT``
* ``DPF``

The report also includes several Python packages by default. These packages are always included:

* ``ansys-mapdl-core``
* ``ansys-dpf-core``
* ``ansys-dpf-post``
* ``ansys-dpf-gate``
* ``ansys-fluent-core``
* ``pyaedt``
* ``ansys-platform-instancemanagement``
* ``ansys-grantami-bomanalytics``
* ``ansys-openapi-common``
* ``ansys-mapdl-reader``
* ``ansys-fluent-visualization``
* ``ansys-fluent-parametric``
* ``ansys-sphinx-theme``
* ``ansys-seascape``
* ``pyansys-tools-report``
* ``pyansys-tools-versioning``
* ``matplotlib``
* ``numpy``
* ``pyvista``
* ``platformdirs``
* ``tqdm``
* ``pyiges``
* ``scipy``
* ``grpc``
* ``google.protobuf``

If you want the ``Report`` class to include additional environment variables by default, create an
`issue <https://github.com/ansys/ansys-tools-common/issues>`_ and provide details about the variables that you want to include.