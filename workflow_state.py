"""
Enhanced state management for the pet grooming Discord bot workflow.
This extends the existing models.py State class with additional workflow-specific fields.
"""

from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class ConversationState(BaseModel):
    """
    Enhanced state for the LangGraph workflow that tracks the entire conversation flow.
    """
    # Core identifiers
    lead_id: str
    discord_user_id: str
    pet_id: Optional[str] = None
    service_id: Optional[str] = None
    appointment_id: Optional[str] = None
    
    # Workflow status
    status: Literal[
        "initiated",
        "onboarded",
        "qualified",
        "booked",
        "completed",
        "cancelled"
    ] = "initiated"
    
    # Lead information
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    created_at_iso: str = datetime.now().isoformat()
    source: Literal["discord"] = "discord"
    
    # Pet information
    pet_name: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    weight_kg: Optional[float] = None
    age_years: Optional[int] = None
    coat_condition: Optional[str] = None
    pet_notes: Optional[str] = None
    
    # Conversation tracking
    last_message: str = ""
    conversation_history: List[Dict[str, str]] = []
    attempts_count: int = 0
    last_activity: str = datetime.now().isoformat()
    response: str = ""
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.last_message = content
        self.last_activity = datetime.now().isoformat()
    
    def update_status(self, new_status: str):
        """Update the workflow status."""
        self.status = new_status
        self.last_activity = datetime.now().isoformat()
    
    def get_missing_lead_fields(self) -> List[str]:
        """Get list of missing required lead fields."""
        required_fields = ["customer_name", "phone"]
        missing = []
        for field in required_fields:
            if not getattr(self, field):
                missing.append(field)
        return missing
    
    def get_missing_pet_fields(self) -> List[str]:
        """Get list of missing required pet fields."""
        required_fields = ["pet_name", "species", "breed", "weight_kg", "age_years"]
        missing = []
        for field in required_fields:
            if not getattr(self, field):
                missing.append(field)
        return missing
    
    def is_qualified(self) -> bool:
        """Check if lead has all required information to be qualified."""
        return (
            len(self.get_missing_lead_fields()) == 0 and 
            len(self.get_missing_pet_fields()) == 0
        )
