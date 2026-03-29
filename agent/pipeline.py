import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataclasses import dataclass
from agent.step1_openai import parse_incident, ParsedIncident
from agent.step2_openai import research_incident, EnrichedContext
from agent.step3_openai import analyze_incident, RootCauseAnalysis
from agent.step4_openai import generate_brief, IncidentBrief


class PipelineStepError(Exception):
    """Raised when a specific pipeline step fails."""
    def __init__(self, step: int, step_name: str, original_error: Exception):
        self.step = step
        self.step_name = step_name
        self.original_error = original_error
        super().__init__(f"Step {step} ({step_name}) failed: {original_error}")


@dataclass
class PipelineResult:
    parsed:   ParsedIncident
    context:  EnrichedContext
    analysis: RootCauseAnalysis
    brief:    IncidentBrief


def run_pipeline(
    incident_text: str,
    status_callback=None
) -> PipelineResult:
    """
    Master orchestrator — runs all 4 steps in sequence.
    Raises PipelineStepError with the step number and name if any step fails.
    """

    def update(step: int, message: str):
        if status_callback:
            status_callback(step, message)
        else:
            print(f"  [Step {step}/4] {message}")

    # Step 1 — Parse
    update(1, "Parsing incident report...")
    try:
        parsed = parse_incident(incident_text)
    except ValueError as e:
        raise PipelineStepError(1, "Incident Parser", e)
    except Exception as e:
        raise PipelineStepError(1, "Incident Parser", e)
    update(1, f"Done — {parsed.incident_type}, severity {parsed.severity}/5")

    # Step 2 — Research
    update(2, "Researching context and precedents...")
    try:
        context = research_incident(parsed)
    except ValueError as e:
        raise PipelineStepError(2, "Context Researcher", e)
    except Exception as e:
        raise PipelineStepError(2, "Context Researcher", e)
    update(2, f"Done — confidence: {context.confidence_level}")

    # Step 3 — Analyze
    update(3, "Running root cause analysis...")
    try:
        analysis = analyze_incident(parsed, context)
    except ValueError as e:
        raise PipelineStepError(3, "Root Cause Analyzer", e)
    except Exception as e:
        raise PipelineStepError(3, "Root Cause Analyzer", e)
    update(3, f"Done — {analysis.vulnerability_type}")

    # Step 4 — Brief
    update(4, "Generating incident brief...")
    try:
        brief = generate_brief(parsed, context, analysis)
    except ValueError as e:
        raise PipelineStepError(4, "Brief Generator", e)
    except Exception as e:
        raise PipelineStepError(4, "Brief Generator", e)
    update(4, f"Done — severity: {brief.severity_level}")

    return PipelineResult(
        parsed=parsed,
        context=context,
        analysis=analysis,
        brief=brief
    )


if __name__ == "__main__":
    from tests.test_incidents import TEST_INCIDENTS

    incident = TEST_INCIDENTS[0]
    print("=" * 60)
    print("PIPELINE ORCHESTRATOR TEST")
    print(f"Incident: {incident['id']} — {incident['label']}")
    print("=" * 60)

    try:
        result = run_pipeline(incident["text"])
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)
        print(f"  Incident ID:   {result.brief.incident_id}")
        print(f"  Severity:      {result.brief.severity_level}")
        print(f"  Vulnerability: {result.analysis.vulnerability_type}")
        print(f"  Recovery:      {result.analysis.severity_assessment.recovery_timeline}")
        print(f"  Financial:     "
              f"${result.brief.financial_exposure.minimum_usd:,} – "
              f"${result.brief.financial_exposure.maximum_usd:,}")
        print(f"\n  Executive summary:")
        print(f"  {result.brief.executive_summary}")
        top = result.brief.immediate_actions[0]
        print(f"\n  Top action: [{top.priority}] {top.action}")
        print("\nAll 4 steps chained and working.")

    except PipelineStepError as e:
        print(f"\nPipeline failed at Step {e.step} ({e.step_name})")
        print(f"Error: {e.original_error}")
    except Exception as e:
        print(f"\nUnexpected error: {e}")