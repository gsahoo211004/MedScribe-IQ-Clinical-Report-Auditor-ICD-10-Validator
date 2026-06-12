import mlflow
import mlflow.tracking
from datetime import datetime, UTC


# Set MLflow tracking URI — stores runs locally in mlruns/ folder
mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("medscribe-iq-pipeline")


def log_pipeline_run(
    clinical_text: str,
    entities: list[dict],
    audit_results: list[dict],
    processing_time: float
) -> str:
    """
    Log a complete pipeline run to MLflow.
    Returns the run_id for reference.
    """

    validated = [r for r in audit_results if r["status"] == "VALIDATED"]
    negated = [r for r in audit_results if r["status"] == "NEGATED"]
    flagged = [r for r in audit_results if r["status"] == "FLAGGED"]
    api_validated = [r for r in audit_results if r["status"] == "VALIDATED_VIA_API"]

    with mlflow.start_run():
        # Log input parameters
        mlflow.log_param("report_length_chars", len(clinical_text))
        mlflow.log_param("run_timestamp", datetime.now(UTC).isoformat())

        # Log pipeline metrics
        mlflow.log_metric("total_entities_extracted", len(entities))
        mlflow.log_metric("validated_count", len(validated) + len(api_validated))
        mlflow.log_metric("negated_count", len(negated))
        mlflow.log_metric("flagged_count", len(flagged))
        mlflow.log_metric("processing_time_seconds", processing_time)

        # Log validation rate
        if len(entities) > 0:
            validation_rate = (len(validated) + len(api_validated)) / len(entities)
            mlflow.log_metric("validation_rate", round(validation_rate, 3))

        # Log entity type breakdown
        disease_count = sum(1 for e in entities if e["entity_label"] == "DISEASE")
        symptom_count = sum(1 for e in entities if e["entity_label"] == "SYMPTOM")
        medication_count = sum(1 for e in entities if e["entity_label"] == "MEDICATION")

        mlflow.log_metric("disease_entities", disease_count)
        mlflow.log_metric("symptom_entities", symptom_count)
        mlflow.log_metric("medication_entities", medication_count)

        run_id = mlflow.active_run().info.run_id
        print(f"MLflow run logged: {run_id}")
        return run_id


if __name__ == "__main__":
    import time

    # Simulate a pipeline run
    sample_text = (
        "Patient presents with hypertension and tachycardia. "
        "No signs of diabetes. Denies fever. Currently on metformin."
    )

    sample_entities = [
        {"entity_text": "hypertension", "entity_label": "DISEASE",    "is_negated": "No"},
        {"entity_text": "tachycardia",  "entity_label": "DISEASE",    "is_negated": "No"},
        {"entity_text": "diabetes",     "entity_label": "DISEASE",    "is_negated": "Yes"},
        {"entity_text": "fever",        "entity_label": "SYMPTOM",    "is_negated": "Yes"},
        {"entity_text": "metformin",    "entity_label": "MEDICATION", "is_negated": "No"},
    ]

    sample_audit = [
        {"entity_text": "hypertension", "suggested_icd10": "I10",    "status": "VALIDATED"},
        {"entity_text": "tachycardia",  "suggested_icd10": "R00.0",  "status": "VALIDATED"},
        {"entity_text": "diabetes",     "suggested_icd10": "N/A",    "status": "NEGATED"},
        {"entity_text": "fever",        "suggested_icd10": "N/A",    "status": "NEGATED"},
        {"entity_text": "metformin",    "suggested_icd10": "Z79.84", "status": "VALIDATED"},
    ]

    start = time.time()
    time.sleep(0.5)  # Simulate processing time
    elapsed = round(time.time() - start, 3)

    run_id = log_pipeline_run(sample_text, sample_entities, sample_audit, elapsed)
    print(f"Run ID: {run_id}")
    print("\nTo view MLflow UI, run: mlflow ui")