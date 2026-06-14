import os
import json
import urllib.request
from django.conf import settings

def get_gemini_api_key():
    return getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY', ''))

def call_gemini_api(prompt):
    """
    Calls Gemini API using standard urllib to avoid extra package dependencies.
    Returns the string text response, or None if failed/no key.
    """
    api_key = get_gemini_api_key()
    if not api_key:
        return None
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            text_response = res_data['candidates'][0]['content']['parts'][0]['text']
            return text_response
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

def generate_itinerary(destination, budget, duration_days, interests="general"):
    """
    Generates a structured travel itinerary with daily activities and cost estimates.
    """
    prompt = f"""
    You are an expert travel planner. Generate a travel itinerary for a trip to {destination}.
    Budget: ${budget} USD
    Duration: {duration_days} days
    Interests: {interests}
    
    You MUST respond with a valid JSON array of objects. Each object represents one day and MUST have these exact fields:
    - day_number: integer
    - activity_title: string (short, engaging title of main activity)
    - activity_description: string (description of day activities, sights, and logistics)
    - estimated_cost: number (estimated activity cost in USD, do not include dollar signs)
    
    Ensure the sum of estimated costs is within the budget limits. Do not include any markdown format tags other than the JSON itself.
    """
    
    api_response = call_gemini_api(prompt)
    if api_response:
        try:
            cleaned = api_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except Exception:
            pass
            
    # Mock fallback
    mock_itinerary = []
    base_cost_per_day = float(budget) / float(duration_days) * 0.7
    for day in range(1, int(duration_days) + 1):
        mock_itinerary.append({
            "day_number": day,
            "activity_title": f"Explore {destination} - Day {day}",
            "activity_description": f"A beautiful day experiencing the best of {destination} tailored to your interest in {interests}. Includes sightseeing, local meals, and guided walks.",
            "estimated_cost": round(base_cost_per_day, 2)
        })
    return mock_itinerary

def audit_itinerary_feasibility(title, duration_days, itinerary_items):
    """
    Audits a custom-built itinerary for feasibility and logical correctness.
    """
    formatted_items = []
    for item in itinerary_items:
        formatted_items.append(
            f"Day {item.get('day_number')}: {item.get('activity_title')} - {item.get('activity_description')} (Cost: ${item.get('estimated_cost')})"
        )
    items_str = "\n".join(formatted_items)
    
    prompt = f"""
    You are a professional travel auditor. Review the following custom travel itinerary for a {duration_days}-day trip titled '{title}':
    
    {items_str}
    
    Evaluate this itinerary for:
    1. Feasibility: Are the day-by-day activities logically scheduled?
    2. Budget realism: Are the estimated costs realistic?
    3. Safety and logistics: Any warnings or suggestions?
    
    You MUST respond in JSON format with these exact fields:
    - is_feasible: boolean
    - warnings: array of strings (list of potential issues, e.g., 'Day 2 activities are too far apart')
    - suggestions: array of strings (constructive improvements)
    - score: number (overall itinerary score out of 100)
    
    Do not include any markdown code blocks other than the JSON.
    """
    
    api_response = call_gemini_api(prompt)
    if api_response:
        try:
            cleaned = api_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except Exception:
            pass
            
    # Rule-based fallback
    warnings = []
    suggestions = []
    score = 90
    
    if len(itinerary_items) != duration_days:
        warnings.append(f"Itinerary item count ({len(itinerary_items)}) does not match trip duration ({duration_days} days).")
        score -= 20
        
    total_cost = sum(float(item.get('estimated_cost', 0)) for item in itinerary_items)
    if total_cost <= 0:
        warnings.append("Total estimated cost is $0, which is unrealistic for travel.")
        score -= 15
        
    if not warnings:
        suggestions.append("The itinerary looks well balanced. Consider adding airport transfer details on Day 1.")
    else:
        suggestions.append("Adjust your itinerary schedule and day items to ensure they align with your travel dates.")
        
    return {
        "is_feasible": len(warnings) == 0,
        "warnings": warnings,
        "suggestions": suggestions,
        "score": max(10, score)
    }
