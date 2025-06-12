.. _contribute:

Contribute
##########

Overall guidance on contributing to a PyAnsys library appears in the
`Contributing <https://dev.docs.pyansys.com/how-to/contributing.html>`_ topic
in the *PyAnsys developer's guide*. Ensure that you are thoroughly familiar
with this guide before attempting to contribute to the Ansys tools common repo.

The following contribution information is specific to the Ansys tools common.

Install in developer mode
-------------------------

Installing the Ansys tools in developer mode allows you to modify and enhance
the source.

To clone and install the latest Ansys tools release in development mode, run
these commands:

.. code::

    git clone https://github.com/ansys/ansys-tools-common
    cd ansys-tools-common
    python -m pip install --upgrade pip
    pip install -e .

Run tests
---------

Ansys tools common uses `pytest <https://docs.pytest.org/en/stable/>`_ for testing.

#. Prior to running tests, you must run this command to install
   test dependencies::

    pip install -e .[tests]

#. To then run the tests, navigate to the root directory of the repository and run this
   command::

    pytest

Adhere to code style
--------------------

The Ansys tools common follows the PEP8 standard as outlined in
`PEP 8 <https://dev.docs.pyansys.com/coding-style/pep8.html>`_ in
the *PyAnsys developer's guide* and implements style checking using
`pre-commit <https://pre-commit.com/>`_.

To ensure your code meets minimum code styling standards, run these commands::

  pip install pre-commit
  pre-commit run --all-files

You can also install this as a pre-commit hook by running this command::

  pre-commit install

This way, it's not possible for you to push code that fails the style checks::

  $ pre-commit install
  $ git commit -am "added my cool feature"
  blacken-docs.............................................................Passed
  codespell................................................................Passed
  check for merge conflicts................................................Passed
  debug statements (python)................................................Passed
  check yaml...............................................................Passed
  trim trailing whitespace.................................................Passed
  Add License Headers......................................................Passed
  Validate GitHub Workflows................................................Passed
  ruff check...............................................................Passed
  ruff format..............................................................Passed

Build the documentation
-----------------------

You can build the Ansys tools common documentation locally.

#. Prior to building the documentation, you must run this command to install
   documentation dependencies::

    pip install -e .[doc]

#. To then build the documentation, navigate to the ``docs`` directory and run
   this command::

    # On Linux or macOS
    make html

    # On Windows
    ./make.bat html

The documentation is built in the ``docs/_build/html`` directory.

You can clean the documentation build by running this command::

  # On Linux or macOS
  make clean

  # On Windows
  ./make.bat clean

Post issues
-----------

Use the `Ansys tools common Issues <https://github.com/ansys/ansys-tools-common/issues>`_
page to report bugs and request new features. When possible, use the issue templates provided.
If your issue does not fit into one of these templates, click the link for opening a blank issue.

If you have general questions about the PyAnsys ecosystem, email
`pyansys.core@ansys.com <pyansys.core@ansys.com>`_. If your
question is specific to the Ansys tools common, ask your
question in an issue as described in the previous paragraph.
