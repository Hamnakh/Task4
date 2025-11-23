# import streamlit as st
# from pypdf import PdfReader
# import google.generativeai as genai
# import os
# from dotenv import load_dotenv

# load_dotenv()
# genai.configure(api_key=os.getenv("GEMINI_API_KEY") or st.secrets["GEMINI_API_KEY"])

# st.title("Study Notes Summarizer + Quiz Generator")

# uploaded_file = st.file_uploader("Apna PDF yahan daalo", type="pdf")

# if uploaded_file:
#     reader = PdfReader(uploaded_file)
#     text = ""
#     for page in reader.pages:
#         text += page.extract_text()

#     st.success("PDF padh liya!")

#     if st.button("Summary Banao"):
#         with st.spinner("Summary ban raha hai..."):
#             model = genai.GenerativeModel("gemini-1.5-flash")
#             prompt = f"""
#             Ye study notes hain. Inka ekdam clean, short aur samajhne wala summary banao.
#             Sirf important points, headings ke saath. Hindi/English mix mein bhi chalega.

#             Text: {text[:30000]}
#             """
#             response = model.generate_content(prompt)
#             st.subheader("Summary")
#             st.write(response.text)

#     if st.button("Quiz Banao (MCQs)"):
#         with st.spinner("Quiz ban raha hai..."):
#             model = genai.GenerativeModel("gemini-1.5-flash")
#             prompt = f"""
#             Is PDF se 8 achhe MCQs banao (4 options, 1 sahi jawab).
#             Har question ke baad sahi answer bhi bold mein likhna.

#             Text: {text[:30000]}
#             """
#             response = model.generate_content(prompt)
#             st.subheader("Quiz (MCQs)")
#             st.write(response.text)









from agents import Agent, Runner, function_tool, OpenAIChatCompletionsModel
import os 
import pypdf
from dotenv import load_dotenv
import streamlit as st
import asyncio
from openai import AsyncOpenAI

load_dotenv()

API = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-2.5-flash"

# --- Normal PDF text extraction for UI ---
def extract_pdf_text_normal(file_path: str) -> str:
    """
    Reads and extracts text from a PDF file for UI display.
    """
    text = ""
    with open(file_path, 'rb') as file:
        reader = pypdf.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

# --- Tool function for the Agent ---
@function_tool
def extract_pdf_text(file_path: str) -> str:
    """
    Reads and extracts text from a PDF file for the Agent.
    """
    return extract_pdf_text_normal(file_path)

# --- Agent Setup ---
@st.cache_resource
def get_agent():
    external_client = AsyncOpenAI(
    api_key=API,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    model = OpenAIChatCompletionsModel(
    model=MODEL,
    openai_client=external_client
    )
    agent = Agent(
        model=model,
        name="StudyNotesAssistant",
        instructions="You are a Study Notes Assistant. First produce a summary, then generate a quiz.",
        tools=[extract_pdf_text],
    )
    return agent

# --- Streamlit UI ---
def run_streamlit_app():
    st.title("📚 Study Notes & Quiz Generator")

    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

    if uploaded_file is not None:
        # Save uploaded PDF temporarily
        temp_dir = "temp_pdfs"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"PDF uploaded: {uploaded_file.name}")

        # Extract text for UI
        extracted_text = extract_pdf_text_normal(file_path)
        st.subheader("📄 Extracted Text:")
        st.text_area("PDF Content", extracted_text, height=300)

        # Initialize agent
        agent = get_agent()

        if agent and st.button("Generate Summary & Quiz"):
            st.info("Generating summary and quiz... This may take a moment.")
            
        async def run_agent_async():
           return await Runner.run(
            starting_agent=agent,
           input=f"Summarize this text and then create a quiz:\n\n{extracted_text}"
           )
        
        result = asyncio.run(run_agent_async())
        st.subheader("📝 Summary & Quiz:")
        st.write(result.final_output)

if __name__ == "__main__":
    run_streamlit_app()