
from datetime import datetime, timezone

from core.database import get_database


def get_conversations_collection():
    """Get the conversations collection and create useful indexes."""

    db = get_database()
    conversations = db["conversations"]

    conversations.create_index([
        ("user_id", 1),
        ("updated_at", -1)
    ])

    return conversations


def make_serializable(value):
    """Convert nested values into MongoDB-compatible Python values."""

    if isinstance(value, dict):
        return {
            str(key): make_serializable(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [make_serializable(item) for item in value]

    # Convert NumPy-like scalar values into native Python values.
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, TypeError):
            pass

    return value


def save_conversation(user_id, chat_id, chat):
    """
    Save or update a conversation belonging to a specific user.

    PDF bytes, FAISS indexes, and extracted document data are
    intentionally excluded. Persistent PDF storage comes later.
    """

    conversations = get_conversations_collection()

    now = datetime.now(timezone.utc).isoformat()

    document = {
        "_id": chat_id,
        "user_id": str(user_id),
        "title": chat.get("title", "New Chat"),
        "title_customized": chat.get("title_customized", False),
        "pdf_name": chat.get("pdf_name"),
        "pdf_hash": chat.get("pdf_hash"),
        "chat_history": make_serializable(
            chat.get("chat_history", [])
        ),
        "last_retrieved_chunks": make_serializable(
            chat.get("last_retrieved_chunks", [])
        ),
        "document_summary": chat.get("document_summary"),
        "created_at": chat.get("created_at", now),
        "pdf_file_id": chat.get("pdf_file_id"),
        "updated_at": now
    }

    result = conversations.replace_one(
        {
            "_id": chat_id,
            "user_id": str(user_id)
        },
        document,
        upsert=True
    )

    return result.acknowledged


def load_conversations(user_id):
    """Load only conversations belonging to the logged-in user."""

    conversations = get_conversations_collection()

    cursor = conversations.find(
        {"user_id": str(user_id)}
    ).sort("updated_at", -1)

    chats = {}

    for document in cursor:

        chat_id = document["_id"]

        chats[chat_id] = {
            "title": document.get("title", "New Chat"),
            "title_customized": document.get(
                "title_customized", False
            ),
            "pdf_name": document.get("pdf_name"),
            "pdf_hash": document.get("pdf_hash"),

            # PDF and retrieval artifacts will be restored in Phase 9.
            "pdf_bytes": None,
            "extracted_pages": None,
            "vector_index": None,
            "chunks": None,

            "chat_history": document.get("chat_history", []),
            "last_retrieved_chunks": document.get(
                "last_retrieved_chunks", []
            ),
            "document_summary": document.get("document_summary"),
            "processing_error": None,
            "pdf_file_id": document.get("pdf_file_id"),
            "created_at": document.get("created_at")
        }

    return chats


def delete_conversation(user_id, chat_id):
    """Delete a conversation only if it belongs to this user."""

    conversations = get_conversations_collection()

    result = conversations.delete_one({
        "_id": chat_id,
        "user_id": str(user_id)
    })

    return result.deleted_count == 1
