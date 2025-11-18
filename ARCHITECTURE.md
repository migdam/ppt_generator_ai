# System Architecture

This document describes the technical architecture of the AI-Powered HTML to PowerPoint Generator.

## Overview

The system follows a modular architecture with clear separation of concerns:

```
┌─────────────┐
│   main.py   │  ← CLI Entry Point
└──────┬──────┘
       │
       ├─────────────────────────────────────────┐
       │                                         │
       ▼                                         ▼
┌──────────────────┐                    ┌──────────────┐
│ ContentExtractor │                    │ AIGenerator  │
└──────────────────┘                    └──────┬───────┘
       │                                        │
       │ Extracted Content                      │ Plan Request
       │ + Images                               │
       │                                        │
       └────────────────┬───────────────────────┘
                        │
                        ▼
                 ┌──────────────┐
                 │ AIEvaluator  │
                 └──────┬───────┘
                        │
                        │ Feedback Loop
                        │ (Score < 45)
                        │
                        ▼
                 ┌──────────────┐
                 │ Final Plan   │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │ PPTXBuilder  │
                 └──────┬───────┘
                        │
                        ▼
                  .pptx File
```

## Module Descriptions

### 1. main.py
**Responsibility:** CLI interface and workflow orchestration

**Key Functions:**
- `parse_arguments()`: Parses command-line arguments using argparse
- `validate_api_key()`: Ensures Gemini API key is available
- `main()`: Orchestrates the entire presentation generation workflow

**Dependencies:**
- All module classes
- argparse, sys, os

### 2. modules/content_extractor.py
**Responsibility:** HTML parsing and content extraction

**Class:** `ContentExtractor`

**Key Methods:**
- `extract_from_url(url)`: Fetches and parses web content
- `extract_from_file(filepath)`: Reads and parses local HTML files
- `_parse_html(html_content, base_url)`: Internal HTML parsing logic
- `calculate_suggested_slides(text)`: Heuristic for slide count

**Technologies:**
- BeautifulSoup4 (with lxml parser)
- requests (for HTTP fetching)
- urllib.parse (for URL resolution)

**Output:**
```python
(clean_text: str, image_urls: List[str], page_title: str)
```

### 3. modules/ai_generator.py
**Responsibility:** AI-powered presentation plan generation

**Class:** `AIGenerator`

**Key Methods:**
- `__init__(api_key)`: Initializes Gemini AI model
- `generate_presentation_plan(...)`: Creates structured JSON plan
- `_validate_plan(plan, expected_slides)`: Validates plan structure
- `get_api_key_from_env()`: Static method to retrieve API key

**Technologies:**
- google-generativeai (Gemini 1.5 Flash)
- JSON parsing and validation

**Plan Structure:**
```json
{
  "title": "Main Title",
  "subtitle": "Subtitle",
  "slides": [
    {
      "slide_number": 1,
      "title": "Slide Title",
      "content": ["Point 1", "Point 2"],
      "visual": {
        "type": "image|chart|diagram|none",
        "source": "url or description",
        "chart_data": {
          "categories": ["A", "B"],
          "values": [10, 20]
        }
      }
    }
  ]
}
```

### 4. modules/ai_evaluator.py
**Responsibility:** Quality control through AI feedback loop

**Class:** `AIEvaluator`

**Constants:**
- `PASSING_SCORE = 45`
- `MAX_SCORE = 50`
- `MAX_ATTEMPTS = 5`

**Key Methods:**
- `evaluate_plan(plan)`: Scores a plan against rubric
- `generate_with_feedback_loop(...)`: Iterative improvement process

**Evaluation Rubric:**
1. Content Alignment (10 pts)
2. Visual Balance (10 pts)
3. Design Consistency (10 pts)
4. Visual Relevance (10 pts)
5. Professional Appeal (10 pts)

**Workflow:**
```
Generate → Evaluate → Score ≥ 45? → YES → Return plan
                         ↓ NO
                    Add feedback → Regenerate (max 5 times)
```

### 5. modules/pptx_builder.py
**Responsibility:** PowerPoint file generation

**Class:** `PPTXBuilder`

**Style Constants:**
- Background: RGB(240, 248, 255) - Light Blue
- Title: RGB(0, 51, 102) - Dark Blue, 36pt, Bold
- Body: RGB(0, 0, 0) - Black, 24pt
- Slide Numbers: 14pt, Gray

**Key Methods:**
- `build_presentation(plan, output_dir)`: Main builder method
- `_add_title_slide(title, subtitle)`: Creates title slide
- `_add_content_slide(slide_data)`: Creates content slides
- `_add_image(slide, source, ...)`: Downloads and adds images
- `_add_chart(slide, chart_data, ...)`: Creates native PPT charts
- `_add_diagram(slide, description, ...)`: Renders diagram descriptions
- `_add_slide_number(slide)`: Adds slide numbering

**Technologies:**
- python-pptx (PowerPoint manipulation)
- requests (image downloading)
- Pillow (image validation)

**Layout Strategy:**
- Title slide: Centered title and subtitle
- Content with visual: 2-column (text left, visual right)
- Content without visual: Full-width text

## Data Flow

### 1. Input Phase
```
User → CLI Arguments → main.py
                        ├─ URL or HTML file
                        ├─ Slide count (auto or integer)
                        └─ Style (general or detailed)
```

### 2. Extraction Phase
```
ContentExtractor
├─ Fetch HTML (from URL or file)
├─ Parse with BeautifulSoup
├─ Remove scripts, styles, nav, footer
├─ Extract clean text
├─ Find all <img> tags
├─ Resolve relative URLs to absolute
└─ Return (text, images, title)
```

### 3. AI Generation Phase
```
AIGenerator
├─ Format prompt with content + context
├─ Include available images
├─ Specify slide count and style
├─ Include feedback (if retry)
├─ Call Gemini API
├─ Parse JSON response
├─ Validate structure
└─ Return plan dict
```

### 4. Evaluation Phase
```
AIEvaluator
├─ Attempt 1: Generate plan
├─ Evaluate against rubric
├─ Score < 45?
│   ├─ YES: Generate feedback → Retry (max 5)
│   └─ NO: Accept plan
└─ Return (plan, score, history)
```

### 5. Generation Phase
```
PPTXBuilder
├─ Create Presentation object
├─ Add title slide
├─ For each content slide:
│   ├─ Add title and bullets
│   ├─ Check for visual
│   │   ├─ Image: Download and insert
│   │   ├─ Chart: Create native PPT chart
│   │   ├─ Diagram: Render as text box
│   │   └─ None: Text-only layout
│   └─ Add slide number
├─ Save as .pptx
└─ Return file path
```

## Error Handling Strategy

### Network Errors
- **Location:** ContentExtractor, PPTXBuilder
- **Strategy:** Try-except with informative messages
- **Fallback:** Skip failed images, continue processing

### API Errors
- **Location:** AIGenerator, AIEvaluator
- **Strategy:** Catch and re-raise with context
- **Retry Logic:** Evaluator handles retries internally

### Validation Errors
- **Location:** AIGenerator._validate_plan()
- **Strategy:** Raise ValueError with specific issue
- **Impact:** Triggers retry in feedback loop

### File System Errors
- **Location:** ContentExtractor, PPTXBuilder
- **Strategy:** os.makedirs(exist_ok=True) for directories
- **Impact:** Auto-create Input/ and Output/ as needed

## Configuration Management

### Environment Variables
- `GEMINI_API_KEY`: Required for AI operations
- **Sources:**
  1. os.environ
  2. ~/.zshrc (parsed manually)

### Hard-coded Configurations
- Model: `gemini-1.5-flash`
- Colors: Light blue theme
- Font sizes: 36pt title, 24pt body
- Max attempts: 5
- Passing score: 45/50

### User-configurable Options
- Slide count (CLI)
- Style (CLI)
- Input source (CLI)

## Dependencies

### Core Python Libraries
- argparse: CLI argument parsing
- json: Plan structure serialization
- os: File system operations
- sys: System operations and exit codes
- datetime: Timestamp generation

### External Libraries
- **google-generativeai** ≥0.3.0: Gemini API client
- **python-pptx** ≥0.6.21: PowerPoint generation
- **requests** ≥2.28.0: HTTP requests
- **beautifulsoup4** ≥4.11.0: HTML parsing
- **lxml** ≥4.9.0: HTML parser backend
- **Pillow** ≥9.0.0: Image handling

## Performance Considerations

### API Calls
- **Count:** 2N + 1 (N = number of attempts)
  - N plan generation calls
  - N evaluation calls
  - 1 final plan (if successful)
- **Timing:** ~3-10 seconds per call
- **Cost:** Based on Gemini API pricing

### Image Processing
- Downloaded on-demand during PPT generation
- Validated with Pillow before insertion
- Failed downloads skip gracefully

### Memory Usage
- HTML content truncated to 8000 chars for prompts
- Images loaded as BytesIO streams
- Plans stored as dict structures

## Security Considerations

### API Key Management
- Never hardcoded in source
- Read from environment or shell config
- Not logged or printed

### URL Validation
- Uses requests library (handles redirects, SSL)
- Timeout: 30 seconds for page fetch, 10 seconds for images
- User-Agent header to avoid bot blocks

### HTML Parsing
- BeautifulSoup handles malformed HTML safely
- Removes script and style tags automatically
- No code execution from HTML content

### File System Access
- Input files restricted to Input/ directory
- Output files written to Output/ directory
- No path traversal vulnerabilities (os.path.join used correctly)

## Extensibility Points

### Adding New Visual Types
**Location:** `pptx_builder.py`

Add new method:
```python
def _add_new_visual(self, slide, data, left, top, width, height):
    # Implementation
    pass
```

Update `_add_content_slide()` to handle new type.

### Adding New Input Formats
**Location:** `content_extractor.py`

Add new method:
```python
def extract_from_pdf(self, filepath):
    # PDF parsing logic
    return (text, images, title)
```

Update CLI to accept new argument.

### Custom Styling
**Location:** `pptx_builder.py`

Modify class constants:
```python
BG_COLOR = RGBColor(...)
TITLE_COLOR = RGBColor(...)
# etc.
```

Or add method to load from .potx template file.

### Different AI Models
**Location:** `ai_generator.py`, `ai_evaluator.py`

Change model string:
```python
self.model = genai.GenerativeModel('gemini-1.5-pro')
```

## Testing Strategy

### Unit Tests (Future)
- ContentExtractor: Mock HTML responses
- AIGenerator: Mock API responses
- PPTXBuilder: Verify slide structure

### Integration Tests (Future)
- End-to-end workflow with sample HTML
- Verify output file exists and is valid .pptx

### Manual Testing
- Sample HTML file provided in Input/
- Test various URLs (Wikipedia, blogs, docs)
- Verify visual types render correctly

## Future Enhancements

### Planned Features (from PRD)
1. PDF and DOCX direct input
2. Custom .potx template support
3. Web interface (Flask/Streamlit)
4. AI image generation integration

### Technical Improvements
1. Async API calls for better performance
2. Caching of API responses
3. Batch image downloads
4. Progress bars for long operations
5. Logging framework integration
6. Configuration file support (YAML/JSON)
