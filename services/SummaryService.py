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
                f"{msg.sender_name}: {msg.content}"
                for msg in chat.messages
            ])

            # Prepare the detailed and structured prompt
            prompt = PromptTemplate(
                input_variables=["messages"],
                template="""
    You are an AI assistant that specializes in summarizing group discussions or chats. You have the following goal:

    **Goal**: Produce a concise, well-structured, and engaging summary of the conversation that captures:
    1. Chat overview (name, agenda, date/time).
    2. Key topics and how much focus each received.
    3. Who contributed which ideas or suggestions.
    4. Any pending items or unresolved decisions.
    5. Action items with assigned individuals and deadlines.

    Follow these instructions carefully:

    1. **Read and Analyze Messages**:
    - You will be given a list of messages. Each message has:
        - A senders name.
        - A timestamp.
        - Text content (the message body).
    - Treat these messages as if they were sent in chronological order.
    - Identify repeated or related concepts to cluster them into “topics.”

    2. **Identify Topics and Focus**:
    - Look for distinct subjects or themes in the chat (e.g., destinations, budgeting, schedules, etc.).
    - Estimate how much of the overall conversation was dedicated to each topic (for example, 50% on choosing a destination, 30% on budgeting, 20% on logistics).
    - Provide a short status for each topic (e.g., “undecided,” “in progress,” “finalized,” etc.).

    3. **Extract Contributors and Key Points**:
    - For each topic, note which participants contributed ideas.
    - Write down any unique or noteworthy suggestions (e.g., “Alice suggested Airbnb to cut costs,” “Bob wants a road trip to Coorg,” etc.).
    - If a user proposes a solution or approach, highlight that contribution clearly.

    4. **Pending & Next Steps**:
    - Identify any discussion points that were not resolved or need follow-up (e.g., “Destination not decided yet,” “Budget needs final confirmation”).
    - Summarize these in a short “Pending” or “Next Steps” section.

    5. **Action Items**:
    - Create a list of concrete tasks or to-dos.
    - Clearly state **who** is responsible and **any deadlines** or timeframes.

    6. **Formatting Requirements**:
    - Use **headings** and **bullet points** where appropriate.
    - Use **emojis** to make the summary more visually appealing (e.g., 📍 for location, 💸 for budget, ✅ for completed items, etc.).
    - Maintain a **friendly and clear tone**—imagine you are providing a quick readout for the group so they can see what’s done, what’s pending, and who needs to act.

    7. **Style & Tone**:
    - Write in a **concise** manner: aim for a 200-400 word summary total (approx.).
    - Keep the language **positive**, **helpful**, and **engaging**.
    - If there’s any critical or urgent matter, use an appropriate emoji (e.g., ⚠️) or short note to highlight it.

    8. **Example Structure** (for reference only; adapt as needed):

    🌴 Friends' Trip Planning – Evening Chat 🌴 📅 Date/Time: ... 🎯 Agenda: ...

    🔍 Key Topics & Focus

    ...
    ...
    ...
    👥 Contributors & Their Ideas

    Alice: ...
    Bob: ...
    ⏳ Pending & Next Steps

    ...
    📋 Action Items

    ...
    ...
    🎉 Wrap-Up
    Feel free to adjust the emojis, headings, or bullet points to fit the conversation’s context.

    **Input to Summarize**:
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
