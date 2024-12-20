from typing import Optional, Tuple, Dict
from repositories.ChatRepository import ChatRepository
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv

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

                The given below is an example response. 
                Please provide a structured summary in the following JSON format:
                {
                    "topic_of_discussion": "planning goa trip",
                    "initiator": "Prajwal",
                    "no_of_participants": "4",
                    "closed_questions": [
                        {
                            "question": "Where are we staying in goa",
                            "answer": "panaji hotel"
                        },
                        {
                            "question": "Did someone book the hotel?",
                            "answer": "Nithin is going to book tomorrow"
                        }
                    ],
                    "under_discussion_questions": [
                        {
                            "question": "How many days are we staying there?",
                            "answer": "Manoj is telling 5, Nithin is telling 3 but people are still thinking on it"
                        }
                    ],
                    "open_questions": [
                        {
                            "question": "What is the budget of the trip?"
                        }
                    ]
                }
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
            return None, f"Error generating summary: {str(e)}"
