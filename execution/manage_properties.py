"""
Property management utilities
Add, update, delete properties
"""
from typing import Dict, Optional
from loguru import logger
from execution.database import get_db


def add_property(agent_id: str, property_data: Dict) -> Dict:
    """
    Add new property

    Args:
        agent_id: UUID of agent
        property_data: Property details dict

    Returns:
        Created property dict
    """
    db = get_db()

    # Ensure agent_id is set
    property_data['agent_id'] = agent_id

    # Set defaults
    if 'availability' not in property_data:
        property_data['availability'] = 'available'
    if 'is_archived' not in property_data:
        property_data['is_archived'] = False

    property_record = db.insert("properties", property_data)

    logger.info(f"Property created: {property_record['property_id']}")

    return property_record


def update_property(property_id: str, updates: Dict) -> bool:
    """
    Update existing property

    Args:
        property_id: UUID of property
        updates: Fields to update

    Returns:
        True if successful
    """
    db = get_db()

    # Don't allow changing agent_id or property_id
    updates.pop('agent_id', None)
    updates.pop('property_id', None)

    success = db.update(
        "properties",
        updates,
        {"property_id": property_id}
    )

    if success:
        logger.info(f"Property updated: {property_id}")
    else:
        logger.warning(f"Property not found: {property_id}")

    return success


def delete_property(property_id: str, hard_delete: bool = False) -> bool:
    """
    Delete property (soft delete by default)

    Args:
        property_id: UUID of property
        hard_delete: If True, permanently delete. If False, archive.

    Returns:
        True if successful
    """
    db = get_db()

    if hard_delete:
        query = "DELETE FROM properties WHERE property_id = %s"
        db.execute(query, (property_id,))
        logger.info(f"Property hard deleted: {property_id}")
    else:
        success = db.update(
            "properties",
            {"is_archived": True},
            {"property_id": property_id}
        )
        if success:
            logger.info(f"Property archived: {property_id}")
        return success

    return True


def mark_property_sold(property_id: str) -> bool:
    """Mark property as sold"""
    return update_property(property_id, {"availability": "sold"})


def mark_property_available(property_id: str) -> bool:
    """Mark property as available"""
    return update_property(property_id, {"availability": "available"})


if __name__ == "__main__":
    # Test - add sample property
    import sys

    if len(sys.argv) < 2:
        print("Usage: python manage_properties.py <agent_id>")
        sys.exit(1)

    agent_id = sys.argv[1]

    # Sample property
    sample_property = {
        "title": "Luxury Marina Bay Condo",
        "property_type": "condo",
        "location": "Marina Bay",
        "price": 1500000,
        "bedrooms": 3,
        "bathrooms": 2,
        "size_sqft": 1400,
        "key_selling_points": "Stunning sea view, infinity pool, gym, 24/7 security",
        "viewing_instructions": "Contact agent to schedule viewing"
    }

    property_record = add_property(agent_id, sample_property)
    print(f"Property created: {property_record['property_id']}")
