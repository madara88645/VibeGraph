import logging

from app import configure_logging


def test_configure_logging_preserves_existing_root_handlers():
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    sentinel = logging.StreamHandler()
    root.handlers = [sentinel]

    try:
        configure_logging()
        assert sentinel in root.handlers
    finally:
        root.handlers = original_handlers
