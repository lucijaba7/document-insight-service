import os

import gradio as gr
from api_client import ask_question, upload_pdf


def upload_and_extract(pdf_path: str):
    if not pdf_path:
        raise gr.Error("Please upload a PDF file before clicking **Extract Text**.")

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    class FakeFile:
        name = os.path.basename(pdf_path)

        def read(self):
            return file_bytes

    token, session_id, full_text = upload_pdf(FakeFile())

    return token, session_id, full_text


def send_question(token, question):
    if not token:
        raise gr.Error("No document session found. Please extract text first.")
    if not question or not question.strip():
        raise gr.Error("Please type a question before clicking **Ask**.")
    results = ask_question(token, question)

    return results


with gr.Blocks() as demo:
    token_state = gr.State()

    gr.Markdown("## AI-driven Document Insight")

    with gr.Row(equal_height=True):
        pdf_input = gr.File(label="Upload a PDF", file_types=[".pdf"], type="filepath")
        with gr.Column():
            session_txt = gr.Textbox(label="Session ID", interactive=False)
            extracted_txt = gr.Textbox(
                label="Extracted Text",
                lines=10,
                interactive=False,
                placeholder="The raw text from your PDF will appear here…",
            )
    extract_btn = gr.Button("Extract Text")

    gr.Markdown("---")
    question_txt = gr.Textbox(label="Your Question About the Document")
    ask_btn = gr.Button("Ask")

    with gr.Row(equal_height=True):
        with gr.Column():
            gr.Markdown("### Full-Context QA (DistilBERT-SQuAD)")
            answer1 = gr.Textbox(
                label="Answer",
                lines=3,
                interactive=False,
                placeholder="Answer…",
            )
            score1 = gr.Textbox(label="Confidence", interactive=False)
            entities1 = gr.JSON(label="Named Entities")

        with gr.Column():
            gr.Markdown("### RAG-Augmented QA (MiniLM + DistilBERT-SQuAD)")
            answer2 = gr.Textbox(
                label="Answer",
                lines=3,
                interactive=False,
                placeholder="Answer…",
            )
            score2 = gr.Textbox(label="Confidence", interactive=False)
            entities2 = gr.JSON(label="Named Entities")

    extract_btn.click(
        fn=upload_and_extract,
        inputs=[pdf_input],
        outputs=[token_state, session_txt, extracted_txt],
    )
    ask_btn.click(
        fn=send_question,
        inputs=[token_state, question_txt],
        outputs=[answer1, score1, entities1, answer2, score2, entities2],
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
