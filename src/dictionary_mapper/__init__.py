# SPDX-FileCopyrightText: 2025-present Jhon Alvarez <jjalvarezl@unicauca.edu.co>
#
# SPDX-License-Identifier: MIT

"""
Dictionary mapping utilities.

This package provides classes for mapping and transforming dictionaries
with type safety and custom transformation rules.
"""

from .main import RawDictionaryMapper, SpecEntry, TransformationMapping, TypedDictionaryMapper

__all__ = ["RawDictionaryMapper", "SpecEntry", "TransformationMapping", "TypedDictionaryMapper"]
