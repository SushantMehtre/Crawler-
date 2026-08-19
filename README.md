# 🤖 Reddit RAG Chatbot

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Data%20Store-orange.svg)
![Gemini](https://img.shields.io/badge/Google%20Gemini-AI-green.svg)

**Reddit RAG Chatbot** is an interactive, Streamlit-based web application that allows you to scrape Reddit posts and comments, store them in a local vector database, and chat with them using Google's powerful Gemini LLM models.

This project implements Retrieval-Augmented Generation (RAG) to provide highly contextual, accurate answers based specifically on the Reddit threads you choose to index.

---

## ✨ Features

- **🌐 Live Reddit Scraping:** Directly scrape threads using Reddit URLs. We utilize public Redlib proxies to bypass standard scraping restrictions and ensure robust data retrieval.
- **📥 Alternative Inputs:** If scraping fails or you have specific text, you can index content by pasting raw Text/HTML or uploading `.txt` / `.html` files.
- **🗄️ Local Vector Storage:** Employs [ChromaDB](https://www.trychroma.com/) for fully local, persistent vector storage. Embeddings are generated locally using ONNX, ensuring your data stays private and avoiding API quota issues.
- **🧠 Advanced AI Chat:** Powered by Google's Gemini models (including `gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-2.0-flash`). Ask questions about the indexed content and receive intelligent, context-aware answers.
- **📚 Source Citations:** Every AI response includes a "Sources & Context" expander, allowing you to see exactly which parts of the Reddit thread the AI used to generate its answer, along with similarity scores.
- **🎨 Premium UI/UX:** A clean, dark-themed interface built with custom Streamlit styling for an optimal user experience.

---

## 🛠️ Architecture

1.  **Data Extraction (`crawler.py`):** Takes a Reddit URL, routes it through a randomized list of Redlib proxy instances, and extracts the post body, title, and all comments.
2.  **Vectorization & Storage (`vector_store.py`):** The extracted text is chunked and stored in a local ChromaDB collection. It uses ChromaDB's default `all-MiniLM-L6-v2` embedding model (running locally).
3.  **Chat Interface (`app.py`):** A Streamlit app that handles user configuration (API key, model selection), manages the indexing workflows, and provides the chat interface.
4.  **Generation:** When a user asks a question, the app queries ChromaDB for the most relevant text chunks. These chunks are appended as context to a prompt sent to the Gemini API, which formulates the final answer.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher.
- A Google Gemini API Key. You can get one for free at [Google AI Studio](https://aistudio.google.com/).

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/reddit-rag-chatbot.git
    cd reddit-rag-chatbot
    ```

2.  **Create a virtual environment (optional but recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the App

1.  Start the Streamlit application:
    ```bash
    streamlit run app.py
    ```
2.  Open your browser and navigate to `http://localhost:8501`.

---

## 📖 Usage Guide

1.  **Configure API Key:** Open the app and paste your Google Gemini API Key into the sidebar configuration panel.
2.  **Select Input Method:**
    *   **Reddit URL:** Paste a standard Reddit post URL. Click "Scrape & Index".
    *   **Paste Text/HTML:** Manually paste thread content.
    *   **Upload File:** Upload a saved text or HTML file.
3.  **Wait for Indexing:** The app will chunk and store the data in a local folder called `chroma_db`.
4.  **Chat!:** Use the chat input at the bottom of the main screen to ask questions. Example: *"What were the top complaints in this thread?"* or *"Summarize the author's main point."*
5.  **View Sources:** Click the "📚 Sources & Context" expander under the AI's response to verify where the information came from.
6.  **Manage Database:** You can clear the database from the sidebar if you want to start fresh with a different topic.

---

## ⚠️ Notes & Troubleshooting

-   **Rate Limits:** If you are using the free tier of the Gemini API, you may encounter `429 (Too Many Requests)` errors if you ask questions too quickly or exceed your daily quota. If this happens, try switching the selected model in the sidebar to a less resource-intensive one (like `gemini-1.5-flash`).
-   **Scraping Failures:** Reddit frequently updates its anti-scraping measures. If the "Reddit URL" method fails continuously, the included Redlib proxies might be temporarily down. Use the "Paste Text/HTML" fallback method by visiting the thread in your browser, copying the page content, and pasting it into the app.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
