"""
SafetyAgent implementation from AGENTS.md specification
Applies safety guardrails and ensures appropriate responses
"""
from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import logging
import re

logger = logging.getLogger(__name__)


class SafetyAgent:
    """
    SafetyAgent implementation as specified in AGENTS.md
    Handles content moderation, medical disclaimers, and tone adjustment
    """

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

        # Safety rules from AGENTS.md specification
        self.safety_rules = {
            "block_medical_diagnosis": True,
            "block_harmful_content": True,
            "add_disclaimers": True,
            "enforce_respectful_tone": True
        }

        # Disclaimer templates from PROMPTS.md specification
        self.disclaimers = {
            "medical": "📝 Note: This information is based on Traditional Chinese Medicine principles and general wellness practices. It is not intended as medical advice. Always consult with qualified healthcare professionals for medical conditions or before making significant changes to your health regimen.",
            "financial": "📝 Note: This content discusses general financial principles and strategies. It is not personalized financial advice. Investment carries risks, and you should consult with qualified financial advisors before making investment decisions.",
            "legal": "📝 Note: This information is for educational purposes only and does not constitute legal advice. For legal matters, please consult with a qualified attorney who can address your specific situation.",
            "exercise": "📝 Note: These exercises and physical practices should be approached gradually and with proper form. Consider your current fitness level and any health conditions. Consult with healthcare providers before beginning new exercise programs, especially if you have pre-existing conditions."
        }

        # Keywords that trigger safety checks
        self.safety_keywords = {
            "medical": [
                "diagnose", "diagnosis", "disease", "illness", "symptoms", "cure", "treatment",
                "medicine", "medication", "prescription", "doctor", "medical", "health condition",
                "pain", "sick", "fever", "infection", "cancer", "diabetes", "heart disease"
            ],
            "financial": [
                "invest", "investment", "stocks", "bonds", "portfolio", "financial advice",
                "buy", "sell", "trading", "market", "profit", "loss", "tax", "retirement",
                "savings", "loan", "mortgage", "insurance"
            ],
            "legal": [
                "legal advice", "lawsuit", "contract", "law", "legal", "attorney", "lawyer",
                "court", "judge", "sue", "rights", "violation", "illegal", "criminal"
            ],
            "exercise": [
                "exercise", "workout", "training", "martial arts", "shaolin", "kung fu",
                "physical practice", "movement", "stretching", "qi gong", "meditation",
                "breathing", "posture", "form", "routine", "practice"
            ],
            "harmful": [
                "suicide", "self-harm", "kill", "die", "death", "violence", "abuse",
                "illegal", "drugs", "weapon", "hate", "discrimination"
            ]
        }

    async def check_safety(self, state: dict) -> dict:
        """
        Apply safety checks as specified in AGENTS.md

        Args:
            state: ConversationState dict with final_response

        Returns:
            Updated state with safety_flags and potentially modified response
        """
        try:
            response = state["final_response"]

            if not response:
                state["safety_flags"] = ["empty_response"]
                state["current_node"] = "safety"
                state["next_node"] = None
                state["status"] = "complete"
                return state

            # Check for safety violations
            violations = await self._detect_violations(response)

            if violations.get("block_response"):
                state["final_response"] = self._get_safe_fallback(violations)
                state["safety_flags"] = ["blocked", violations.get("reason", "content_blocked")]

            elif violations.get("needs_disclaimer"):
                disclaimer_type = violations.get("type")
                disclaimer = self._get_disclaimer(disclaimer_type)
                if disclaimer:
                    state["final_response"] += f"\n\n{disclaimer}"
                state["safety_flags"] = [f"disclaimer_added_{disclaimer_type}"]

            elif violations.get("tone_adjustment"):
                state["final_response"] = await self._adjust_tone(response)
                state["safety_flags"] = ["tone_adjusted"]

            else:
                # No violations found
                state["safety_flags"] = ["safe"]

            state["current_node"] = "safety"
            state["next_node"] = None  # Terminal node
            state["status"] = "complete"

            logger.info(f"Safety check complete. Flags: {state['safety_flags']}")

        except Exception as e:
            logger.error(f"Error in SafetyAgent.check_safety: {e}")
            state["safety_flags"] = ["safety_check_failed"]
            state["error"] = f"Safety check failed: {str(e)}"

        return state

    async def _detect_violations(self, response: str) -> Dict[str, Any]:
        """
        Detect safety violations in the response

        Returns:
            Dict with violation type and action needed
        """
        violations = {
            "block_response": False,
            "needs_disclaimer": False,
            "tone_adjustment": False,
            "type": None,
            "reason": None
        }

        response_lower = response.lower()

        # Check for harmful content that should be blocked
        if self.safety_rules["block_harmful_content"]:
            for keyword in self.safety_keywords["harmful"]:
                if keyword in response_lower:
                    violations["block_response"] = True
                    violations["reason"] = f"harmful_content_{keyword}"
                    return violations

        # Check for medical content that needs disclaimers
        if self.safety_rules["block_medical_diagnosis"]:
            medical_keywords_found = []
            for keyword in self.safety_keywords["medical"]:
                if keyword in response_lower:
                    medical_keywords_found.append(keyword)

            # If medical content is detected, add disclaimer
            if medical_keywords_found:
                # Check if it's giving medical advice vs general health info
                advice_indicators = ["you should", "i recommend", "take this", "stop taking"]
                is_giving_advice = any(indicator in response_lower for indicator in advice_indicators)

                if is_giving_advice:
                    violations["needs_disclaimer"] = True
                    violations["type"] = "medical"

        # Check for financial advice
        if self.safety_rules["add_disclaimers"]:
            financial_keywords_found = []
            for keyword in self.safety_keywords["financial"]:
                if keyword in response_lower:
                    financial_keywords_found.append(keyword)

            if financial_keywords_found:
                advice_indicators = ["you should invest", "buy", "sell", "i recommend investing"]
                is_giving_advice = any(indicator in response_lower for indicator in advice_indicators)

                if is_giving_advice:
                    violations["needs_disclaimer"] = True
                    violations["type"] = "financial"

        # Check for legal content
        legal_keywords_found = []
        for keyword in self.safety_keywords["legal"]:
            if keyword in response_lower:
                legal_keywords_found.append(keyword)

        if legal_keywords_found:
            advice_indicators = ["you should sue", "file a lawsuit", "this is illegal", "your rights are"]
            is_giving_advice = any(indicator in response_lower for indicator in advice_indicators)

            if is_giving_advice:
                violations["needs_disclaimer"] = True
                violations["type"] = "legal"

        # Check for exercise/physical advice
        exercise_keywords_found = []
        for keyword in self.safety_keywords["exercise"]:
            if keyword in response_lower:
                exercise_keywords_found.append(keyword)

        if exercise_keywords_found:
            advice_indicators = ["you should do", "practice", "try this", "start with"]
            is_giving_advice = any(indicator in response_lower for indicator in advice_indicators)

            if is_giving_advice:
                violations["needs_disclaimer"] = True
                violations["type"] = "exercise"

        # Check tone if enabled
        if self.safety_rules["enforce_respectful_tone"]:
            tone_issues = await self._check_tone(response)
            if tone_issues:
                violations["tone_adjustment"] = True
                violations["reason"] = "tone_adjustment_needed"

        return violations

    async def _check_tone(self, response: str) -> bool:
        """Check if tone adjustment is needed"""
        # Simple checks for tone issues
        response_lower = response.lower()

        # Check for dismissive or harsh language
        dismissive_phrases = [
            "that's stupid", "obviously", "you're wrong", "that's ridiculous",
            "don't be silly", "that's dumb", "you should know"
        ]

        for phrase in dismissive_phrases:
            if phrase in response_lower:
                return True

        # Check for overly technical or cold language
        # Use LLM for more nuanced tone checking if needed
        return False

    async def _adjust_tone(self, response: str) -> str:
        """Adjust tone to be more respectful and warm"""
        try:
            prompt = [
                SystemMessage(content="""
Please adjust the tone of the following response to be more warm, respectful, and approachable while maintaining all the factual content. Make it sound like Herman Siu's compassionate and wise voice.

Guidelines:
- Remove any dismissive or harsh language
- Add warmth and empathy
- Maintain all factual information
- Keep the practical advice
- Make it conversational and caring
                """),
                HumanMessage(content=f"Original response: {response}")
            ]

            adjusted_response = await self.llm.ainvoke(prompt)
            return adjusted_response.content

        except Exception as e:
            logger.error(f"Error adjusting tone: {e}")
            # Return original response if tone adjustment fails
            return response

    def _get_disclaimer(self, violation_type: str) -> str:
        """Get appropriate disclaimer for violation type"""
        return self.disclaimers.get(violation_type, "")

    def _get_safe_fallback(self, violations: Dict) -> str:
        """Get safe fallback response for blocked content"""
        reason = violations.get("reason", "content_policy")

        if "harmful" in reason:
            return "I understand you're looking for guidance, but I'm not able to provide advice on that topic. If you're struggling with difficult thoughts, please reach out to a mental health professional or crisis helpline for support."

        elif "medical" in reason:
            return "I appreciate your question about health matters. While I can share general wellness wisdom, I'm not qualified to provide medical advice. Please consult with healthcare professionals for any health concerns."

        else:
            return "I apologize, but I'm not able to provide guidance on that particular topic. Is there something else I can help you with today?"

    def get_safety_summary(self, state: dict) -> Dict:
        """Get summary of safety checks performed"""
        return {
            "safety_flags": state.get("safety_flags", []),
            "rules_applied": list(self.safety_rules.keys()),
            "disclaimers_available": list(self.disclaimers.keys()),
            "status": "safe" if "safe" in state.get("safety_flags", []) else "modified"
        }