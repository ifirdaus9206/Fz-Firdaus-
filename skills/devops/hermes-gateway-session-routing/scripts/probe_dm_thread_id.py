#!/usr/bin/env python
"""Prove which branch a Telegram message source takes for thread_id.

Usage (from the Hermes source tree, with the LIVE venv python):

    ./venv/bin/python <skill>/scripts/probe_dm_thread_id.py [repo_root]

repo_root defaults to ~/.hermes20/tools/hermes-source/hermes-agent (the copy the
$PREFIX/bin/hermes symlink actually runs on Termux).

Exit 0 = plain DM has no thread (one continuous session), configured DM topic and
forum group still keep theirs. Exit 1 = regression: a plain DM is back to one
session per message.
"""
import os
import sys

REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/.hermes20/tools/hermes-source/hermes-agent"
)
sys.path.insert(0, REPO)

from plugins.platforms.telegram.adapter import TelegramAdapter  # noqa: E402


class Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def mk(chat_type="private", chat_id=1312929583, thread=26084, topic=True, is_forum=False):
    chat = Obj(id=chat_id, type=chat_type, is_forum=is_forum)
    user = Obj(id=1312929583, username="probe", full_name="probe user")
    return Obj(chat=chat, from_user=user, sender_chat=None,
               message_thread_id=thread, is_topic_message=topic)


class FakeSelf:
    """Only the attributes the source builder reads."""

    def __init__(self, dm_topic_ids):
        self._dm_topic_chat_ids = dm_topic_ids


build = TelegramAdapter._source_from_message_for_auth

plain = build(FakeSelf(set()), mk())
topic = build(FakeSelf({"1312929583"}), mk())
forum = build(FakeSelf(set()), mk(chat_type="supergroup", topic=True, is_forum=True))

print("DM biasa        -> thread_id =", plain.thread_id, "| chat_type =", plain.chat_type)
print("DM topic config -> thread_id =", topic.thread_id)
print("Forum group     -> thread_id =", forum.thread_id)

ok = plain.thread_id is None and topic.thread_id == "26084" and forum.thread_id == "26084"
print("SEMUA UJIAN LULUS" if ok else "GAGAL: semak semula cabang dm/is_topic_message")
sys.exit(0 if ok else 1)
