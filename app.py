
import uuid
import hashlib
from datetime import datetime, timezone

import streamlit as st

from core.auth import register_user, login_user
from core.chat_storage import (
    save_conversation,
    load_conversations,
    delete_conversation
)
from core.pdf_processor import extract_text_from_pdf
from core.text_chunker import create_chunks
from core.vector_store import build_vector_index, search_similar_chunks
from core.answer_generator import generate_answer, generate_summary

from io import BytesIO
from core.pdf_storage import save_pdf, load_pdf, delete_pdf

# ---------------------------------
# Page Configuration
# ---------------------------------

st.set_page_config(
    page_title="StudyPod | AI Study Companion",
    page_icon="📚",
    layout="wide"
)


# ---------------------------------
# Custom Styling
# ---------------------------------

st.markdown(
    """
    <style>
        :root {
            --sp-ink: #172033;
            --sp-muted: #64748b;
            --sp-line: #e2e8f0;
            --sp-accent: #635bdb;
            --sp-accent-dark: #4f46c8;
            --sp-surface: #ffffff;
        }

        .stApp {
            background:
                radial-gradient(circle at 8% 0%, rgba(99, 91, 219, 0.07), transparent 28%),
                #f7f8fc;
            color: var(--sp-ink);
        }

        .block-container {
            max-width: 1120px;
            padding-top: 1.7rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            color: var(--sp-ink);
            letter-spacing: -0.025em;
        }

        h1 { font-weight: 750; }
        h2, h3 { font-weight: 680; }

        p, label, .stCaption {
            color: #475569;
        }

        [data-testid="stSidebar"] {
            background: #f0f1f8;
            border-right: 1px solid #e4e7f0;
        }

        [data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem;
        }

        [data-testid="stSidebar"] h1 {
            color: #29265e;
            font-size: 1.55rem;
            letter-spacing: -0.04em;
        }

        [data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
            background: white;
            border: 1px solid #dfe3ee;
            border-radius: 12px;
        }

        div.stButton > button,
        div[data-testid="stFormSubmitButton"] > button {
            border-radius: 11px;
            border: 1px solid #dfe3ee;
            font-weight: 650;
            min-height: 2.55rem;
            transition: all 0.15s ease;
        }

        div.stButton > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover {
            border-color: #a9a4ef;
            color: var(--sp-accent-dark);
        }

        div[data-testid="stForm"] {
            border: 1px solid #dfe3ee;
            border-radius: 18px;
            padding: 0.55rem 0.65rem;
            background: white;
            box-shadow: 0 8px 28px rgba(31, 41, 55, 0.06);
        }

        div[data-testid="stForm"] [data-testid="stTextInput"] input {
            border: none;
            box-shadow: none;
            background: transparent;
            min-height: 2.5rem;
        }

        div[data-testid="stForm"] [data-testid="stTextInput"] input:focus {
            box-shadow: none;
        }

        [data-testid="stFileUploader"] {
            background: white;
            border: 1px dashed #b8b8e7;
            border-radius: 16px;
            padding: 0.75rem;
        }

        [data-testid="stChatMessage"] {
            background: white;
            border: 1px solid #e8eaf2;
            border-radius: 16px;
            padding: 0.8rem 1rem;
            margin-bottom: 0.7rem;
            box-shadow: 0 3px 14px rgba(31, 41, 55, 0.035);
        }

        [data-testid="stMetric"] {
            background: white;
            padding: 14px;
            border-radius: 13px;
            border: 1px solid var(--sp-line);
        }

        [data-testid="stExpander"] {
            border: 1px solid #e5e7ef;
            border-radius: 12px;
            background: rgba(255,255,255,0.75);
        }

        .studypod-hero {
            background: linear-gradient(120deg, #25245c 0%, #514bb5 58%, #7771df 100%);
            border-radius: 22px;
            padding: 1.65rem 1.8rem;
            color: white;
            margin: 0.2rem 0 1.35rem 0;
            box-shadow: 0 12px 32px rgba(65, 60, 160, 0.17);
        }

        .studypod-hero h1 {
            color: white;
            font-size: 2rem;
            line-height: 1.15;
            margin: 0 0 0.45rem 0;
        }

        .studypod-hero p {
            color: rgba(255,255,255,0.84);
            margin: 0;
            font-size: 0.98rem;
        }

        .studypod-kicker {
            color: #dcdafe;
            font-size: 0.75rem;
            font-weight: 750;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            margin-bottom: 0.55rem;
        }

        .section-eyebrow {
            color: #7772c9;
            font-size: 0.72rem;
            font-weight: 750;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 0.2rem;
        }

        .upload-note {
            color: #64748b;
            font-size: 0.88rem;
            margin-top: -0.35rem;
            margin-bottom: 0.8rem;
        }

        .status-chip {
            display: inline-block;
            background: rgba(255,255,255,0.14);
            border: 1px solid rgba(255,255,255,0.25);
            border-radius: 999px;
            padding: 0.35rem 0.7rem;
            color: white;
            font-size: 0.78rem;
            font-weight: 650;
            margin-top: 1rem;
        }

        .soft-divider {
            height: 1px;
            background: #e7e9f1;
            margin: 1.1rem 0;
        }

        .auth-heading {
            text-align: center;
            margin-bottom: 1.5rem;
        }

        .auth-heading h1 {
            color: #29265e;
            font-size: 2.1rem;
        }

        .auth-heading p {
            color: #64748b;
        }

        .stAlert {
            border-radius: 12px;
        }

        @media (max-width: 700px) {
            .block-container {
                padding-top: 1rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .studypod-hero {
                padding: 1.25rem;
                border-radius: 17px;
            }

            .studypod-hero h1 {
                font-size: 1.65rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ---------------------------------
# Authentication State
# ---------------------------------

if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "Login"


# ---------------------------------
# Logout
# ---------------------------------

def logout_user():
    """Clear the current session without deleting saved conversations."""

    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()


# ---------------------------------
# Login and Registration Interface
# ---------------------------------

if st.session_state.authenticated_user is None:

    st.markdown(
        """
        <div class="auth-heading">
            <h1>📚 StudyPod</h1>
            <p>Your personal AI-powered study companion</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    auth_col1, auth_col2, auth_col3 = st.columns([1, 2, 1])

    with auth_col2:

        auth_mode = st.radio(
            "Choose an option",
            ["Login", "Register"],
            horizontal=True,
            key="auth_mode",
            label_visibility="collapsed"
        )

        st.divider()

        if auth_mode == "Login":

            st.subheader("Welcome back!")
            st.caption("Log in to continue learning with StudyPod.")

            with st.form("login_form"):

                login_email = st.text_input(
                    "Email address",
                    placeholder="Enter your email"
                )

                login_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password"
                )

                login_submitted = st.form_submit_button(
                    "Login",
                    use_container_width=True,
                    type="secondary"
                )

                if login_submitted:

                    if not login_email.strip() or not login_password:
                        st.error("Please enter your email and password.")

                    else:
                        with st.spinner("Verifying your account..."):

                            success, message, user = login_user(
                                login_email,
                                login_password
                            )

                        if success:
                            st.session_state.authenticated_user = user
                            st.rerun()

                        else:
                            st.error(message)

        else:

            st.subheader("Create your account")
            st.caption("Register to start using your personal study workspace.")

            with st.form("register_form"):

                register_username = st.text_input(
                    "Username",
                    placeholder="Choose a username"
                )

                register_email = st.text_input(
                    "Email address",
                    placeholder="Enter your email"
                )

                register_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Create a password"
                )

                confirm_password = st.text_input(
                    "Confirm password",
                    type="password",
                    placeholder="Re-enter your password"
                )

                register_submitted = st.form_submit_button(
                    "Create Account",
                    use_container_width=True,
                    type="secondary"
                )

                if register_submitted:

                    if not all([
                        register_username.strip(),
                        register_email.strip(),
                        register_password,
                        confirm_password
                    ]):
                        st.error("Please fill in all fields.")

                    elif register_password != confirm_password:
                        st.error("Passwords do not match.")

                    else:
                        with st.spinner("Creating your account..."):

                            success, message, user = register_user(
                                register_username,
                                register_email,
                                register_password
                            )

                        if success:
                            st.session_state.authenticated_user = user
                            st.rerun()

                        else:
                            st.error(message)

    st.stop()


# ---------------------------------
# Logged-in User and Database Loading
# ---------------------------------

current_user = st.session_state.authenticated_user
user_id = str(current_user["id"])


# Load conversations only once per login session.
# The flag prevents reloading and overwriting in-memory changes
# on every Streamlit rerun.

if not st.session_state.get("conversations_loaded", False):

    try:
        with st.spinner("Loading your conversations..."):

            st.session_state.chats = load_conversations(user_id)

            chat_ids = list(st.session_state.chats.keys())

            st.session_state.active_chat_id = (
                chat_ids[0] if chat_ids else None
            )

            st.session_state.conversations_loaded = True

    except Exception as error:

        st.error(f"Unable to load your conversations: {error}")
        st.stop()

# ---------------------------------
# Restore Previously Uploaded PDFs
# ---------------------------------

if not st.session_state.get("pdfs_restored", False):

    try:
        with st.spinner("Restoring your saved study documents..."):

            for chat_id, chat in st.session_state.chats.items():

                # Skip conversations without a saved PDF.
                if not chat.get("pdf_file_id"):
                    continue

                # Skip if the PDF is already loaded in this session.
                if chat.get("vector_index") is not None:
                    continue

                restored_pdf = load_pdf(
                    user_id,
                    chat_id,
                    chat["pdf_file_id"]
                )

                if restored_pdf is None:
                    chat["processing_error"] = (
                        "The saved PDF could not be found. "
                        "Please upload the document again."
                    )
                    continue

                pdf_bytes = restored_pdf["pdf_bytes"]

                # Extract text from the restored PDF.
                extracted_pages = extract_text_from_pdf(
                    BytesIO(pdf_bytes)
                )

                extracted_text = "".join(
                    page.get("text", "")
                    for page in extracted_pages
                )

                if not extracted_text.strip():
                    chat["processing_error"] = (
                        "No readable text was found in the saved PDF."
                    )
                    continue

                # Recreate chunks and the FAISS index.
                chunks = create_chunks(extracted_pages)

                if not chunks:
                    chat["processing_error"] = (
                        "Unable to create searchable text chunks "
                        "from the saved PDF."
                    )
                    continue

                index, stored_chunks = build_vector_index(chunks)

                # Restore document data in memory.
                chat["pdf_bytes"] = pdf_bytes
                chat["pdf_name"] = restored_pdf["filename"]
                chat["extracted_pages"] = extracted_pages
                chat["vector_index"] = index
                chat["chunks"] = stored_chunks
                chat["processing_error"] = None

            st.session_state.pdfs_restored = True

    except Exception as error:
        st.error(f"Unable to restore saved PDFs: {error}")
        st.stop()

# ---------------------------------
# Chat Management
# ---------------------------------

def persist_chat(chat_id):
    """Save one conversation to MongoDB."""

    chat = st.session_state.chats.get(chat_id)

    if chat is None:
        return

    save_conversation(user_id, chat_id, chat)


def create_new_chat():
    """Create, save, and activate a new conversation."""

    chat_id = str(uuid.uuid4())

    now = datetime.now(timezone.utc).isoformat()

    st.session_state.chats[chat_id] = {
        "title": "New Chat",
        "title_customized": False,
        "pdf_name": None,
        "pdf_hash": None,
        "pdf_bytes": None,
        "extracted_pages": None,
        "vector_index": None,
        "chunks": None,
        "chat_history": [],
        "last_retrieved_chunks": [],
        "document_summary": None,
        "processing_error": None,
        "pdf_file_id": None,
        "created_at": now
    }

    st.session_state.active_chat_id = chat_id

    persist_chat(chat_id)

    return chat_id


def delete_chat(chat_id):
    """Delete a conversation and its stored PDF."""

    chat = st.session_state.chats.get(chat_id)

    if chat is not None:

        # Delete the associated PDF from GridFS first.
        delete_pdf(
            user_id,
            chat_id,
            chat.get("pdf_file_id")
        )

    # Delete the conversation from MongoDB.
    delete_conversation(user_id, chat_id)

    st.session_state.chats.pop(chat_id, None)

    if st.session_state.get("rename_chat_id") == chat_id:
        st.session_state.rename_chat_id = None

    remaining_chat_ids = list(st.session_state.chats.keys())

    if remaining_chat_ids:

        next_chat_id = remaining_chat_ids[0]
        st.session_state.active_chat_id = next_chat_id

    else:

        next_chat_id = create_new_chat()

    st.session_state["chat_selector"] = next_chat_id


# ---------------------------------
# Sidebar - User Account and Chats
# ---------------------------------

with st.sidebar:

    st.title("📚 StudyPod")
    st.caption("Your AI study companion")

    st.markdown(
        '<div class="section-eyebrow">Your Account</div>',
        unsafe_allow_html=True
    )

    st.markdown(f"**{current_user['username']}**")
    st.caption(current_user["email"])

    if st.button(
        "🚪 Logout",
        use_container_width=True,
        type="secondary"
    ):
        logout_user()

    st.divider()

    st.markdown(
        '<div class="section-eyebrow">Workspace</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "＋  New conversation",
        use_container_width=True,
        type="secondary"
    ):

        new_chat_id = create_new_chat()
        st.session_state["chat_selector"] = new_chat_id
        st.rerun()

    st.divider()
    st.subheader("Your Conversations")

    
    chat_ids = list(st.session_state.chats.keys())

    # Ensure the user has at least one conversation.
    if not chat_ids:
        create_new_chat()
        chat_ids = list(st.session_state.chats.keys())

    # Ensure the active conversation belongs to this user's chat list.
    if st.session_state.active_chat_id not in chat_ids:
        st.session_state.active_chat_id = chat_ids[0]

    # Reset an outdated selector value if it is not a valid option.
    if st.session_state.get("chat_selector") not in chat_ids:
        st.session_state["chat_selector"] = st.session_state.active_chat_id

    selected_chat_id = st.selectbox(
        "Select a conversation",
        options=chat_ids,
        format_func=lambda chat_id: st.session_state.chats[chat_id]["title"],
        index=chat_ids.index(st.session_state.active_chat_id),
        key="chat_selector"
    )

    if selected_chat_id != st.session_state.active_chat_id:
        st.session_state.active_chat_id = selected_chat_id
        st.rerun()


    if selected_chat_id != st.session_state.active_chat_id:
        st.session_state.active_chat_id = selected_chat_id
        st.rerun()

    # Rename conversation

    if "rename_chat_id" not in st.session_state:
        st.session_state.rename_chat_id = None

    if st.button(
        "✏️ Rename This Chat",
        use_container_width=True
    ):
        st.session_state.rename_chat_id = st.session_state.active_chat_id
        st.rerun()

    if st.session_state.rename_chat_id == st.session_state.active_chat_id:

        with st.form(f"rename_form_{st.session_state.active_chat_id}"):

            new_chat_title = st.text_input(
                "Conversation name",
                value=st.session_state.chats[
                    st.session_state.active_chat_id
                ]["title"],
                max_chars=60
            )

            save_rename = st.form_submit_button("Save Name")
            cancel_rename = st.form_submit_button("Cancel")

            if save_rename:

                cleaned_title = new_chat_title.strip()

                if cleaned_title:

                    selected_chat = st.session_state.chats[
                        st.session_state.active_chat_id
                    ]

                    selected_chat["title"] = cleaned_title
                    selected_chat["title_customized"] = True

                    persist_chat(st.session_state.active_chat_id)

                    st.session_state.rename_chat_id = None
                    st.rerun()

                else:
                    st.warning("Please enter a conversation name.")

            if cancel_rename:
                st.session_state.rename_chat_id = None
                st.rerun()

    st.button(
        "🗑️ Delete This Chat",
        key=f"sidebar_delete_chat_{st.session_state.active_chat_id}",
        use_container_width=True,
        help="Delete this conversation and its saved study data.",
        on_click=delete_chat,
        args=(st.session_state.active_chat_id,)
    )

    st.divider()

    st.caption(
        "Your conversations are saved to your StudyPod account."
    )


# ---------------------------------
# Get Active Conversation
# ---------------------------------

active_chat_id = st.session_state.active_chat_id
active_chat = st.session_state.chats[active_chat_id]


# ---------------------------------
# Application Header
# ---------------------------------

st.markdown(
    """
    <div class="studypod-hero">
        <div class="studypod-kicker">Your AI-powered learning space</div>
        <h1>StudyPod</h1>
        <p>Turn your study material into clear answers, useful summaries, and better understanding.</p>
        <div class="status-chip">✦ Read · Ask · Understand</div>
    </div>
    """,
    unsafe_allow_html=True
)


# ---------------------------------
# PDF Upload and Automatic Processing
# ---------------------------------

st.markdown(
    '<div class="section-eyebrow">Start here</div>',
    unsafe_allow_html=True
)

st.subheader("📄 Your study material")

st.markdown(
    '<div class="upload-note">Upload a text-based PDF. StudyPod will automatically prepare it for questions and summaries.</div>',
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader(
    "Choose a PDF document",
    type=["pdf"],
    help="Upload your lecture notes, textbooks, or study materials.",
    key=f"pdf_uploader_{active_chat_id}"
)


if uploaded_file is not None:

    uploaded_bytes = uploaded_file.getvalue()
    uploaded_hash = hashlib.sha256(uploaded_bytes).hexdigest()

    # If a different PDF is uploaded to an existing conversation,
    # create a separate conversation for the new document.

    if (
        active_chat["pdf_hash"] is not None
        and active_chat["pdf_hash"] != uploaded_hash
    ):

        new_chat_id = create_new_chat()

        st.session_state["chat_selector"] = new_chat_id

        active_chat_id = new_chat_id
        active_chat = st.session_state.chats[active_chat_id]

    # Process if this is a new PDF OR if the old PDF needs to be
    # re-uploaded because its index is not persisted yet.

    if (
        active_chat["pdf_hash"] != uploaded_hash
        or active_chat["vector_index"] is None
    ):

        try:

            with st.spinner(
                "StudyPod is extracting your PDF and building the search index..."
            ):

                extracted_pages = extract_text_from_pdf(uploaded_file)

                extracted_text = "".join(
                    page.get("text", "")
                    for page in extracted_pages
                )

                if not extracted_text.strip():

                    active_chat["processing_error"] = (
                        "No readable text was found. This may be a scanned PDF. "
                        "Please upload a text-based PDF."
                    )

                    st.error(active_chat["processing_error"])

                else:

                    chunks = create_chunks(extracted_pages)

                    if not chunks:

                        active_chat["processing_error"] = (
                            "No text chunks could be created from this PDF."
                        )

                        st.error(active_chat["processing_error"])

                    else:

                        index, stored_chunks = build_vector_index(chunks)

                        # Save the original PDF in MongoDB GridFS.
                        pdf_file_id = save_pdf(
                            user_id,
                            active_chat_id,
                            uploaded_bytes,
                            uploaded_file.name
                        )

                        if not active_chat.get("title_customized", False):
                            active_chat["title"] = uploaded_file.name

                        active_chat["pdf_name"] = uploaded_file.name
                        active_chat["pdf_hash"] = uploaded_hash
                        active_chat["pdf_bytes"] = uploaded_bytes
                        active_chat["extracted_pages"] = extracted_pages
                        active_chat["vector_index"] = index
                        active_chat["chunks"] = stored_chunks
                        active_chat["chat_history"] = []
                        active_chat["last_retrieved_chunks"] = []
                        active_chat["document_summary"] = None
                        active_chat["processing_error"] = None
                        active_chat["pdf_file_id"] = pdf_file_id

                        persist_chat(active_chat_id)

                        st.success(
                            f"PDF processed successfully! "
                            f"{len(stored_chunks)} text chunks indexed."
                        )

        except Exception as error:

            active_chat["processing_error"] = (
                f"Unable to process PDF: {error}"
            )

            st.error(active_chat["processing_error"])


# ---------------------------------
# Document Status
# ---------------------------------

if active_chat["pdf_name"]:

    if active_chat["vector_index"] is not None:

        st.success(f"Ready to study: {active_chat['pdf_name']}")

        st.caption(
            f"✓ {len(active_chat['chunks'])} searchable text chunks prepared."
        )

    else:

        st.warning(
            f"This conversation previously used **{active_chat['pdf_name']}**. "
            "Please upload the same PDF again to continue asking questions. "
            "Your previous messages are still available below."
        )

elif active_chat["processing_error"]:

    st.error(active_chat["processing_error"])

else:

    st.info(
        "Upload a PDF to start studying. "
        "Your document will be processed automatically."
    )


# ---------------------------------
# Response Feedback
# ---------------------------------

def render_response_feedback(message, chat_id, message_index):

    """Show and save thumbs-up / thumbs-down feedback."""

    st.caption("Was this answer helpful?")

    feedback_col1, feedback_col2, _ = st.columns([1, 1, 8])

    with feedback_col1:

        if st.button(
            "👍",
            key=f"feedback_up_{chat_id}_{message_index}",
            help="This answer was helpful"
        ):

            message["feedback"] = "positive"
            persist_chat(chat_id)
            st.rerun()

    with feedback_col2:

        if st.button(
            "👎",
            key=f"feedback_down_{chat_id}_{message_index}",
            help="This answer was not helpful"
        ):

            message["feedback"] = "negative"
            persist_chat(chat_id)
            st.rerun()

    if message.get("feedback") == "positive":

        st.caption("Thanks for your feedback: helpful")

    elif message.get("feedback") == "negative":

        st.caption(
            "Thanks for your feedback. We'll use it to improve StudyPod."
        )


# ---------------------------------
# Conversational Study Assistant
# ---------------------------------

st.divider()

st.markdown(
    '<div class="section-eyebrow">Your conversation</div>',
    unsafe_allow_html=True
)

st.header("💬 Chat with StudyPod")


# Display conversation history even when the PDF index
# has not yet been restored.

if active_chat["chat_history"]:

    for message_index, message in enumerate(active_chat["chat_history"]):

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

            if message["role"] == "assistant" and message.get("sources"):

                source_count = len(message["sources"])

                with st.expander(
                    f"📚 Sources used · {source_count} passages"
                ):

                    st.caption(
                        "These passages were retrieved from your uploaded PDF "
                        "to help generate this answer. Scores are retrieval/"
                        "reranking signals, not answer-confidence percentages."
                    )

                    for source_number, source in enumerate(
                        message["sources"],
                        start=1
                    ):

                        with st.container(border=True):

                            st.markdown(
                                f"**Source {source_number}**  ·  "
                                f"**Page {source.get('page', 'N/A')}**"
                            )

                            st.markdown(source.get("text", ""))

                            score_details = []

                            if source.get("faiss_score") is not None:

                                score_details.append(
                                    f"FAISS similarity: {source['faiss_score']:.4f}"
                                )

                            if source.get("rerank_score") is not None:

                                score_details.append(
                                    f"Cross-Encoder reranking score: {source['rerank_score']:.4f}"
                                )

                            if score_details:
                                st.caption(" · ".join(score_details))

            if message["role"] == "assistant":

                render_response_feedback(
                    message,
                    active_chat_id,
                    message_index
                )


# Show the question input only when a PDF index is available.

if active_chat["vector_index"] is not None and active_chat["chunks"]:

    st.caption(
        "Ask a question, explore a concept, or request clarification "
        "from your uploaded material."
    )

    question = None

    with st.form(
        key=f"chat_composer_{active_chat_id}",
        clear_on_submit=True
    ):

        prompt_col, voice_col, send_col = st.columns([0.82, 0.08, 0.10])

        with prompt_col:

            prompt_text = st.text_input(
                "Ask a question about your PDF",
                placeholder="Ask a question about your PDF...",
                label_visibility="collapsed"
            )

        with voice_col:

            st.form_submit_button(
                "🎙️",
                disabled=True,
                help="Voice Assistant — Coming Soon",
                use_container_width=True
            )

        with send_col:

            submitted = st.form_submit_button(
                "➤",
                type="secondary",
                use_container_width=True
            )

        if submitted and prompt_text.strip():
            question = prompt_text.strip()

    if question:

        try:

            with st.spinner("StudyPod is finding information..."):

                results = search_similar_chunks(
                    question,
                    active_chat["vector_index"],
                    active_chat["chunks"],
                    top_k=5
                )

                if not results:

                    st.warning(
                        "No relevant passages were found in your document."
                    )

                else:

                    combined_chunks = (
                        results + active_chat["last_retrieved_chunks"]
                    )

                    unique_chunks = []
                    seen_chunks = set()

                    for chunk in combined_chunks:

                        chunk_key = (chunk["page"], chunk["text"])

                        if chunk_key not in seen_chunks:

                            seen_chunks.add(chunk_key)
                            unique_chunks.append(chunk)

                    unique_chunks = unique_chunks[:8]

                    answer = generate_answer(
                        question,
                        unique_chunks,
                        active_chat["chat_history"]
                    )

                    active_chat["chat_history"].append({
                        "role": "user",
                        "content": question
                    })

                    active_chat["chat_history"].append({
                        "role": "assistant",
                        "content": answer,
                        "sources": unique_chunks
                    })

                    active_chat["last_retrieved_chunks"] = results[:3]

                    if not active_chat.get("title_customized", False):
                        active_chat["title"] = question[:40]

                    persist_chat(active_chat_id)

                    st.rerun()

        except Exception as error:

            st.error(f"Unable to generate an answer: {error}")

else:

    if active_chat["pdf_name"]:
        st.info(
            "Re-upload the PDF associated with this conversation "
            "to continue asking questions."
        )
    else:
        st.info("Upload a PDF above to start a document-based conversation.")


# ---------------------------------
# PDF Summarization
# ---------------------------------

if active_chat["extracted_pages"] and active_chat["chunks"]:

    st.divider()

    st.markdown(
        '<div class="section-eyebrow">Study smarter</div>',
        unsafe_allow_html=True
    )

    st.header("📝 Document summary")

    st.write(
        "Create a concise overview of your uploaded study material "
        "to revise key ideas."
    )

    if st.button(
        "Generate Document Summary",
        key=f"generate_summary_{active_chat_id}"
    ):

        try:

            with st.spinner(
                "StudyPod is summarizing your document..."
            ):

                summary = generate_summary(active_chat["chunks"])

                active_chat["document_summary"] = summary

                persist_chat(active_chat_id)

            st.success("Summary generated successfully!")

        except Exception as error:

            st.error(f"Unable to generate summary: {error}")

    if active_chat["document_summary"]:

        st.subheader("📖 Your Study Summary")

        st.markdown(active_chat["document_summary"])

        st.download_button(
            label="Download Summary",
            data=active_chat["document_summary"],
            file_name="studypod_summary.md",
            mime="text/markdown",
            key=f"download_summary_{active_chat_id}"
        )

elif active_chat["document_summary"]:

    st.divider()
    st.header("📝 Saved document summary")
    st.markdown(active_chat["document_summary"])


# ---------------------------------
# Footer
# ---------------------------------

st.markdown(
    '<div class="soft-divider"></div>',
    unsafe_allow_html=True
)

st.caption("StudyPod · Your personal AI study companion")
