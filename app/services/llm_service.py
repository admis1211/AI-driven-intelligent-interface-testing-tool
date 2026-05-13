from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from app.core.config import settings
from app.services.document_service import document_reader
from app.services import document_manager
from app.services.chat_service import chat_service
from app.core.logger import get_logger
from typing import Optional, Dict, List, Any
import uuid
import os

logger = get_logger("llm_service")


class LLMService:
    def __init__(self):
        self._init_llm()
        self.sessions: Dict[str, Dict] = {}
        self.update_config()

    def _init_llm(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        self.llm = ChatOpenAI(
            model=model_name or settings.OPENAI_MODEL,
            temperature=temperature
            if temperature is not None
            else settings.OPENAI_TEMPERATURE,
            api_key=api_key or settings.OPENAI_API_KEY,
            base_url=api_base or settings.OPENAI_API_BASE,
        )

    def update_config(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        self._init_llm(api_key, api_base, model_name, temperature)

        self.qa_template = """你是一个智能助手，可以使用提供的上下文来回答问题。如果上下文中没有相关信息，请根据你的知识库回答。

上下文:
{context}

对话历史:
{chat_history}

用户问题: {question}

请给出详细、准确的回答："""

        self.qa_prompt = PromptTemplate(
            template=self.qa_template,
            input_variables=["context", "chat_history", "question"],
        )

    def _get_session(self, session_id: str) -> Dict:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "memory": ConversationBufferMemory(
                    memory_key="chat_history", return_messages=True
                ),
            }
        return self.sessions[session_id]

    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        use_context: bool = True,
        selected_documents: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if session_id is None:
            session_id = str(uuid.uuid4())

        session = self._get_session(session_id)

        chat_service.create_session(session_id)

        sources = []

        try:
            if use_context and document_manager.uploaded_files:
                file_paths = []

                if selected_documents:
                    for doc in document_manager.uploaded_files:
                        if doc.filename in selected_documents:
                            file_path = os.path.join(settings.UPLOAD_DIR, doc.filename)
                            if os.path.exists(file_path):
                                file_paths.append(file_path)
                                logger.debug(f"Selected document: {file_path}")
                    logger.info(f"Using {len(selected_documents)} selected documents")
                else:
                    for doc in document_manager.uploaded_files:
                        file_path = os.path.join(settings.UPLOAD_DIR, doc.filename)
                        if os.path.exists(file_path):
                            file_paths.append(file_path)
                            logger.debug(f"Found document: {file_path}")

                if file_paths:
                    logger.info(f"Reading {len(file_paths)} documents for context")
                    context = document_reader.read_all_documents(file_paths)
                    logger.info(f"Context prepared: {len(context)} characters")

                    sources = [
                        {
                            "page_content": context,
                            "metadata": {"source": "uploaded_documents"},
                        }
                    ]

                    chat_history_str = ""
                    if session["memory"].chat_memory.messages:
                        chat_history_str = "\n".join(
                            [
                                f"用户: {getattr(msg, 'content', str(msg))}"
                                for msg in session["memory"].chat_memory.messages
                            ]
                        )

                    prompt_text = self.qa_prompt.format(
                        context=context,
                        chat_history=chat_history_str or "无对话历史",
                        question=message,
                    )

                    logger.debug(
                        f"Calling LLM with context, prompt length: {len(prompt_text)}"
                    )
                    response = self.llm.invoke(prompt_text)
                    response_text = (
                        response.content
                        if hasattr(response, "content")
                        else str(response)
                    )
                    logger.debug(f"LLM response length: {len(response_text)}")
                else:
                    logger.info("No valid file paths found, invoking without context")
                    response = self.llm.invoke(message)
                    response_text = (
                        response.content
                        if hasattr(response, "content")
                        else str(response)
                    )
            else:
                logger.info(f"Chat without context, use_context={use_context}")
                response = self.llm.invoke(message)
                response_text = (
                    response.content if hasattr(response, "content") else str(response)
                )

            session["memory"].chat_memory.add_user_message(message)
            session["memory"].chat_memory.add_ai_message(response_text)

            chat_service.update_session(session_id, str(message))
            chat_service.add_message(session_id, "user", str(message))
            chat_service.add_message(session_id, "ai", str(response_text))

            logger.chat_event(session_id, use_context, bool(sources))

            return {
                "response": response_text,
                "session_id": session_id,
                "sources": sources if use_context and sources else None,
            }
        except Exception as e:
            logger.error(f"Chat error: {str(e)}", session_id=session_id)
            return {
                "response": f"处理您的问题时发生错误: {str(e)}",
                "session_id": session_id,
                "sources": None,
            }

    async def chat_stream(
        self,
        message: str,
        session_id: Optional[str] = None,
        use_context: bool = True,
        selected_documents: Optional[List[str]] = None,
    ):
        """流式聊天方法"""
        if session_id is None:
            session_id = str(uuid.uuid4())

        session = self._get_session(session_id)

        chat_service.create_session(session_id)

        try:
            # 准备上下文
            context = ""
            sources = []

            if use_context and document_manager.uploaded_files:
                file_paths = []

                if selected_documents:
                    for doc in document_manager.uploaded_files:
                        if doc.filename in selected_documents:
                            file_path = os.path.join(settings.UPLOAD_DIR, doc.filename)
                            if os.path.exists(file_path):
                                file_paths.append(file_path)
                    logger.info(
                        f"Using {len(selected_documents)} selected documents for streaming"
                    )
                else:
                    for doc in document_manager.uploaded_files:
                        file_path = os.path.join(settings.UPLOAD_DIR, doc.filename)
                        if os.path.exists(file_path):
                            file_paths.append(file_path)

                if file_paths:
                    context = document_reader.read_all_documents(file_paths)
                    sources = [
                        {
                            "page_content": context,
                            "metadata": {"source": "uploaded_documents"},
                        }
                    ]

            # 构建提示词
            if context:
                chat_history_str = ""
                if session["memory"].chat_memory.messages:
                    chat_history_str = "\n".join(
                        [
                            f"用户: {getattr(msg, 'content', str(msg))}"
                            for msg in session["memory"].chat_memory.messages
                        ]
                    )

                prompt_text = self.qa_prompt.format(
                    context=context,
                    chat_history=chat_history_str or "无对话历史",
                    question=message,
                )
            else:
                prompt_text = message

            session["memory"].chat_memory.add_user_message(message)

            # 使用流式输出
            full_response = ""
            for chunk in self.llm.stream(prompt_text):
                content = chunk.content if hasattr(chunk, "content") else str(chunk)
                full_response += content
                yield {"type": "chunk", "content": content, "session_id": session_id}

            session["memory"].chat_memory.add_ai_message(full_response)

            chat_service.update_session(session_id, str(message))
            chat_service.add_message(session_id, "user", message)
            chat_service.add_message(session_id, "ai", full_response)

            yield {
                "type": "done",
                "session_id": session_id,
                "sources": sources if use_context and sources else None,
            }

        except Exception as e:
            logger.error(f"Streaming chat error: {str(e)}", session_id=session_id)
            yield {
                "type": "error",
                "content": f"处理您的问题时发生错误: {str(e)}",
                "session_id": session_id,
            }

    def clear_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False


llm_service = LLMService()
