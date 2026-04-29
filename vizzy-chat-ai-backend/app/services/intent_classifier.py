from dataclasses import dataclass

from app.schemas.chat import IntentClassification


@dataclass(frozen=True)
class IntentRule:
    pathway: str
    keywords: tuple[str, ...]


class IntentClassifier:
    PRIORITY_BOOSTS: dict[str, float] = {
        "poster_design": 0.2,
        "product_visual": 0.18,
        "signage": 0.18,
        "quote_poster": 0.18,
        "moodboard": 0.14,
    }

    RULES: dict[str, IntentRule] = {
        "image_generation": IntentRule(
            pathway="creative_visual_generation",
            keywords=("artwork", "image", "illustration", "generate", "visual", "render"),
        ),
        "poster_design": IntentRule(
            pathway="creative_visual_generation",
            keywords=("poster", "flyer", "banner", "layout", "typography"),
        ),
        "story_visualization": IntentRule(
            pathway="narrative_scene_design",
            keywords=("story", "scene", "character", "world", "comic"),
        ),
        "moodboard": IntentRule(
            pathway="visual_direction_curation",
            keywords=("moodboard", "inspiration board", "look and feel", "visual direction"),
        ),
        "brand_campaign": IntentRule(
            pathway="brand_marketing_concepts",
            keywords=("brand", "campaign", "launch", "promotion", "ad"),
        ),
        "product_visual": IntentRule(
            pathway="product_visual_composition",
            keywords=("product", "packaging", "mockup", "hero shot", "packshot", "skincare"),
        ),
        "signage": IntentRule(
            pathway="environmental_graphics",
            keywords=("signage", "sign board", "storefront", "wayfinding", "billboard"),
        ),
        "quote_poster": IntentRule(
            pathway="expressive_typography_composition",
            keywords=("quote poster", "motivational quote", "quote design", "inspirational poster"),
        ),
        "style_transfer": IntentRule(
            pathway="style_remix_workflow",
            keywords=("style transfer", "in the style of", "restyle", "convert style"),
        ),
        "general_creative_help": IntentRule(
            pathway="creative_assistance",
            keywords=("copy", "caption", "headline", "tagline", "creative help", "ideas"),
        ),
    }

    def classify(self, message: str) -> IntentClassification:
        normalized = message.lower()
        best_intent = "general_creative_help"
        best_score = 0.0
        matched_keywords: list[str] = []

        for intent, rule in self.RULES.items():
            intent_matches = [keyword for keyword in rule.keywords if keyword in normalized]
            if not intent_matches:
                continue
            score = min(
                0.99,
                0.45 + (0.18 * len(intent_matches)) + self.PRIORITY_BOOSTS.get(intent, 0.0),
            )
            if score > best_score:
                best_score = score
                best_intent = intent
                matched_keywords = intent_matches

        if best_score == 0.0:
            best_score = 0.52
            reasoning = "No strong keyword match was found, so the request was routed to general creative help."
        else:
            reasoning = (
                f"Matched keywords {matched_keywords} which strongly suggest "
                f"{best_intent.replace('_', ' ')}."
            )

        rule = self.RULES[best_intent]
        return IntentClassification(
            intent=best_intent,
            confidence=round(best_score, 2),
            reasoning=reasoning,
            pathway=rule.pathway,
        )
