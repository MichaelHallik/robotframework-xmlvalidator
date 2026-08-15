# Copyright 2024-2026 Michael Hallik
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.


"""
Package entry point, exposing the XmlValidator class directly at
the package level.

Provides versioning metadata for use in documentation and automation.

Features:

- Defines the public API (__all__ + aliasing).
- Simplifies imports by exposing XmlValidator at the top level.
- Supports dynamic version discovery from installed metadata.
"""

# pylint: disable=C0103:invalid-name  # On account of the class name, which is not snake-cased (required by RF).


# Re-export the resolved package version as xmlvalidator.__version__.
from ._version import __version__

# Re-export the Robot Framework library class at package level.
from .XmlValidator import XmlValidator

# Provide the lowercase import alias expected by Robot library imports.
xmlvalidator = XmlValidator

# Declare package-level public API and distribution metadata.
__all__ = [
    # Names to export for wildcard ('*') imports from this package.
    "XmlValidator",
    "xmlvalidator",
    "__version__",
]
__author__ = "Michael Hallik"
