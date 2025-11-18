#!/usr/bin/env python3
"""
Monitoring and Metrics Viewer
View application metrics and health status.
"""

import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
from modules.metrics import get_metrics_collector


def show_summary(days: int = 7):
    """Show summary statistics."""
    collector = get_metrics_collector()
    stats = collector.get_summary_stats(days=days)

    print(f"\n📊 Summary Statistics (Last {days} days)")
    print("=" * 70)
    print(f"Total Sessions:        {stats['total_sessions']}")
    print(f"Successful:            {stats['successful_sessions']} "
          f"({stats['successful_sessions']/max(stats['total_sessions'], 1)*100:.1f}%)")
    print(f"Failed:                {stats['failed_sessions']}")
    print(f"Total API Calls:       {stats['total_api_calls']}")
    print(f"Slides Generated:      {stats['total_slides_generated']}")
    print(f"Average Quality Score: {stats['avg_quality_score']:.1f}/50")
    print(f"Average Time:          {stats['avg_generation_time']:.1f}s")
    print(f"Total Errors:          {stats['total_errors']}")
    print("=" * 70)


def show_recent(count: int = 10):
    """Show recent sessions."""
    metrics_dir = Path("metrics")
    sessions = []

    # Read all metrics files
    for metrics_file in sorted(metrics_dir.glob("metrics_*.jsonl"), reverse=True):
        try:
            with open(metrics_file, 'r') as f:
                for line in f:
                    session_data = json.loads(line)
                    sessions.append(session_data)
                    if len(sessions) >= count:
                        break
            if len(sessions) >= count:
                break
        except Exception as e:
            print(f"Error reading {metrics_file}: {e}")

    if not sessions:
        print("\n⚠️  No metrics found")
        return

    print(f"\n📋 Recent Sessions (Last {len(sessions)})")
    print("=" * 70)
    print(f"{'Time':<20} {'Source':<30} {'Status':<10} {'Score':<7} {'Time':<7}")
    print("-" * 70)

    for session in sessions[:count]:
        timestamp = datetime.fromtimestamp(session['start_time'])
        time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        source = session.get('source', 'Unknown')[:28]
        status = session.get('status', 'unknown')
        score = session.get('final_quality_score', 0)
        total_time = session.get('total_time', 0)

        status_icon = {
            'success': '✅',
            'failed': '❌',
            'cancelled': '⚠️'
        }.get(status, '❓')

        print(f"{time_str:<20} {source:<30} {status_icon} {status:<8} {score:<7} {total_time:.1f}s")

    print("=" * 70)


def show_errors(days: int = 7):
    """Show recent errors."""
    metrics_dir = Path("metrics")
    errors = []

    cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)

    # Read metrics files
    for metrics_file in sorted(metrics_dir.glob("metrics_*.jsonl"), reverse=True):
        try:
            with open(metrics_file, 'r') as f:
                for line in f:
                    session_data = json.loads(line)
                    if (session_data.get('status') == 'failed' and
                        session_data['start_time'] >= cutoff_date):
                        errors.append(session_data)
        except Exception as e:
            print(f"Error reading {metrics_file}: {e}")

    if not errors:
        print(f"\n✅ No errors in the last {days} days")
        return

    print(f"\n❌ Errors (Last {days} days)")
    print("=" * 70)

    for i, error in enumerate(errors[:20], 1):
        timestamp = datetime.fromtimestamp(error['start_time'])
        time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        source = error.get('source', 'Unknown')
        error_msg = error.get('error_message', 'No error message')

        print(f"\n{i}. {time_str}")
        print(f"   Source: {source}")
        print(f"   Error: {error_msg}")

    print("=" * 70)


def show_health():
    """Show system health status."""
    print("\n🏥 System Health Check")
    print("=" * 70)

    # Check directories
    dirs = {
        'Input': Path('Input'),
        'Output': Path('Output'),
        'Logs': Path('logs'),
        'Metrics': Path('metrics')
    }

    for name, path in dirs.items():
        status = "✅ OK" if path.exists() else "❌ Missing"
        print(f"{name} directory: {status}")

    # Check configuration
    try:
        from modules.config import get_config
        config = get_config()
        api_key_status = "✅ Set" if config.gemini_api_key else "❌ Missing"
        print(f"API Key: {api_key_status}")
    except Exception as e:
        print(f"Configuration: ❌ Error - {e}")

    # Check recent activity
    metrics_dir = Path("metrics")
    if metrics_dir.exists():
        recent_files = list(metrics_dir.glob("metrics_*.jsonl"))
        if recent_files:
            latest_file = max(recent_files, key=lambda p: p.stat().st_mtime)
            latest_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
            time_diff = datetime.now() - latest_time

            if time_diff < timedelta(hours=1):
                activity = "✅ Active (< 1 hour ago)"
            elif time_diff < timedelta(days=1):
                activity = f"⚠️  Last activity {time_diff.seconds // 3600} hours ago"
            else:
                activity = f"⚠️  Last activity {time_diff.days} days ago"
            print(f"Recent Activity: {activity}")
        else:
            print("Recent Activity: ⚠️  No metrics found")

    print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="PPT Generator AI - Monitoring Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'command',
        choices=['summary', 'recent', 'errors', 'health'],
        help='Command to execute'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to look back (default: 7)'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=10,
        help='Number of items to show (default: 10)'
    )

    args = parser.parse_args()

    if args.command == 'summary':
        show_summary(days=args.days)
    elif args.command == 'recent':
        show_recent(count=args.count)
    elif args.command == 'errors':
        show_errors(days=args.days)
    elif args.command == 'health':
        show_health()


if __name__ == '__main__':
    main()
