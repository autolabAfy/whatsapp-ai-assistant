# Property Retrieval Logic

## Goal
Match user inquiries to the agent's property listings accurately and safely.

## Core Principles

1. **No hallucination** - Only return properties that exist in the database
2. **No assumptions** - If uncertain, ask clarifying questions
3. **Agent-scoped only** - Only query properties belonging to the current agent
4. **Structured data only** - No external sources, no web search

## Query Flow

### 1. Intent Detection
Identify if message contains property inquiry:
- "show me properties"
- "what's available in [location]"
- "I'm looking for 2 bedroom"
- "how much is [property name]"
- "any condos under $500k"

### 2. Extract Parameters
From user message, extract:
- **Location** (area, district, city)
- **Property type** (condo, HDB, landed, commercial)
- **Price range** (min, max)
- **Bedrooms** (number)
- **Availability** (immediate, next month, etc.)

### 3. Query Database
```sql
SELECT * FROM properties
WHERE agent_id = {current_agent_id}
  AND (location ILIKE %{location}% OR {location} IS NULL)
  AND (type = {type} OR {type} IS NULL)
  AND (price BETWEEN {min_price} AND {max_price} OR {price} IS NULL)
  AND (bedrooms = {bedrooms} OR {bedrooms} IS NULL)
  AND availability = 'available'
ORDER BY relevance_score DESC
LIMIT 3
```

### 4. Response Strategy

#### Exact match found (1 property)
```
I found this property that matches:

[Property Name]
- Type: [type]
- Location: [location]
- Price: $[price]
- Bedrooms: [bedrooms]
- [key_selling_points]

Would you like to schedule a viewing?
```

#### Multiple matches (2-3 properties)
```
I found [N] properties that match:

1. [Property Name] - [location] - $[price]
2. [Property Name] - [location] - $[price]
3. [Property Name] - [location] - $[price]

Which one would you like to know more about?
```

#### No exact match
**Option A: Close matches exist**
```
I don't have an exact match, but here are similar properties:

[List close matches with what's different]

Would any of these work for you?
```

**Option B: No close matches**
```
I don't currently have properties matching those criteria.

Would you like me to:
- Show what's available in nearby areas?
- Adjust your price range?
- Notify you when something matching becomes available?
```

### 5. Disambiguation
If query is ambiguous:
```
Just to make sure I find the right property for you:
- Are you looking in [area A] or [area B]?
- What's your budget range?
- How many bedrooms do you need?
```

## Guardrails

### NEVER do this:
- Invent property details
- Provide pricing from external sources
- Promise availability without checking database
- Share properties from other agents
- Recommend properties outside agent's portfolio

### ALWAYS do this:
- Query only agent's properties
- Return structured property data
- Acknowledge uncertainty
- Ask clarifying questions when needed

## Tools

- `execution/property_lookup.py` - Main query function
- `execution/extract_property_intent.py` - Parse user inquiry
- `execution/match_properties.py` - Scoring and ranking

## Database Schema

### Properties table
```
property_id (PK)
agent_id (FK)
title
type (ENUM: condo, HDB, landed, commercial)
location
price (numeric)
availability (ENUM: available, pending, sold)
bedrooms (int)
bathrooms (int)
size_sqft (int)
amenities (text[])
key_selling_points (text)
viewing_instructions (text)
created_at
updated_at
```

## Edge Cases

### User asks about sold property
```
That property has been sold, but I have similar options:
[Show available alternatives]
```

### User asks about future availability
```
I don't have visibility on future listings yet, but I can:
- Show you what's available now
- Take note of your preferences for when something comes up
```

### User asks for price negotiation
**Escalate to HUMAN immediately**
```
Let me connect you with the agent directly to discuss pricing.
[Auto-switch to HUMAN mode]
```

## Logging

Log every property query:
- User query text
- Extracted parameters
- Properties returned
- User response (if any)
