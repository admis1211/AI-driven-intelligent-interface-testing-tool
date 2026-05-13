from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain.document_loaders import UnstructuredPowerPointLoader as PPTXLoader
from langchain.embeddings.base import Embeddings
from app.core.config import settings
import os
from typing import List, Optional, Union
from pathlib import Path
import requests
from langchain.schema import Document


class SiliconFlowEmbeddings(Embeddings):
    def __init__(
        self,
        model: str = "BAAI/bge-large-zh-v1.5",
        api_key: Optional[str] = None,
        base_url: str = "https://api.siliconflow.cn/v1",
    ):
        self.model = model
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = base_url

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            embedding = self._embed(text)
            embeddings.append(embedding)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: Union[str, Document]) -> List[float]:
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        text_to_embed = (
            text.page_content if hasattr(text, "page_content") else str(text)  # type: ignore
        )
        # API expects input to be an array
        data = {"model": self.model, "input": [text_to_embed]}
        print(
            f"Embedding request: model={self.model}, input_length={len(text_to_embed)}"
        )
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Embedding response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Embedding response body: {response.text}")
        response.raise_for_status()
        result = response.json()
        return result["data"][0]["embedding"]


class VectorStoreManager:
    def __init__(self):
        self.embeddings = SiliconFlowEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP
        )
        self.vector_store = None
        self._load_vector_store()

    def _load_vector_store(self):
        index_path = os.path.join(settings.VECTOR_STORE_DIR, settings.FAISS_INDEX_NAME)
        if os.path.exists(index_path):
            try:
                self.vector_store = FAISS.load_local(index_path, self.embeddings)
            except Exception as e:
                print(f"Failed to load vector store: {e}")
                self.vector_store = None

    def _get_loader(self, file_path: str):
        ext = Path(file_path).suffix.lower()

        loaders = {
            ".txt": lambda fp: TextLoader(fp, encoding="utf-8"),
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
            ".pptx": PPTXLoader,
            ".ppt": PPTXLoader,
        }

        loader_class = loaders.get(ext)
        if not loader_class:
            raise ValueError(f"Unsupported file type: {ext}")

        return loader_class(file_path)

    def add_document(self, file_path: str) -> bool:
        try:
            print(f"Loading document from: {file_path}")
            loader = self._get_loader(file_path)
            print(f"Loader: {loader}")
            documents = loader.load()
            print(f"Loaded {len(documents)} documents")

            if not documents:
                return False

            texts = self.text_splitter.split_documents(documents)
            print(f"Split into {len(texts)} chunks")

            if not texts:
                return False

            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(texts, self.embeddings)
            else:
                self.vector_store.add_documents(texts)

            self._save_vector_store()
            return True
        except Exception as e:
            import traceback

            print(f"Error adding document: {e}")
            traceback.print_exc()
            return False

    def _save_vector_store(self):
        if self.vector_store:
            index_path = os.path.join(
                settings.VECTOR_STORE_DIR, settings.FAISS_INDEX_NAME
            )
            self.vector_store.save_local(index_path)

    def similarity_search(self, query: str, k: int = 4) -> List:
        if self.vector_store is None:
            return []

        return self.vector_store.similarity_search(query, k=k)

    def delete_index(self) -> bool:
        try:
            index_path = os.path.join(
                settings.VECTOR_STORE_DIR, settings.FAISS_INDEX_NAME
            )
            if os.path.exists(index_path):
                import shutil

                shutil.rmtree(index_path)
            self.vector_store = None
            return True
        except Exception as e:
            print(f"Error deleting index: {e}")
            return False

    def get_document_count(self) -> int:
        if self.vector_store is None:
            return 0
        return self.vector_store.index.ntotal


vector_store_manager = VectorStoreManager()
