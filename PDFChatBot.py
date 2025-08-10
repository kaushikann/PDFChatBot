from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
import os
import streamlit as st
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
os.environ["PINECONE_API_KEY"] = st.secrets["PINECONE_API_KEY"]
from langchain.chains import RetrievalQA
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from pypdf import PdfReader
st.title("PDF Chat Bot")
st.header(":blue[PDF ChatBot]")
st.write("Upload a PDF file and chat with it")
uploaded_pdf=st.file_uploader(label="Upload a PDF", type="pdf", accept_multiple_files=False)
if uploaded_pdf is not None:
    pdf_reader=PdfReader(uploaded_pdf)
    text=""
    for page in pdf_reader.pages:
        text=text+page.extract_text()
        text=" ".join(text)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    doc=text_splitter.create_documents([text])
    chunks = text_splitter.split_documents(doc)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    index="pdfchatbot"
    vectorstore = PineconeVectorStore.from_documents(chunks, embeddings, index_name=index)
    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0)
    qa=RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=vectorstore.as_retriever())
    st.write("9")
    user_query=st.text_input("Enter your query")
    st.write("10")
    if st.button("Submit"):
        st.write(qa.invoke({"query": user_query}))
    else:
        st.write("Please upload a PDF file")
