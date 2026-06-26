"""
llm/prompts.py
LangChain PromptTemplate definitions for the Geological AI Assistant.
"""

from langchain.prompts import PromptTemplate


# ---------------------------------------------------------------------------
# System Persona
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = PromptTemplate(
    input_variables=["context"],
    template="""You are GeoBot, an expert geological AI assistant specializing in
lithology classification, mineralogy, and drill core analysis. You have deep
knowledge of igneous, sedimentary, and metamorphic rocks, as well as economic
geology and mining exploration.

Your role is to:
- Explain rock and mineral classifications clearly and accurately
- Help geologists interpret drill core samples
- Provide geological context for classification results
- Generate professional geological reports
- Answer questions about geological formations and processes

Always be precise, professional, and cite relevant geological characteristics
when making assessments. Use correct geological terminology while also
explaining concepts in accessible language.

Context information:
{context}

Respond in a clear, professional geological style.""",
)


# ---------------------------------------------------------------------------
# Prediction Explanation
# ---------------------------------------------------------------------------

PREDICTION_EXPLANATION_PROMPT = PromptTemplate(
    input_variables=[
        "rock_type",
        "confidence",
        "top_predictions",
        "minerals_detected",
        "rock_description",
        "formation_context",
    ],
    template="""You are a senior geologist analyzing a drill core sample classification result.

CLASSIFICATION RESULT:
- Primary Rock Type: {rock_type}
- Confidence: {confidence:.1f}%
- Alternative Predictions: {top_predictions}
- Detected Minerals: {minerals_detected}

GEOLOGICAL CONTEXT:
{rock_description}

FORMATION CONTEXT:
{formation_context}

Provide a detailed geological explanation of this classification result. Include:
1. Why this rock type was identified (key diagnostic features)
2. What the detected minerals tell us about the rock's origin
3. The geological environment where this rock likely formed
4. Any caveats or reasons for uncertainty (if confidence is below 80%)
5. What additional analysis might confirm the classification

Write in professional geological language suitable for a geological report.""",
)


# ---------------------------------------------------------------------------
# Full Geological Report Generation
# ---------------------------------------------------------------------------

REPORT_GENERATION_PROMPT = PromptTemplate(
    input_variables=[
        "rock_type",
        "confidence",
        "minerals_detected",
        "borehole_id",
        "depth_from",
        "depth_to",
        "sample_id",
        "rock_description",
        "formation_info",
        "date",
        "project_name",
    ],
    template="""Generate a comprehensive geological classification report for a drill core sample.

SAMPLE DETAILS:
- Project: {project_name}
- Borehole ID: {borehole_id}
- Sample ID: {sample_id}
- Depth Interval: {depth_from}m – {depth_to}m
- Date: {date}

CLASSIFICATION RESULTS:
- Rock Type: {rock_type}
- Confidence Score: {confidence:.1f}%
- Detected Minerals: {minerals_detected}

GEOLOGICAL REFERENCE DATA:
{rock_description}

FORMATION INFORMATION:
{formation_info}

Write a full professional geological report in markdown format with the following sections:
1. Executive Summary
2. Sample Information
3. Classification Results
4. Mineralogical Assessment
5. Geological Interpretation
6. Economic Significance
7. Recommendations
8. References

Use professional geological terminology and provide actionable insights.""",
)


# ---------------------------------------------------------------------------
# Geological Q&A
# ---------------------------------------------------------------------------

GEOLOGICAL_QA_PROMPT = PromptTemplate(
    input_variables=["question", "context", "knowledge_base"],
    template="""You are an expert geological assistant. Answer the following geological
question accurately and thoroughly, using the provided context and your geological knowledge.

QUESTION:
{question}

RELEVANT CONTEXT FROM DOCUMENTS:
{context}

GEOLOGICAL KNOWLEDGE BASE:
{knowledge_base}

Provide a comprehensive answer that:
1. Directly addresses the question
2. Cites relevant geological principles
3. Provides examples where appropriate
4. Notes any limitations or uncertainties
5. Suggests follow-up investigations if relevant

Answer in clear, professional geological language:""",
)


# ---------------------------------------------------------------------------
# Mineral Explanation
# ---------------------------------------------------------------------------

MINERAL_EXPLANATION_PROMPT = PromptTemplate(
    input_variables=["mineral_name", "mineral_data", "associated_rocks", "context"],
    template="""Provide a detailed geological explanation of the mineral {mineral_name}.

MINERAL DATA:
{mineral_data}

ASSOCIATED ROCK TYPES:
{associated_rocks}

SAMPLE CONTEXT:
{context}

Explain:
1. Chemical composition and crystal structure
2. Physical properties (hardness, cleavage, color, luster)
3. Formation conditions and geological occurrence
4. How to identify this mineral in hand specimen
5. Its significance when found in a drill core sample
6. Associated minerals and what they indicate about the geological environment
7. Economic importance and any associated mineral deposits

Write in a clear, informative style suitable for both geologists and non-specialists:""",
)


# ---------------------------------------------------------------------------
# Geological Formation Explanation
# ---------------------------------------------------------------------------

FORMATION_EXPLANATION_PROMPT = PromptTemplate(
    input_variables=["formation_name", "formation_data", "region_context"],
    template="""Provide a detailed explanation of the {formation_name} geological formation.

FORMATION DATA:
{formation_data}

REGIONAL CONTEXT:
{region_context}

Explain:
1. Definition and key characteristics of this formation type
2. How this formation develops (geological processes involved)
3. Typical rock types and minerals found
4. Structural features and spatial extent
5. Tectonic setting and plate tectonic context
6. Exploration significance (what resources are typically associated)
7. Notable world examples of this formation type

Write in professional geological language:""",
)


# ---------------------------------------------------------------------------
# Borehole Summary
# ---------------------------------------------------------------------------

BOREHOLE_SUMMARY_PROMPT = PromptTemplate(
    input_variables=[
        "borehole_id",
        "total_depth",
        "location",
        "date_drilled",
        "lithology_log",
        "dominant_rock_type",
        "rock_type_percentages",
        "minerals_summary",
        "project_name",
    ],
    template="""Generate a professional borehole geological summary report.

BOREHOLE INFORMATION:
- Project: {project_name}
- Borehole ID: {borehole_id}
- Location: {location}
- Total Depth: {total_depth}m
- Date Drilled: {date_drilled}

LITHOLOGICAL LOG SUMMARY:
{lithology_log}

DOMINANT ROCK TYPE: {dominant_rock_type}

ROCK TYPE DISTRIBUTION:
{rock_type_percentages}

MINERALOGICAL SUMMARY:
{minerals_summary}

Generate a comprehensive borehole summary including:
1. Borehole Overview
2. Stratigraphic Column Description
3. Lithological Intervals (depth and rock type)
4. Mineralogical Notes
5. Geological Interpretation
6. Structural Observations
7. Alteration Zones Identified
8. Economic Potential Assessment
9. Recommended Follow-up Action

Format as a professional geological document:""",
)


# ---------------------------------------------------------------------------
# Mining / Exploration Recommendations
# ---------------------------------------------------------------------------

RECOMMENDATION_PROMPT = PromptTemplate(
    input_variables=[
        "rock_type",
        "minerals_detected",
        "confidence",
        "depth",
        "borehole_id",
        "rock_economic_info",
        "associated_deposits",
    ],
    template="""As a senior exploration geologist, provide mining and exploration
recommendations based on the following drill core classification results.

DRILL CORE DATA:
- Borehole: {borehole_id}
- Depth: {depth}m
- Identified Rock Type: {rock_type}
- Confidence: {confidence:.1f}%
- Detected Minerals: {minerals_detected}

ECONOMIC GEOLOGY CONTEXT:
{rock_economic_info}

ASSOCIATED DEPOSIT TYPES:
{associated_deposits}

Provide specific, actionable recommendations covering:
1. Immediate Next Steps (additional sampling, assaying, logging)
2. Geophysical Surveys (what types and why)
3. Geochemical Analysis (which elements to assay and why)
4. Structural Mapping Priorities
5. Resource Estimation Considerations
6. Risk Factors and Uncertainties
7. Priority Ranking (High/Medium/Low) for follow-up actions

Be specific and quantitative where possible. Base recommendations on
the identified lithology and minerals:""",
)


# ---------------------------------------------------------------------------
# Batch Classification Summary
# ---------------------------------------------------------------------------

BATCH_SUMMARY_PROMPT = PromptTemplate(
    input_variables=[
        "total_samples",
        "rock_type_counts",
        "average_confidence",
        "low_confidence_count",
        "dominant_lithology",
        "mineral_frequency",
    ],
    template="""Summarize the results of a batch lithology classification session.

BATCH STATISTICS:
- Total Samples Classified: {total_samples}
- Dominant Lithology: {dominant_lithology}
- Average Confidence: {average_confidence:.1f}%
- Low Confidence Samples (< 60%): {low_confidence_count}

ROCK TYPE DISTRIBUTION:
{rock_type_counts}

MINERAL FREQUENCY:
{mineral_frequency}

Provide a concise geological summary of the batch classification results including:
1. Overall lithological characterization
2. Geological significance of the rock type distribution
3. Quality assessment of the classification (confidence levels)
4. Samples requiring manual review
5. Preliminary geological interpretation

Keep the summary concise but geologically informative:""",
)
