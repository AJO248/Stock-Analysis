"""
Retrieval-Augmented Generation (RAG) engine for question-answering.
Uses LangChain with FAISS vector store and OpenAI embeddings.
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import pickle

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_classic.chains import ConversationalRetrievalChain, RetrievalQA
from langchain_classic.memory import ConversationBufferMemory

import config
from logger import get_logger
from exceptions import VectorStoreError, APIError
from database import DatabaseManager

logger = get_logger("rag_engine")


class RAGQueryEngine:
    """RAG-based question answering system for financial news."""
    
    def __init__(self, db_manager: DatabaseManager = None, api_key: str = None):
        """
        Initialize RAG query engine.
        
        Args:
            db_manager: Database manager instance
            api_key: OpenAI API key (uses config if not provided)
        """
        self.db_manager = db_manager or DatabaseManager()
        self.api_key = api_key or config.OPENAI_API_KEY
        
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            logger.warning("OpenAI API key not configured. RAG system will not work.")
            self.embeddings = None
            self.llm = None
        else:
            # Initialize embeddings
            self.embeddings = OpenAIEmbeddings(
                model=config.OPENAI_EMBEDDING_MODEL,
                openai_api_key=self.api_key,
                openai_api_base=config.OPENAI_BASE_URL
            )
            
            # Initialize LLM
            self.llm = ChatOpenAI(
                model=config.OPENAI_MODEL,
                temperature=config.LLM_TEMPERATURE,
                openai_api_key=self.api_key,
                openai_api_base=config.OPENAI_BASE_URL
            )
        
        self.vector_store = None
        self.qa_chain = None
        self.conversation_chain = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        self.vector_store_path = config.VECTOR_STORE_PATH
        
        logger.info("Initialized RAG Query Engine")
    
    def _check_components(self):
        """Check if required components are initialized."""
        if self.embeddings is None or self.llm is None:
            raise APIError("OpenAI components not initialized. Please configure OPENAI_API_KEY.")
    
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
        Build or load vector store from articles.
        
        Args:
            articles: List of articles (if None, loads from database)
            days: Number of days to look back if loading from database
            force_rebuild: Force rebuild even if vector store exists
        """
        self._check_components()
        
        # Try to load existing vector store
        if not force_rebuild and self._load_vector_store():
            logger.info("Loaded existing vector store")
            return
        
        # Get articles if not provided
        if articles is None:
            articles = self.db_manager.get_recent_articles(days=days)
        
        if not articles:
            logger.warning("No articles available to build vector store")
            return
        
        logger.info(f"Building vector store from {len(articles)} articles")
        
        try:
            # Create and split documents
            documents = self._create_documents(articles)
            chunks = self._split_documents(documents)
            
            if not chunks:
                logger.warning("No document chunks created")
                return
            
            # Create vector store
            self.vector_store = FAISS.from_documents(
                documents=chunks,
                embedding=self.embeddings
            )
            
            # Save vector store
            self._save_vector_store()
            
            # Initialize chains
            self._initialize_chains()
            
            logger.info(f"Vector store built with {len(chunks)} chunks")
        
        except Exception as e:
            logger.error(f"Failed to build vector store: {e}")
            raise VectorStoreError(f"Failed to build vector store: {e}")
    
    def _save_vector_store(self):
        """Save vector store to disk."""
        try:
            self.vector_store_path.mkdir(parents=True, exist_ok=True)
            
            # Save FAISS index
            self.vector_store.save_local(str(self.vector_store_path))
            
            logger.info(f"Vector store saved to {self.vector_store_path}")
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")
    
    def _load_vector_store(self) -> bool:
        """
        Load vector store from disk.
        
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
                allow_dangerous_deserialization=True  # We trust our own saved data
            )
            
            self._initialize_chains()
            
            logger.info("Vector store loaded from disk")
            return True
        
        except Exception as e:
            logger.warning(f"Failed to load vector store: {e}")
            return False
    
    def _initialize_chains(self):
        """Initialize QA and conversation chains."""
        if self.vector_store is None:
            logger.warning("Vector store not available, cannot initialize chains")
            return
        
        # Create retriever
        retriever = self.vector_store.as_retriever(
            search_kwargs={"k": config.RAG_TOP_K}
        )
        
        # Create custom prompt
        prompt_template = f"""{config.RAG_SYSTEM_PROMPT}

Context: {{context}}

Question: {{question}}

Answer:"""
        
        QA_PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Initialize RetrievalQA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type=config.RAG_CHAIN_TYPE,
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": QA_PROMPT}
        )
        
        # Initialize Conversational chain for multi-turn conversations
        self.conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=self.memory,
            return_source_documents=True,
            verbose=False
        )
        
        logger.debug("QA chains initialized")
    
    def query(self, question: str, use_conversation: bool = True, 
              use_cache: bool = True) -> Dict[str, Any]:
        """
        Query the RAG system.
        
        Args:
            question: User question
            use_conversation: Whether to use conversation history
            use_cache: Whether to check cache first
        
        Returns:
            Dictionary with answer and source documents
        """
        self._check_components()
        
        if self.vector_store is None:
            raise VectorStoreError("Vector store not initialized. Call build_vector_store() first.")
        
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
            # Choose chain based on conversation flag
            if use_conversation and self.conversation_chain:
                result = self.conversation_chain({"question": question})
            else:
                result = self.qa_chain({"query": question})
            
            # Extract answer and sources
            answer = result.get('answer', result.get('result', ''))
            source_docs = result.get('source_documents', [])
            
            # Format sources
            sources = self._format_sources(source_docs)
            
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
            raise VectorStoreError("Vector store not initialized")
        
        try:
            # Perform similarity search
            docs = self.vector_store.similarity_search(query, k=k)
            
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
        
        except Exception as e:
            logger.error(f"Failed to get relevant articles: {e}")
            return []
