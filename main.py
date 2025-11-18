#!/usr/bin/env python3
"""
AI-Powered HTML to PowerPoint Generator
Main CLI Application

Usage:
    python main.py --url https://example.com/article
    python main.py --html myfile.html --slides 10 --style detailed
"""

import argparse
import sys
import os
from typing import Optional

from modules.content_extractor import ContentExtractor
from modules.ai_generator import AIGenerator
from modules.ai_evaluator import AIEvaluator
from modules.pptx_builder import PPTXBuilder


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="AI-Powered HTML to PowerPoint Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --url https://example.com/article
  python main.py --html myfile.html --slides 10
  python main.py --url https://example.com --slides auto --style detailed
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

    return parser.parse_args()


def validate_api_key(api_key: Optional[str]) -> str:
    """
    Validate that an API key is present.

    Args:
        api_key: The API key to validate

    Returns:
        The validated API key

    Raises:
        SystemExit if no API key found
    """
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in environment")
        print("\nPlease set your API key by adding this to ~/.zshrc or ~/.bashrc:")
        print('export GEMINI_API_KEY="your-api-key-here"')
        print("\nThen reload your shell configuration:")
        print("source ~/.zshrc")
        sys.exit(1)

    return api_key


def main():
    """Main application entry point."""
    print("🚀 AI-Powered HTML to PowerPoint Generator")
    print("=" * 60)

    # Parse arguments
    args = parse_arguments()

    # Validate API key
    api_key = AIGenerator.get_api_key_from_env()
    api_key = validate_api_key(api_key)

    try:
        # Step 1: Extract content
        print("\n📄 Step 1: Extracting content...")
        extractor = ContentExtractor()

        if args.url:
            print(f"   Source: {args.url}")
            content, image_urls, title = extractor.extract_from_url(args.url)
        else:
            # HTML file from Input directory
            filepath = os.path.join('Input', args.html)
            print(f"   Source: {filepath}")
            content, image_urls, title = extractor.extract_from_file(filepath)

        print(f"   ✓ Extracted {len(content.split())} words")
        print(f"   ✓ Found {len(image_urls)} images")
        print(f"   ✓ Title: {title}")

        # Step 2: Determine number of slides
        if args.slides.lower() == 'auto':
            num_slides = extractor.calculate_suggested_slides(content)
            print(f"\n📊 Calculated {num_slides} slides based on content length")
        else:
            try:
                num_slides = int(args.slides)
                if num_slides < 2:
                    print("⚠️  Warning: Minimum 2 slides required (title + 1 content). Using 2.")
                    num_slides = 2
                elif num_slides > 20:
                    print("⚠️  Warning: Maximum 20 slides recommended. Using 20.")
                    num_slides = 20
            except ValueError:
                print(f"❌ Error: Invalid slides value '{args.slides}'. Use 'auto' or an integer.")
                sys.exit(1)

        print(f"   Style: {args.style}")
        print(f"   Target slides: {num_slides}")

        # Step 3: Generate presentation plan with feedback loop
        print("\n🤖 Step 2: Generating presentation plan with AI quality control...")

        generator = AIGenerator(api_key)
        evaluator = AIEvaluator(api_key)

        plan, score, history = evaluator.generate_with_feedback_loop(
            generator=generator,
            content=content,
            title=title,
            num_slides=num_slides,
            style=args.style,
            image_urls=image_urls
        )

        if not plan:
            print("❌ Error: Failed to generate a valid presentation plan")
            sys.exit(1)

        print(f"\n✅ Final plan generated:")
        print(f"   Quality score: {score}/{AIEvaluator.MAX_SCORE}")
        print(f"   Attempts: {len(history)}")
        print(f"   Total slides: {len(plan.get('slides', []))} + title slide")

        # Step 4: Build PowerPoint presentation
        print("\n📊 Step 3: Building PowerPoint presentation...")
        builder = PPTXBuilder()

        output_path = builder.build_presentation(plan, output_dir='Output')

        print(f"\n✅ Success! Presentation saved to:")
        print(f"   {output_path}")

        # Display summary
        print("\n📈 Generation Summary:")
        print(f"   - Source: {args.url if args.url else args.html}")
        print(f"   - Content: {len(content.split())} words")
        print(f"   - Images: {len(image_urls)} available")
        print(f"   - Slides: {len(plan.get('slides', []))} + 1 title slide")
        print(f"   - Quality score: {score}/{AIEvaluator.MAX_SCORE}")
        print(f"   - AI attempts: {len(history)}")
        print(f"   - Output: {output_path}")

        print("\n" + "=" * 60)
        print("🎉 Done!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
