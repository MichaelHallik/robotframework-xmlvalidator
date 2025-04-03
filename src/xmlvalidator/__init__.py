# Copyright 2024-2025 Michael Hallik
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
This module serves as the package entry point, by exposing the 
XmlValidator class directly at the package level.

It further provides versioning metadata for use in documentation and 
automation.

Features:

- Defines the public API (__all__, aliasing).
- Simplifies imports by exposing XmlValidator at the top level.
- Supports dynamic version retrieval/discovery from installed metadata.
- Maintains compatibility with Python < 3.8 via fallback imports.
"""


# pylint: disable=C0103:invalid-name    # On account of the class name, which is not snake-cased (required by RF).


# Import versioning utilities to fetch package metadata dynamically.
# - `version` retrieves the installed package version from metadata.
# - `PackageNotFoundError` handles cases where the package is not installed.
from importlib.metadata import version, PackageNotFoundError
# Expose XmlValidator directly for cleaner imports.
from .XmlValidator import XmlValidator


# Alias (i.e.: make available) XmlValidator at the package level for RF.
xmlvalidator = XmlValidator

# Define package metadata & control what is exposed when importing the package.
__all__ = ["XmlValidator"] # Controls what's exposed by: from package import *.
__author__ = "Michael Hallik"
# Expose the version (package version or fallback version).
try:
    # Fetches version when installed as package.
    __version__ = version("robotframework-xmlvalidator")
except PackageNotFoundError:
    # Fall back when package not installed (default version for development).
    __version__ = "0.0.1"
    import warnings
    warnings.warn("Package metadata not found, using fallback version.")
