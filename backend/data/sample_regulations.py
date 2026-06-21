"""
Illustrative placeholder safety-guideline snippets for prototype RAG grounding.

NOT verified or official AFS / Arbetsmiljöverket text. A production deployment
must ingest licensed, current, official regulation corpora instead of these
fictional demo snippets.
"""

SAMPLE_REGULATIONS: list[str] = [
    (
        "[DEMO-AFS 4:1] Employers shall ensure that scaffolding is erected, "
        "modified, and dismantled only by competent persons. Scaffolding must "
        "be inspected before each work shift and after any event that could "
        "affect structural integrity. Guardrails, toe boards, and safe access "
        "ladders are mandatory on platforms above 2 metres."
    ),
    (
        "[DEMO-AFS 4:2] Fall protection is required when there is a risk of "
        "falling more than 2 metres, or when working over dangerous machinery "
        "or hazardous substances regardless of height. Acceptable measures "
        "include guardrails, collective protection, or personal fall-arrest "
        "systems inspected before use."
    ),
    (
        "[DEMO-AFS 4:3] Walkways and traffic routes must be kept free of ice, "
        "snow, and slip hazards. During winter conditions, employers shall "
        "implement gritting, heating, or rerouting so that employees and "
        "visitors can pass safely. Temporary signage must warn of residual risk."
    ),
    (
        "[DEMO-AFS 4:4] Personal protective equipment (PPE) shall be provided "
        "at no cost when risks cannot be eliminated or sufficiently reduced by "
        "other means. PPE must be suitable for the hazard, correctly fitted, "
        "and maintained. Training on correct use is mandatory before work begins."
    ),
    (
        "[DEMO-AFS 4:5] Lockout/tagout (LOTO) procedures are required before "
        "maintenance or repair of machinery where unexpected energisation could "
        "cause injury. Each energy source must be isolated, locked, and verified "
        "de-energised. Only the authorised worker may remove their lock."
    ),
    (
        "[DEMO-AFS 4:6] Chemical storage areas must have adequate ventilation, "
        "secondary containment, and clearly labelled containers. Safety data "
        "sheets must be accessible to all workers handling the substances. "
        "Incompatible chemicals shall not be stored together."
    ),
    (
        "[DEMO-AFS 4:7] Forklift and mobile-plant traffic routes must be "
        "segregated from pedestrian walkways where reasonably practicable. "
        "Speed limits, visibility aids, and audible warnings are required in "
        "areas where vehicles and pedestrians may interact."
    ),
    (
        "[DEMO-AFS 4:8] Excavation work deeper than 1.3 metres requires a "
        "written risk assessment, shoring or sloping to prevent collapse, and "
        "safe means of entry and exit. Underground services must be located "
        "before digging begins."
    ),
    (
        "[DEMO-AFS 4:9] Noise exposure above 80 dB(A) requires a noise survey "
        "and hearing-conservation programme. Engineering controls and job rotation "
        "shall be prioritised over hearing protection alone."
    ),
    (
        "[DEMO-AFS 4:10] Emergency evacuation routes must remain unobstructed "
        "and clearly marked. Employers shall conduct fire drills at least twice "
        "per year and ensure extinguishers are inspected monthly."
    ),
]
