.. ref_ansys_downloader:

Ansys example downloader
========================

You can use any of the functions available in the
to identify the path of the local Ansys installation.

For example you can use :func:`find_ansys <ansys.tools.common.path.find_ansys>`
to locate the path of the latest Ansys installation available:

.. code:: pycon

   >>> from ansys.tools.example_download import download_manager
   >>> filename = "11_blades_mode_1_ND_0.csv"
   >>> directory = "pymapdl/cfx_mapping"
   >>> local_path = download_manager.download_file(filename, directory)
