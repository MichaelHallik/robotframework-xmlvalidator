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
Resolve the *runtime* package version.

The project version is defined in installed packaging metadata, instead
of being hard-coded in library source files.

This module reads that installed metadata and exposes it as
``__version__`` so users, smoke tests, Libdoc and/or other automation
can inspect the active package version at runtime via access to that
name.

When the package is imported directly from a source checkout that has
not been installed yet, package metadata may be unavailable. In that
case, the module falls back to ``"0.0.0"`` and emits a warning instead
of failing the import.

Technical note:

The source version is defined in ``pyproject.toml``. During build and
installation, that value is written into the installed distribution
metadata, such as ``*.dist-info/METADATA``.

``importlib.metadata.version()`` reads that installed metadata (it does
not read ``pyproject.toml`` directly).
"""

import warnings
from importlib.metadata import PackageNotFoundError, version

try:
    # Prefer the canonical version recorded in the installed distribution.
    __version__ = version("robotframework-xmlvalidator")
except PackageNotFoundError:
    # Keep source-checkout imports usable when no distribution metadata exists.
    __version__ = "0.0.0"
    warnings.warn("Package metadata not found, using fallback version.", stacklevel=2)
