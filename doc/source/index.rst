Ansys tools common |version|
====================================================

The Ansys tools project is a collection of tools for the PyAnsys ecosystem.



.. grid:: 1 2 2 2


    .. grid-item-card:: Getting started :material-regular:`directions_run`
        :padding: 2 2 2 2
        :link: getting_started/index
        :link-type: doc

        Learn how to install the collection.

    .. grid-item-card:: User guide :material-regular:`menu_book`
        :padding: 2 2 2 2
        :link: user_guide/index
        :link-type: doc

        Understand key concepts for using the tools into your workflow.

    .. jinja:: main_toctree

        {% if build_api %}
        .. grid-item-card:: API reference :material-regular:`bookmark`
            :padding: 2 2 2 2
            :link: api/index
            :link-type: doc

            Understand how to use Python to interact programmatically with
            the Ansys tools collection.
        {% endif %}

        {% if build_examples %}
        .. grid-item-card:: Examples :material-regular:`play_arrow`
            :padding: 2 2 2 2
            :link: examples/index
            :link-type: doc

            Explore examples that show how to use the different tools.
        {% endif %}

        .. grid-item-card:: Contribute :material-regular:`group`
            :padding: 2 2 2 2
            :link: contributing
            :link-type: doc

            Learn how to contribute to the Ansys tools codebase or documentation.


.. jinja:: main_toctree

    .. toctree::
       :hidden:
       :maxdepth: 3

       getting_started/index
       user_guide/index
       {% if build_api %}
       api/index
       {% endif %}
       {% if build_examples %}
       examples/index
       {% endif %}
       contributing