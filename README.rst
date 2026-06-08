
#######
tg-up
#######
Upload and download files to Telegram up to **4 GiB** (2 GiB for free users) using your personal account. Turn Telegram into your personal ☁ cloud!

To **install 🔧 tg-up**, run this command in your terminal:

.. code-block:: console

    $ pip install tg-up

Or from source:

.. code-block:: console

    $ pip install -e <path-to-repo>

🐍 **Python 3.7-3.13** supported.

❓ Usage
========
To use this program you need a Telegram account and your **App api_id & api_hash** (get it in
`my.telegram.org <https://my.telegram.org/>`_). The first time you use tg-up it requests your
📱 **telephone**, **api_id** and **api_hash**. Bot tokens cannot be used (bot uploads are limited to 50MB).

To **send ⬆️ files** (default: saved messages):

.. code-block:: console

    $ tg-up file1.mp4 file2.mkv

To **reply to a specific message**:

.. code-block:: console

    $ tg-up video.mp4 --to @chat --reply-to 12345

You can **download ⤵️ files** from your saved messages (default) or from a channel:

.. code-block:: console

    $ tg-dw

Interactive mode
----------------
The **interactive option** (``--interactive``) allows you to choose the dialog and the files with a **terminal 🪄 wizard**:

.. code-block:: console

    $ tg-up --interactive          # Interactive upload
    $ tg-dw --interactive          # Interactive download

Set group or chat
-----------------
For upload, use ``--to <entity>``:

.. code-block::

    $ tg-up --to @channel video.mkv

For download, use ``--from <entity>``:

.. code-block::

    $ tg-dw --from username

Reply to a message
------------------
You can reply to a specific message ID with ``--reply-to``:

.. code-block::

    $ tg-up file.mp4 --to @chat --reply-to 42

Split & join files
------------------
Enable ✂ **split mode** for large files:

.. code-block:: console

    $ tg-up --large-files split large-video.mkv

Rejoin on download:

.. code-block:: console

    $ tg-dw --split-files join

Delete on success
-----------------
``--delete-on-success`` deletes the Telegram message after downloading / the local file after uploading.

Configuration
-------------
Credentials saved in ``~/.config/tg-up.json`` and ``~/.config/tg-up.session``.
You can copy these 📁 files to authenticate on more machines.

More options
------------
Customize thumbnail (``--thumbnail-file``), caption with variables (``--caption``), proxy (``--proxy`` / ``TG_UP_PROXY``),
parallel upload blocks (``TG_UP_PARALLEL_UPLOAD_BLOCKS``), and more.

💡 Features
===========

* **Upload** and **download** multiples files (up to 4 GiB).
* **Interactive** mode.
* **Reply to** a specific message (``--reply-to``).
* Add video **thumbs**.
* **Split** and **join** large files.
* **Delete** local or remote file on success.
* Use **variables** in the **caption** message.
* **Proxy** support (http, socks4/5, mtproxy).
* **Parallel upload** blocks (env: ``TG_UP_PARALLEL_UPLOAD_BLOCKS``).


