from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
import pinecone
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

# Initialize Pinecone using the new class-based approach
pc = pinecone.Pinecone(api_key=os.environ["PINECONE_API_KEY"])

class PDFChatBotBackend:
    def __init__(self):
        self.vectorstore = None
        self.qa_chain = None
        self.memory = None
        self.is_initialized = False
        self.clear_pinecone_namespace()
    
    def clear_pinecone_namespace(self):
        """Clear all vectors from the Pinecone index namespace"""
        try:
            index_name = "pdfchatbot"
            
            # Check if index exists
            if index_name in pc.list_indexes().names():
                # Get the index
                index = pc.Index(index_name)
                
                # Get current stats to see how many vectors exist
                stats = index.describe_index_stats()
                total_vectors = stats.total_vector_count
                
                if total_vectors > 0:
                    # Delete all vectors using the delete method
                    index.delete(delete_all=True)
            else:
                print(f"Index {index_name} does not exist yet")
                
        except Exception as e:
            print(f"Error clearing Pinecone namespace: {str(e)}")
    
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
            
            # Use PineconeVectorStore with the new Pinecone SDK
            self.vectorstore = PineconeVectorStore.from_documents(
                documents, 
                embeddings, 
                index_name=index
            )
            
            # Initialize LLM and QA chain
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
            
            # Add system instructions to guide the bot's behavior
            system_instructions = """You are a helpful PDF analysis assistant. Your role is to:

1. **Answer questions accurately** based on the PDF content provided
2. **Be concise and clear** in your responses
3. **Cite specific information** from the PDF when possible
4. **Stay on topic** and only answer questions related to the PDF content. If you don't know the answer reply "I don't know. Ask me something from the PDF."
5. **Be professional and helpful** in your tone
6. **Format responses** in a readable way with proper spacing and structure
7. **Ask for clarification** if a question is unclear

Remember: Only use information from the uploaded PDF to answer questions."""
            
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=self.vectorstore.as_retriever(),
                memory=self.memory,
                return_source_documents=True,
                output_key="answer",
                system_message=system_instructions
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
