"""
Retrieval-Augmented Generation (RAG) engine for question-answering.
Uses a LangChain document pipeline (loading + chunking financial news articles),
local sentence-transformers embeddings (via HuggingFaceEmbeddings), and a FAISS
vector store for semantic similarity search. Conversation history is tracked
with LangChain's ConversationBufferMemory so multi-turn chats retain context.
"""

from typing import List, Dict, Any
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_classic.memory import ConversationBufferMemory

import config
from logger import get_logger
from exceptions import VectorStoreError, APIError
from database import DatabaseManager

logger = get_logger("rag_engine")


class RAGQueryEngine:
    """RAG-based question answering system for financial news using FAISS semantic search."""

    def __init__(self, db_manager: DatabaseManager = None, api_key: str = None):
        """
        Initialize RAG query engine.

        Args:
            db_manager: Database manager instance
            api_key: OpenAI-compatible API key (uses config if not provided)
        """
        self.db_manager = db_manager or DatabaseManager()
        self.api_key = api_key or config.OPENAI_API_KEY

        # Local embeddings model - no external embeddings API required
        logger.info(f"Loading local embedding model: {config.EMBEDDING_MODEL_NAME}")
        self.embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)

        # Initialize LLM for chat
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            logger.warning("OpenAI API key not configured. Chat will not work.")
            self.llm = None
        else:
            self.llm = ChatOpenAI(
                model=config.OPENAI_MODEL,
                temperature=config.LLM_TEMPERATURE,
                openai_api_key=self.api_key,
                openai_api_base=config.OPENAI_BASE_URL
            )

        self.vector_store = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )

        self.vector_store_path = config.VECTOR_STORE_PATH

        logger.info("Initialized RAG Query Engine with FAISS retrieval")

    def _check_components(self):
        """Check if required components are initialized."""
        if self.llm is None:
            raise APIError("LLM not initialized. Please configure OPENAI_API_KEY.")

    def _create_documents(self, articles: List[Dict[str, Any]]) -> List[Document]:
        """
        Create LangChain documents from articles.

        Args:
            articles: List of article dictionaries

        Returns:
            List of Document objects
        """
        documents = []

        for article in articles:
            # Get summary if available
            summary_data = None
            if article.get('id'):
                summary_data = self.db_manager.get_summary(article['id'])

            # Combine title, summary, and content
            content_parts = [f"Title: {article.get('title', '')}"]

            if summary_data and summary_data.get('summary'):
                content_parts.append(f"Summary: {summary_data['summary']}")
            elif article.get('summary'):
                content_parts.append(f"Summary: {article['summary']}")

            if article.get('content'):
                content_parts.append(f"Content: {article['content']}")

            content = "\n\n".join(content_parts)

            # Create metadata
            metadata = {
                'ticker': article.get('ticker', ''),
                'source': article.get('source', ''),
                'url': article.get('url', ''),
                'title': article.get('title', ''),
                'published_date': article.get('published_date', ''),
                'sentiment': summary_data.get('sentiment', 'neutral') if summary_data else 'neutral'
            }

            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)

        logger.debug(f"Created {len(documents)} documents from articles")
        return documents

    def _split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks for embedding.

        Args:
            documents: List of documents

        Returns:
            List of document chunks
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.EMBEDDING_CHUNK_SIZE,
            chunk_overlap=config.EMBEDDING_CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        chunks = text_splitter.split_documents(documents)
        logger.debug(f"Split {len(documents)} documents into {len(chunks)} chunks")
        return chunks

    def build_vector_store(self, articles: List[Dict[str, Any]] = None,
                          days: int = 7, force_rebuild: bool = False):
        """
        Build or load FAISS vector store from articles.

        Args:
            articles: List of articles (if None, loads from database)
            days: Number of days to look back if loading from database
            force_rebuild: Force rebuild even if vector store exists
        """
        self._check_components()

        # Try to load existing index
        if not force_rebuild and self._load_vector_store():
            logger.info("Loaded existing FAISS index")
            return

        # Get articles if not provided
        if articles is None:
            articles = self.db_manager.get_recent_articles(days=days)

        if not articles:
            logger.warning("No articles available to build index")
            return

        logger.info(f"Building FAISS index from {len(articles)} articles")

        try:
            # Create and split documents
            documents = self._create_documents(articles)
            chunks = self._split_documents(documents)

            if not chunks:
                logger.warning("No document chunks created")
                return

            # Build the FAISS vector store from chunks using local embeddings
            self.vector_store = FAISS.from_documents(chunks, self.embeddings)

            # Save to disk
            self._save_vector_store()

            logger.info(f"FAISS index built with {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"Failed to build FAISS index: {e}")
            raise VectorStoreError(f"Failed to build FAISS index: {e}")

    def _save_vector_store(self):
        """Save FAISS index to disk."""
        try:
            self.vector_store_path.mkdir(parents=True, exist_ok=True)
            self.vector_store.save_local(str(self.vector_store_path))
            logger.info(f"FAISS index saved to {self.vector_store_path}")
        except (OSError, RuntimeError, ValueError) as e:
            logger.error(f"Failed to save FAISS index: {e}")

    def _load_vector_store(self) -> bool:
        """
        Load FAISS index from disk.

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            index_file = self.vector_store_path / "index.faiss"
            if not index_file.exists():
                return False

            self.vector_store = FAISS.load_local(
                str(self.vector_store_path),
                self.embeddings,
                allow_dangerous_deserialization=True
            )

            logger.info("FAISS index loaded from disk")
            return True

        except (OSError, RuntimeError, ValueError) as e:
            logger.warning(f"Failed to load FAISS index: {e}")
            return False

    def _retrieve_relevant_docs(self, query: str, k: int = 5) -> List[Document]:
        """
        Retrieve relevant documents using FAISS similarity search.

        Args:
            query: Search query
            k: Number of documents to retrieve

        Returns:
            List of relevant documents
        """
        if self.vector_store is None:
            return []

        return self.vector_store.similarity_search(query, k=k)

    def query(self, question: str, use_conversation: bool = True,
              use_cache: bool = True) -> Dict[str, Any]:
        """
        Query the RAG system using FAISS retrieval.

        Args:
            question: User question
            use_conversation: Whether to use conversation history
            use_cache: Whether to check cache first

        Returns:
            Dictionary with answer and source documents
        """
        self._check_components()

        if self.vector_store is None:
            raise VectorStoreError("FAISS index not initialized. Call build_vector_store() first.")

        # Check cache
        if use_cache:
            cached = self.db_manager.get_cached_query(question)
            if cached:
                logger.debug(f"Using cached query result for: {question[:50]}")
                return {
                    'answer': cached['response'],
                    'sources': cached.get('sources', ''),
                    'from_cache': True
                }

        try:
            # Retrieve relevant documents
            source_docs = self._retrieve_relevant_docs(question, k=config.RAG_TOP_K)

            if not source_docs:
                answer = "I don't have enough information to answer that question based on the available articles."
                sources = "No relevant sources found"
            else:
                # Build context from retrieved documents
                context = "\n\n".join([
                    f"Article: {doc.metadata.get('title', 'Unknown')}\n{doc.page_content}"
                    for doc in source_docs[:3]  # Use top 3 docs
                ])

                # Build conversation history from memory, if requested
                history_text = ""
                if use_conversation:
                    history_messages = self.memory.chat_memory.messages
                    if history_messages:
                        history_lines = []
                        for msg in history_messages:
                            role = "User" if msg.type == "human" else "Assistant"
                            history_lines.append(f"{role}: {msg.content}")
                        history_text = "\n\nPrevious conversation:\n" + "\n".join(history_lines)

                # Create prompt
                prompt = f"""{config.RAG_SYSTEM_PROMPT}

Context from recent financial news:
{context}
{history_text}

Question: {question}

Answer:"""

                # Call LLM
                response_msg = self.llm.invoke(prompt)
                answer = response_msg.content if hasattr(response_msg, 'content') else str(response_msg)

                # Format sources
                sources = self._format_sources(source_docs)

                # Persist this turn to conversation memory
                if use_conversation:
                    self.memory.save_context({"question": question}, {"answer": answer})

            response = {
                'answer': answer,
                'sources': sources,
                'source_documents': source_docs,
                'from_cache': False
            }

            # Cache the result
            self.db_manager.cache_query(question, answer, sources)

            logger.info(f"Query processed: {question[:50]}...")
            return response

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise APIError(f"Failed to process query: {e}")

    def _format_sources(self, source_docs: List[Document]) -> str:
        """Format source documents for display."""
        if not source_docs:
            return "No sources available"

        sources = []
        seen_urls = set()

        for doc in source_docs:
            url = doc.metadata.get('url', '')
            title = doc.metadata.get('title', 'Unknown')
            ticker = doc.metadata.get('ticker', '')

            # Avoid duplicates
            if url and url not in seen_urls:
                seen_urls.add(url)
                source_line = f"- [{ticker}] {title}"
                if url:
                    source_line += f" ({url})"
                sources.append(source_line)

        return "\n".join(sources[:5])  # Limit to top 5 sources

    def clear_conversation_history(self):
        """Clear conversation history."""
        self.memory.clear()
        logger.debug("Conversation history cleared")

    def get_relevant_articles(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Get relevant articles for a query without generating an answer.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of relevant article metadata
        """
        if self.vector_store is None:
            raise VectorStoreError("FAISS index not initialized")

        try:
            # Retrieve relevant documents
            docs = self._retrieve_relevant_docs(query, k=k)

            # Extract metadata
            results = []
            for doc in docs:
                results.append({
                    'title': doc.metadata.get('title', ''),
                    'ticker': doc.metadata.get('ticker', ''),
                    'url': doc.metadata.get('url', ''),
                    'source': doc.metadata.get('source', ''),
                    'sentiment': doc.metadata.get('sentiment', ''),
                    'content_preview': doc.page_content[:200] + "..."
                })

            return results

        except (RuntimeError, ValueError) as e:
            logger.error(f"Failed to get relevant articles: {e}")
            return []
