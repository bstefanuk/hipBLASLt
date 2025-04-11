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

from pathlib import Path
from typing import List, Optional, Callable

from Tensile.Common import print1, setVerbosity
from Tensile.Common.Architectures import SUPPORTED_ISA
from Tensile.Common.Capabilities import makeIsaInfoMap
from Tensile.Common.GlobalParameters import assignGlobalParameters
from Tensile.LibraryIO import readYAML
from Tensile.Toolchain.Validators import validateToolchain

from .ParseArguments import parseArguments
from .HandleCustomKernel import hasCustomKernel
from .Types import Action


def readFile(file: Path, action: Action) -> Optional[List[dict]]:
    if action.CheckOnlyCustomKernels and not hasCustomKernel(file):
        return None
    return readYAML(file)


def _getLogicFiles(logicPath: Path) -> List[Path]:
    if logicPath.is_file() and logicPath.suffix == ".yaml":
        return [logicPath]

    pattern = "**/*.yaml"
    files = list(filter(lambda file: "Experimental" not in file.parts, logicPath.glob(pattern)))
    if len(files) == 0:
        print1(f"No files found in {logicPath}")
        exit(1)

    print1(f"Found {len(files)} files")
    return files


def setupApp():
    args = parseArguments()

    setVerbosity(args.verbose)
    jobs = int(args.jobs)
    cxxCompiler = validateToolchain(args.cxx_compiler)
    logicPath = Path(args.logic_path)
    files = _getLogicFiles(logicPath)
    action = Action(
        CheckOnlyCustomKernels=args.check_only_custom_kernels,
        CheckAll=args.check_all,
        UpdateBuildKernels=args.update_build_kernels,
        UpdateKernelNames=args.update_kernel_names,
    )

    # Retrieve ISA info and globals
    isaInfoMap = makeIsaInfoMap(SUPPORTED_ISA, str(cxxCompiler))
    assignGlobalParameters({"PrintSolutionRejectionReason": True}, isaInfoMap)

    return jobs, isaInfoMap, logicPath, files, action
