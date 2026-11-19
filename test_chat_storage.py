
import uuid

from core.chat_storage import (
    save_conversation,
    load_conversations,
    delete_conversation
)

# Use a temporary conversation ID for testing.
test_chat_id = str(uuid.uuid4())

# Use the existing test account from your authentication test.
test_user_id = "6afeb3c2adb059d46a591984"

test_chat = {
    "title": "MongoDB Storage Test",
    "title_customized": True,
    "pdf_name": None,
    "pdf_hash": None,
    "chat_history": [
        {
            "role": "user",
            "content": "What is DBMS?"
        },
        {
            "role": "assistant",
            "content": "DBMS stands for Database Management System."
        }
    ],
    "last_retrieved_chunks": [],
    "document_summary": None,
    "created_at": "2026-11-19"
}

try:
    # 1. Save conversation
    saved = save_conversation(
        test_user_id,
        test_chat_id,
        test_chat
    )

    print("Save test:", saved)

    # 2. Load conversations
    chats = load_conversations(test_user_id)

    print(
        "Load test:",
        test_chat_id in chats
    )

    if test_chat_id in chats:
        print("Conversation title:", chats[test_chat_id]["title"])
        print("Saved messages:", len(chats[test_chat_id]["chat_history"]))

    # 3. Delete test conversation
    deleted = delete_conversation(
        test_user_id,
        test_chat_id
    )

    print("Delete test:", deleted)

except Exception as error:
    print("Storage test failed:", error)
