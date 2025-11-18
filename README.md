# AI-Powered HTML to PowerPoint Generator

**Version:** 2.0 (Production)
**Status:** Production-Ready

## Overview

The **PPT Generator** is a command-line tool that automates the conversion of HTML content (from web URLs or local files) into professional, visually appealing PowerPoint presentations. It leverages Google's Gemini AI to synthesize content, structure slides, and iteratively improve the presentation's visual quality through a self-correcting feedback loop.

## Features

### Core Features
- ✅ Convert web pages (URLs) to PowerPoint presentations
- ✅ Convert local HTML files to presentations
- ✅ AI-powered content synthesis and slide structuring
- ✅ Automatic image extraction and inclusion
- ✅ Quality control through AI evaluation (feedback loop)
- ✅ Native PowerPoint charts generation
- ✅ Configurable slide count and presentation style
- ✅ Professional styling with customizable layouts

### Production Features
- 🔒 **Security**: Input validation, path traversal protection, API key management
- 📊 **Monitoring**: Comprehensive logging, metrics collection, health checks
- 🔄 **Reliability**: Retry logic with exponential backoff, error recovery
- ⚙️  **Configuration**: Environment variables, config files, Docker support
- 📈 **Progress Tracking**: Progress bars, verbose logging, detailed summaries
- 🐳 **Deployment**: Docker, Docker Compose, Kubernetes support
- ✅ **Testing**: Comprehensive test suite with pytest
- 📝 **Observability**: Structured logging, JSON metrics, monitoring CLI

## Installation

### Prerequisites

- Python 3.9+
- Conda (recommended) or pip
- Google Gemini API key

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ppt_generator_ai
   ```

2. **Create conda environment:**
   ```bash
   conda env create -f environment.yml
   conda activate ppt_generator
   ```

3. **Set up API key:**

   Add your Gemini API key to your `~/.zshrc` (or `~/.bashrc`):
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

   Then reload your shell configuration:
   ```bash
   source ~/.zshrc
   ```

## Usage

### Basic Usage

**Convert a web page:**
```bash
python main.py --url https://example.com/article
```

**Convert a local HTML file:**
```bash
python main.py --html myfile.html
```

### Advanced Options

**Specify number of slides:**
```bash
python main.py --url https://example.com --slides 10
```

**Auto-calculate slides based on content:**
```bash
python main.py --url https://example.com --slides auto
```

**Choose presentation style:**
```bash
# Concise, high-level overview
python main.py --url https://example.com --style general

# Comprehensive, detailed analysis
python main.py --url https://example.com --style detailed
```

### Full Example

```bash
python main.py --url https://en.wikipedia.org/wiki/Artificial_intelligence --slides 8 --style general
```

## Command-Line Arguments

| Argument | Required | Description | Default |
|----------|----------|-------------|---------|
| `--url` | Yes* | URL to fetch content from | - |
| `--html` | Yes* | HTML filename in Input/ directory | - |
| `--slides` | No | Number of slides ('auto' or integer) | auto |
| `--style` | No | Presentation style ('general' or 'detailed') | general |

*One of `--url` or `--html` must be provided.

## How It Works

1. **Content Extraction**: Fetches and parses HTML using BeautifulSoup
2. **AI Planning**: Gemini AI creates a structured presentation plan
3. **Quality Evaluation**: AI evaluates the plan against a rubric (50-point scale)
4. **Feedback Loop**: If score < 45, regenerates plan with feedback (max 5 attempts)
5. **Presentation Generation**: Creates .pptx file with images, charts, and styled content
6. **Output**: Saves timestamped file to Output/ directory

## Project Structure

```
ppt_generator_ai/
├── main.py                 # CLI entry point
├── modules/
│   ├── content_extractor.py   # HTML parsing and extraction
│   ├── ai_generator.py        # Gemini AI integration
│   ├── ai_evaluator.py        # Quality control system
│   └── pptx_builder.py        # PowerPoint generation
├── Input/                  # Local HTML files (auto-created)
├── Output/                 # Generated presentations (auto-created)
├── environment.yml         # Conda environment specification
└── README.md
```

## Output

Generated presentations include:
- **Title Slide**: Main title and subtitle
- **Content Slides**: Structured information with:
  - Titles (36pt, Dark Blue, Bold)
  - Body text (24pt, Black)
  - Images (centered, auto-downloaded)
  - Charts (native PowerPoint charts)
  - Diagrams (text descriptions)
- **Styling**: Light blue background (RGB 240, 248, 255)
- **Slide numbers**: On all slides except title

Files are saved as `Output/ppt_YYYYMMDD_HHMMSS.pptx`

## Troubleshooting

**API Key Error:**
```
Error: GEMINI_API_KEY not found in environment
```
Solution: Ensure the API key is exported in your shell configuration file.

**Network Errors:**
- Check internet connection
- Verify URL is accessible
- Some sites may block automated requests

**Image Download Failures:**
- Images may not be publicly accessible
- CORS or authentication required
- Tool will skip failed images and continue

## Future Enhancements

- 📄 Direct PDF and DOCX input support via CLI
- 🎨 Custom template support (.potx files)
- 🌐 Web interface (Flask/Streamlit)
- 🖼️ AI image generation integration
- 📊 Advanced chart types

## License

[Specify your license here]

## Contributing

[Contribution guidelines here]

## Support

For issues and questions, please open an issue on GitHub.
