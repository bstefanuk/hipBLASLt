################################################################################
#
# Copyright (C) 2022-2025 Advanced Micro Devices, Inc. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
################################################################################

import sys
# import importlib

if not (sys.version_info[0] >= 3 and sys.version_info[1] >= 6):
    raise Exception("Must be using Python 3.6 or above")

# # List of submodules to import and re-export
# submodules = [
#     'Base',
#     'Code',
#     'Containers',
#     'DataType',
#     'Enums',
#     'ExtInstructions',
#     'Formatting',
#     'Instructions',
#     'Macros',
#     'Math',
#     'Pass',
#     'RegisterPool',
#     'Utils'
# ]

# # Import each submodule and update the current module's namespace
# for submodule in submodules:
#     module = importlib.import_module(f'.{submodule}', package=__name__)
#     for attr in dir(module):
#         if not attr.startswith('_'):
#             globals()[attr] = getattr(module, attr)

# # Clean up the namespace
# del sys, importlib, submodules, submodule, module, attr
