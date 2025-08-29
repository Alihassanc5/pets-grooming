"""
LangGraph workflow definition for the pet grooming Discord bot.
This creates the main workflow graph with conditional routing between nodes.
"""

import logging
from typing import Dict, Any
import random
import string
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from google_sheet_service import goole_sheet_service
from sheet_structures import SheetType


from workflow_state import ConversationState
from workflow_nodes import workflow_nodes

logger = logging.getLogger('workflow_graph')


def should_continue(state: ConversationState) -> str:
    """
    Conditional routing function to determine the next node based on state.
    """
    logger.info(f"Routing decision for status: {state.status}, last_message: {state.last_message[:50]}...")
    
    # Classify intent based on current state and message
    intent = workflow_nodes.classify_intent(state)
    
    logger.info(f"Classified intent: {intent}")
    
    # Route based on intent
    if intent == "qualify_lead":
        return "qualify_lead"
    elif intent == "collect_details":
        return "collect_details"
    elif intent == "show_services":
        return "show_services"
    elif intent == "book_appointment":
        return "book_appointment"
    elif intent == "provide_brand_info":
        return "provide_brand_info"
    elif intent == "follow_up":
        return "follow_up"
    else:
        return "generate_response"


def create_workflow_graph() -> StateGraph:
    """
    Create and configure the LangGraph workflow.
    """
    logger.info("Creating workflow graph")
    
    # Create the graph
    workflow = StateGraph(ConversationState)
    
    # Add nodes
    workflow.add_node("classify_intent", workflow_nodes.classify_intent_node)
    workflow.add_node("qualify_lead", workflow_nodes.qualify_lead_node)
    workflow.add_node("collect_details", workflow_nodes.collect_details_node)
    workflow.add_node("show_services", workflow_nodes.show_services_node)
    workflow.add_node("book_appointment", workflow_nodes.book_appointment_node)
    workflow.add_node("provide_brand_info", workflow_nodes.provide_brand_info_node)
    workflow.add_node("follow_up", workflow_nodes.follow_up_node)
    workflow.add_node("generate_response", workflow_nodes.generate_response_node)
    
    # Set entry point
    workflow.set_entry_point("classify_intent")
    
    # Add conditional routing
    # workflow.add_conditional_edges(
    #     "qualify_lead",
    #     should_continue,
    #     {
    #         "qualify_lead": "qualify_lead",
    #         "collect_details": "collect_details",
    #         "show_services": "show_services",
    #         "book_appointment": "book_appointment",
    #         "provide_brand_info": "provide_brand_info",
    #         "follow_up": "follow_up",
    #         "generate_response": "generate_response"
    #     }
    # )
    
    # workflow.add_conditional_edges(
    #     "collect_details",
    #     should_continue,
    #     {
    #         "qualify_lead": "qualify_lead",
    #         "collect_details": "collect_details",
    #         "show_services": "show_services",
    #         "book_appointment": "book_appointment",
    #         "provide_brand_info": "provide_brand_info",
    #         "follow_up": "follow_up",
    #         "generate_response": "generate_response"
    #     }
    # )
    
    # workflow.add_conditional_edges(
    #     "show_services",
    #     should_continue,
    #     {
    #         "qualify_lead": "qualify_lead",
    #         "collect_details": "collect_details",
    #         "show_services": "show_services",
    #         "book_appointment": "book_appointment",
    #         "provide_brand_info": "provide_brand_info",
    #         "follow_up": "follow_up",
    #         "generate_response": "generate_response"
    #     }
    # )
    
    # workflow.add_conditional_edges(
    #     "book_appointment",
    #     should_continue,
    #     {
    #         "qualify_lead": "qualify_lead",
    #         "collect_details": "collect_details",
    #         "show_services": "show_services",
    #         "book_appointment": "book_appointment",
    #         "provide_brand_info": "provide_brand_info",
    #         "follow_up": "follow_up",
    #         "generate_response": "generate_response"
    #     }
    # )
    
    # workflow.add_conditional_edges(
    #     "provide_brand_info",
    #     should_continue,
    #     {
    #         "qualify_lead": "qualify_lead",
    #         "collect_details": "collect_details",
    #         "show_services": "show_services",
    #         "book_appointment": "book_appointment",
    #         "provide_brand_info": "provide_brand_info",
    #         "follow_up": "follow_up",
    #         "generate_response": "generate_response"
    #     }
    # )
    
    # workflow.add_conditional_edges(
    #     "follow_up",
    #     should_continue,
    #     {
    #         "qualify_lead": "qualify_lead",
    #         "collect_details": "collect_details",
    #         "show_services": "show_services",
    #         "book_appointment": "book_appointment",
    #         "provide_brand_info": "provide_brand_info",
    #         "follow_up": "follow_up",
    #         "generate_response": "generate_response"
    #     }
    # )
    
    # Generate response always ends the workflow
    workflow.add_edge("generate_response", END)
    
    return workflow


class WorkflowManager:
    """
    Manager class for the LangGraph workflow with state persistence.
    """
    
    def __init__(self):
        self.workflow_graph = create_workflow_graph()
        self.memory = MemorySaver()
        self.app = self.workflow_graph.compile(checkpointer=self.memory)
        self.thread_states: Dict[str, ConversationState] = {}
        self.sheet_service = goole_sheet_service
        
        logger.info("Workflow manager initialized")
    
    def get_or_create_state(self, lead_id: str, discord_user_id: str) -> ConversationState:
        """
        Get existing state for a thread or create a new one.
        """
        if lead_id not in self.thread_states:
            logger.info(f"Creating new conversation state for thread {lead_id}")
            lead = self.sheet_service.get_record(SheetType.LEADS, lead_id)

            if not lead:
                pet_id = "PET" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                conversation_state = ConversationState(
                    lead_id=lead_id,
                    discord_user_id=discord_user_id,
                    pet_id=pet_id,
                    created_at_iso=datetime.now().isoformat()
                )

                # Insert lead into sheet
                self.sheet_service.insert_record(SheetType.LEADS, conversation_state.model_dump())
                self.sheet_service.insert_record(SheetType.PETS, conversation_state.model_dump())
            else:
                status = lead["status"]
                # Prepare base kwargs for ConversationState
                state_kwargs = {
                    "lead_id": lead_id,
                    "discord_user_id": discord_user_id,
                    "status": status,
                    "created_at_iso": lead["created_at_iso"],
                    "source": lead["source"],
                }

                # Add user details if available
                if status in ["onboarded", "qualified", "booked"]:
                    state_kwargs.update({
                        "customer_name": lead["name"],
                        "phone": lead["phone"],
                        "city": lead["city"],
                    })

                # Add pet details if available
                if status in ["qualified", "booked"]:
                    pet = self.sheet_service.get_record(SheetType.PETS, lead_id)                    
                    state_kwargs.update({
                        "pet_id": pet["pet_id"],
                        "pet_name": pet["pet_name"],
                        "species": pet["species"],
                        "breed": pet["breed"],
                        "weight_kg": pet["weight_kg"],
                        "age_years": pet["age_years"],
                        "coat_condition": pet["coat_condition"],
                        "pet_notes": pet["notes"],
                    })

                # Add appointment details if available
                if status == "booked":
                    appointment = self.sheet_service.get_record(SheetType.APPOINTMENTS, lead_id)
                    state_kwargs.update({
                        "appointment_id": appointment["appointment_id"],
                        "service_id": appointment["service_id"],
                        "meeting_link": appointment["meeting_link"],
                    })

                conversation_state = ConversationState(**state_kwargs)
            
            self.thread_states[lead_id] = conversation_state
        
        return self.thread_states[lead_id]
    
    async def process_message(self, message: str, lead_id: str, discord_user_id: str) -> str:
        """
        Process a message through the workflow and return the response.
        """
        logger.info(f"Processing message in thread {lead_id}: {message[:100]}...")
        
        try:
            # Get or create conversation state
            state = self.get_or_create_state(lead_id, discord_user_id)
            logger.info(f"State: {state}")
            
            # Add the user message to history
            state.add_message("user", message)
            
            # Create thread configuration for checkpointing
            thread_config = {"configurable": {"thread_id": lead_id}}
            
            # Process through workflow
            result = await self.app.ainvoke(state, config=thread_config)
            
            state.add_message("assistant", result["response"])
            
            return result["response"]
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "I'm sorry, I encountered an error. Please try again or contact support."
    
    def get_thread_state(self, lead_id: str) -> ConversationState:
        """Get the current state for a thread."""
        return self.thread_states.get(lead_id)
    
    def update_thread_state(self, lead_id: str, state: ConversationState):
        """Update the state for a thread."""
        self.thread_states[lead_id] = state


# Create global workflow manager instance
workflow_manager = WorkflowManager()
