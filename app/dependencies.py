"""Shared dependencies for the VibeGraph API."""

from analyst.exporter import GraphExporter
from teacher.groq_agent import GroqTeacher

teacher = GroqTeacher()
exporter = GraphExporter()
