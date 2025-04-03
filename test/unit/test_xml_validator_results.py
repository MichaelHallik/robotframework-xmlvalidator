# Copyright 2024-2025 Michael Hallik
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The methods in the two classes ValidatorResultRecorder() and 
ValidatorResult() are not tested in the unit tests. These methods are:

_get_summary()
add_file_errors()
add_invalid_file()
add_valid_file()
log_file_errors()
log_summary()
reset()
write_errors_to_csv()

They will be tested in the integration tests though.

See for an overview of all tests the file test/overview_of_tests.html.
"""
