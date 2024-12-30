from typing import Optional, Tuple, Dict
from repositories.ChatRepository import ChatRepository
from services.ChatService import ChatService
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv
import traceback
import logging

class SummaryService:
    def __init__(self, chat_repository: ChatRepository, chat_service: ChatService):
        """
        Initialize SummaryService with required repository and service
        
        Args:
            chat_repository (ChatRepository): Repository for chat operations
            chat_service (ChatService): Service for chat operations
        """
        # Load environment variables from .env file
        load_dotenv()
        
        self.chat_repository = chat_repository
        self.chat_service = chat_service
        self.ai_user_id = 'd973e76d-0b64-493b-91ed-f4de8182f53a'  # AI admin user
        
        # Initialize OpenAI LLM with API key from .env
        self.llm = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-3.5-turbo-instruct"
        )

    def get_chat_summary(self, chat_id: str) -> Tuple[Optional[Dict], str]:
        """
        Get a concise and engaging summary of a chat using the LLM.
        
        Args:
            chat_id (str): ID of the chat to summarize
        
        Returns:
            Tuple[Optional[Dict], str]: (Summary dictionary or None, success/error message)
        """
        try:
            # Retrieve the chat
            chat = self.chat_repository.get_chat_by_id(chat_id)
            if not chat:
                return None, "Chat not found"

            # Gather messages into text
            messages_text = "\n".join([
                f"{msg.sender_id}: {msg.content}"
                for msg in chat.messages
            ])

            # Prepare an engaging and detailed prompt
            prompt = PromptTemplate(
                input_variables=["messages"],
                template="""
    Analyze the following conversation and provide a structured summary in a clear and engaging manner. Your response should:
    - Use simple, concise language
    - Include emojis to make it visually appealing
    - Break the output into short paragraphs or bullet points

    Focus on:
    1️⃣ Main topics discussed
    2️⃣ Key points or decisions made
    3️⃣ Topics that were left unresolved or half-discussed (if any)

    Avoid guessing or hallucinating details. If the conversation lacks enough information, clearly mention that.

    Chat messages:
    {messages}

    Provide the summary below:
    """
            )

            # Format and invoke the LLM
            formatted_prompt = prompt.format(messages=messages_text)
            summary = self.llm.invoke(formatted_prompt)

            return {
                "chat_id": chat_id,
                "message_count": len(chat.messages),
                "summary": summary
            }, "Summary generated successfully"
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            return None, f"Error generating summary: {str(e)}"


    def validate_chat_context(self, chat_id: str) -> Tuple[Optional[Dict], str]:
        try:
            chat = self.chat_repository.get_chat_by_id(chat_id)
            if not chat:
                return None, "Chat not found"

            messages_text = "\n".join([
                f"{msg.sender_id}: {msg.content}" 
                for msg in chat.messages[-25:]
            ])

            prompt = PromptTemplate(
                input_variables=["chat_name", "agenda", "messages"],
                template="""
                Analyze if the following chat messages align with the chat agenda.
                Chat Name: {chat_name}
                Chat Agenda: {agenda}
                Recent Messages: {messages}
                
                Respond in the following format:
                1. Is_On_Topic: [Yes/No]
                2. Confidence: [percentage]
                3. Analysis: [brief explanation]
                4. Off_Topic_Examples: [list specific messages if any]
                """
            )

            formatted_prompt = prompt.format(
                chat_name=chat.chat_name,
                agenda=chat.agenda,
                messages=messages_text
            )

            response = self.llm.invoke(formatted_prompt)
            
            # Parse LLM response
            is_on_topic = 'yes' in response.lower().split('is_on_topic:')[1].split('\n')[0].lower()

            if not is_on_topic:
                # Send AI reminder message
                reminder_message = (
                    "🤖 Friendly reminder: Let's stay focused on our agenda: "
                    f"'{chat.agenda}'. I noticed some off-topic discussions."
                )
                self.chat_service.send_message(
                    self.ai_user_id,
                    chat_id,
                    reminder_message
                )

            return {
                "is_on_topic": is_on_topic,
                "validation_details": response,
                "chat_name": chat.chat_name,
                "message_count": len(chat.messages),
                "agenda": chat.agenda
            }, "Context validation complete"

        except Exception as e:
            logging.error(f"Error validating chat context: {str(e)}")
            return None, f"Error validating chat context: {str(e)}"
