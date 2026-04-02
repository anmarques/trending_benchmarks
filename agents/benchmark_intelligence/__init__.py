"""
Benchmark Intelligence Agent

A comprehensive system for tracking, extracting, and analyzing benchmark results
from trending AI models across major labs and organizations.

Main Components:
    - BenchmarkIntelligenceAgent: Main orchestrator for the workflow
    - ReportGenerator: Generates comprehensive reports and insights
    - CacheManager: Persistent storage for models and benchmarks
    - Model discovery, parsing, extraction, consolidation, and classification tools

Usage:
    From command line:
        python -m agents.benchmark_intelligence.main

    From Python:
        from agents.benchmark_intelligence import BenchmarkIntelligenceAgent

        agent = BenchmarkIntelligenceAgent()
        result = agent.run()
"""

from .main import BenchmarkIntelligenceAgent
from .reporting import ReportGenerator
from .tools.cache import CacheManager

__version__ = "1.0.0"

__all__ = [
    "BenchmarkIntelligenceAgent",
    "ReportGenerator",
    "CacheManager",
]
