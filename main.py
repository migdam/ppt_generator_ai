#!/usr/bin/env python3
"""
AI-Powered HTML to PowerPoint Generator
Main CLI Application - Production Version

Usage:
    python main.py --url https://example.com/article
    python main.py --html myfile.html --slides 10 --style detailed
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional
from tqdm import tqdm

from modules.content_extractor import ContentExtractor
from modules.ai_generator import AIGenerator
from modules.ai_evaluator import AIEvaluator
from modules.pptx_builder import PPTXBuilder
from modules.logger import get_logger
from modules.config import get_config, ConfigManager
from modules.validators import InputValidator
from modules.metrics import get_metrics_collector, SessionMetrics

# Initialize logger
logger = get_logger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="AI-Powered HTML to PowerPoint Generator (Production)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --url https://example.com/article
  python main.py --html myfile.html --slides 10
  python main.py --url https://example.com --slides auto --style detailed

Environment Variables:
  GEMINI_API_KEY    - Google Gemini API key (required)
  QUALITY_THRESHOLD - Minimum quality score (default: 45)
  MAX_RETRIES       - Maximum retry attempts (default: 4)
        """
    )

    # Input source (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--url',
        type=str,
        help='URL to fetch content from'
    )
    input_group.add_argument(
        '--html',
        type=str,
        help='HTML filename in Input/ directory'
    )

    # Configuration options
    parser.add_argument(
        '--slides',
        type=str,
        default='auto',
        help="Number of slides ('auto' or integer, default: auto)"
    )
    parser.add_argument(
        '--style',
        type=str,
        choices=['general', 'detailed'],
        default='general',
        help='Presentation style (default: general)'
    )

    # Production options
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress bars'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )

    return parser.parse_args()


def validate_inputs(args: argparse.Namespace) -> bool:
    """
    Validate all input arguments.

    Args:
        args: Parsed command-line arguments

    Returns:
        True if all validations pass
    """
    logger.info("Validating inputs...")

    # Validate URL or file
    if args.url:
        is_valid, error_msg = InputValidator.validate_url(args.url)
        if not is_valid:
            print(f"❌ Invalid URL: {error_msg}")
            return False

    if args.html:
        config = get_config()
        is_valid, error_msg, _ = InputValidator.validate_file_path(
            args.html,
            base_dir=config.input_dir,
            must_exist=True
        )
        if not is_valid:
            print(f"❌ Invalid file path: {error_msg}")
            return False

    # Validate slide count
    is_valid, error_msg, _ = InputValidator.validate_slide_count(args.slides)
    if not is_valid:
        print(f"❌ Invalid slide count: {error_msg}")
        return False

    # Validate style
    is_valid, error_msg = InputValidator.validate_style(args.style)
    if not is_valid:
        print(f"❌ Invalid style: {error_msg}")
        return False

    logger.info("All inputs validated successfully")
    return True


def setup_environment(args: argparse.Namespace) -> bool:
    """
    Set up the runtime environment.

    Args:
        args: Parsed command-line arguments

    Returns:
        True if setup successful
    """
    config = get_config()

    # Create necessary directories
    for directory in [config.input_dir, config.output_dir, config.log_dir, "metrics"]:
        Path(directory).mkdir(exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")

    # Validate API key
    api_key = config.gemini_api_key
    is_valid, error_msg = InputValidator.validate_api_key(api_key)

    if not is_valid:
        print("❌ Error: GEMINI_API_KEY not found or invalid")
        print("\nPlease set your API key by adding this to ~/.zshrc or ~/.bashrc:")
        print('export GEMINI_API_KEY="your-api-key-here"')
        print("\nThen reload your shell configuration:")
        print("source ~/.zshrc")
        logger.error("API key validation failed")
        return False

    logger.info("Environment setup complete")
    return True


def main():
    """Main application entry point."""
    start_time = time.time()

    print("🚀 AI-Powered HTML to PowerPoint Generator (Production)")
    print("=" * 70)

    # Parse arguments
    args = parse_arguments()

    # Set up logging level
    if args.verbose:
        logger.setLevel(logger.DEBUG)

    logger.info("=" * 70)
    logger.info("Starting PPT Generator")
    logger.info(f"Arguments: {vars(args)}")

    # Load config
    if args.config:
        logger.info(f"Loading configuration from {args.config}")
        # Config loading logic here if needed

    config = get_config()

    # Validate inputs
    if not validate_inputs(args):
        logger.error("Input validation failed")
        sys.exit(1)

    # Setup environment
    if not setup_environment(args):
        logger.error("Environment setup failed")
        sys.exit(1)

    # Initialize metrics
    metrics_collector = get_metrics_collector()
    session = metrics_collector.start_session()

    try:
        # Step 1: Extract content
        print("\n📄 Step 1/4: Extracting content...")
        logger.info("Starting content extraction")

        extraction_start = time.time()
        extractor = ContentExtractor()

        if args.url:
            session.source_type = "url"
            session.source = args.url
            content, image_urls, title = extractor.extract_from_url(args.url)
        else:
            session.source_type = "file"
            session.source = args.html
            filepath = args.html
            content, image_urls, title = extractor.extract_from_file(filepath)

        session.extraction_time = time.time() - extraction_start
        session.content_length = len(content)
        session.images_found = len(image_urls)

        print(f"   ✓ Extracted {len(content.split())} words")
        print(f"   ✓ Found {len(image_urls)} images")
        print(f"   ✓ Title: {title}")
        logger.info(f"Extraction complete in {session.extraction_time:.2f}s")

        # Step 2: Determine number of slides
        print("\n📊 Step 2/4: Planning presentation...")

        if args.slides.lower() == 'auto':
            num_slides = extractor.calculate_suggested_slides(content)
            print(f"   ✓ Calculated {num_slides} slides based on content length")
        else:
            num_slides = int(args.slides)
            # Validate range
            num_slides = max(config.min_slides, min(config.max_slides, num_slides))

        session.num_slides_requested = num_slides
        print(f"   ✓ Style: {args.style}")
        print(f"   ✓ Target slides: {num_slides}")

        # Step 3: Generate presentation plan with feedback loop
        print(f"\n🤖 Step 3/4: Generating presentation with AI quality control...")
        logger.info("Starting AI generation with feedback loop")

        generation_start = time.time()

        api_key = config.gemini_api_key
        generator = AIGenerator(api_key)
        evaluator = AIEvaluator(api_key)

        # Create progress bar if enabled
        if not args.no_progress:
            pbar = tqdm(
                total=config.max_quality_attempts,
                desc="Quality iterations",
                unit="attempt",
                ncols=70
            )
        else:
            pbar = None

        plan, score, history = evaluator.generate_with_feedback_loop(
            generator=generator,
            content=content,
            title=title,
            num_slides=num_slides,
            style=args.style,
            image_urls=image_urls
        )

        if pbar:
            pbar.n = len(history)
            pbar.close()

        session.generation_time = time.time() - generation_start
        session.quality_attempts = len(history)
        session.final_quality_score = score
        session.api_calls_made = len(history) * 2  # Generate + evaluate per attempt

        if not plan:
            error_msg = "Failed to generate a valid presentation plan"
            logger.error(error_msg)
            print(f"\n❌ Error: {error_msg}")
            session.finish("failed", error_msg)
            metrics_collector.save_session(session)
            sys.exit(1)

        session.num_slides_generated = len(plan.get('slides', []))

        print(f"\n   ✅ Final plan generated:")
        print(f"      • Quality score: {score}/{config.max_quality_score}")
        print(f"      • Attempts: {len(history)}")
        print(f"      • Total slides: {len(plan.get('slides', []))} + title slide")
        logger.info(f"Generation complete in {session.generation_time:.2f}s")

        # Step 4: Build PowerPoint presentation
        print(f"\n📊 Step 4/4: Building PowerPoint presentation...")
        logger.info("Starting PPTX building")

        building_start = time.time()
        builder = PPTXBuilder()

        output_path = builder.build_presentation(plan, output_dir=config.output_dir)

        session.building_time = time.time() - building_start
        session.output_file = output_path

        # Get output file size
        output_size = Path(output_path).stat().st_size / 1024  # KB
        session.output_size_kb = output_size

        print(f"\n✅ Success! Presentation saved to:")
        print(f"   {output_path}")
        logger.info(f"Building complete in {session.building_time:.2f}s")

        # Display summary
        total_time = time.time() - start_time
        print("\n📈 Generation Summary:")
        print(f"   • Source: {args.url if args.url else args.html}")
        print(f"   • Content: {len(content.split())} words, {len(image_urls)} images")
        print(f"   • Slides: {len(plan.get('slides', []))} + 1 title slide")
        print(f"   • Quality: {score}/{config.max_quality_score} (after {len(history)} attempts)")
        print(f"   • Output: {output_size:.1f} KB")
        print(f"   • Time: {total_time:.1f}s (extract: {session.extraction_time:.1f}s, "
              f"AI: {session.generation_time:.1f}s, build: {session.building_time:.1f}s)")

        print("\n" + "=" * 70)
        print("🎉 Done!")

        # Mark session as successful
        session.finish("success")
        metrics_collector.save_session(session)

        logger.info(f"Total execution time: {total_time:.2f}s")
        logger.info("Session completed successfully")

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        logger.warning("User interrupted execution")
        session.finish("cancelled", "User interrupted")
        metrics_collector.save_session(session)
        return 130

    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Error: {error_msg}")
        logger.error(f"Fatal error: {error_msg}", exc_info=True)

        session.finish("failed", error_msg)
        session.api_errors = 1
        metrics_collector.save_session(session)

        if args.verbose:
            import traceback
            traceback.print_exc()

        return 1


if __name__ == '__main__':
    sys.exit(main())
