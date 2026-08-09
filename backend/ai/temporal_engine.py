"""
temporal_engine.py
------------------
Facade re-exporting consolidated temporal analysis functions for backward compatibility.
All core temporal calculations and session management reside in temporal_analysis.py.
"""

from ai.temporal_analysis import (
    SessionManager,
    session_manager,
    analyze_temporal_session,
    analyze_temporal_stress,
    analyze_lap_performance,
    generate_engineering_insight,
    pearson_correlation,
)

__all__ = [
    "SessionManager",
    "session_manager",
    "analyze_temporal_session",
    "analyze_temporal_stress",
    "analyze_lap_performance",
    "generate_engineering_insight",
    "pearson_correlation",
]
