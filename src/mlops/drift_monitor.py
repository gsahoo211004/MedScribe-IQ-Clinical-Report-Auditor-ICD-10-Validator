import pandas as pd
from evidently import Dataset, DataDefinition, Report
from evidently.presets import DataDriftPreset
import os


def build_entity_dataframe(audit_results: list[dict]) -> pd.DataFrame:
    """Convert audit results into a DataFrame for Evidently analysis."""
    rows = []
    for r in audit_results:
        rows.append({
            "confidence": r.get("confidence", 0.0),
            "is_negated": 1 if r["status"] == "NEGATED" else 0,
            "is_validated": 1 if r["status"] in ["VALIDATED", "VALIDATED_VIA_API"] else 0,
            "is_flagged": 1 if r["status"] == "FLAGGED" else 0,
        })
    return pd.DataFrame(rows)


def run_drift_report(
    reference_results: list[dict],
    current_results: list[dict],
    output_path: str = "reports/drift_report.html"
) -> str:
    """
    Compare reference (baseline) audit results against current run.
    Generates an HTML drift report.
    """
    os.makedirs("reports", exist_ok=True)

    reference_df = build_entity_dataframe(reference_results)
    current_df = build_entity_dataframe(current_results)

    definition = DataDefinition(
        numerical_columns=["confidence", "is_negated", "is_validated", "is_flagged"]
    )

    reference_dataset = Dataset.from_pandas(reference_df, data_definition=definition)
    current_dataset = Dataset.from_pandas(current_df, data_definition=definition)

    report = Report(metrics=[DataDriftPreset()])
    result = report.run(reference_dataset, current_dataset)
    result.save_html(output_path)

    print(f"Drift report saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    reference = [
        {"entity_text": "hypertension", "status": "VALIDATED",  "confidence": 0.95},
        {"entity_text": "tachycardia",  "status": "VALIDATED",  "confidence": 0.95},
        {"entity_text": "diabetes",     "status": "NEGATED",    "confidence": 0.0},
        {"entity_text": "metformin",    "status": "VALIDATED",  "confidence": 0.95},
        {"entity_text": "fever",        "status": "NEGATED",    "confidence": 0.0},
    ]

    current = [
        {"entity_text": "hypertension", "status": "VALIDATED",  "confidence": 0.95},
        {"entity_text": "pneumonia",    "status": "FLAGGED",    "confidence": 0.0},
        {"entity_text": "copd",         "status": "FLAGGED",    "confidence": 0.0},
        {"entity_text": "stroke",       "status": "VALIDATED",  "confidence": 0.80},
        {"entity_text": "dementia",     "status": "FLAGGED",    "confidence": 0.0},
    ]

    path = run_drift_report(reference, current)
    print(f"Open {path} in your browser to view the report.")