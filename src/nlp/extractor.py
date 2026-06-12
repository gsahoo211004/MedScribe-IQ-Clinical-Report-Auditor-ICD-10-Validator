import spacy
from negate import Negator

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Initialize negation detector
negator = Negator()

# Biomedical entity dictionary
# Key = term to look for, Value = entity label
MEDICAL_TERMS = {
    # Cardiovascular
    "hypertension": "DISEASE",
    "tachycardia": "DISEASE",
    "bradycardia": "DISEASE",
    "heart failure": "DISEASE",
    "atrial fibrillation": "DISEASE",
    "chest pain": "SYMPTOM",

    # Metabolic
    "diabetes": "DISEASE",
    "obesity": "DISEASE",
    "hypothyroidism": "DISEASE",
    "hyperthyroidism": "DISEASE",

    # Respiratory
    "asthma": "DISEASE",
    "pneumonia": "DISEASE",
    "copd": "DISEASE",
    "bronchitis": "DISEASE",

    # Neurological
    "migraine": "DISEASE",
    "seizure": "SYMPTOM",
    "stroke": "DISEASE",
    "dementia": "DISEASE",

    # Symptoms
    "fever": "SYMPTOM",
    "nausea": "SYMPTOM",
    "fatigue": "SYMPTOM",
    "shortness of breath": "SYMPTOM",
    "headache": "SYMPTOM",
    "dizziness": "SYMPTOM",

    # Medications
    "metformin": "MEDICATION",
    "insulin": "MEDICATION",
    "aspirin": "MEDICATION",
    "lisinopril": "MEDICATION",
}


def extract_entities(text: str) -> list[dict]:
    """
    Extract medical entities from clinical text.
    Returns a list of dicts with entity info including negation status.
    """
    text_lower = text.lower()
    doc = nlp(text_lower)
    found_entities = []

    for term, label in MEDICAL_TERMS.items():
        if term in text_lower:
            # Find the sentence containing this term
            is_negated = False
            for sent in doc.sents:
                if term in sent.text:
                    # Check negation on this sentence
                    negated_sent = negator.negate_sentence(sent.text)
                    # If negating produces the same sentence, term is already negated
                    # Simpler approach: check for negation words near the term
                    negation_words = [
                        "no", "not", "without", "denies", "denied",
                        "negative", "absent", "no signs of", "no evidence of"
                    ]
                    sentence_text = sent.text.lower()
                    for neg_word in negation_words:
                        if neg_word in sentence_text:
                            # Check if neg word appears before the term
                            neg_pos = sentence_text.find(neg_word)
                            term_pos = sentence_text.find(term)
                            if neg_pos < term_pos:
                                is_negated = True
                                break
                    break

            found_entities.append({
                "entity_text": term,
                "entity_label": label,
                "is_negated": "Yes" if is_negated else "No"
            })

    return found_entities


if __name__ == "__main__":
    # Quick test
    sample = (
        "Patient presents with hypertension and tachycardia. "
        "No signs of diabetes. Denies fever or headache. "
        "Currently on metformin and aspirin."
    )

    print("Input text:")
    print(sample)
    print("\nExtracted entities:")
    entities = extract_entities(sample)
    for e in entities:
        print(f"  {e['entity_text']:25} | {e['entity_label']:10} | Negated: {e['is_negated']}")