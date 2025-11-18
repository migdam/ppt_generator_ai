"""
AI Evaluator Module
Implements the quality control feedback loop for presentation plans.
"""

import google.generativeai as genai
import json
from typing import Dict, Tuple


class AIEvaluator:
    """Evaluates presentation plans and provides feedback for improvement."""

    PASSING_SCORE = 45
    MAX_SCORE = 50
    MAX_ATTEMPTS = 5

    def __init__(self, api_key: str):
        """
        Initialize the AI evaluator.

        Args:
            api_key: Google Gemini API key
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def evaluate_plan(self, plan: Dict) -> Tuple[int, str]:
        """
        Evaluate a presentation plan against quality criteria.

        Args:
            plan: The presentation plan to evaluate

        Returns:
            Tuple of (score, detailed_feedback)
        """
        prompt = f"""You are an expert presentation critic and designer. Evaluate the following PowerPoint presentation plan.

PRESENTATION PLAN:
{json.dumps(plan, indent=2)}

EVALUATION RUBRIC (50 points total):

1. CONTENT ALIGNMENT (10 points)
   - Does the content match the title and flow logically?
   - Are slides well-organized and coherent?
   - Is there a clear narrative or structure?

2. VISUAL BALANCE (10 points)
   - Are visuals distributed well across slides?
   - Is there a good mix of images, charts, and diagrams?
   - Do slides avoid being too text-heavy?

3. DESIGN CONSISTENCY (10 points)
   - Are slide titles descriptive and consistent in style?
   - Is the amount of content per slide balanced?
   - Are bullet points concise and scannable?

4. VISUAL RELEVANCE (10 points)
   - Do images/charts actually relate to the slide content?
   - Are chart data and categories meaningful?
   - Are diagram descriptions clear and useful?

5. PROFESSIONAL APPEAL (10 points)
   - Would this presentation engage an audience?
   - Is the content neither too basic nor too complex?
   - Does it look polished and well-thought-out?

INSTRUCTIONS:
1. Score each category out of 10 points
2. Provide specific, actionable feedback for improvement
3. Be critical but constructive
4. Focus on the most impactful changes

Return your evaluation in this exact JSON format:
{{
  "scores": {{
    "content_alignment": 8,
    "visual_balance": 7,
    "design_consistency": 9,
    "visual_relevance": 8,
    "professional_appeal": 9
  }},
  "total_score": 41,
  "feedback": "Detailed multi-line feedback explaining what needs improvement. Be specific about which slides need work and what changes would improve the score."
}}

Return ONLY the JSON object, no additional text.
"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            # Parse JSON
            evaluation = json.loads(response_text)

            total_score = evaluation.get('total_score', 0)
            feedback = evaluation.get('feedback', 'No feedback provided')

            # Validate score
            if total_score < 0 or total_score > self.MAX_SCORE:
                total_score = max(0, min(self.MAX_SCORE, total_score))

            return total_score, feedback

        except json.JSONDecodeError as e:
            # If parsing fails, return a failing score with error feedback
            return 0, f"Evaluation failed: {str(e)}"
        except Exception as e:
            return 0, f"Evaluation error: {str(e)}"

    def generate_with_feedback_loop(
        self,
        generator,
        content: str,
        title: str,
        num_slides: int,
        style: str,
        image_urls: list
    ) -> Tuple[Dict, int, List[Dict]]:
        """
        Generate a presentation plan with iterative feedback and improvement.

        Args:
            generator: AIGenerator instance
            content: Text content to generate from
            title: Presentation title
            num_slides: Number of slides
            style: Presentation style
            image_urls: Available image URLs

        Returns:
            Tuple of (best_plan, best_score, attempt_history)
        """
        best_plan = None
        best_score = 0
        attempt_history = []

        feedback = None

        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            print(f"\n🔄 Attempt {attempt}/{self.MAX_ATTEMPTS}: Generating presentation plan...")

            # Generate plan
            try:
                plan = generator.generate_presentation_plan(
                    content=content,
                    title=title,
                    num_slides=num_slides,
                    style=style,
                    image_urls=image_urls,
                    feedback=feedback
                )
            except Exception as e:
                print(f"❌ Generation failed: {str(e)}")
                attempt_history.append({
                    'attempt': attempt,
                    'status': 'generation_failed',
                    'error': str(e)
                })
                continue

            # Evaluate plan
            print(f"📊 Evaluating plan quality...")
            score, feedback_text = self.evaluate_plan(plan)

            print(f"📈 Score: {score}/{self.MAX_SCORE}")

            attempt_history.append({
                'attempt': attempt,
                'score': score,
                'feedback': feedback_text,
                'num_slides': len(plan.get('slides', []))
            })

            # Update best plan if this is better
            if score > best_score:
                best_score = score
                best_plan = plan

            # Check if we've reached passing score
            if score >= self.PASSING_SCORE:
                print(f"✅ Plan meets quality threshold ({score} >= {self.PASSING_SCORE})")
                return plan, score, attempt_history

            # Prepare feedback for next iteration
            feedback = f"""Previous attempt scored {score}/{self.MAX_SCORE}. Issues identified:

{feedback_text}

Please revise the presentation plan to address these specific issues."""

            print(f"⚠️  Score below threshold. Regenerating with feedback...")

        # Max attempts reached, return best plan
        print(f"\n⚠️  Max attempts reached. Using best plan (score: {best_score}/{self.MAX_SCORE})")
        return best_plan, best_score, attempt_history
