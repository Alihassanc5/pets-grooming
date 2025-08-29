"""
Sheet structure definitions for different types of data in the pet grooming system.
Each sheet type has its own field structure and validation rules.
"""

from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

class SheetType(Enum):
    """Enumeration of different sheet types."""
    PETS = "Pets"
    LEADS = "Leads"
    SERVICES = "Services"
    APPOINTMENTS = "Appointments"
    BRANDS = "Brands"

@dataclass
class FieldDefinition:
    """Definition of a field in a sheet."""
    name: str
    column: str  # Excel column letter (A, B, C, etc.)

@dataclass
class SheetStructure:
    """Structure definition for a sheet type."""
    name: str
    fields: List[FieldDefinition]

# Define sheet structures
SHEET_STRUCTURES = {
    SheetType.PETS: SheetStructure(
        name="Pets",
        fields=[
            FieldDefinition("lead_id", "A"),
            FieldDefinition("pet_id", "B"),
            FieldDefinition("pet_name", "C"),
            FieldDefinition("species", "D"),
            FieldDefinition("breed", "E"),
            FieldDefinition("weight_kg", "F"),
            FieldDefinition("age_years", "H"),
            FieldDefinition("coat_condition", "I"),
            FieldDefinition("notes", "J"),
        ]
    ),
    
    SheetType.LEADS: SheetStructure(
        name="Leads",
        fields=[
            FieldDefinition("lead_id", "A"),
            FieldDefinition("created_at_iso", "B"),
            FieldDefinition("source", "C"),
            FieldDefinition("discord_user_id", "D"),
            FieldDefinition("name", "E"),
            FieldDefinition("phone", "F"),
            FieldDefinition("city", "G"),
            FieldDefinition("status", "H"),
        ]
    ),
    
    SheetType.SERVICES: SheetStructure(
        name="Services",
        fields=[
            FieldDefinition("service_id", "A"),
            FieldDefinition("title", "B"),
            FieldDefinition("description", "C"),
            FieldDefinition("base_price", "D"),
            FieldDefinition("duration_min", "E"),
            FieldDefinition("breed_modifier_json", "F"),
            FieldDefinition("weight_brackets_json", "G"),
            FieldDefinition("upsells_json", "H"),
        ]
    ),
    
    SheetType.APPOINTMENTS: SheetStructure(
        name="Appointments",
        fields=[
            FieldDefinition("lead_id", "A"),
            FieldDefinition("appointment_id", "B"),
            FieldDefinition("service_id", "C"),
            FieldDefinition("meeting_link", "D"),
        ]
    ),
    
    SheetType.BRANDS: SheetStructure(
        name="Brands",
        fields=[
            FieldDefinition("brand_id", "A"),
            FieldDefinition("brand_name", "B"),
            FieldDefinition("welcome_copy", "C"),
            FieldDefinition("website", "D"),
            FieldDefinition("hours", "E"),
            FieldDefinition("location", "F"),
            FieldDefinition("timezone", "G"),
            FieldDefinition("upsells_json", "H"),
            FieldDefinition("objection_snippets_json", "I"),
        ]
    )
}

def get_sheet_structure(sheet_type: SheetType) -> SheetStructure:
    """Get the structure definition for a specific sheet type."""
    return SHEET_STRUCTURES.get(sheet_type)

def get_field_mapping(sheet_type: SheetType) -> Dict[str, str]:
    """Get the field to column mapping for a sheet type."""
    structure = get_sheet_structure(sheet_type)
    if not structure:
        return {}
    
    return {field.name: field.column for field in structure.fields}


