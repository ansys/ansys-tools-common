.. _ref_report:

User guide
============

This section explains how to use ``pyansys-tools-report`` and its features.

Using PyAnsys Tools Report
--------------------------

Once the ``pyansys-tools-report`` package is installed in your own personal environment (if not, please proceed
to :ref:`ref_getting_started`), you can start importing the package and using it.

In order to import the package, please run:

.. code:: python

    import ansys.tools.report as pyansys_report

The ``pyansys-tools-report`` contains a main class called ``Report``. This class is basically an extension of the
``scooby.Report``, but customized for showing Ansys libraries and variables in a common format.

The possible arguments that the ``Report`` class accepts can be found in the `API reference <../api/index.html>`_. Please, have a look
at it to understand the arguments you may use. A simple example of Ansys variables and libraries is shown below.

.. code:: python

    # After defining my_ansys_libs and my_ansys_vars with the needed format (see API Reference)
    # we can start the instantiation of the report
    #
    # Instantiate a Report object
    rep = report.Report(ansys_libs=my_ansys_libs, ansys_vars=my_ansys_vars)

    # For printing the report
    rep

The typical output of a ``Report`` would look as follows:

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
    >>>                           appdirs : X.Y.Z
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


By default, the ``Report`` class would look for a certain set of environment variables. The following
strings are searched for in the available environment variables. If any match is found, they are included
in the report:

* ``AWP_ROOT``
* ``ANS``
* ``MAPDL``
* ``FLUENT``
* ``AEDT``
* ``DPF``

Also, several Python packages are reported by default. The set of reported packages always includes
the following list:

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
* ``appdirs``
* ``tqdm``
* ``pyiges``
* ``scipy``
* ``grpc``
* ``google.protobuf``

If you want the ``Report`` class to look for some extra environment variables by default, please
`raise an issue <https://github.com/ansys/pyansys-tools-report/issues>`_.

Enjoy its use. If you have any doubts, please raise a question/issue in the
`PyAnsys Tools Report Issues <https://github.com/ansys/pyansys-tools-report/issues>`_ site.