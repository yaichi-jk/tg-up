
#######
tg-up
#######
Upload, download and clone files on Telegram up to **4 GiB** (2 GiB for free users) using your personal account. Turn Telegram into your personal ☁ cloud!

.. code-block:: console

    $ pip install yaichi-tg

🐍 **Python 3.7-3.13** supported.

❓ Setup
========
You need a Telegram account and your **App api_id & api_hash** (get it in
`my.telegram.org <https://my.telegram.org/>`_). The first time you run a command it requests your
📱 **telephone**, **api_id** and **api_hash**. Bot tokens cannot be used.

---

⬆️ Upload
==========

.. code-block:: console

    $ tg-up file1.mp4 file2.mkv          # Upload to saved messages
    $ tg-up video.mp4 --to @chat         # Upload to a chat/channel
    $ tg-up video.mp4 --to @chat --reply-to 42   # Reply to a message
    $ tg-up --interactive                # Interactive file selection

Options:
``--to``, ``--reply-to``, ``--thumbnail-file``, ``--no-thumbnail``,
``--caption``, ``--large-files split``, ``--proxy``, ``--config``, ``-i``.

---

⤵️ Download
============

.. code-block:: console

    $ tg-dw                              # Latest files from saved messages
    $ tg-dw --from @channel              # From a chat/channel
    $ tg-dw --interactive                # Interactive dialog & file selection
    $ tg-dw --url https://t.me/c/123/456/789       # By message URL
    $ tg-dw --url https://t.me/username/100-105    # URL with range
    $ tg-dw --from @chat --ids "1-5,10,15-20"      # By message IDs
    $ tg-dw --url ... --raw              # Print JSON metadata only
    $ tg-dw --url ... --raw-dl           # Print JSON metadata AND download

Options:
``--from``, ``--url``, ``--ids``, ``--raw``, ``--raw-dl``,
``--delete-on-success``, ``--split-files``, ``--proxy``, ``--config``, ``-i``.

**--url** supports:
- Public: ``https://t.me/username/123``, ``https://t.me/username/100-105``
- Private: ``https://t.me/c/chatid/123``, ``https://t.me/c/chatid/topic/123``
- Ranges: ``100-105``, ``100,102,105-110``

**--ids** accepts comma-separated IDs and ranges: ``1-5,10,15-20``.

**--raw/--raw-dl** outputs all details: caption, entities, file attributes (video/audio/doc), forward info, media type, document thumbs, chat entity, message flags.

---

🔄 Clone
=========
Copy messages between chats — media, captions, formatting, and all attributes preserved.

.. code-block:: console

    $ tg-clone --to @dest --url https://t.me/source/123        # By URL
    $ tg-clone --to @dest --from @source --ids "1-5,10"        # By IDs
    $ tg-clone --to @dest --from @source                       # All latest files
    $ tg-clone --to @dest -i                                   # Interactive selection
    $ tg-clone --to @dest --url ... --forward                  # Forward (keeps sender)
    $ tg-clone --to @dest --url ... --dry-run                  # Preview only

Clone strategy:

1. **Direct copy** (server-side, instant) — sends the media reference directly. Works when you have access to the source media.
2. **Fallback download+upload** (auto) — downloads the file and re-uploads with all original attributes (mime_type, video/audio attrs, thumbnails, caption entities, filename, streaming support).
3. Disable fallback with ``--no-fallback``.

Options:
``--to`` (required), ``--from``, ``--url``, ``--ids``, ``--forward``,
``--no-fallback``, ``--keep-files``, ``--dry-run``, ``--proxy``, ``--config``, ``-i``.

---

Interactive mode
-----------------
The ``--interactive`` / ``-i`` flag opens a terminal 🪄 wizard to pick dialogs and files:

.. code-block:: console

    $ tg-up --interactive       # Upload (select files)
    $ tg-dw --interactive       # Download (select files)
    $ tg-clone -i --to @dest    # Clone (select source + files)

---

Split & join files
------------------
Upload large files split into Telegram parts:

.. code-block:: console

    $ tg-up --large-files split large-video.mkv
    $ tg-dw --split-files join

---

Delete on success
-----------------
``--delete-on-success`` deletes the Telegram message after download / local file after upload.

---

Configuration
--------------
Credentials saved in ``~/.config/tg-up.json`` and ``~/.config/tg-up.session``.
You can copy these files to authenticate on more machines.

Proxy: ``--proxy socks5://user:pass@1.2.3.4:8080`` or env ``TG_UP_PROXY``.
Parallel upload blocks: env ``TG_UP_PARALLEL_UPLOAD_BLOCKS`` (default: 2).

---

💡 Features
===========

* **Upload** and **download** files up to 4 GiB.
* **Clone** messages between chats with full attribute preservation.
* **URL download** — download by any Telegram message URL, including ranges.
* **ID download** — download by message ID range (``1-5,10,15-20``).
* **JSON metadata** (``--raw`` / ``--raw-dl``) — full message info: caption, entities, file attrs, forward, media, thumbs.
* **Forward mode** for clone — preserves original sender attribution.
* **Dry-run** for clone — preview without executing.
* **Interactive** wizard for dialog and file selection.
* **Reply to** a specific message (``--reply-to``).
* **Thumbnails** for videos and documents.
* **Split** and **join** large files.
* **Delete** local or remote file on success.
* **Variables** in caption messages.
* **Proxy** support (http, socks4/5, mtproxy).
* **Parallel upload** blocks (env: ``TG_UP_PARALLEL_UPLOAD_BLOCKS``).
