import faiss
import numpy as np

import streamlit as st
from sentence_transformers import SentenceTransformer
from sentence_transformers import CrossEncoder


# Load the embedding model only once
@st.cache_resource
def load_embedding_model():

    model = SentenceTransformer(
        "all-MiniLM-L6-v2"
    )

    return model

# Load reranking model only once
@st.cache_resource
def load_reranker():

    reranker = CrossEncoder(
        "cross-encoder/ms-marco-MiniLM-L-6-v2"
    )

    return reranker


def build_vector_index(chunks):

    model = load_embedding_model()

    texts = [
        chunk["text"] for chunk in chunks
    ]

    # Generate embeddings in batches
    embeddings = model.encode(
        texts,
        batch_size=32,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    embeddings = np.asarray(
        embeddings,
        dtype="float32"
    )

    # Create FAISS index
    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    return index, chunks




def search_similar_chunks(
    question,
    index,
    chunks,
    top_k=5
):

    embedding_model = load_embedding_model()

    # Stage 1: Retrieve candidate passages using FAISS
    question_embedding = embedding_model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    question_embedding = np.asarray(
        question_embedding,
        dtype="float32"
    )

    candidate_k = min(top_k * 3, len(chunks))

    scores, indices = index.search(
        question_embedding,
        candidate_k
    )

    candidates = []

    for score, idx in zip(scores[0], indices[0]):

        if idx == -1:
            continue

        candidates.append({
            "text": chunks[idx]["text"],
            "page": chunks[idx]["page"],
            "faiss_score": float(score)
        })

    if not candidates:
        return []

    # Stage 2: Rerank candidates using CrossEncoder
    reranker = load_reranker()

    pairs = [
        (question, candidate["text"])
        for candidate in candidates
    ]

    rerank_scores = reranker.predict(
        pairs,
        batch_size=16,
        show_progress_bar=False
    )

    for candidate, rerank_score in zip(
        candidates,
        rerank_scores
    ):

        candidate["rerank_score"] = float(rerank_score)

    # Sort by reranking score
    candidates.sort(
        key=lambda item: item["rerank_score"],
        reverse=True
    )

    return candidates[:top_k]
