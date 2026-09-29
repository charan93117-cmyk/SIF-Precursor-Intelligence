"""Dataframe-based orchestration for the safety-report prototype."""

if __package__:
    from .input_validation import validate_reports
    from .preprocessing import preprocess_dataframe
    from .entity_extraction import extract_from_dataframe
    from .sif_detector import apply_sif_detection
    from .risk_scoring import apply_risk_scoring
    from .pattern_analysis import analyze_patterns
else:
    from input_validation import validate_reports
    from preprocessing import preprocess_dataframe
    from entity_extraction import extract_from_dataframe
    from sif_detector import apply_sif_detection
    from risk_scoring import apply_risk_scoring
    from pattern_analysis import analyze_patterns


def analyze_reports(df):
    """Validate and analyze a dataframe without modifying its input.

    Returns:
        analyzed dataframe, dictionary of the seven descriptive tables
    """
    validation = validate_reports(df)
    validation.raise_for_errors()

    analyzed = preprocess_dataframe(df)
    analyzed = extract_from_dataframe(analyzed)
    analyzed = apply_sif_detection(analyzed)
    analyzed = apply_risk_scoring(analyzed)

    patterns = analyze_patterns(analyzed)
    return analyzed, patterns
