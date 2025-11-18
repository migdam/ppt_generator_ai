"""
AI Generator Module
Handles Gemini AI integration for presentation plan generation.
"""

import google.generativeai as genai
import json
import os
from typing import Dict, List, Optional


class AIGenerator:
    """Generates presentation plans using Google's Gemini AI."""

    def __init__(self, api_key: str):
        """
        Initialize the AI generator.

        Args:
            api_key: Google Gemini API key
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate_presentation_plan(
        self,
        content: str,
        title: str,
        num_slides: int,
        style: str,
        image_urls: List[str],
        feedback: Optional[str] = None
    ) -> Dict:
        """
        Generate a structured presentation plan from content.

        Args:
            content: The extracted text content
            title: The page/presentation title
            num_slides: Number of slides to generate
            style: Presentation style ('general' or 'detailed')
            image_urls: List of available image URLs from the source
            feedback: Optional feedback from previous evaluation attempt

        Returns:
            Dictionary containing the presentation plan in JSON format
        """
        style_description = {
            'general': 'Create a concise, high-level overview. Focus on key points and main ideas. Keep content brief and impactful.',
            'detailed': 'Create a comprehensive, detailed analysis. Include supporting details, examples, and in-depth explanations.'
        }

        feedback_section = ""
        if feedback:
            feedback_section = f"""
IMPORTANT - PREVIOUS ATTEMPT FEEDBACK:
The previous presentation plan received the following critique:
{feedback}

Please carefully address all the issues mentioned above in your new plan.
"""

        prompt = f"""You are an expert presentation designer. Create a professional PowerPoint presentation plan from the following content.

SOURCE TITLE: {title}

STYLE REQUIREMENT: {style_description.get(style, style_description['general'])}

NUMBER OF SLIDES: {num_slides} (including title slide)

AVAILABLE IMAGES: {len(image_urls)} images available
{chr(10).join([f"- {url}" for url in image_urls[:10]])}
{"... and more" if len(image_urls) > 10 else ""}

CONTENT TO SUMMARIZE:
{content[:8000]}
{"... (content truncated)" if len(content) > 8000 else ""}

{feedback_section}

Create a presentation plan with the following structure:

{{
  "title": "Main presentation title",
  "subtitle": "Brief subtitle or tagline",
  "slides": [
    {{
      "slide_number": 1,
      "title": "Slide Title",
      "content": [
        "Key point 1",
        "Key point 2",
        "Key point 3"
      ],
      "visual": {{
        "type": "image|chart|diagram|none",
        "source": "image_url or description",
        "chart_data": {{
          "categories": ["Cat1", "Cat2"],
          "values": [10, 20]
        }}
      }}
    }}
  ]
}}

VISUAL GUIDELINES:
1. Use "image" type with actual URLs from the AVAILABLE IMAGES list when relevant
2. Use "chart" type for data visualization - provide chart_data with categories and values
3. Use "diagram" type for conceptual visuals - provide a description
4. Use "none" if no visual is needed

DESIGN PRINCIPLES:
- Slide 0 is always the title slide (use title and subtitle only, no content or visuals)
- Each content slide should have 3-5 bullet points maximum
- Balance text and visuals - aim for 60-70% of slides to have visuals
- Use diverse visual types (mix images, charts, diagrams)
- Ensure colors are professional and harmonious
- Make titles descriptive and engaging
- Keep bullet points concise (max 10-12 words each)

Return ONLY the JSON object, no additional text or markdown formatting.
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
            plan = json.loads(response_text)

            # Validate plan structure
            self._validate_plan(plan, num_slides)

            return plan

        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse AI response as JSON: {str(e)}\nResponse: {response_text[:500]}")
        except Exception as e:
            raise Exception(f"AI generation failed: {str(e)}")

    def _validate_plan(self, plan: Dict, expected_slides: int) -> None:
        """
        Validate the structure of the generated plan.

        Args:
            plan: The generated presentation plan
            expected_slides: Expected number of slides

        Raises:
            ValueError if plan structure is invalid
        """
        if 'title' not in plan or 'slides' not in plan:
            raise ValueError("Plan must contain 'title' and 'slides' fields")

        if not isinstance(plan['slides'], list):
            raise ValueError("'slides' must be a list")

        if len(plan['slides']) < expected_slides - 2:
            raise ValueError(f"Expected ~{expected_slides} slides, got {len(plan['slides'])}")

        for i, slide in enumerate(plan['slides']):
            if 'title' not in slide:
                raise ValueError(f"Slide {i} missing 'title' field")

            # Title slide (first slide) doesn't need content
            if i > 0 and 'content' not in slide:
                raise ValueError(f"Slide {i} missing 'content' field")

    @staticmethod
    def get_api_key_from_env() -> Optional[str]:
        """
        Retrieve Gemini API key from environment variables.

        Returns:
            API key string or None if not found
        """
        # First check environment variable
        api_key = os.environ.get('GEMINI_API_KEY')

        if not api_key:
            # Try to read from ~/.zshrc
            zshrc_path = os.path.expanduser('~/.zshrc')
            if os.path.exists(zshrc_path):
                try:
                    with open(zshrc_path, 'r') as f:
                        for line in f:
                            if 'GEMINI_API_KEY' in line and '=' in line:
                                # Extract the key value
                                parts = line.split('=', 1)
                                if len(parts) == 2:
                                    key = parts[1].strip().strip('"').strip("'")
                                    if key and not key.startswith('export'):
                                        return key
                except Exception:
                    pass

        return api_key
