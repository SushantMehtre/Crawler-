import streamlit as st
import os
import chromadb
from google import genai
from google.genai import types
from crawler import scrape_reddit
from vector_store import RedditVectorStore
from bs4 import BeautifulSoup

# Page configuration
st.set_page_config(
    page_title="Bimakavach Reddit",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Premium Aesthetics
st.markdown("""
<style>
    .reportview-container {
        background: #0f172a;
    }
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    div[data-testid="stSidebar"] {
        background-color: #1e293b;
        color: #f8fafc;
        border-right: 1px solid #334155;
    }
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #ef4444 0%, #f97316 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
    }
    /* Cards / Expander */
    div[data-testid="stExpander"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to get Gemini client
def get_gemini_client(api_key: str):
    os.environ["GEMINI_API_KEY"] = api_key
    return genai.Client(api_key=api_key)

# App Header
st.title("💬 Reddit RAG Chatbot")
st.markdown("Scrape posts and comments from any Reddit thread, store them in a local vector database, and chat using Gemini.")

# Initialize Session State for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar Config
st.sidebar.header("🛠️ Configuration")

# API Key
api_key = st.sidebar.text_input(
    "Google Gemini API Key",
    type="password",
    value=os.environ.get("GEMINI_API_KEY", ""),
    help="Provide your Google Gemini API Key. Get one from Google AI Studio."
)

# Vector Store Path
db_path = os.path.join(os.getcwd(), "chroma_db")
st.sidebar.text_input("Local Vector DB Path", value=db_path, disabled=True)

# Data Input Mode selection
input_mode = st.sidebar.radio("Choose Input Method:", ["Reddit URL", "Paste Text/HTML", "Upload File"])

# Model selection
available_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "gemini-2.0-pro"]
if api_key:
    try:
        temp_client = get_gemini_client(api_key)
        # Fetch models dynamically
        fetched = temp_client.models.list()
        cleaned_models = []
        for m in fetched:
            name = m.name.replace("models/", "")
            # Exclude deprecated gemini-2.5 models that Google API lists but doesn't allow new users to run
            is_deprecated = "gemini-2.5-flash" in name or "gemini-2.5-pro" in name
            if "gemini" in name and "embed" not in name and "vision" not in name and not is_deprecated:
                cleaned_models.append(name)
        if cleaned_models:
            # Place gemini-2.0-flash or gemini-flash-latest at the very top of the list
            cleaned_models.sort(key=lambda x: (
                "gemini-2.0-flash" != x,
                "gemini-flash-latest" != x,
                x
            ))
            available_models = cleaned_models
    except Exception as e:
        # Fallback to defaults on error (e.g. initial load or network issue)
        pass

model_name = st.sidebar.selectbox(
    "Gemini Model",
    available_models,
    index=0,
    help="Select the Gemini model to use for generating answers."
)

if input_mode == "Reddit URL":
    reddit_url = st.sidebar.text_input(
        "Reddit URL",
        placeholder="https://www.reddit.com/r/Python/comments/..."
    )
    if st.sidebar.button("🕸️ Scrape & Index"):
        if not api_key:
            st.error("Please enter a valid Google Gemini API Key first.")
        elif not reddit_url:
            st.error("Please enter a Reddit URL.")
        else:
            with st.spinner("Scraping Reddit and generating embeddings..."):
                try:
                    data = scrape_reddit(reddit_url)
                    st.sidebar.success(f"Scraped '{data['title']}' successfully! Found {len(data['texts'])} texts.")
                    
                    vector_store = RedditVectorStore(persist_directory=db_path, api_key=api_key)
                    vector_store.add_reddit_data(
                        title=data['title'],
                        texts=data['texts'],
                        source_url=data['url']
                    )
                    st.sidebar.success("Successfully chunked and indexed in ChromaDB!")
                except Exception as e:
                    st.sidebar.error(f"Error: {str(e)}")

elif input_mode == "Paste Text/HTML":
    doc_title = st.sidebar.text_input("Document Title", value="Pasted Content")
    pasted_text = st.sidebar.text_area("Paste Content Here", height=200, placeholder="Paste posts, comments, or raw HTML content...")
    if st.sidebar.button("📥 Index Pasted Content"):
        if not api_key:
            st.error("Please enter your API Key.")
        elif not pasted_text.strip():
            st.error("Please paste some content.")
        else:
            with st.spinner("Indexing pasted content..."):
                try:
                    # Clean simple tags if HTML
                    soup = BeautifulSoup(pasted_text, 'html.parser')
                    comment_divs = soup.find_all(class_=lambda x: x and 'comment_body' in x)
                    
                    texts = []
                    if comment_divs:
                        # It's Redlib/Reddit HTML
                        for i, div in enumerate(comment_divs, 1):
                            text = div.get_text("\n", strip=True)
                            if text:
                                texts.append(f"Comment {i}:\n{text}")
                    else:
                        # Split by lines/paragraphs or keep as a single block
                        texts = [pasted_text.strip()]

                    vector_store = RedditVectorStore(persist_directory=db_path, api_key=api_key)
                    vector_store.add_reddit_data(
                        title=doc_title,
                        texts=texts,
                        source_url="Pasted Source"
                    )
                    st.sidebar.success(f"Indexed {len(texts)} chunks successfully!")
                except Exception as e:
                    st.sidebar.error(f"Error: {str(e)}")

elif input_mode == "Upload File":
    uploaded_file = st.sidebar.file_uploader("Upload .txt or .html file", type=["txt", "html"])
    if uploaded_file is not None:
        if st.sidebar.button("📤 Index Uploaded File"):
            if not api_key:
                st.error("Please enter your API Key.")
            else:
                with st.spinner("Indexing file content..."):
                    try:
                        content = uploaded_file.read().decode("utf-8")
                        filename = uploaded_file.name
                        
                        texts = []
                        if filename.endswith(".html"):
                            soup = BeautifulSoup(content, 'html.parser')
                            comment_divs = soup.find_all(class_=lambda x: x and 'comment_body' in x)
                            if comment_divs:
                                for i, div in enumerate(comment_divs, 1):
                                    text = div.get_text("\n", strip=True)
                                    if text:
                                        texts.append(f"Comment {i}:\n{text}")
                            else:
                                texts = [soup.get_text("\n", strip=True)]
                        else:
                            texts = [content]

                        vector_store = RedditVectorStore(persist_directory=db_path, api_key=api_key)
                        vector_store.add_reddit_data(
                            title=filename,
                            texts=texts,
                            source_url=f"Uploaded File: {filename}"
                        )
                        st.sidebar.success(f"Indexed file successfully as {len(texts)} chunks!")
                    except Exception as e:
                        st.sidebar.error(f"Error: {str(e)}")

# Database Operations
st.sidebar.markdown("---")
st.sidebar.header("🧹 Database Management")

# Display currently stored documents
try:
    vector_store = RedditVectorStore(persist_directory=db_path)
    stored_docs = vector_store.get_stored_documents()
    if stored_docs:
        with st.sidebar.expander("📚 Stored Sources", expanded=True):
            st.markdown(f"Total Sources: **{len(stored_docs)}**")
            for title, url in stored_docs.items():
                if url.startswith("http"):
                    st.markdown(f"- [{title}]({url})")
                else:
                    st.markdown(f"- **{title}** ({url})")
    else:
        st.sidebar.info("Database is currently empty.")
except Exception as e:
    pass

if st.sidebar.button("Clear Vector DB"):
    if not api_key:
        st.error("Please enter your API Key to clear the DB (needed to instantiate store).")
    else:
        try:
            vector_store = RedditVectorStore(persist_directory=db_path, api_key=api_key)
            vector_store.clear_collection()
            st.sidebar.success("Database cleared successfully!")
        except Exception as e:
            st.sidebar.error(f"Error clearing DB: {str(e)}")

# Main Chat Interface
if not api_key:
    st.info("👈 Please enter your Gemini API Key in the sidebar to start.")
else:
    # Render chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("references"):
                with st.expander("📚 Sources & Context"):
                    for ref in msg["references"]:
                        st.markdown(f"**Source:** {ref['metadata'].get('title')} ([Link]({ref['metadata'].get('source_url')}))")
                        st.markdown(f"**Chunk Content:**\n```\n{ref['content']}\n```")
                        st.markdown(f"**Similarity Distance:** {ref['distance']:.4f}")
                        st.markdown("---")

    # Chat input
    if prompt := st.chat_input("Ask a question about the indexed Reddit posts..."):
        # Add user message to state
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)

        # Generate response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            with st.spinner("Searching knowledge base and generating answer..."):
                try:
                    # 1. Instantiate vector store and query it
                    vector_store = RedditVectorStore(persist_directory=db_path, api_key=api_key)
                    results = vector_store.query(prompt, n_results=5)
                    
                    if not results:
                        context = "No relevant context found in database. The database is empty or no posts have been indexed."
                    else:
                        context = "\n\n".join([f"[Source: {r['metadata'].get('title')}]\n{r['content']}" for r in results])
                    
                    # 2. Build system instruction / system context
                    system_prompt = (
                        "You are an AI assistant answering questions about Reddit threads and posts that the user has scraped.\n"
                        "Use the provided context to answer the user's question accurately.\n"
                        "If the context does not contain the answer, say so, but utilize any relevant background information to help.\n\n"
                        f"--- CONTEXT START ---\n{context}\n--- CONTEXT END ---"
                    )
                    
                    # 3. Call Gemini
                    client = get_gemini_client(api_key)
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            temperature=0.2
                        )
                    )
                    
                    answer = response.text
                    response_placeholder.write(answer)
                    
                    # Store message with references
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "references": results
                    })
                    
                    # Rerender to show expander source documents
                    st.rerun()
                    
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        st.error(
                            "⚠️ **Gemini API Rate Limit Exceeded (429)**\n\n"
                            "Your API key has exceeded the free tier quota for this specific model. "
                            "Please try the following:\n"
                            "1. **Switch the Gemini Model** in the sidebar to **`gemini-1.5-flash`** or **`gemini-1.5-pro`** (these have different quotas).\n"
                            "2. Wait a few seconds and try resending your message."
                        )
                    else:
                        st.error(f"Error generating answer: {error_msg}")
