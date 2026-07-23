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
Provides path resolution helpers for XML and XSD validation workflows.
"""

# Standard library imports.
from pathlib import Path


def get_file_paths(
    file_path: str | Path,
    file_extension: str
) -> tuple[list[Path], bool]:
    """
    Resolves files from the given path and filters them by extension.

    If the path is a file, it returns a single-item-list and a True
    flag. If the path is a directory, it returns all files with the
    matching extension and a boolean indicating whether exactly one file
    was found.
    """
    file_extension = file_extension.lower().removeprefix(".")
    resolved_path = _resolve_path(file_path)
    if resolved_path.is_file():
        return [resolved_path], True
    if resolved_path.is_dir():
        resolved_paths = sorted(
            resolved_path.glob(f"*.{file_extension}")
        )
        if not resolved_paths:
            raise ValueError(
                f"No .{file_extension} files found in folder: "
                f"{resolved_path}."
            )
        return resolved_paths, len(resolved_paths) == 1
    raise ValueError(
        f"The provided path is neither a file nor a folder: {resolved_path}."
    )


def _resolve_path(path: str | Path) -> Path:
    """
    Returns a resolved absolute path to a file or directory.
    """
    return Path(path).resolve() if isinstance(path, str) else path.resolve()
