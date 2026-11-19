import fitz


def extract_text_from_pdf(pdf_file):
    """
    Extract text from an uploaded PDF file.

    Args:
        pdf_file: Uploaded PDF file from Streamlit.

    Returns:
        A list containing page numbers and extracted text.
    """

    pdf_bytes = pdf_file.getvalue()

    document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    extracted_pages = []

    for page_number, page in enumerate(document, start=1):

        text = page.get_text("text")

        extracted_pages.append({
            "page": page_number,
            "text": text
        })

    document.close()

    return extracted_pages