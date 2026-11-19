
import json
import streamlit as st
import numpy as np

import csv
import io

from core.pdf_processor import extract_text_from_pdf
from core.text_chunker import create_chunks
from core.vector_store import (
    build_vector_index,
    load_embedding_model,
    load_reranker
)


st.set_page_config(
    page_title="StudyPod | Evaluation",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 StudyPod Retrieval Evaluation")

st.write(
    "Compare FAISS-only retrieval with "
    "FAISS + Cross-Encoder reranking."
)


# ---------------------------------
# Load Evaluation Questions
# ---------------------------------

try:

    with open(
        "evaluation_questions.json",
        "r",
        encoding="utf-8"
    ) as file:

        evaluation_questions = json.load(file)

except Exception as error:

    st.error(f"Unable to load evaluation questions: {error}")
    st.stop()


# ---------------------------------
# Upload PDF
# ---------------------------------

uploaded_file = st.file_uploader(
    "Upload your evaluation PDF",
    type=["pdf"]
)


if uploaded_file is not None:

    if st.button("Prepare Evaluation"):

        try:

            with st.spinner("Preparing document..."):

                pages = extract_text_from_pdf(uploaded_file)

                chunks = create_chunks(pages)

                if not chunks:
                    st.error("No readable text was extracted.")
                    st.stop()

                index, stored_chunks = build_vector_index(chunks)

                st.session_state.eval_index = index
                st.session_state.eval_chunks = stored_chunks

                # Clear previous evaluation results
                st.session_state.pop("eval_results", None)

            st.success(
                f"Document prepared with {len(chunks)} chunks."
            )

        except Exception as error:

            st.error(f"Preparation failed: {error}")


# ---------------------------------
# Evaluation Function
# ---------------------------------

def evaluate_retrieval(question, expected_pages, index, chunks):

    embedding_model = load_embedding_model()

    # ---------------------------------
    # Stage 1: FAISS Retrieval
    # ---------------------------------

    question_embedding = embedding_model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    question_embedding = np.asarray(
        question_embedding,
        dtype="float32"
    )

    # Retrieve up to 15 candidates
    candidate_k = min(15, len(chunks))

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

    # ---------------------------------
    # FAISS-only: Top 5
    # ---------------------------------

    faiss_results = candidates[:5]

    # ---------------------------------
    # Stage 2: Cross-Encoder Reranking
    # ---------------------------------

    reranked_results = []

    if candidates:

        reranker = load_reranker()

        pairs = [
            (question, candidate["text"])
            for candidate in candidates
        ]

        rerank_scores = reranker.predict(pairs)

        for candidate, rerank_score in zip(
            candidates,
            rerank_scores
        ):

            reranked_results.append({
                **candidate,
                "rerank_score": float(rerank_score)
            })

        reranked_results.sort(
            key=lambda item: item["rerank_score"],
            reverse=True
        )

    # Final top 5 after reranking
    reranked_results = reranked_results[:5]

    # ---------------------------------
    # Calculate Metrics
    # ---------------------------------

    def calculate_metrics(results):

        retrieved_pages = [
            result["page"] for result in results
        ]

        relevant_rank = None

        for rank, page in enumerate(
            retrieved_pages,
            start=1
        ):

            if page in expected_pages:
                relevant_rank = rank
                break

        hit = relevant_rank is not None

        reciprocal_rank = (
            1 / relevant_rank if relevant_rank else 0
        )

        return {
            "retrieved_pages": retrieved_pages,
            "hit": hit,
            "rank": relevant_rank,
            "reciprocal_rank": reciprocal_rank
        }

    return {
        "faiss": calculate_metrics(faiss_results),
        "reranked": calculate_metrics(reranked_results),
        "faiss_results": faiss_results,
        "reranked_results": reranked_results
    }


# ---------------------------------
# Run Evaluation
# ---------------------------------

if st.session_state.get("eval_index") is not None:

    st.divider()

    st.subheader("Evaluation Questions")

    for number, item in enumerate(
        evaluation_questions,
        start=1
    ):

        st.write(f"{number}. {item['question']}")

    if st.button("Run Evaluation", type="primary"):

        try:

            evaluated = []

            with st.spinner(
                "Evaluating retrieval performance..."
            ):

                for item in evaluation_questions:

                    expected_pages = item["expected_pages"]

                    if not expected_pages:
                        continue

                    results = evaluate_retrieval(
                        item["question"],
                        expected_pages,
                        st.session_state.eval_index,
                        st.session_state.eval_chunks
                    )

                    evaluated.append({
                        "question": item["question"],
                        "expected_pages": expected_pages,
                        **results
                    })

            if not evaluated:

                st.warning(
                    "No valid evaluation questions found. "
                    "Check expected_pages in evaluation_questions.json."
                )

            else:

                st.session_state.eval_results = evaluated

                st.success("Evaluation completed successfully!")

        except Exception as error:

            st.error(f"Evaluation failed: {error}")


# ---------------------------------
# Display Evaluation Results
# ---------------------------------

if st.session_state.get("eval_results"):

    evaluated = st.session_state.eval_results

    total = len(evaluated)

    # ---------------------------------
    # Aggregate Metrics
    # ---------------------------------

    faiss_hits = sum(
        result["faiss"]["hit"]
        for result in evaluated
    )

    reranked_hits = sum(
        result["reranked"]["hit"]
        for result in evaluated
    )

    faiss_mrr = sum(
        result["faiss"]["reciprocal_rank"]
        for result in evaluated
    ) / total

    reranked_mrr = sum(
        result["reranked"]["reciprocal_rank"]
        for result in evaluated
    ) / total

    faiss_hit_rate = faiss_hits / total

    reranked_hit_rate = reranked_hits / total

    # ---------------------------------
    # Results Comparison
    # ---------------------------------

    st.divider()

    st.header("📊 Evaluation Results")

    st.subheader("Overall Performance")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### FAISS-only")

        st.metric(
            "Hit Rate @ 5",
            f"{faiss_hit_rate * 100:.1f}%"
        )

        st.metric(
            "MRR @ 5",
            f"{faiss_mrr:.3f}"
        )

    with col2:

        st.markdown("### FAISS + Cross-Encoder")

        st.metric(
            "Hit Rate @ 5",
            f"{reranked_hit_rate * 100:.1f}%"
        )

        st.metric(
            "MRR @ 5",
            f"{reranked_mrr:.3f}"
        )

    st.write(f"**Questions evaluated:** {total}")

    # ---------------------------------
    # Metric Comparison Table
    # ---------------------------------

    st.subheader("Performance Comparison")

    comparison = {
        "Metric": [
            "Hit Rate @ 5",
            "MRR @ 5"
        ],
        "FAISS-only": [
            f"{faiss_hit_rate * 100:.1f}%",
            f"{faiss_mrr:.3f}"
        ],
        "FAISS + Cross-Encoder": [
            f"{reranked_hit_rate * 100:.1f}%",
            f"{reranked_mrr:.3f}"
        ]
    }

    st.table(comparison)


    # ---------------------------------
    # CSV Export
    # ---------------------------------

    st.subheader("📥 Export Evaluation Reports")

    # Create detailed question-wise CSV
    detailed_buffer = io.StringIO()

    detailed_columns = [
        "Question",
        "Expected Pages",
        "FAISS Retrieved Pages",
        "FAISS Hit",
        "FAISS First Relevant Rank",
        "FAISS Reciprocal Rank",
        "Reranked Retrieved Pages",
        "Reranked Hit",
        "Reranked First Relevant Rank",
        "Reranked Reciprocal Rank"
    ]

    writer = csv.DictWriter(
        detailed_buffer,
        fieldnames=detailed_columns
    )

    writer.writeheader()

    for result in evaluated:

        writer.writerow({
            "Question": result["question"],

            "Expected Pages": ", ".join(
                map(str, result["expected_pages"])
            ),

            "FAISS Retrieved Pages": ", ".join(
                map(str, result["faiss"]["retrieved_pages"])
            ),

            "FAISS Hit": result["faiss"]["hit"],

            "FAISS First Relevant Rank":
                result["faiss"]["rank"] or "Not found",

            "FAISS Reciprocal Rank":
                result["faiss"]["reciprocal_rank"],

            "Reranked Retrieved Pages": ", ".join(
                map(str, result["reranked"]["retrieved_pages"])
            ),

            "Reranked Hit": result["reranked"]["hit"],

            "Reranked First Relevant Rank":
                result["reranked"]["rank"] or "Not found",

            "Reranked Reciprocal Rank":
                result["reranked"]["reciprocal_rank"]
        })

    detailed_csv = detailed_buffer.getvalue()

    # Create overall summary CSV
    summary_buffer = io.StringIO()

    summary_writer = csv.writer(summary_buffer)

    summary_writer.writerow([
        "Approach",
        "Metric",
        "Value",
        "Questions Evaluated"
    ])

    summary_writer.writerow([
        "FAISS-only",
        "Hit Rate @ 5",
        f"{faiss_hit_rate * 100:.1f}%",
        total
    ])

    summary_writer.writerow([
        "FAISS-only",
        "MRR @ 5",
        f"{faiss_mrr:.3f}",
        total
    ])

    summary_writer.writerow([
        "FAISS + Cross-Encoder",
        "Hit Rate @ 5",
        f"{reranked_hit_rate * 100:.1f}%",
        total
    ])

    summary_writer.writerow([
        "FAISS + Cross-Encoder",
        "MRR @ 5",
        f"{reranked_mrr:.3f}",
        total
    ])

    summary_csv = summary_buffer.getvalue()

    # Download buttons
    col1, col2 = st.columns(2)

    with col1:

        st.download_button(
            label="⬇️ Download Detailed Results",
            data=detailed_csv,
            file_name="studypod_detailed_evaluation.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col2:

        st.download_button(
            label="⬇️ Download Summary Report",
            data=summary_csv,
            file_name="studypod_evaluation_summary.csv",
            mime="text/csv",
            use_container_width=True
        )


    # ---------------------------------
    # Question-wise Results
    # ---------------------------------

    st.subheader("Question-wise Results")

    for number, result in enumerate(
        evaluated,
        start=1
    ):

        with st.expander(
            f"{number}. {result['question']}"
        ):

            st.write(
                f"**Expected pages:** {result['expected_pages']}"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.markdown("#### FAISS-only")

                st.write(
                    f"Retrieved pages: "
                    f"{result['faiss']['retrieved_pages']}"
                )

                st.write(
                    f"Relevant page found: "
                    f"{'Yes' if result['faiss']['hit'] else 'No'}"
                )

                st.write(
                    f"First relevant rank: "
                    f"{result['faiss']['rank'] or 'Not found'}"
                )

            with col2:

                st.markdown("#### FAISS + Cross-Encoder")

                st.write(
                    f"Retrieved pages: "
                    f"{result['reranked']['retrieved_pages']}"
                )

                st.write(
                    f"Relevant page found: "
                    f"{'Yes' if result['reranked']['hit'] else 'No'}"
                )

                st.write(
                    f"First relevant rank: "
                    f"{result['reranked']['rank'] or 'Not found'}"
                )
