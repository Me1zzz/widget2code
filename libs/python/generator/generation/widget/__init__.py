"""Widget DSL generation module."""

from .single import (
    generate_widget_text,
    generate_widget_text_with_reference,
    generate_widget_full,
    generate_single_widget,
)
from .html_compiler import compile_widget_dsl_to_html
from .batch import BatchGenerator, batch_generate

__all__ = [
    "generate_widget_text",
    "generate_widget_text_with_reference",
    "generate_widget_full",
    "generate_single_widget",
    "compile_widget_dsl_to_html",
    "BatchGenerator",
    "batch_generate",
]
