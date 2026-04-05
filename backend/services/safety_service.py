"""
Safety Service -- Rule-based Safety Override (Layer 2).

WHY: Non-negotiable safety rules that execute AFTER LLM fusion.
     Even if LLM outputs a dangerous value, this layer catches it.
     CRITICAL rules force correction. WARNING rules add alerts only.
RISK: eval_condition uses simple comparison parsing -- NOT eval().
INTERVIEW: "Layer 2 is deterministic. No ML, no LLM, no probability.
            If discharge_temp > 200 for Material A, it's CRITICAL. Period."
"""

import json
import logging

logger = logging.getLogger(__name__)

_RISK_LEVEL_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}

RULES_PATH = "data/safety/safety_rules.json"


class SafetyService:
    """
    Deterministic rule engine for safety overrides.

    WHY: Layer 2 of dual-layer architecture.
         Executes after LLM fusion (Layer 1).
         Cannot be bypassed, disabled, or overridden by LLM output.
    """

    def __init__(self):
        with open(RULES_PATH, "r") as f:
            data = json.load(f)
        self.rules = data.get("rules", [])
        logger.info(f"SafetyService loaded {len(self.rules)} rules from {RULES_PATH}")

    def apply_rules(
        self,
        fusion_result: dict,
        ml_prediction: dict,
        material: str,
        conditions: dict,
    ) -> list[dict]:
        """
        Apply all matching safety rules to the fusion result.

        WHY: Always runs after LLM fusion. Even if LLM already corrected,
             rules provide a second deterministic check.
        RISK: None -- deterministic, no external calls.
        """
        overrides = []

        for rule in self.rules:
            if rule["material"] != material:
                continue

            # WHY: Build variable context for condition evaluation.
            #      discharge_temp comes from fused_prediction (post-LLM).
            context = self._build_context(fusion_result, ml_prediction, conditions)

            if not self._eval_condition(rule["condition"], context):
                continue

            logger.info(f"Safety rule {rule['rule_id']} triggered for {material}")

            if rule["severity"] == "CRITICAL" and rule["action"] == "force_correction":
                original_value = fusion_result.get("fused_prediction", 0)
                correction_target = rule["correction_target"]
                fusion_result["fused_prediction"] = correction_target
                fusion_result["correction_applied"] = True
                fusion_result["correction_delta"] = correction_target - original_value
                fusion_result["risk_level"] = "CRITICAL"
                method = fusion_result.get("fusion_method", "")
                if "rule_override" not in method:
                    fusion_result["fusion_method"] = method + " + rule_override"

                overrides.append({
                    "rule_id": rule["rule_id"],
                    "severity": rule["severity"],
                    "action": rule["action"],
                    "original_value": round(original_value, 1),
                    "corrected_value": correction_target,
                    "message": rule["message"],
                })

            elif rule["severity"] == "WARNING":
                current_risk = fusion_result.get("risk_level", "LOW")
                if _RISK_LEVEL_RANK.get(current_risk, 0) < _RISK_LEVEL_RANK["HIGH"]:
                    fusion_result["risk_level"] = "HIGH"

                overrides.append({
                    "rule_id": rule["rule_id"],
                    "severity": rule["severity"],
                    "action": rule["action"],
                    "message": rule["message"],
                })

        return overrides

    def _build_context(
        self, fusion_result: dict, ml_prediction: dict, conditions: dict
    ) -> dict:
        """
        Build variable context for condition evaluation.

        WHY: Maps rule variable names to actual values from prediction/conditions.
        """
        # WHY: discharge_temp uses fused_prediction (post-LLM value).
        #      If LLM already corrected, rules check the corrected value.
        #      If LLM failed and fused_prediction = ML original, rules catch it.
        fused = fusion_result.get("fused_prediction", 0)

        return {
            "discharge_temp": fused,
            "rpm": conditions.get("rpm", 0),
            "input_rate": conditions.get("input_rate_kg_h", 0),
            "jacket_temp": conditions.get("temperature_celsius", 0),
            "grinding_pressure": conditions.get("grinding_pressure_mpa", 0),
            "classifier_rpm": conditions.get("classifier_rpm", 0),
            "feed_rate": conditions.get("feed_rate_kg_h", 0),
        }

    def _eval_condition(self, condition_str: str, context: dict) -> bool:
        """
        Evaluate a rule condition string using simple parsing.

        WHY: eval() is a security risk -- never use it.
             Only supports '>' and '<' operators with AND conjunction.
        INTERVIEW: "No eval(). String parsing only. Security over cleverness."
        """
        # Split on AND
        parts = [p.strip() for p in condition_str.split("AND")]

        for part in parts:
            if not self._eval_single(part, context):
                return False
        return True

    def _eval_single(self, expr: str, context: dict) -> bool:
        """Evaluate a single comparison like 'discharge_temp > 200'."""
        for op in [">", "<"]:
            if op in expr:
                left, right = expr.split(op, 1)
                var_name = left.strip()
                threshold = float(right.strip())
                value = context.get(var_name, 0)

                if op == ">":
                    return value > threshold
                elif op == "<":
                    return value < threshold

        logger.warning(f"Cannot parse condition: {expr}")
        return False


# WHY: Singleton instance loaded at import time for fail-fast.
safety_service = SafetyService()
