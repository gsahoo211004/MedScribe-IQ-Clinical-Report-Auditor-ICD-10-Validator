import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Local ICD-10 lookup dictionary (fallback + speed)
ICD10_LOCAL_DB = {
    # Cardiovascular
    "hypertension":       {"code": "I10",     "description": "Essential (primary) hypertension"},
    "tachycardia":        {"code": "R00.0",   "description": "Tachycardia, unspecified"},
    "bradycardia":        {"code": "R00.1",   "description": "Bradycardia, unspecified"},
    "heart failure":      {"code": "I50.9",   "description": "Heart failure, unspecified"},
    "atrial fibrillation":{"code": "I48.91",  "description": "Unspecified atrial fibrillation"},
    "chest pain":         {"code": "R07.9",   "description": "Chest pain, unspecified"},

    # Metabolic
    "diabetes":           {"code": "E11.9",   "description": "Type 2 diabetes mellitus without complications"},
    "obesity":            {"code": "E66.9",   "description": "Obesity, unspecified"},
    "hypothyroidism":     {"code": "E03.9",   "description": "Hypothyroidism, unspecified"},
    "hyperthyroidism":    {"code": "E05.90",  "description": "Thyrotoxicosis, unspecified"},

    # Respiratory
    "asthma":             {"code": "J45.909", "description": "Unspecified asthma, uncomplicated"},
    "pneumonia":          {"code": "J18.9",   "description": "Pneumonia, unspecified organism"},
    "copd":               {"code": "J44.9",   "description": "COPD, unspecified"},
    "bronchitis":         {"code": "J40",     "description": "Bronchitis, not specified as acute or chronic"},

    # Neurological
    "migraine":           {"code": "G43.909", "description": "Migraine, unspecified"},
    "seizure":            {"code": "R56.9",   "description": "Unspecified convulsions"},
    "stroke":             {"code": "I63.9",   "description": "Cerebral infarction, unspecified"},
    "dementia":           {"code": "F03.90",  "description": "Unspecified dementia without behavioral disturbance"},

    # Symptoms
    "fever":              {"code": "R50.9",   "description": "Fever, unspecified"},
    "nausea":             {"code": "R11.0",   "description": "Nausea"},
    "fatigue":            {"code": "R53.83",  "description": "Other fatigue"},
    "shortness of breath":{"code": "R06.00",  "description": "Dyspnea, unspecified"},
    "headache":           {"code": "R51.9",   "description": "Headache, unspecified"},
    "dizziness":          {"code": "R42",     "description": "Dizziness and giddiness"},

    # Medications
    "metformin":          {"code": "Z79.84",  "description": "Long-term (current) use of oral hypoglycemic drugs"},
    "insulin":            {"code": "Z79.4",   "description": "Long-term (current) use of insulin"},
    "aspirin":            {"code": "Z79.82",  "description": "Long-term (current) use of aspirin"},
    "lisinopril":         {"code": "Z79.899", "description": "Other long-term (current) drug therapy"},
}


def get_who_token() -> str | None:
    """Get access token from WHO ICD API."""
    client_id = os.getenv("ICD_CLIENT_ID")
    client_secret = os.getenv("ICD_CLIENT_SECRET")

    if not client_id or not client_secret:
        return None

    try:
        response = requests.post(
            "https://icdaccessmanagement.who.int/connect/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
                "scope": "icdapi_access",
            },
            timeout=10
        )
        return response.json().get("access_token")
    except Exception as e:
        print(f"WHO API token error: {e}")
        return None


def validate_with_who_api(term: str, token: str) -> dict | None:
    """Look up a term in the WHO ICD-10 API."""
    try:
        response = requests.get(
            "https://id.who.int/icd/release/10/2019/search",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Accept-Language": "en",
                "API-Version": "v2"
            },
            params={"q": term, "subtreeFilterUsesFoundationDescendants": "false"},
            timeout=10
        )
        data = response.json()
        if data.get("destinationEntities"):
            top = data["destinationEntities"][0]
            return {
                "code": top.get("theCode", "UNKNOWN"),
                "description": top.get("title", "No description")
            }
    except Exception as e:
        print(f"WHO API lookup error: {e}")
    return None


def validate_entities(entities: list[dict]) -> list[dict]:
    """
    Validate extracted entities against ICD-10 codes.
    Returns audit results with validation status.
    """
    token = get_who_token()
    audit_results = []

    for entity in entities:
        term = entity["entity_text"]
        is_negated = entity["is_negated"]
        label = entity["entity_label"]

        # Skip negated entities — not present in patient
        if is_negated == "Yes":
            audit_results.append({
                "entity_text": term,
                "suggested_icd10": "N/A",
                "icd10_description": "Condition negated — not present",
                "confidence": 0.0,
                "status": "NEGATED"
            })
            continue

        # Try local DB first
        local_match = ICD10_LOCAL_DB.get(term)

        if local_match:
            audit_results.append({
                "entity_text": term,
                "suggested_icd10": local_match["code"],
                "icd10_description": local_match["description"],
                "confidence": 0.95,
                "status": "VALIDATED"
            })

        # Try WHO API if no local match and token available
        elif token:
            who_match = validate_with_who_api(term, token)
            if who_match:
                audit_results.append({
                    "entity_text": term,
                    "suggested_icd10": who_match["code"],
                    "icd10_description": who_match["description"],
                    "confidence": 0.80,
                    "status": "VALIDATED_VIA_API"
                })
            else:
                audit_results.append({
                    "entity_text": term,
                    "suggested_icd10": "UNKNOWN",
                    "icd10_description": "No ICD-10 match found",
                    "confidence": 0.0,
                    "status": "FLAGGED"
                })
        else:
            audit_results.append({
                "entity_text": term,
                "suggested_icd10": "UNKNOWN",
                "icd10_description": "No ICD-10 match found",
                "confidence": 0.0,
                "status": "FLAGGED"
            })

    return audit_results


if __name__ == "__main__":
    # Test with sample entities
    sample_entities = [
        {"entity_text": "hypertension", "entity_label": "DISEASE", "is_negated": "No"},
        {"entity_text": "tachycardia",  "entity_label": "DISEASE", "is_negated": "No"},
        {"entity_text": "diabetes",     "entity_label": "DISEASE", "is_negated": "Yes"},
        {"entity_text": "metformin",    "entity_label": "MEDICATION", "is_negated": "No"},
        {"entity_text": "fever",        "entity_label": "SYMPTOM", "is_negated": "Yes"},
    ]

    print("ICD-10 Validation Results:")
    print("-" * 70)
    results = validate_entities(sample_entities)
    for r in results:
        print(f"  {r['entity_text']:25} | {r['suggested_icd10']:10} | {r['status']}")