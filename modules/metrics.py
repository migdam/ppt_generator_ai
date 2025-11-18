"""
Metrics and Monitoring Module
Tracks application metrics and performance.
"""

import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from modules.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SessionMetrics:
    """Metrics for a single generation session."""

    session_id: str
    start_time: float
    end_time: Optional[float] = None

    # Input metrics
    source_type: str = ""  # 'url' or 'file'
    source: str = ""
    content_length: int = 0
    images_found: int = 0

    # Processing metrics
    num_slides_requested: int = 0
    num_slides_generated: int = 0
    quality_attempts: int = 0
    final_quality_score: int = 0

    # API metrics
    api_calls_made: int = 0
    api_errors: int = 0

    # Performance metrics
    extraction_time: float = 0.0
    generation_time: float = 0.0
    evaluation_time: float = 0.0
    building_time: float = 0.0
    total_time: float = 0.0

    # Output metrics
    output_file: str = ""
    output_size_kb: float = 0.0

    # Status
    status: str = "running"  # 'running', 'success', 'failed'
    error_message: str = ""

    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finish(self, status: str, error: Optional[str] = None):
        """Mark session as finished."""
        self.end_time = time.time()
        self.total_time = self.end_time - self.start_time
        self.status = status
        if error:
            self.error_message = error


class MetricsCollector:
    """Collects and stores application metrics."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MetricsCollector, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.metrics_dir = Path("metrics")
            self.metrics_dir.mkdir(exist_ok=True)
            self.current_session: Optional[SessionMetrics] = None
            self.initialized = True

    def start_session(self, session_id: Optional[str] = None) -> SessionMetrics:
        """Start a new metrics session."""
        if session_id is None:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.current_session = SessionMetrics(
            session_id=session_id,
            start_time=time.time()
        )
        logger.info(f"Started metrics session: {session_id}")
        return self.current_session

    def get_session(self) -> Optional[SessionMetrics]:
        """Get the current session."""
        return self.current_session

    def save_session(self, session: Optional[SessionMetrics] = None):
        """Save session metrics to file."""
        if session is None:
            session = self.current_session

        if session is None:
            logger.warning("No session to save")
            return

        # Create metrics file
        date_str = datetime.now().strftime("%Y%m%d")
        metrics_file = self.metrics_dir / f"metrics_{date_str}.jsonl"

        # Append to file (JSON Lines format)
        try:
            with open(metrics_file, 'a') as f:
                json.dump(asdict(session), f)
                f.write('\n')
            logger.info(f"Saved metrics to {metrics_file}")
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def get_summary_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get summary statistics for the last N days.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary of summary statistics
        """
        stats = {
            'total_sessions': 0,
            'successful_sessions': 0,
            'failed_sessions': 0,
            'total_api_calls': 0,
            'total_slides_generated': 0,
            'avg_quality_score': 0.0,
            'avg_generation_time': 0.0,
            'total_errors': 0
        }

        # Read metrics files
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        quality_scores = []
        generation_times = []

        for metrics_file in self.metrics_dir.glob("metrics_*.jsonl"):
            try:
                with open(metrics_file, 'r') as f:
                    for line in f:
                        session_data = json.loads(line)
                        if session_data['start_time'] >= cutoff_date:
                            stats['total_sessions'] += 1
                            stats['total_api_calls'] += session_data.get('api_calls_made', 0)
                            stats['total_slides_generated'] += session_data.get('num_slides_generated', 0)

                            if session_data['status'] == 'success':
                                stats['successful_sessions'] += 1
                            elif session_data['status'] == 'failed':
                                stats['failed_sessions'] += 1
                                stats['total_errors'] += 1

                            if session_data.get('final_quality_score', 0) > 0:
                                quality_scores.append(session_data['final_quality_score'])

                            if session_data.get('total_time', 0) > 0:
                                generation_times.append(session_data['total_time'])
            except Exception as e:
                logger.warning(f"Error reading metrics file {metrics_file}: {e}")

        # Calculate averages
        if quality_scores:
            stats['avg_quality_score'] = sum(quality_scores) / len(quality_scores)

        if generation_times:
            stats['avg_generation_time'] = sum(generation_times) / len(generation_times)

        return stats


def get_metrics_collector() -> MetricsCollector:
    """Get the metrics collector instance."""
    return MetricsCollector()
