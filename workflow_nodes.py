"""
LangGraph nodes for the pet grooming Discord bot workflow.
Each node handles a specific step in the customer journey.
"""

import logging
import json
from typing import Literal

from sheet_structures import SheetType
from google_sheet_service import goole_sheet_service
from google_calendar_service import google_calendar_service
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END
from langgraph.types import Command

from workflow_state import ConversationState
from llm import chat_model

logger = logging.getLogger('workflow_nodes')


class WorkflowNodes:
    """Collection of workflow nodes for the pet grooming bot."""
    
    def __init__(self):
        self.chat_model = chat_model
        self.sheets_service = goole_sheet_service
        self.calendar_service = google_calendar_service
    
    def classify_intent_node(self, state: ConversationState) -> Command[Literal["provide_brand_info", "qualify_lead"]]:
        """
        Classify user intent to determine next action.
        """
        prompt = """
        You are an AI assistant for a pet grooming business. Your job is to classify the user's intent if it's asking about brand information or not.
        
        return:
        - "brand_information" if the user is asking about brand information
        - "other" if the user is asking about anything else
        """
        logger.info(f"Classifying intent for thread {state.lead_id}")

        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=state.last_message)
        ]
        
        response = self.chat_model.invoke(messages)
        intent = response.content.lower()
        logger.info(f"Intent: {intent}")
        
        return Command(goto="provide_brand_info" if "brand_information" == intent else "qualify_lead")
    
    def qualify_lead_node(self, state: ConversationState) -> ConversationState:
        """
        Node to qualify the lead and start collecting basic information.
        """
        logger.info(f"Qualifying lead for thread {state.lead_id}")
        
        # Create lead record if not exists
        if state.status == "initiated":
            success = True #service_integrator.create_lead_record(state)
            if success:
                logger.info(f"Created lead record for {state.lead_id}")
            else:
                logger.warning(f"Failed to create lead record for {state.lead_id}")
        
        state.update_status("qualifying")
        
        # Check what information we still need
        missing_lead = state.get_missing_lead_fields()
        missing_pet = state.get_missing_pet_fields()
        
        if missing_lead or missing_pet:
            state.update_status("collecting_details")
            
        return state
    
    def collect_details_node(self, state: ConversationState) -> ConversationState:
        """
        Node to collect customer and pet details using LLM.
        """
        logger.info(f"Collecting details for thread {state.lead_id}")
        
        # Use LLM to extract information from the conversation
        system_prompt = """
        You are an AI assistant for a pet grooming business. Your job is to extract customer and pet information from conversations.
        
        Extract the following information from the user's message:
        - customer_name: Full name of the customer
        - phone: Phone number
        - city: City where customer lives
        - pet_name: Name of the pet
        - species: Type of animal (Dog, Cat, etc.)
        - breed: Breed of the pet
        - weight_kg: Weight in kilograms (convert from pounds if needed: pounds * 0.453592)
        - age_years: Age in years
        - coat_condition: Condition of the pet's coat (Good, Fair, Poor, Matted, etc.)
        
        Return ONLY a JSON object with the extracted information. Use null for missing information.
        Do not include any other text or explanations.
        """
        
        user_message = f"Previous conversation: {state.conversation_history[-5:] if state.conversation_history else []}\nCurrent message: {state.last_message}"
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = self.chat_model.invoke(messages)
            extracted_data = json.loads(response.content.strip())
            
            # Update state with extracted information
            for field, value in extracted_data.items():
                if value is not None and hasattr(state, field):
                    setattr(state, field, value)
                    logger.info(f"Updated {field}: {value}")
            
        except Exception as e:
            logger.error(f"Error extracting information: {e}")
        
        # Check if we have all required information
        if state.is_qualified():
            state.update_status("qualified")
            
            # Update lead record
            service_integrator.update_lead_record(state)
            
            # Create or update pet record
            service_integrator.create_or_update_pet_record(state)
        
        return state
    
    def show_services_node(self, state: ConversationState) -> ConversationState:
        """
        Node to show available services from the Services sheet.
        """
        logger.info(f"Showing services for thread {state.lead_id}")
        
        # Get all services from the sheet
        services = service_integrator.get_available_services()
        
        if services:
            state.available_services = services
            state.update_status("showing_services")
        else:
            logger.warning("No services found in the Services sheet")
        
        return state
    
    def book_appointment_node(self, state: ConversationState) -> ConversationState:
        """
        Node to handle appointment booking with calendar integration.
        """
        logger.info(f"Booking appointment for thread {state.lead_id}")
        
        state.update_status("booking_appointment")
        
        # For now, we'll set this up for the next step
        # The actual booking logic will be handled by the response generation
        
        return state
    
    def provide_brand_info_node(self, state: ConversationState) -> ConversationState:
        """
        Node to provide business information from the Brands sheet.
        """
        logger.info(f"Providing brand info for thread {state.lead_id}")
        brand_info = self.sheets_service.get_all_records(SheetType.BRANDS)

        prompt = """
        You are an AI assistant for a pet grooming business. Your job is to provide business information from the Brands sheet.      
        Business Information:
        {brand_info}
        """

        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=state.last_message)
        ]

        response = self.chat_model.invoke(messages)

        return Command(update={"response": response.content}, goto=END)
    
    def follow_up_node(self, state: ConversationState) -> ConversationState:
        """
        Node to handle follow-up for stalled leads.
        """
        logger.info(f"Following up on stalled lead {state.lead_id}")
        
        # Check if lead has been inactive
        last_activity = datetime.fromisoformat(state.last_activity)
        time_diff = datetime.now() - last_activity
        
        if time_diff.total_seconds() > 3600:  # 1 hour
            state.update_status("stalled")
        
        return state
    
    def generate_response_node(self, state: ConversationState) -> ConversationState:
        """
        Node to generate appropriate response based on current state.
        """
        logger.info(f"Generating response for thread {state.lead_id}, status: {state.status}")
        
        # Determine response based on current status
        if state.status == "qualifying":
            response = self._generate_qualifying_response(state)
        elif state.status == "collecting_details":
            response = self._generate_collection_response(state)
        elif state.status == "qualified":
            response = self._generate_qualified_response(state)
        elif state.status == "showing_services":
            response = self._generate_services_response(state)
        elif state.status == "booking_appointment":
            response = self._generate_booking_response(state)
        elif state.status == "booked":
            response = self._generate_confirmation_response(state)
        else:
            response = self._generate_generic_response(state)
        
        state.add_message("assistant", response)
        return state
    
    def _generate_qualifying_response(self, state: ConversationState) -> str:
        """Generate response for lead qualification."""
        return ("Hi there! 🐾 Welcome to our pet grooming service! I'd love to help you get your furry friend "
                "looking their best. To get started, could you please tell me:\n\n"
                "• Your name and phone number\n"
                "• Your pet's name, breed, and approximate weight\n"
                "• Your pet's age and current coat condition")
    
    def _generate_collection_response(self, state: ConversationState) -> str:
        """Generate response for collecting missing details."""
        missing_lead = state.get_missing_lead_fields()
        missing_pet = state.get_missing_pet_fields()
        
        missing_items = []
        if "customer_name" in missing_lead:
            missing_items.append("your name")
        if "phone" in missing_lead:
            missing_items.append("your phone number")
        if "pet_name" in missing_pet:
            missing_items.append("your pet's name")
        if "breed" in missing_pet:
            missing_items.append("your pet's breed")
        if "weight_kg" in missing_pet:
            missing_items.append("your pet's weight")
        if "age_years" in missing_pet:
            missing_items.append("your pet's age")
        
        if missing_items:
            items_text = ", ".join(missing_items[:-1])
            if len(missing_items) > 1:
                items_text += f" and {missing_items[-1]}"
            else:
                items_text = missing_items[0]
            
            return f"Thanks for that information! I still need {items_text} to help you better. Could you provide that?"
        
        return "Perfect! I have all the information I need. Let me show you our available services."
    
    def _generate_qualified_response(self, state: ConversationState) -> str:
        """Generate response when lead is qualified."""
        return (f"Wonderful! I have all your details, {state.customer_name}. "
                f"{state.pet_name} sounds like a lovely {state.breed}! "
                "Let me show you our available services and pricing.")
    
    def _generate_services_response(self, state: ConversationState) -> str:
        """Generate response showing available services."""
        if not state.available_services:
            return "I'm sorry, I'm having trouble accessing our services right now. Please try again later."
        
        response = f"Here are our grooming services for {state.pet_name}:\n\n"
        
        for service in state.available_services:
            title = service.get('title', 'Unknown Service')
            description = service.get('description', '')
            base_price = service.get('base_price', 'Contact for pricing')
            duration = service.get('duration_min', 'N/A')
            
            response += f"**{title}** - ${base_price}\n"
            if description:
                response += f"• {description}\n"
            if duration != 'N/A':
                response += f"• Duration: {duration} minutes\n"
            response += "\n"
        
        response += "Which service would you like to book for your pet? Just let me know and I'll check our available time slots! 📅"
        
        return response
    
    def _generate_booking_response(self, state: ConversationState) -> str:
        """Generate response for appointment booking."""
        return ("Great choice! Let me check our available time slots. "
                "What days work best for you this week or next? "
                "I can check morning (9 AM - 12 PM) or afternoon (1 PM - 5 PM) slots.")
    
    def _generate_confirmation_response(self, state: ConversationState) -> str:
        """Generate confirmation response after booking."""
        return (f"Perfect! Your appointment has been booked for {state.pet_name}. "
                f"You'll receive a confirmation with all the details. "
                "Is there anything else I can help you with today?")
    
    def _generate_generic_response(self, state: ConversationState) -> str:
        """Generate generic response using LLM."""
        system_prompt = f"""
        You are a friendly AI assistant for a pet grooming business. 
        
        Business Information:
        {state.brand_info if state.brand_info else "Contact us for hours and location information."}
        
        Current customer: {state.customer_name or "Customer"}
        Pet: {state.pet_name or "their pet"} ({state.breed or "unknown breed"})
        Status: {state.status}
        
        Respond helpfully and professionally. Keep responses concise but warm.
        If asked about services, mention that you can show available services.
        If asked about booking, guide them through the process.
        """
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=state.last_message)
            ]
            
            response = self.chat_model.invoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return "I'm here to help with your pet grooming needs! How can I assist you today?"


# Create global instance
workflow_nodes = WorkflowNodes()
