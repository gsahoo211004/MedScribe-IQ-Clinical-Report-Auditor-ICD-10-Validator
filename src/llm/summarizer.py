import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate_audit_summary(
    clinical_text: str,
    audit_results: list[dict]
) -> str:
    """
    Generate a plain-English audit summary from ICD-10 validation results.
    Uses Gemini to produce a clinical audit report.
    """

    validated = [r for r in audit_results if r["status"] == "VALIDATED"]
    negated = [r for r in audit_results if r["status"] == "NEGATED"]
    flagged = [r for r in audit_results if r["status"] == "FLAGGED"]
    api_validated = [r for r in audit_results if r["status"] == "VALIDATED_VIA_API"]

    validated_text = "\n".join(
        f"  - {r['entity_text']} → {r['suggested_icd10']} ({r['icd10_description']})"
        for r in validated + api_validated
    ) or "  None"

    negated_text = "\n".join(
        f"  - {r['entity_text']} (negated — condition not present)"
        for r in negated
    ) or "  None"

    flagged_text = "\n".join(
        f"  - {r['entity_text']} (no ICD-10 match found)"
        for r in flagged
    ) or "  None"

    prompt = f"""
You are a clinical audit assistant specialized in medical billing compliance.

A clinical NLP pipeline has processed the following discharge summary and
extracted medical entities with ICD-10 validation results.

ORIGINAL CLINICAL TEXT:
{clinical_text}

ICD-10 VALIDATION RESULTS:

VALIDATED CONDITIONS (present and coded):
{validated_text}

NEGATED CONDITIONS (mentioned but NOT present in patient):
{negated_text}

FLAGGED CONDITIONS (no ICD-10 match found):
{flagged_text}

Generate a concise clinical audit report (3-5 sentences) that:
1. Summarizes what conditions were found and validated
2. Highlights negated conditions that should NOT be billed
3. Flags any coding gaps or risks
4. Ends with a clear billing recommendation

Write in professional clinical language suitable for a medical billing auditor.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"LLM summary unavailable: {str(e)}"


if __name__ == "__main__":
    sample_text = (
        "Patient presents with hypertension and tachycardia. "
        "No signs of diabetes. Denies fever or headache. "
        "Currently on metformin and aspirin."
    )

    sample_results = [
        {"entity_text": "hypertension", "suggested_icd10": "I10",
         "icd10_description": "Essential hypertension", "status": "VALIDATED"},
        {"entity_text": "tachycardia", "suggested_icd10": "R00.0",
         "icd10_description": "Tachycardia, unspecified", "status": "VALIDATED"},
        {"entity_text": "diabetes", "suggested_icd10": "N/A",
         "icd10_description": "Condition negated", "status": "NEGATED"},
        {"entity_text": "metformin", "suggested_icd10": "Z79.84",
         "icd10_description": "Long-term use of oral hypoglycemic drugs", "status": "VALIDATED"},
        {"entity_text": "fever", "suggested_icd10": "N/A",
         "icd10_description": "Condition negated", "status": "NEGATED"},
    ]

    print("Generating LLM audit summary...\n")
    summary = generate_audit_summary(sample_text, sample_results)
    print("AUDIT SUMMARY:")
    print("-" * 60)
    print(summary)