import openai
import streamlit as st
import fitz  # PyMuPDF
from fpdf import FPDF  # Library to create PDF files

openai.api_key = "sk-proj-2v4srjCAqtK7ZkqPirklT3BlbkFJTqIgpcDwHPitTCYOf05b"

# Access the API key from Streamlit secrets
api_key = st.secrets["openai"]["api_key"]

if not api_key:
    st.error("No API key found. Please add your OpenAI API key to the Streamlit secrets.")
else:
    # Configure the OpenAI API client
    openai.api_key = api_key

# Initialize session state variables
if "start_chat" not in st.session_state:
    st.session_state.start_chat = False
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []

st.set_page_config(page_title="PDFSUMMARIZER", page_icon=":speech_balloon:")

def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def generate_quiz_questions(pdf_text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Generate a quiz with multiple choice questions based on the following text."},
            {"role": "user", "content": pdf_text}
        ]
    )
    return response['choices'][0]['message']['content']

def create_quiz_pdf(quiz_questions):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for question in quiz_questions:
        pdf.multi_cell(0, 10, question)

    return pdf

st.sidebar.title("PDFSUMMARIZER")
st.sidebar.write("Hi, I'm Psum!")

if st.sidebar.button("Upload File"):
    st.session_state.start_chat = True
    st.session_state.messages = []  # Reset messages when chat starts
    st.session_state.thread_id = None  # Reset thread_id

if st.sidebar.button("Exit Chat"):
    st.session_state.messages = []
    st.session_state.start_chat = False
    st.session_state.thread_id = None

if st.session_state.start_chat:
    st.title("PDF Summarizer Chatbot")

    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
    if uploaded_file is not None:
        with st.spinner("Extracting text from PDF..."):
            pdf_text = extract_text_from_pdf(uploaded_file)
            st.success("Text extracted successfully!")
            st.session_state.messages.append({"role": "user", "content": pdf_text})
            with st.expander("Extracted Text"):
                st.write(pdf_text)

            # Summarize the extracted text using OpenAI API
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Summarize the following PDF text."},
                        {"role": "user", "content": pdf_text}
                    ]
                )
                summary = response['choices'][0]['message']['content']
                st.session_state.messages.append({"role": "assistant", "content": summary})
                with st.chat_message("assistant"):
                    st.markdown(summary)
            except openai.error.OpenAIError as e:
                st.error(f"An error occurred: {e}")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question or request a summary!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an assistant that helps with summarizing PDFs and answering questions based on their content."},
                    {"role": "user", "content": prompt}
                ]
            )
            assistant_response = response['choices'][0]['message']['content']
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            with st.chat_message("assistant"):
                st.markdown(assistant_response)
        except openai.error.OpenAIError as e:
            st.error(f"An error occurred: {e}")

    # Button to generate quiz questions
    if st.button("Generate Quiz"):
        if uploaded_file is not None:
            with st.spinner("Generating quiz questions..."):
                try:
                    quiz_content = generate_quiz_questions(pdf_text)
                    st.session_state.quiz_questions = quiz_content.split('\n')
                    st.success("Quiz questions generated successfully!")
                    with st.expander("Quiz Questions"):
                        st.write(quiz_content)
                except openai.error.OpenAIError as e:
                    st.error(f"An error occurred: {e}")
        else:
            st.error("Please upload a PDF file first.")

    # Button to create and download quiz PDF
    if st.session_state.quiz_questions:
        if st.button("Download Quiz as PDF"):
            pdf = create_quiz_pdf(st.session_state.quiz_questions)
            pdf_output = pdf.output(dest='S').encode('latin1')
            st.download_button(
                label="Download Quiz PDF",
                data=pdf_output,
                file_name="quiz.pdf",
                mime="application/pdf"
            )
else:
    st.write("Click 'Upload File' to begin")
