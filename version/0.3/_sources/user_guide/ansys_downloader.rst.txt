.. ref_ansys_downloader:

Ansys example downloader
========================

Use the Ansys example downloader to download an example from a PyAnsys library. Import this tool and then specify the filename, directory, and local path for the file to download:

.. code:: pycon

   >>> from ansys.tools.example_download import download_manager
   >>> filename = "11_blades_mode_1_ND_0.csv"
   >>> directory = "pymapdl/cfx_mapping"
   >>> local_path = download_manager.download_file(filename, directory)
