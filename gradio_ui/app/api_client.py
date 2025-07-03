import os

import requests

# Base URL for the FastAPI backend
DOC_INSIGHT_SERVICE_URL = os.getenv("DOC_INSIGHT_SERVICE_URL")


def upload_pdf(pdf_file, session_id=None):
    file = {"file": (pdf_file.name, pdf_file.read(), "application/pdf")}

    resp = requests.post(f"{DOC_INSIGHT_SERVICE_URL}/upload", files=file)
    resp.raise_for_status()
    result = resp.json()

    token = result["session_token"]
    session_id = result["session_id"]
    full_text = "\n\n".join(result["text"])

    return token, session_id, full_text


def ask_question(token, question):
    if not token:
        raise RuntimeError("No session token—call upload_pdf() first")

    headers = {"Authorization": f"Bearer {token}"}
    data = {"question": question}
    resp = requests.post(f"{DOC_INSIGHT_SERVICE_URL}/ask", headers=headers, data=data)
    resp.raise_for_status()
    result = resp.json()

    simple, rag = result["results"]

    return [
        simple["answer"],
        simple["score"],
        simple["entities"] or [{"status": "No entities found"}],
        rag["answer"],
        rag["score"],
        rag["entities"] or [{"status": "No entities found"}],
    ]
