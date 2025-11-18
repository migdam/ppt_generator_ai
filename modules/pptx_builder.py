"""
PPTX Builder Module
Handles PowerPoint presentation generation with styling, images, charts, and diagrams.
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
import requests
from PIL import Image
from io import BytesIO
import os
from typing import Dict, Optional
from datetime import datetime


class PPTXBuilder:
    """Builds PowerPoint presentations from structured plans."""

    # Style configuration
    BG_COLOR = RGBColor(240, 248, 255)  # Light Blue
    TITLE_COLOR = RGBColor(0, 51, 102)  # Dark Blue
    BODY_COLOR = RGBColor(0, 0, 0)      # Black

    TITLE_FONT_SIZE = Pt(36)
    SUBTITLE_FONT_SIZE = Pt(24)
    BODY_FONT_SIZE = Pt(24)
    SMALL_FONT_SIZE = Pt(14)

    def __init__(self):
        """Initialize the PPTX builder."""
        self.prs = Presentation()
        self.prs.slide_width = Inches(10)
        self.prs.slide_height = Inches(7.5)

    def build_presentation(self, plan: Dict, output_dir: str = "Output") -> str:
        """
        Build a complete PowerPoint presentation from a plan.

        Args:
            plan: The presentation plan dictionary
            output_dir: Directory to save the output file

        Returns:
            Path to the generated .pptx file
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Add title slide
        self._add_title_slide(plan.get('title', 'Untitled'), plan.get('subtitle', ''))

        # Add content slides
        for slide_data in plan.get('slides', []):
            # Skip if this is redundant title slide data (slide_number 0)
            if slide_data.get('slide_number', 1) == 0:
                continue

            self._add_content_slide(slide_data)

        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"ppt_{timestamp}.pptx")

        # Save presentation
        self.prs.save(output_path)
        return output_path

    def _add_title_slide(self, title: str, subtitle: str) -> None:
        """
        Add a title slide to the presentation.

        Args:
            title: Main title text
            subtitle: Subtitle text
        """
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])  # Blank layout

        # Set background
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = self.BG_COLOR

        # Add title
        title_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(2.5), Inches(9), Inches(1.5)
        )
        title_frame = title_box.text_frame
        title_frame.text = title
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(48)
        title_para.font.bold = True
        title_para.font.color.rgb = self.TITLE_COLOR
        title_para.alignment = PP_ALIGN.CENTER

        # Add subtitle if provided
        if subtitle:
            subtitle_box = slide.shapes.add_textbox(
                Inches(0.5), Inches(4.2), Inches(9), Inches(1)
            )
            subtitle_frame = subtitle_box.text_frame
            subtitle_frame.text = subtitle
            subtitle_para = subtitle_frame.paragraphs[0]
            subtitle_para.font.size = self.SUBTITLE_FONT_SIZE
            subtitle_para.font.color.rgb = RGBColor(64, 64, 64)
            subtitle_para.alignment = PP_ALIGN.CENTER

    def _add_content_slide(self, slide_data: Dict) -> None:
        """
        Add a content slide to the presentation.

        Args:
            slide_data: Dictionary containing slide information
        """
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])  # Blank layout

        # Set background
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = self.BG_COLOR

        # Determine layout based on visual content
        has_visual = slide_data.get('visual', {}).get('type') not in [None, 'none']

        if has_visual:
            # Two-column layout: text on left, visual on right
            text_left = Inches(0.5)
            text_width = Inches(4.5)
            visual_left = Inches(5.5)
            visual_width = Inches(4)
        else:
            # Full-width text layout
            text_left = Inches(0.5)
            text_width = Inches(9)

        # Add title
        title_box = slide.shapes.add_textbox(text_left, Inches(0.5), text_width, Inches(0.8))
        title_frame = title_box.text_frame
        title_frame.text = slide_data.get('title', 'Untitled Slide')
        title_para = title_frame.paragraphs[0]
        title_para.font.size = self.TITLE_FONT_SIZE
        title_para.font.bold = True
        title_para.font.color.rgb = self.TITLE_COLOR

        # Add content bullets
        content = slide_data.get('content', [])
        if content:
            content_top = Inches(1.5)
            content_height = Inches(5.5)

            content_box = slide.shapes.add_textbox(
                text_left, content_top, text_width, content_height
            )
            content_frame = content_box.text_frame
            content_frame.word_wrap = True

            for i, bullet in enumerate(content):
                if i == 0:
                    p = content_frame.paragraphs[0]
                else:
                    p = content_frame.add_paragraph()

                p.text = str(bullet)
                p.font.size = self.BODY_FONT_SIZE
                p.font.color.rgb = self.BODY_COLOR
                p.level = 0
                p.space_before = Pt(6)

        # Add visual if present
        if has_visual:
            visual = slide_data.get('visual', {})
            visual_type = visual.get('type')

            visual_top = Inches(1.5)
            visual_height = Inches(5.5)

            if visual_type == 'image':
                self._add_image(slide, visual.get('source'), visual_left, visual_top, visual_width, visual_height)
            elif visual_type == 'chart':
                self._add_chart(slide, visual.get('chart_data', {}), visual_left, visual_top, visual_width, visual_height)
            elif visual_type == 'diagram':
                self._add_diagram(slide, visual.get('source', ''), visual_left, visual_top, visual_width, visual_height)

        # Add slide number
        self._add_slide_number(slide)

    def _add_image(self, slide, image_source: str, left: Inches, top: Inches, width: Inches, height: Inches) -> None:
        """
        Add an image to a slide.

        Args:
            slide: The slide object
            image_source: URL or file path to image
            left, top, width, height: Position and size
        """
        try:
            if image_source.startswith(('http://', 'https://')):
                # Download image from URL
                response = requests.get(image_source, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                image_data = BytesIO(response.content)

                # Verify it's a valid image
                img = Image.open(image_data)
                img.verify()
                image_data.seek(0)

                # Add to slide
                pic = slide.shapes.add_picture(image_data, left, top, width=width)

                # Center vertically within allocated space
                if pic.height < height:
                    pic.top = top + (height - pic.height) // 2

            elif os.path.exists(image_source):
                # Local file
                pic = slide.shapes.add_picture(image_source, left, top, width=width)
                if pic.height < height:
                    pic.top = top + (height - pic.height) // 2

        except Exception as e:
            # If image fails, add a placeholder text box
            placeholder = slide.shapes.add_textbox(left, top, width, height)
            text_frame = placeholder.text_frame
            text_frame.text = f"[Image unavailable]\n{str(e)[:50]}"
            p = text_frame.paragraphs[0]
            p.font.size = Pt(12)
            p.font.italic = True
            p.font.color.rgb = RGBColor(128, 128, 128)

    def _add_chart(self, slide, chart_data: Dict, left: Inches, top: Inches, width: Inches, height: Inches) -> None:
        """
        Add a chart to a slide.

        Args:
            slide: The slide object
            chart_data: Dictionary with 'categories' and 'values'
            left, top, width, height: Position and size
        """
        try:
            categories = chart_data.get('categories', [])
            values = chart_data.get('values', [])

            if not categories or not values:
                raise ValueError("Chart data missing categories or values")

            # Create chart data
            chart_data_obj = CategoryChartData()
            chart_data_obj.categories = categories
            chart_data_obj.add_series('Series 1', values)

            # Add chart to slide
            chart = slide.shapes.add_chart(
                XL_CHART_TYPE.COLUMN_CLUSTERED,
                left, top, width, height,
                chart_data_obj
            ).chart

            # Style chart
            chart.has_legend = False
            chart.chart_title.has_text_frame = False

        except Exception as e:
            # If chart fails, add a text representation
            text_box = slide.shapes.add_textbox(left, top, width, height)
            text_frame = text_box.text_frame
            text_frame.text = "[Chart]\n\n"

            try:
                categories = chart_data.get('categories', [])
                values = chart_data.get('values', [])
                for cat, val in zip(categories, values):
                    text_frame.text += f"{cat}: {val}\n"
            except:
                text_frame.text += "Chart data unavailable"

            p = text_frame.paragraphs[0]
            p.font.size = Pt(14)

    def _add_diagram(self, slide, description: str, left: Inches, top: Inches, width: Inches, height: Inches) -> None:
        """
        Add a diagram (as styled text) to a slide.

        Args:
            slide: The slide object
            description: Text description of the diagram
            left, top, width, height: Position and size
        """
        diagram_box = slide.shapes.add_textbox(left, top, width, height)
        text_frame = diagram_box.text_frame
        text_frame.word_wrap = True

        # Add diagram label
        text_frame.text = f"[Diagram]\n\n{description}"

        p = text_frame.paragraphs[0]
        p.font.size = Pt(14)
        p.font.italic = True
        p.font.color.rgb = RGBColor(64, 64, 128)

    def _add_slide_number(self, slide) -> None:
        """
        Add slide number to a slide.

        Args:
            slide: The slide object
        """
        # Get slide number (1-indexed, excluding title slide)
        slide_number = len(self.prs.slides)

        if slide_number > 1:  # Don't add to title slide
            number_box = slide.shapes.add_textbox(
                Inches(9), Inches(7), Inches(0.5), Inches(0.3)
            )
            text_frame = number_box.text_frame
            text_frame.text = str(slide_number)
            p = text_frame.paragraphs[0]
            p.font.size = self.SMALL_FONT_SIZE
            p.font.color.rgb = RGBColor(128, 128, 128)
            p.alignment = PP_ALIGN.RIGHT
