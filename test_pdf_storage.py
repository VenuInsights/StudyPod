
from core.pdf_storage import save_pdf, load_pdf, delete_pdf


# Test account and conversation identifiers
test_user_id = "studypod_test_user"
test_chat_id = "studypod_test_chat"

# A small PDF-like byte sample for testing GridFS storage.
# This test checks storage and retrieval, not PDF parsing.
test_pdf_bytes = b"%PDF-1.4\nStudyPod GridFS storage test\n%%EOF"

print("\n1. Testing PDF storage...")

file_id = save_pdf(
    test_user_id,
    test_chat_id,
    test_pdf_bytes,
    "test_document.pdf"
)

print("Saved PDF file ID:", file_id)


print("\n2. Testing PDF retrieval...")

retrieved_pdf = load_pdf(
    test_user_id,
    test_chat_id,
    file_id
)

assert retrieved_pdf is not None
assert retrieved_pdf["filename"] == "test_document.pdf"
assert retrieved_pdf["pdf_bytes"] == test_pdf_bytes

print("PDF retrieval successful!")


print("\n3. Testing user ownership...")

wrong_user_pdf = load_pdf(
    "another_user",
    test_chat_id,
    file_id
)

assert wrong_user_pdf is None

print("Ownership verification successful!")


print("\n4. Testing PDF deletion...")

deleted = delete_pdf(
    test_user_id,
    test_chat_id,
    file_id
)

assert deleted is True

print("PDF deletion successful!")


print("\n5. Verifying deletion...")

deleted_pdf = load_pdf(
    test_user_id,
    test_chat_id,
    file_id
)

assert deleted_pdf is None

print("PDF no longer exists.")

print("\nAll PDF storage tests passed!")
