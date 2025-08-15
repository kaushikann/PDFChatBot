import streamlit as st
from PDFChatBot_backend import PDFChatBotBackend

# Initialize the backend
if "backend" not in st.session_state:
    st.session_state["backend"] = PDFChatBotBackend()

backend = st.session_state["backend"]

# Initialize memory
backend.initialize_memory()

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# UI Components
st.title("PDF Chat Bot")
st.header(":blue[PDF ChatBot]")
st.write("Upload a PDF file and chat with it")

# PDF Upload Section
uploaded_pdf = st.file_uploader(label="Upload a PDF", type="pdf", accept_multiple_files=False)

# Process PDF only when uploaded (not on every rerun)
if uploaded_pdf is not None and not backend.is_ready():
    with st.spinner("Processing the PDF, Please wait, this may take a while..."):
        success = backend.process_pdf(uploaded_pdf)
        if success:
            st.success("PDF processed successfully! You can now chat with it.")
        else:
            st.error("Failed to process PDF. Please try again.")

# Chat Interface
st.subheader("Chat with your PDF")

# Display chat history
for i, (user, bot) in enumerate(st.session_state["chat_history"]):
    st.markdown(f"**You:** {user}")
    st.markdown(f"**Bot:** {bot}")

# Chat input
user_query = st.text_input("Type your message", key="user_input", placeholder="Ask a question about the PDF...")

# Send button
if st.button("Send", key="send_button") and user_query:
    if backend.is_ready():
        bot_response = backend.get_response(user_query)
        st.session_state["chat_history"].append((user_query, bot_response))
        # Rerun to show the new message
        st.rerun()
    else:
        st.warning("Please upload and process a PDF file first.")

# Display status
if not backend.is_ready():
    st.info("Upload a PDF file to start chatting!")
