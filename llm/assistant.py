"""
llm/assistant.py
GeologicalAssistant — wraps a HuggingFace LLM with a complete rule-based
fallback so the system works with no GPU and no internet access.
"""

import logging
import textwrap
from typing import Optional

from llm.config import LLMConfig, GEOLOGICAL_KNOWLEDGE
from llm.prompts import (
    PREDICTION_EXPLANATION_PROMPT,
    GEOLOGICAL_QA_PROMPT,
    REPORT_GENERATION_PROMPT,
    MINERAL_EXPLANATION_PROMPT,
    FORMATION_EXPLANATION_PROMPT,
    BOREHOLE_SUMMARY_PROMPT,
    RECOMMENDATION_PROMPT,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: confidence label
# ---------------------------------------------------------------------------

def _confidence_label(confidence: float) -> str:
    if confidence >= 90:
        return "Very High"
    if confidence >= 70:
        return "High"
    if confidence >= 50:
        return "Moderate"
    return "Low"


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class GeologicalAssistant:
    """
    AI assistant for geological Q&A, explanation, and report generation.

    Primary mode: HuggingFace Transformers seq2seq model (flan-t5-base by default).
    Fallback mode: Rule-based responses built from GEOLOGICAL_KNOWLEDGE.
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self.model = None
        self.tokenizer = None
        self.use_llm = False
        self._geo = GEOLOGICAL_KNOWLEDGE

        logger.info("Initialising GeologicalAssistant …")
        self.load_model()

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def load_model(self) -> None:
        """Try to load HuggingFace model; silently fall back to rule-based."""
        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            import torch

            logger.info("Loading tokenizer: %s", self.config.tokenizer_name)
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.tokenizer_name,
                use_fast=True,
            )

            logger.info("Loading model: %s", self.config.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.config.model_name,
                torch_dtype=torch.float32,
            )
            self.model.eval()
            self.use_llm = True
            logger.info("HuggingFace model loaded successfully (device=%s).", self.config.device)

        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Could not load HuggingFace model (%s). "
                "Falling back to rule-based responses.",
                exc,
            )
            self.use_llm = False

    # ------------------------------------------------------------------
    # Core generation
    # ------------------------------------------------------------------

    def generate_response(self, prompt: str, max_new_tokens: int = 512) -> str:
        """
        Generate a response from the LLM.

        Returns a plain string response.  If the model is not loaded,
        returns a concise rule-based answer derived from the prompt context.
        """
        if not self.use_llm or self.model is None:
            # Minimalist fallback — callers handle richer rule-based logic
            return (
                "The geological assistant is operating in offline mode. "
                "Please refer to the rule-based analysis below for details."
            )

        try:
            import torch

            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=1024,
            )
            with torch.no_grad():
                output_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    top_k=self.config.top_k,
                    repetition_penalty=self.config.repetition_penalty,
                    do_sample=self.config.do_sample,
                )
            response = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
            return response.strip()

        except Exception as exc:  # noqa: BLE001
            logger.error("LLM generation failed: %s", exc)
            return "Response generation encountered an error. Please try again."

    # ------------------------------------------------------------------
    # Explain prediction
    # ------------------------------------------------------------------

    def explain_prediction(self, prediction_result: dict) -> str:
        """
        Given a prediction dict (rock_type, confidence, top_predictions,
        minerals_detected, …), return a detailed geological explanation.
        """
        rock_type = prediction_result.get("rock_type", "Unknown")
        confidence = float(prediction_result.get("confidence", 0.0))
        top_predictions = prediction_result.get("top_predictions", [])
        minerals_detected = prediction_result.get("minerals_detected", [])

        # Gather description from knowledge base
        rock_info = self._geo["lithology"].get(rock_type, {})
        rock_description = self._format_rock_info(rock_type, rock_info)
        formation_context = rock_info.get("geological_setting", "No formation data available.")

        if self.use_llm:
            prompt = PREDICTION_EXPLANATION_PROMPT.format(
                rock_type=rock_type,
                confidence=confidence,
                top_predictions=", ".join(
                    [f"{p['rock_type']} ({p['confidence']:.1f}%)" for p in top_predictions]
                ) if top_predictions else "N/A",
                minerals_detected=", ".join(minerals_detected) if minerals_detected else "None detected",
                rock_description=rock_description,
                formation_context=formation_context,
            )
            response = self.generate_response(prompt, max_new_tokens=600)
            if "offline mode" not in response:
                return response

        # ---- Rule-based fallback ----
        return self._rule_based_prediction_explanation(
            rock_type, confidence, top_predictions, minerals_detected, rock_info
        )

    def _rule_based_prediction_explanation(
        self,
        rock_type: str,
        confidence: float,
        top_predictions: list,
        minerals_detected: list,
        rock_info: dict,
    ) -> str:
        label = _confidence_label(confidence)
        lines = [
            f"## Geological Classification Explanation",
            f"",
            f"**Identified Rock Type:** {rock_type}",
            f"**Confidence:** {confidence:.1f}% ({label})",
            f"",
        ]

        if rock_info:
            lines += [
                f"### Rock Characteristics",
                f"- **Type:** {rock_info.get('type', 'N/A').title()} — {rock_info.get('subtype', '')}",
                f"- **Color:** {rock_info.get('color', 'N/A')}",
                f"- **Texture:** {rock_info.get('texture', 'N/A')}",
                f"- **Hardness:** {rock_info.get('hardness', 'N/A')}",
                f"",
                f"### Formation Process",
                rock_info.get("formation", "No formation data available."),
                f"",
                f"### Diagnostic Features",
                rock_info.get("characteristics", "No characteristic data available."),
                f"",
                f"### Geological Setting",
                rock_info.get("geological_setting", "N/A"),
                f"",
            ]
        else:
            lines.append(f"*No detailed information available for {rock_type}.*\n")

        if minerals_detected:
            lines += [
                f"### Detected Minerals",
                f"The following minerals were identified: {', '.join(minerals_detected)}.",
                f"",
                f"These minerals are consistent with the {rock_type} classification:",
            ]
            expected_minerals = rock_info.get("minerals", [])
            for mineral in minerals_detected:
                if mineral in expected_minerals:
                    lines.append(f"- **{mineral}** ✓ — characteristic mineral for {rock_type}")
                else:
                    lines.append(f"- **{mineral}** — accessory mineral; verify presence")
            lines.append("")

        if top_predictions and len(top_predictions) > 1:
            lines += [
                f"### Alternative Classifications",
                f"The model also considered:",
            ]
            for pred in top_predictions[1:]:
                lines.append(
                    f"- {pred.get('rock_type', 'N/A')}: {pred.get('confidence', 0):.1f}%"
                )
            lines.append("")

        if confidence < 70:
            lines += [
                f"### ⚠ Confidence Note",
                f"The {label.lower()} confidence ({confidence:.1f}%) suggests some visual "
                f"ambiguity. Manual verification by a qualified geologist is recommended. "
                f"Additional thin-section petrography or XRD analysis may be warranted.",
                f"",
            ]

        lines += [
            f"### Economic Significance",
            rock_info.get("economic_importance", "No economic information available."),
        ]

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Answer geological questions
    # ------------------------------------------------------------------

    def answer_question(self, question: str, context: str = "") -> str:
        """General geological Q&A with optional RAG context."""
        knowledge_snippet = self._extract_relevant_knowledge(question)

        if self.use_llm:
            prompt = GEOLOGICAL_QA_PROMPT.format(
                question=question,
                context=context if context else "No additional context provided.",
                knowledge_base=knowledge_snippet,
            )
            response = self.generate_response(prompt, max_new_tokens=512)
            if "offline mode" not in response:
                return response

        # Rule-based Q&A
        return self._rule_based_qa(question, context, knowledge_snippet)

    def _extract_relevant_knowledge(self, question: str) -> str:
        """Search GEOLOGICAL_KNOWLEDGE for terms mentioned in the question."""
        question_lower = question.lower()
        snippets = []

        for rock_type, info in self._geo["lithology"].items():
            if rock_type.lower() in question_lower:
                snippets.append(
                    f"{rock_type}: {info.get('characteristics', '')} "
                    f"Formation: {info.get('formation', '')}"
                )

        for mineral, info in self._geo["minerals"].items():
            if mineral.lower() in question_lower:
                snippets.append(f"{mineral}: {info.get('description', '')}")

        if not snippets:
            # Return a general geological overview
            snippets.append(self._geo["general"]["lithology_classification"])

        return "\n".join(snippets[:5])  # Limit to 5 snippets

    def _rule_based_qa(self, question: str, context: str, knowledge_snippet: str) -> str:
        question_lower = question.lower()

        # Check for specific rock types
        for rock_type, info in self._geo["lithology"].items():
            if rock_type.lower() in question_lower:
                return (
                    f"## About {rock_type}\n\n"
                    f"**Type:** {info.get('type', 'N/A').title()} rock\n"
                    f"**Formation:** {info.get('formation', 'N/A')}\n"
                    f"**Characteristics:** {info.get('characteristics', 'N/A')}\n"
                    f"**Minerals:** {', '.join(info.get('minerals', []))}\n"
                    f"**Economic Importance:** {info.get('economic_importance', 'N/A')}\n"
                    f"**Geological Setting:** {info.get('geological_setting', 'N/A')}\n"
                )

        # Check for specific minerals
        for mineral, info in self._geo["minerals"].items():
            if mineral.lower() in question_lower:
                return (
                    f"## About {mineral}\n\n"
                    f"**Formula:** {info.get('formula', 'N/A')}\n"
                    f"**Hardness:** {info.get('hardness', 'N/A')}\n"
                    f"**Color:** {info.get('color', 'N/A')}\n"
                    f"**Description:** {info.get('description', 'N/A')}\n"
                    f"**Occurrence:** {info.get('occurrence', 'N/A')}\n"
                    f"**Economic Uses:** {info.get('economic_uses', 'N/A')}\n"
                )

        # Generic answer using context
        if context:
            return (
                f"Based on the available geological context:\n\n"
                f"{context}\n\n"
                f"**Additional Information:**\n{knowledge_snippet}"
            )

        return (
            f"I found the following relevant geological information:\n\n"
            f"{knowledge_snippet}\n\n"
            f"For more specific information, please consult a qualified geologist "
            f"or refer to standard geological references (e.g., Best, 2003; "
            f"Blatt & Tracy, 1995)."
        )

    # ------------------------------------------------------------------
    # Generate full report
    # ------------------------------------------------------------------

    def generate_report(self, prediction_result: dict, borehole_info: dict) -> str:
        """Generate a full geological report for a single sample."""
        from datetime import datetime

        rock_type = prediction_result.get("rock_type", "Unknown")
        confidence = float(prediction_result.get("confidence", 0.0))
        minerals_detected = prediction_result.get("minerals_detected", [])
        rock_info = self._geo["lithology"].get(rock_type, {})

        rock_description = self._format_rock_info(rock_type, rock_info)
        formation_info = rock_info.get("geological_setting", "N/A")

        if self.use_llm:
            prompt = REPORT_GENERATION_PROMPT.format(
                rock_type=rock_type,
                confidence=confidence,
                minerals_detected=", ".join(minerals_detected) if minerals_detected else "None",
                borehole_id=borehole_info.get("borehole_id", "N/A"),
                depth_from=borehole_info.get("depth_from", "N/A"),
                depth_to=borehole_info.get("depth_to", "N/A"),
                sample_id=borehole_info.get("sample_id", "N/A"),
                rock_description=rock_description,
                formation_info=formation_info,
                date=datetime.now().strftime("%Y-%m-%d"),
                project_name=borehole_info.get("project_name", "Lithology Classification Project"),
            )
            response = self.generate_response(prompt, max_new_tokens=800)
            if "offline mode" not in response:
                return response

        # Rule-based report
        from llm.report_generator import ReportGenerator
        generator = ReportGenerator()
        return generator.generate_classification_report(prediction_result, borehole_info)

    # ------------------------------------------------------------------
    # Explain mineral
    # ------------------------------------------------------------------

    def explain_mineral(self, mineral_name: str) -> str:
        """Explain a mineral in geological detail."""
        mineral_info = self._geo["minerals"].get(mineral_name, {})

        # Build list of rock types that contain this mineral
        associated_rocks = [
            rock for rock, info in self._geo["lithology"].items()
            if mineral_name in info.get("minerals", [])
        ]

        if self.use_llm:
            prompt = MINERAL_EXPLANATION_PROMPT.format(
                mineral_name=mineral_name,
                mineral_data=str(mineral_info),
                associated_rocks=", ".join(associated_rocks) if associated_rocks else "Various rock types",
                context="Drill core analysis context",
            )
            response = self.generate_response(prompt, max_new_tokens=500)
            if "offline mode" not in response:
                return response

        # Rule-based fallback
        if not mineral_info:
            return (
                f"## {mineral_name}\n\n"
                f"Detailed information for **{mineral_name}** is not available in the "
                f"local knowledge base. Please consult mineralogical references such as "
                f"Deer, Howie & Zussman (1992) 'An Introduction to the Rock-Forming Minerals'."
            )

        lines = [
            f"## Mineral Profile: {mineral_name}",
            f"",
            f"| Property | Value |",
            f"|-----------|-------|",
            f"| Chemical Formula | {mineral_info.get('formula', 'N/A')} |",
            f"| Hardness | {mineral_info.get('hardness', 'N/A')} |",
            f"| Color | {mineral_info.get('color', 'N/A')} |",
            f"| Luster | {mineral_info.get('luster', 'N/A')} |",
            f"| Cleavage | {mineral_info.get('cleavage', 'N/A')} |",
            f"",
            f"### Description",
            mineral_info.get("description", "N/A"),
            f"",
            f"### Geological Occurrence",
            mineral_info.get("occurrence", "N/A"),
            f"",
            f"### Economic Uses",
            mineral_info.get("economic_uses", "N/A"),
            f"",
        ]

        if associated_rocks:
            lines += [
                f"### Associated Rock Types",
                f"Found in: {', '.join(associated_rocks)}",
                f"",
            ]

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Explain formation
    # ------------------------------------------------------------------

    def explain_formation(self, formation_name: str) -> str:
        """Explain a geological formation."""
        formation_data = self._geo["formations"].get(formation_name, {})

        if self.use_llm:
            prompt = FORMATION_EXPLANATION_PROMPT.format(
                formation_name=formation_name,
                formation_data=str(formation_data),
                region_context="General geological context",
            )
            response = self.generate_response(prompt, max_new_tokens=500)
            if "offline mode" not in response:
                return response

        # Rule-based
        if not formation_data:
            return (
                f"## {formation_name}\n\n"
                f"Detailed information for the **{formation_name}** formation is not "
                f"available in the local knowledge base."
            )

        return (
            f"## Geological Formation: {formation_name}\n\n"
            f"### Description\n"
            f"{formation_data.get('description', 'N/A')}\n\n"
            f"### Economic Significance\n"
            f"{formation_data.get('economic_significance', 'N/A')}\n"
        )

    # ------------------------------------------------------------------
    # Summarize borehole
    # ------------------------------------------------------------------

    def summarize_borehole(self, borehole_data: dict) -> str:
        """Summarize a borehole from a list of predictions."""
        borehole_id = borehole_data.get("borehole_id", "N/A")
        predictions = borehole_data.get("predictions", [])
        total_depth = borehole_data.get("total_depth", "N/A")
        location = borehole_data.get("location", "N/A")

        if not predictions:
            return f"## Borehole {borehole_id}\n\nNo prediction data available."

        # Compute statistics
        rock_type_counts: dict = {}
        all_minerals: list = []
        for pred in predictions:
            rt = pred.get("rock_type", "Unknown")
            rock_type_counts[rt] = rock_type_counts.get(rt, 0) + 1
            all_minerals.extend(pred.get("minerals_detected", []))

        dominant_rock = max(rock_type_counts, key=rock_type_counts.get)
        total = len(predictions)
        rock_pct = "\n".join(
            f"  - {rt}: {cnt} samples ({cnt/total*100:.1f}%)"
            for rt, cnt in sorted(rock_type_counts.items(), key=lambda x: -x[1])
        )

        mineral_freq: dict = {}
        for m in all_minerals:
            mineral_freq[m] = mineral_freq.get(m, 0) + 1
        mineral_summary = ", ".join(
            f"{m} ({c})" for m, c in sorted(mineral_freq.items(), key=lambda x: -x[1])
        ) or "None detected"

        # Build lithology log
        log_lines = []
        for pred in predictions:
            d_from = pred.get("depth_from", "?")
            d_to = pred.get("depth_to", "?")
            rt = pred.get("rock_type", "Unknown")
            conf = pred.get("confidence", 0)
            log_lines.append(f"  {d_from}m–{d_to}m: {rt} ({conf:.0f}% confidence)")
        lithology_log = "\n".join(log_lines)

        if self.use_llm:
            prompt = BOREHOLE_SUMMARY_PROMPT.format(
                project_name=borehole_data.get("project_name", "Lithology Project"),
                borehole_id=borehole_id,
                location=location,
                total_depth=total_depth,
                date_drilled=borehole_data.get("date_drilled", "N/A"),
                lithology_log=lithology_log,
                dominant_rock_type=dominant_rock,
                rock_type_percentages=rock_pct,
                minerals_summary=mineral_summary,
            )
            response = self.generate_response(prompt, max_new_tokens=700)
            if "offline mode" not in response:
                return response

        # Rule-based borehole summary
        return textwrap.dedent(f"""
            ## Borehole Summary: {borehole_id}

            ### Overview
            - **Location:** {location}
            - **Total Depth:** {total_depth} m
            - **Samples Classified:** {total}
            - **Dominant Lithology:** {dominant_rock}

            ### Lithological Log
            {lithology_log}

            ### Rock Type Distribution
            {rock_pct}

            ### Mineralogical Summary
            Minerals detected: {mineral_summary}

            ### Geological Interpretation
            The borehole is dominated by **{dominant_rock}**, which is a
            {self._geo['lithology'].get(dominant_rock, {}).get('type', 'unknown type')} rock.
            {self._geo['lithology'].get(dominant_rock, {}).get('formation', '')}

            ### Economic Potential
            {self._geo['lithology'].get(dominant_rock, {}).get('economic_importance', 'No economic data available.')}

            ### Recommendations
            - Review low-confidence intervals for manual logging
            - Consider thin-section petrography for ambiguous intervals
            - Evaluate geochemical assay results in context of identified lithologies
        """).strip()

    # ------------------------------------------------------------------
    # Generate recommendations
    # ------------------------------------------------------------------

    def generate_recommendations(self, prediction_result: dict) -> str:
        """Generate exploration / mining recommendations for a sample."""
        rock_type = prediction_result.get("rock_type", "Unknown")
        confidence = float(prediction_result.get("confidence", 0.0))
        minerals_detected = prediction_result.get("minerals_detected", [])
        depth = prediction_result.get("depth", "N/A")
        borehole_id = prediction_result.get("borehole_id", "N/A")

        rock_info = self._geo["lithology"].get(rock_type, {})
        economic_info = rock_info.get("economic_importance", "No economic data available.")

        # Build associated deposit types from economic importance
        deposit_indicators = {
            "Granite": "Porphyry Cu-Mo, Sn-W veins, pegmatite Li-Cs-Ta deposits",
            "Basalt": "Volcanogenic massive sulfide (VMS), Cu-Ni, geothermal energy",
            "Sandstone": "Oil and gas (reservoir rock), groundwater aquifer, U in roll-front deposits",
            "Limestone": "Pb-Zn (Mississippi Valley type), oil and gas, industrial minerals",
            "Shale": "Shale gas, oil shale, black shale-hosted Au-PGE",
            "Quartzite": "Gold-bearing reef (e.g. Witwatersrand), quartz for silicon",
            "Marble": "Industrial minerals, dimension stone, skarn-type deposits",
            "Gneiss": "Au, base metals in shear zones, rare earth elements",
            "Gabbro": "Ni-Cu-PGE deposits, chromite, Ti-V-Fe",
            "Diorite": "Porphyry Cu-Au, epithermal Au-Ag",
            "Rhyolite": "Epithermal Au-Ag, VMS deposits",
            "Andesite": "Porphyry Cu-Au, epithermal Au-Ag",
        }
        associated_deposits = deposit_indicators.get(rock_type, "General mineral exploration potential")

        if self.use_llm:
            prompt = RECOMMENDATION_PROMPT.format(
                borehole_id=borehole_id,
                depth=depth,
                rock_type=rock_type,
                confidence=confidence,
                minerals_detected=", ".join(minerals_detected) if minerals_detected else "None",
                rock_economic_info=economic_info,
                associated_deposits=associated_deposits,
            )
            response = self.generate_response(prompt, max_new_tokens=600)
            if "offline mode" not in response:
                return response

        # Rule-based recommendations
        confidence_note = ""
        if confidence < 70:
            confidence_note = (
                f"\n> ⚠ **Note:** Confidence is {confidence:.1f}% ({_confidence_label(confidence)}). "
                f"Manual verification is strongly recommended before acting on these recommendations.\n"
            )

        return textwrap.dedent(f"""
            ## Exploration Recommendations

            **Borehole:** {borehole_id} | **Depth:** {depth} m | **Rock Type:** {rock_type}
            {confidence_note}

            ### Identified Lithology
            {rock_type} — {rock_info.get('type', 'N/A').title()} rock
            {rock_info.get('formation', '')}

            ### Associated Deposit Types
            {associated_deposits}

            ### Immediate Next Steps (HIGH PRIORITY)
            - [ ] Submit representative samples for XRF whole-rock geochemical analysis
            - [ ] Conduct thin-section petrographic analysis of this interval
            - [ ] Log adjacent core intervals for continuity of lithology
            - [ ] Check for hydrothermal alteration (silicification, carbonatisation, sericitisation)

            ### Geophysical Surveys Recommended
            - IP (Induced Polarization) / resistivity survey for sulphide detection
            - Magnetic survey to map structural controls
            - Gravity survey for density contrast mapping

            ### Geochemical Analysis
            - Assay for: Au, Ag, Cu, Pb, Zn, Mo, Ni (adapt to {rock_type} context)
            - Pathfinder elements: As, Sb, Bi, Te, Tl
            - Major oxides: SiO₂, Al₂O₃, Fe₂O₃, MgO, CaO

            ### Economic Significance
            {economic_info}

            ### Risk Factors
            - Classification confidence: {confidence:.1f}% — {'acceptable' if confidence >= 70 else 'requires verification'}
            - Structural complexity may affect resource continuity
            - Alteration may mask primary mineralogy

            ### Priority Summary
            | Action | Priority |
            |--------|----------|
            | Geochemical assay | HIGH |
            | Thin-section petrography | HIGH |
            | Geophysical survey | MEDIUM |
            | Additional drilling | MEDIUM |
            | Feasibility study | LOW (after Phase 1 results) |
        """).strip()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _format_rock_info(self, rock_type: str, rock_info: dict) -> str:
        if not rock_info:
            return f"No detailed information available for {rock_type}."
        return (
            f"Type: {rock_info.get('type', 'N/A').title()} ({rock_info.get('subtype', 'N/A')})\n"
            f"Color: {rock_info.get('color', 'N/A')}\n"
            f"Texture: {rock_info.get('texture', 'N/A')}\n"
            f"Hardness: {rock_info.get('hardness', 'N/A')}\n"
            f"Formation: {rock_info.get('formation', 'N/A')}\n"
            f"Characteristics: {rock_info.get('characteristics', 'N/A')}\n"
            f"Minerals: {', '.join(rock_info.get('minerals', []))}\n"
            f"Economic Importance: {rock_info.get('economic_importance', 'N/A')}"
        )
