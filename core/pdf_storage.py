
from bson import ObjectId
from gridfs import GridFS
from core.database import get_database


def get_pdf_collection():
    """Get the GridFS storage handler."""

    db = get_database()
    return GridFS(db, collection="pdf_files")


def save_pdf(user_id, chat_id, pdf_bytes, filename):
    """
    Store a PDF in GridFS.

    Each PDF is associated with a specific user and conversation.
    If a PDF already exists for that conversation, replace it.
    """

    fs = get_pdf_collection()

    # Remove an older PDF belonging to this conversation.
    existing_file = fs.find_one({
        "metadata.user_id": str(user_id),
        "metadata.chat_id": str(chat_id)
    })

    if existing_file:
        fs.delete(existing_file._id)

    file_id = fs.put(
        pdf_bytes,
        filename=filename,
        contentType="application/pdf",
        metadata={
            "user_id": str(user_id),
            "chat_id": str(chat_id)
        }
    )

    return str(file_id)


def load_pdf(user_id, chat_id, file_id):
    """
    Retrieve a PDF only when it belongs to the requested user
    and conversation.
    """

    if not file_id:
        return None

    fs = get_pdf_collection()

    try:
        file_object = fs.get(ObjectId(file_id))

        metadata = file_object.metadata or {}

        # Verify ownership before returning the PDF.
        if (
            metadata.get("user_id") != str(user_id)
            or metadata.get("chat_id") != str(chat_id)
        ):
            return None

        return {
            "filename": file_object.filename,
            "pdf_bytes": file_object.read()
        }

    except Exception:
        return None


def delete_pdf(user_id, chat_id, file_id=None):
    """Delete a PDF belonging to a specific user and conversation."""

    fs = get_pdf_collection()

    if file_id:

        try:
            file_object = fs.get(ObjectId(file_id))

            metadata = file_object.metadata or {}

            if (
                metadata.get("user_id") == str(user_id)
                and metadata.get("chat_id") == str(chat_id)
            ):
                fs.delete(ObjectId(file_id))
                return True

            return False

        except Exception:
            return False

    # Delete all PDFs associated with this user's conversation.
    existing_files = fs.find({
        "metadata.user_id": str(user_id),
        "metadata.chat_id": str(chat_id)
    })

    deleted = False

    for file_object in existing_files:
        fs.delete(file_object._id)
        deleted = True

    return deleted
