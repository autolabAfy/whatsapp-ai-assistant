"""
Property lookup and matching
Query agent's properties based on user intent
"""
from typing import List, Dict, Optional
from loguru import logger
from execution.database import get_db


def search_properties(
    agent_id: str,
    location: Optional[str] = None,
    property_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    limit: int = 3
) -> List[Dict]:
    """
    Search for properties matching criteria

    Args:
        agent_id: UUID of agent
        location: Location search term (partial match)
        property_type: Type of property (condo, HDB, landed, commercial)
        min_price: Minimum price
        max_price: Maximum price
        bedrooms: Number of bedrooms
        limit: Max results to return

    Returns:
        List of matching properties
    """
    db = get_db()

    # Build dynamic query
    conditions = ["agent_id = %s", "availability = 'available'", "is_archived = FALSE"]
    params = [agent_id]

    if location:
        conditions.append("location ILIKE %s")
        params.append(f"%{location}%")

    if property_type:
        conditions.append("property_type = %s")
        params.append(property_type)

    if min_price is not None:
        conditions.append("price >= %s")
        params.append(min_price)

    if max_price is not None:
        conditions.append("price <= %s")
        params.append(max_price)

    if bedrooms is not None:
        conditions.append("bedrooms = %s")
        params.append(bedrooms)

    where_clause = " AND ".join(conditions)

    query = f"""
        SELECT
            property_id,
            title,
            property_type,
            location,
            price,
            bedrooms,
            bathrooms,
            size_sqft,
            key_selling_points,
            viewing_instructions
        FROM properties
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT %s
    """

    params.append(limit)

    results = db.execute(query, tuple(params))

    logger.info(f"Found {len(results)} properties for agent {agent_id}")
    return results


def get_property_by_id(property_id: str) -> Optional[Dict]:
    """Get single property by ID"""
    db = get_db()

    query = """
        SELECT
            property_id,
            title,
            property_type,
            location,
            price,
            bedrooms,
            bathrooms,
            size_sqft,
            amenities,
            key_selling_points,
            viewing_instructions,
            availability
        FROM properties
        WHERE property_id = %s
    """

    return db.execute_one(query, (property_id,))


def format_property_response(properties: List[Dict], format_type: str = "list") -> str:
    """
    Format properties for WhatsApp response

    Args:
        properties: List of property dicts
        format_type: 'single', 'list', or 'summary'

    Returns:
        Formatted string for WhatsApp
    """
    if not properties:
        return ""

    if format_type == "single" and len(properties) == 1:
        prop = properties[0]
        response = f"{prop['title']}\n"
        response += f"Type: {prop['property_type']}\n"
        response += f"Location: {prop['location']}\n"
        response += f"Price: ${prop['price']:,.0f}\n"

        if prop.get('bedrooms'):
            response += f"Bedrooms: {prop['bedrooms']}\n"
        if prop.get('bathrooms'):
            response += f"Bathrooms: {prop['bathrooms']}\n"
        if prop.get('size_sqft'):
            response += f"Size: {prop['size_sqft']} sqft\n"

        if prop.get('key_selling_points'):
            response += f"\n{prop['key_selling_points']}"

        return response

    elif format_type == "list":
        response = f"I found {len(properties)} {'property' if len(properties) == 1 else 'properties'}:\n\n"

        for i, prop in enumerate(properties, 1):
            response += f"{i}. {prop['title']}\n"
            response += f"   {prop['location']} - ${prop['price']:,.0f}\n"
            if prop.get('bedrooms'):
                response += f"   {prop['bedrooms']} bed"
                if prop.get('bathrooms'):
                    response += f", {prop['bathrooms']} bath"
                response += "\n"
            response += "\n"

        return response

    elif format_type == "summary":
        response = ""
        for i, prop in enumerate(properties, 1):
            response += f"{i}. {prop['title']} - {prop['location']} - ${prop['price']:,.0f}\n"
        return response

    return ""


if __name__ == "__main__":
    # Test
    import sys
    if len(sys.argv) < 2:
        print("Usage: python property_lookup.py <agent_id> [location]")
        sys.exit(1)

    agent_id = sys.argv[1]
    location = sys.argv[2] if len(sys.argv) > 2 else None

    properties = search_properties(agent_id, location=location)
    print(format_property_response(properties, format_type="list"))
