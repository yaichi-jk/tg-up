.. highlight:: console

============
Installation
============


Stable release
--------------

To install tg-up, run these commands in your terminal:

.. code-block:: console

    $ sudo pip3 install -U tg-up

This is the preferred method to install tg-up, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


Other releases
--------------
You can install other versions from Pypi using::

    $ pip install tg-up==<version>

For versions that are not in Pypi (it is a development version)::

    $ pip install git+https://github.com/yaichi-jk/tg-up.git@<branch>#egg=tg_up


If you do not have git installed::

    $ pip install https://github.com/yaichi-jk/tg-up/archive/<branch>.zip

Docker
======
Run tg-up without installing it on your system using Docker. Instead of ``tg-up``
and ``tg-dw`` you should use ``upload`` and ``download``. Usage::


    docker run -v <files_dir>:/files/
               -v <config_dir>:/config/
               -it yaichi-jk/tg-up:master
               <command> <args>

* ``<files_dir>``: Upload or download directory.
* ``<config_dir>``: Directory that will be created to store the tg-up configuration.
  It is created automatically.
* ``<command>``: ``upload`` and ``download``.
* ``<args>``: ``tg-up`` and ``tg-dw`` arguments.

For example::

    docker run -v /media/data/:/files/
               -v $PWD/config:/config/
               -it yaichi-jk/tg-up:master
               upload file_to_upload.txt
