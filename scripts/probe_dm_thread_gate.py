import sys, types
sys.path.insert(0, "/data/data/com.termux/files/home/.hermes20/tools/hermes-source/hermes-agent")
from plugins.platforms.telegram.adapter import TelegramAdapter as A

def msg(chat_id, ctype, tid, topic):
    chat = types.SimpleNamespace(id=chat_id, type=ctype, is_forum=False)
    return types.SimpleNamespace(chat=chat, message_thread_id=tid, is_topic_message=topic)

A._dm_topic_chat_ids = set()
r1 = A._effective_message_thread_id(msg(1312929583, "private", 26248, True))
A._dm_topic_chat_ids = {"1312929583"}
r2 = A._effective_message_thread_id(msg(1312929583, "private", 26248, True))
A._dm_topic_chat_ids = set()
r3 = A._effective_message_thread_id(msg(-100123, "supergroup", 77, True))
print("DM topic-flag tanpa konfigurasi ->", r1, "(mesti None)")
print("DM topic-flag DENGAN konfigurasi ->", r2, "(mesti 26248)")
print("Forum group ->", r3, "(mesti 77)")
sys.exit(0 if (r1 is None and r2 == "26248" and r3 == "77") else 1)
