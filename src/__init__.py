"""MASB - Multilingual Adversarial Safety Benchmark."""

__version__ = "1.0.0"
__author__ = "Wolfgang Dremmler"

from src.config import settings, SUPPORTED_LANGUAGES, SUPPORTED_MODELS
from src.models.provider_factory import ProviderFactory

__all__ = [
    "settings",
    "SUPPORTED_LANGUAGES",
    "SUPPORTED_MODELS",
    "ProviderFactory",
]