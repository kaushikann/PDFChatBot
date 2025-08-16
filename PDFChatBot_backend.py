from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone
import os
import streamlit as st
from langchain.chains import ConversationalRetrievalChain
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from pypdf import PdfReader
from langchain.memory import ConversationBufferMemory

# Set environment variables
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
os.environ["PINECONE_API_KEY"] = st.secrets["PINECONE_API_KEY"]

class PDFChatBotBackend:
    def __init__(self):
        self.vectorstore = None
        self.qa_chain = None
        self.memory = None
        self.is_initialized = False
    
    def initialize_memory(self):
        """Initialize conversation memory"""
        if "memory" not in st.session_state:
            st.session_state["memory"] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )
        self.memory = st.session_state["memory"]
    
    def process_pdf(self, uploaded_pdf):
        """Process uploaded PDF and create vector store"""
        if uploaded_pdf is None:
            return False
            
        try:
            # Extract text from PDF
            pdf_reader = PdfReader(uploaded_pdf)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            # Clean and split text
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_text(text)
            
            # Convert text chunks to Document objects
            from langchain.schema import Document
            documents = [Document(page_content=chunk) for chunk in chunks]
            
            # Create embeddings and vector store
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            index = "pdfchatbot"
            self.vectorstore = PineconeVectorStore.from_documents(documents, embeddings, index_name=index)
            
            # Initialize LLM and QA chain
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=self.vectorstore.as_retriever(),
                memory=self.memory,
                return_source_documents=True,
                output_key="answer"
            )
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            return False
    
    def get_response(self, query):
        """Get response from the QA chain"""
        if not self.is_initialized or self.qa_chain is None:
            return "Please upload a PDF file first."
        
        try:
            result = self.qa_chain.invoke({"question": query})
            return result["answer"]
        except Exception as e:
            return f"Error getting response: {str(e)}"
    
    def is_ready(self):
        """Check if the backend is ready to process queries"""
        return self.is_initialized and self.qa_chain is not None

