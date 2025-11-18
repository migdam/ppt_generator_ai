# Usage Examples

This document provides detailed examples of how to use the PPT Generator AI tool.

## Prerequisites

Before running these examples, ensure you have:

1. Installed the conda environment: `conda env create -f environment.yml`
2. Activated the environment: `conda activate ppt_generator`
3. Set your Gemini API key in `~/.zshrc` or `~/.bashrc`

## Example 1: Basic URL Conversion

Convert a Wikipedia article to a presentation:

```bash
python main.py --url https://en.wikipedia.org/wiki/Machine_learning
```

**What happens:**
- Extracts content from the Wikipedia page
- Auto-calculates the optimal number of slides based on content length
- Uses 'general' style (concise, high-level overview)
- Generates a .pptx file in the Output/ directory

## Example 2: URL with Custom Slide Count

Generate exactly 10 slides from a blog post:

```bash
python main.py --url https://blog.example.com/ai-trends-2024 --slides 10
```

**What happens:**
- Fetches content from the URL
- Creates exactly 10 slides (including the title slide)
- AI organizes content to fit the specified slide count

## Example 3: Detailed Style Presentation

Create a comprehensive, detailed presentation:

```bash
python main.py --url https://example.com/research-paper --style detailed
```

**What happens:**
- Uses 'detailed' style for in-depth analysis
- Includes more supporting details and examples
- Better suited for technical or academic content

## Example 4: Local HTML File

Convert a local HTML file to a presentation:

```bash
python main.py --html sample.html
```

**What happens:**
- Reads `Input/sample.html`
- Extracts text and any images referenced in the HTML
- Generates the presentation

## Example 5: Local File with Custom Settings

```bash
python main.py --html report.html --slides 8 --style detailed
```

**What happens:**
- Reads `Input/report.html`
- Creates exactly 8 slides with detailed content
- Ideal for internal reports or documentation

## Example 6: Short Article (Auto Slides)

```bash
python main.py --url https://example.com/short-article --slides auto
```

**What happens:**
- Analyzes word count (~300 words = 3 slides, ~600 words = 5 slides, etc.)
- Automatically determines optimal slide count
- Prevents too many or too few slides

## Example 7: Technical Documentation

```bash
python main.py --url https://docs.python.org/3/tutorial/ --slides 12 --style detailed
```

**What happens:**
- Extracts technical content
- Creates detailed slides with code examples (if present)
- Uses 12 slides to cover the tutorial comprehensively

## Understanding the Output

Every generated presentation includes:

### Slide 0: Title Slide
- Main title (extracted from page title)
- Subtitle (if provided by AI)
- Clean, centered layout

### Slides 1+: Content Slides
- Title (36pt, dark blue, bold)
- 3-5 bullet points (24pt, black)
- Visual content (images, charts, or diagrams) on ~60-70% of slides
- Slide numbers (bottom right)

### Visual Types:
1. **Images:** Downloaded from source HTML or URLs
2. **Charts:** Native PowerPoint column charts with data
3. **Diagrams:** Text descriptions of conceptual visuals
4. **None:** Text-only slides when appropriate

## Quality Control Process

The tool uses an AI feedback loop:

1. **Generation:** AI creates a presentation plan
2. **Evaluation:** AI judges the plan (score out of 50)
3. **Feedback:** If score < 45, regenerate with improvements
4. **Iteration:** Up to 5 attempts to meet quality threshold

You'll see output like:

```
🔄 Attempt 1/5: Generating presentation plan...
📊 Evaluating plan quality...
📈 Score: 42/50
⚠️  Score below threshold. Regenerating with feedback...

🔄 Attempt 2/5: Generating presentation plan...
📊 Evaluating plan quality...
📈 Score: 47/50
✅ Plan meets quality threshold (47 >= 45)
```

## Troubleshooting Examples

### Example: Invalid URL

```bash
python main.py --url https://invalid-url-that-doesnt-exist.com
```

**Expected output:**
```
❌ Error: Failed to fetch URL: [error details]
```

### Example: Missing HTML File

```bash
python main.py --html nonexistent.html
```

**Expected output:**
```
❌ Error: File not found: Input/nonexistent.html
```

### Example: No API Key

If `GEMINI_API_KEY` is not set:

```
❌ Error: GEMINI_API_KEY not found in environment

Please set your API key by adding this to ~/.zshrc or ~/.bashrc:
export GEMINI_API_KEY="your-api-key-here"
```

## Advanced Tips

### 1. Optimal Slide Counts

- **Short articles (< 500 words):** 3-5 slides
- **Medium articles (500-1500 words):** 7-10 slides
- **Long articles (> 1500 words):** 12-15 slides

### 2. When to Use 'detailed' Style

- Research papers
- Technical documentation
- Training materials
- Academic content

### 3. When to Use 'general' Style

- Blog posts
- News articles
- Marketing content
- Executive summaries

### 4. Image Availability

- The tool extracts images from the source HTML
- Images must be publicly accessible URLs
- If images fail to download, placeholders are used
- Not all websites allow image downloading due to CORS/authentication

### 5. Best Sources

**Good sources:**
- Wikipedia articles
- Blog posts with clean HTML
- Documentation sites
- News articles

**Challenging sources:**
- Sites with heavy JavaScript (content may not load)
- Sites with paywalls or login requirements
- Sites that block automated requests

## File Locations

- **Input HTML files:** `Input/`
- **Generated presentations:** `Output/ppt_YYYYMMDD_HHMMSS.pptx`
- **Configuration:** `environment.yml`
- **Modules:** `modules/`

## Complete Workflow Example

```bash
# 1. Ensure environment is activated
conda activate ppt_generator

# 2. (Optional) Place an HTML file in Input/
cp ~/Documents/article.html Input/

# 3. Run the generator
python main.py --url https://en.wikipedia.org/wiki/Neural_network --slides 8 --style general

# 4. Find your presentation in Output/
ls -lh Output/

# 5. Open the presentation
# On macOS: open Output/ppt_20251118_103045.pptx
# On Linux: xdg-open Output/ppt_20251118_103045.pptx
# On Windows: start Output/ppt_20251118_103045.pptx
```

## Getting Help

View all available options:

```bash
python main.py --help
```

Output:
```
usage: main.py [-h] (--url URL | --html HTML) [--slides SLIDES] [--style {general,detailed}]

AI-Powered HTML to PowerPoint Generator

options:
  -h, --help            show this help message and exit
  --url URL             URL to fetch content from
  --html HTML           HTML filename in Input/ directory
  --slides SLIDES       Number of slides ('auto' or integer, default: auto)
  --style {general,detailed}
                        Presentation style (default: general)
```
