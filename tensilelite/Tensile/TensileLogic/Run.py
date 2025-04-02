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

import os
import functools

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, NamedTuple, Callable, Optional

from Tensile.Common import ParallelMap2, print1, IsaVersion, IsaInfo, setVerbosity, elineno
from Tensile.Common.Architectures import SUPPORTED_ISA
from Tensile.Common.Capabilities import makeIsaInfoMap
from Tensile.Common.GlobalParameters import assignGlobalParameters
from Tensile.LibraryIO import readYAML, writeYAML
from Tensile.SolutionStructs.Validators.MatrixInstruction import validateMIParameters
from Tensile.SolutionStructs.Validators.WorkGroup import validateWorkGroup
from Tensile.SolutionStructs.Validators.KernelName import validateKernelName
from Tensile.Toolchain.Validators import validateToolchain

from .ParseArguments import parseArguments
from .HandleCustomKernel import handleCustomKernel, hasCustomKernel

NAME_KEY: str = "KernelNameMin"
INDX_KEY: str = "SolutionIndex"
BUILDK_KEY: str = "BuildKernel"


class Action(NamedTuple):
    UpdateBuildKernels: bool
    CheckOnlyCustomKernels: bool
    CheckAll: bool


@dataclass
class UpdateResults:
    kernelBuildSet: set


@dataclass
class CheckResults:
    keep: int
    total: int
    numBuildKernels: int
    numNames: int
    names: List[str]


def _makeValidator(func: Callable) -> Callable:
    def validator(filepath: Path, sol: dict, *args):
        try:
            ret = func(sol, *args)
            assert sol["Valid"], f"Solution was rejected: {elineno()}"
            return ret
        except AssertionError as e:
            print(f"Error: Validation failed: {e} (file: {filepath}, index: {sol[INDX_KEY]})")
            return False

    return validator


_validateMatrixInstruction = _makeValidator(validateMIParameters)
_validateWorkGroup = _makeValidator(validateWorkGroup)
_validateKernelName = _makeValidator(validateKernelName)


def _update(s: dict, file: Path, logicPath: Path, results: UpdateResults):
    f = file.relative_to(logicPath)
    idx = s[INDX_KEY]
    name = s[NAME_KEY]
    if name in results.kernelBuildSet:
        if BUILDK_KEY in s:
            s.pop(BUILDK_KEY)  # Remove BuildKernel if it exists
            print(f"  - removing `{BUILDK_KEY}`: (file: {f}, index: {idx})")
    else:
        if BUILDK_KEY not in s:
            s[BUILDK_KEY] = True
            print(f"  + adding `{BUILDK_KEY}`: (file: {f}, index: {idx})")
        elif not s[BUILDK_KEY]:
            raise ValueError(
                f"`{BUILDK_KEY}`: false` is not permitted, remove `{BUILDK_KEY}` instead"
            )
        results.kernelBuildSet.add(name)


def _check(
    s: dict,
    file: Path,
    logicPath: Path,
    isaInfoMap: Dict[IsaVersion, IsaInfo],
    action: Action,
    results: CheckResults,
):
    s, isCustom = handleCustomKernel(s, isaInfoMap)
    if action.CheckOnlyCustomKernels and not isCustom:
        return results

    # Rejection checks
    if all(
        [
            _validateMatrixInstruction(file.relative_to(logicPath), s, isaInfoMap),
            _validateWorkGroup(file.relative_to(logicPath), s),
        ]
    ):
        results.keep += 1
    results.total += 1

    # Uniqueness checks
    results.numBuildKernels += int(s.get(BUILDK_KEY, False))
    if _validateKernelName(file.relative_to(logicPath), s):
        results.names.append(s[NAME_KEY])
        results.numNames += 1


def _readFile(file: Path, action: Action) -> Optional[List[dict]]:
    """
    Get solutions from a logic file depending on the checks specified.

    Returns:
        List of solutions if the file is a custom kernel is found and CheckOnlyCustomKernel is
        enabled, or if all checks are enabled. Otherwise, an empty list is returned.
    """
    if action.CheckOnlyCustomKernels and not hasCustomKernel(file):
        return None
    return readYAML(file)


def _processFiles(
    logicPath: Path, isaInfoMap: Dict[IsaVersion, IsaInfo], action: Action, files: List[Path]
):
    isUpdate = action.UpdateBuildKernels
    isCheck = any([action.CheckAll, action.CheckOnlyCustomKernels])
    if (isUpdate and isCheck) or not (isUpdate or isCheck):
        raise ValueError("Updates and checks are mutually exclusive.")

    if isUpdate:
        results = UpdateResults(kernelBuildSet=set())
    if isCheck:
        results = CheckResults(
            keep=0,
            total=0,
            numBuildKernels=0,
            numNames=0,
            names=[],
        )

    for i, file in enumerate(files):
        if "Experimental" in file.parts:
            return results

        yaml = _readFile(file, action)
        if yaml:
            info = f"[file: {i+1:02}/{len(files):02}, pid: {int(os.getpid() % 1e3):03}]"
            print1(f"{info} {file.relative_to(logicPath)}")
            for s in yaml[5]:  # Solutions are the 5th index
                if isUpdate:
                    _update(s, file, logicPath, results)
                elif isCheck:
                    _check(s, file, logicPath, isaInfoMap, action, results)
            if isUpdate:
                writeYAML(file, yaml)
    return results


def _getLogicFiles(logicPath: Path) -> List[Path]:
    if logicPath.is_file() and logicPath.suffix == ".yaml":
        return [logicPath]

    pattern = "**/*.yaml"
    files = list(logicPath.glob(pattern))
    if len(files) == 0:
        print1(f"No files found in {logicPath}")
        exit(1)

    print1(f"Found {len(files)} files")
    return files


def _setup():
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
    )

    # Retrieve ISA info and globals
    isaInfoMap = makeIsaInfoMap(SUPPORTED_ISA, str(cxxCompiler))
    assignGlobalParameters({"PrintSolutionRejectionReason": True}, isaInfoMap)

    return jobs, isaInfoMap, logicPath, files, action


def main():
    jobs, isaInfoMap, logicPath, files, action = _setup()

    fn = functools.partial(_processFiles, logicPath, isaInfoMap, action)

    # TODO: Once we can parallelize the update set, the conditionals here can be eliminated
    if action.UpdateBuildKernels:
        fn(files)  # Must be syncronous for proper uniqueness evaluation of kernel names

    if any([action.CheckOnlyCustomKernels, action.CheckAll]):
        batchSize = len(files) // min(len(files), jobs)
        batches = (files[i : i + batchSize] for i in range(0, len(files), batchSize))

        keep, total = 0, 0
        numBuildKernels, numNames, names = 0, 0, []
        for result in ParallelMap2(fn, batches, multiArg=False, procs=jobs, return_as="list")
            keep += result.keep
            total += result.total
            numBuildKernels += result.numBuildKernels
            numNames += result.numNames
            names.extend(result.names)

        # Post processing
        rejects = total - keep
        print(f"Total         {total} solutions")
        print(f"Keep          {keep} solutions")
        print(f">>  Reject    {rejects} solution(s)")

        buildkDiff = abs(numBuildKernels - len(set(names)))
        print(f"Num names (batched)    {numNames}")
        print(f"Unique names           {len(set(names))}")
        print(f"With `{BUILDK_KEY}`    {numBuildKernels}")
        print(f">>  Difference         {buildkDiff}")

        if rejects > 0 or buildkDiff > 0:
            exit(1)
