.. _install:

*******
Install
*******

Requirements
============
- `Astropy <https://www.astropy.org/>`_ 0.4 or later

Optional Requirements
---------------------
- `dill <https://pypi.python.org/pypi/dill>`_: Python serialization necessary for saving the
  current state of an executing Pipeline

Installing Astromatic-Wrapper
=============================

Anaconda Users
--------------
If you don't already have astropy and six installed you should use conda to install them, then
proceede to :ref:`using_pip`.

.. _using_pip:

Using pip to install from PYPI
------------------------------
Astromatic-Wrapper is registered in the 
`Python Package Index (pypi) <https://pypi.python.org/pypi>`_ and can be installed using ::

    pip install astromatic_wrapper

To install all of the required and optional dependencies use ::

    pip install astromatic_wrapper[all]

Astropy might take a while to compile.

.. note::

    pip can also be used to install the source code (see :ref:`installing_from_source`)

.. _installing_from_source:

Installing from source
----------------------

Obtaining the source code
^^^^^^^^^^^^^^^^^^^^^^^^^
Download the source code `here <https://github.com/fred3m/astromatic_wrapper>`_ on github, 
or by typing::

    git clone git://github.com/fred3m/astromatic_wrapper.git

Installing
^^^^^^^^^^
To install Astromatic-Wrapper from source code if you already have all of the dependencies,
navigate to the root directory of the source code and type::

    python setup.py install

To install all of the required and optional dependencies (currently only dill) navigate 
to the root directory of the source code and type ::

    pip install -e .[all]

.. note:: 

    On unix systems you may be required to prepend '*sudo*' to your install command::

        sudo python setup.py install

As this is a new package, please let me know any problems you have had installing the source code
so I can fix them or share steps needed to resolve them with other users. For bugs, please
create an `issue <https://github.com/fred3m/astromatic_wrapper/issues>`_ on github. 