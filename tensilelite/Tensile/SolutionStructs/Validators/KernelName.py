################################################################################
#
# Copyright (C) 2025 Advanced Micro Devices, Inc. All rights reserved.
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

from Tensile.Common.Utilities import elineno, print1
from Tensile.Common.RequiredParameters import getRequiredParametersMin
from Tensile.SolutionStructs.Naming import getNameMin, getKernelFileBase
from Tensile.SolutionStructs.Problem import ProblemType


def validateKernelName(sol: dict) -> bool:
    name = sol.get("KernelNameMin")
    assert name, f"Solution doesn't have key 'KernelNameMin': {elineno()}"

    sol["ProblemType"] = ProblemType(sol["ProblemType"], False)
    rp = getRequiredParametersMin()
    # calculatedName = getNameMin(sol, rp, False)
    calculatedName = getKernelFileBase(False, False, rp, None, sol)
    assert name == calculatedName, f"'KernelNameMin' doesn't match calculated name:\n   name: {name}\n   calc: {calculatedName}\n   {elineno()}"
    return True
