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

# Initialize input key for clearing text input
if "input_key" not in st.session_state:
    st.session_state["input_key"] = 0

# UI Components
st.title(":blue[PDF Chat Bot]")
st.write("Upload a PDF file and chat with it. Please note that we will not store any of your data after you close the browser.")

# PDF Upload Section
uploaded_pdf = st.file_uploader(label="Upload a PDF", type="pdf", accept_multiple_files=False, label_visibility="hidden")

# Process PDF only when uploaded (not on every rerun)
if uploaded_pdf is not None and not backend.is_ready():
    with st.spinner("Processing the PDF, Please wait, this may take a while..."):
        success = backend.process_pdf(uploaded_pdf)
        if success:
            st.success("PDF processed successfully! You can now chat with it.")
        else:
            st.error("Failed to process PDF. Please try again.")


# Create a chat container with border
chat_container = st.container()

# Chat input area
input_container = st.container()

with chat_container:
    # Add border around the entire chat area
    st.markdown("""
        <div style="
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            background-color: #fafafa;
            margin: 10px 0;
        ">
    """, unsafe_allow_html=True)
    
    # Display chat history in a scrollable area
    chat_messages = st.container()
    
    with chat_messages:
        for i, (user, bot) in enumerate(st.session_state["chat_history"]):
            # User message (right-aligned, blue)
            st.markdown(
                f"""
                <div style="
                    background-color: #e3f2fd; 
                    padding: 15px; 
                    border-radius: 15px; 
                    margin: 10px 0; 
                    text-align: right;
                    border: 1px solid #2196f3;
                    margin-left: 20%;
                    margin-right: 0;
                ">
                    <strong>You:</strong> {user}
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            # Bot message (left-aligned, green)
            st.markdown(
                f"""
                <div style="
                    background-color: #e8f5e8; 
                    padding: 15px; 
                    border-radius: 15px; 
                    margin: 10px 0; 
                    text-align: left;
                    border: 1px solid #4caf50;
                    margin-right: 20%;
                    margin-left: 0;
                ">
                    <strong>Bot:</strong> {bot}
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    # Close the border div
    st.markdown("</div>", unsafe_allow_html=True)

with input_container:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        # Chat input with better styling
        user_query = st.text_input(
            "💬 Type your message here...", 
            key=f"user_input_{st.session_state['input_key']}", 
            placeholder="Ask a question about the PDF...",
            label_visibility="collapsed"
        )
        
        # Send button with better styling
        if st.button("🚀 Send", key="send_button", use_container_width=True) and user_query:
            if backend.is_ready():
                with st.spinner("🤔 Thinking..."):
                    bot_response = backend.get_response(user_query)
                st.session_state["chat_history"].append((user_query, bot_response))
                # Increment the input key to force Streamlit to clear the input field
                st.session_state["input_key"] += 1
                # Rerun to show the new message and clear input
                st.rerun()
            else:
                st.warning("⚠️ Please upload and process a PDF file first.")

# Display status
if not backend.is_ready():
    st.info("Upload a PDF file to start chatting!")
