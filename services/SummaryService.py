from typing import Optional, Tuple, Dict
from repositories.ChatRepository import ChatRepository
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv
import traceback

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

            print("printing messaghes")
            print(messages_text)
            print(type(messages_text))

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

            print("Formated pronpt")
            print(formatted_prompt)
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

    def validate_chat_context(self, chat_id: str) -> Tuple[bool, str]:
        """
        Validate if chat messages align with the agenda
        """
        try:
            # Get chat details
            chat = self.chat_repository.get_chat_by_id(chat_id)
            if not chat:
                return False, "Chat not found"

            # Get all messages
            messages = [msg.content for msg in chat.messages]
            if not messages:
                return True, "No messages to validate"
            
            prompt = f"""
            Chat Agenda: {chat.agenda}
            
            Recent messages in chat:
            {' '.join(messages[-25:])}  # Only analyze last 25 messages
            
            Question: Are these messages staying within the context of the chat agenda? 
            Provide a brief analysis and state if there are any off-topic discussions.
            """

            response = self.llm.invoke(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a context validation assistant."},
                    {"role": "user", "content": prompt}
                ]
            )

            return True, response.choices[0].message.content

        except Exception as e:
            return False, f"Error validating chat context: {str(e)}"
