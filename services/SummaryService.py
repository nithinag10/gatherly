from typing import Optional, Tuple, Dict
from repositories.ChatRepository import ChatRepository
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv
import traceback
import logging

class SummaryService:
    def __init__(self, chat_repository: ChatRepository):
        """
        Initialize SummaryService with required repository
        
        Args:
            chat_repository (ChatRepository): Repository for chat operations
        """
        # Load environment variables from .env file
        load_dotenv()
        
        self.chat_repository = chat_repository
        
        # Initialize OpenAI LLM with API key from .env
        self.llm = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-3.5-turbo-instruct"
        )

    def get_chat_summary(self, chat_id: str) -> Tuple[Optional[Dict], str]:
        """
        Get a summary of the chat using LLM
        
        Args:
            chat_id (str): ID of the chat to summarize
            
        Returns:
            Tuple[Optional[Dict], str]: (Summary dictionary or None, success/error message)
        """
        try:
            # Get chat from repository
            chat = self.chat_repository.get_chat_by_id(chat_id)
            if not chat:
                return None, "Chat not found"

            # Prepare messages for summarization
            messages_text = "\n".join([
                f"{msg.sender_id}: {msg.content}"
                for msg in chat.messages
            ])

            # Create prompt template
            prompt = PromptTemplate(
                input_variables=["messages"],
                template="""
                Analyze the following chat messages and provide a summary including:
                - Main topics discussed
                - Key points or decisions made
                - Overall sentiment of the conversation
                - Number of participants involved

                Chat messages:
                {messages}

                Please provide a structured summary.
                """
            )

            # Generate summary using LLM
            formatted_prompt = prompt.format(messages=messages_text)

            summary = self.llm.invoke(formatted_prompt)

            return {
                "chat_id": chat_id,
                "participant_count": len(chat.participants),
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

                Recent Messages:
                {messages}

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

            print("Printing LLM response")
            print(response)
            
            # Parse LLM response for Yes/No
            is_on_topic = 'yes' in response.lower().split('is_on_topic:')[1].split('\n')[0].lower()

            return {
                "is_on_topic": is_on_topic,
                "validation_details": response,
                "chat_name": chat.chat_name,
                "message_count": len(chat.messages),
                "agenda": chat.agenda
            }, "Context validation complete"

        except Exception as e:
            traceback.print_tb(e.__traceback__)
            logging.error(f"Error validating chat context: {str(e)}")
            return None, f"Error validating chat context: {str(e)}"
