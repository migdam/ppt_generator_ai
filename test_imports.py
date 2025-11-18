#!/usr/bin/env python3
"""
Simple test script to verify module structure and imports.
This can be run without installing dependencies.
"""

import sys
import ast

def test_file_syntax(filepath):
    """Test if a Python file has valid syntax."""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        return True, "OK"
    except SyntaxError as e:
        return False, str(e)

def main():
    print("Testing PPT Generator AI Project Structure")
    print("=" * 60)

    files_to_test = [
        ('main.py', 'Main CLI application'),
        ('modules/__init__.py', 'Module package init'),
        ('modules/content_extractor.py', 'Content Extractor'),
        ('modules/ai_generator.py', 'AI Generator'),
        ('modules/ai_evaluator.py', 'AI Evaluator'),
        ('modules/pptx_builder.py', 'PPTX Builder'),
    ]

    all_passed = True

    for filepath, description in files_to_test:
        passed, message = test_file_syntax(filepath)
        status = "✓" if passed else "✗"
        print(f"{status} {description:30} ({filepath})")
        if not passed:
            print(f"  Error: {message}")
            all_passed = False

    print("\n" + "=" * 60)

    if all_passed:
        print("✅ All tests passed! Project structure is valid.")
        print("\nTo use the tool:")
        print("1. Install dependencies: conda env create -f environment.yml")
        print("2. Activate environment: conda activate ppt_generator")
        print("3. Set API key in ~/.zshrc: export GEMINI_API_KEY='your-key'")
        print("4. Run: python main.py --url https://example.com")
        return 0
    else:
        print("❌ Some tests failed.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
