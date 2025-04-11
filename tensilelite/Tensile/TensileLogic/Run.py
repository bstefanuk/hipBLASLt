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

from pathlib import Path
from typing import List, Dict, Callable

from Tensile.Common import ParallelMap2, print1, IsaVersion, IsaInfo, elineno
from Tensile.LibraryIO import writeYAML
from Tensile.SolutionStructs.Validators.MatrixInstruction import validateMIParameters
from Tensile.SolutionStructs.Validators.WorkGroup import validateWorkGroup
from Tensile.SolutionStructs.Validators.KernelName import validateKernelName
from Tensile.SolutionStructs.Naming import getKernelNameMin
from Tensile.SolutionStructs.Problem import ProblemType

from .HandleCustomKernel import handleCustomKernel
from .Helpers import readFile, setupApp
from .Types import Action, CheckResults, UpdateBuildKernelResults, UpdateKernelNameResults


NAME_KEY: str = "KernelNameMin"
INDX_KEY: str = "SolutionIndex"
BUILDK_KEY: str = "BuildKernel"


def _validatorFactory(func: Callable) -> Callable:
    def validator(filepath: Path, sol: dict, *args):
        try:
            ret = func(sol, *args)
            assert sol["Valid"], f"Solution was rejected: {elineno()}"
            return ret
        except AssertionError as e:
            print(f"Error: Validation failed: {e} (file: {filepath}, index: {sol[INDX_KEY]})")
            return False

    return validator


_validateMatrixInstruction = _validatorFactory(validateMIParameters)
_validateWorkGroup = _validatorFactory(validateWorkGroup)
_validateKernelName = _validatorFactory(validateKernelName)


def _check(
    s: dict,
    file: Path,
    logicPath: Path,
    results: CheckResults,
    isaInfoMap: Dict[IsaVersion, IsaInfo],
    action: Action,
):
    s, isCustom = handleCustomKernel(s, isaInfoMap)
    if action.CheckOnlyCustomKernels and not isCustom:
        return results

    # Rejection checks
    if all(
        [
            _validateMatrixInstruction(file.relative_to(logicPath), s, isaInfoMap),
            _validateWorkGroup(file.relative_to(logicPath), s),
            _validateKernelName(file.relative_to(logicPath), s),
        ]
    ):
        results.keep += 1
    results.total += 1

    # Uniqueness checks
    results.numBuildKernels += int(s.get(BUILDK_KEY, False))
    if _validateKernelName(file.relative_to(logicPath), s):
        results.names.append(s[NAME_KEY])
        results.numNames += 1


def _updateBuildKernel(s: dict, file: Path, logicPath: Path, results: UpdateBuildKernelResults):
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


def _updateKernelName(s: dict, file: Path, logicPath: Path, results: UpdateKernelNameResults):
    f = file.relative_to(logicPath)
    idx = s[INDX_KEY]
    name = s.get(NAME_KEY)

    savedProblemType = s["ProblemType"]
    s["ProblemType"] = ProblemType(s["ProblemType"], False)

    calculatedName = getKernelNameMin(s, False)
    if not name or name != calculatedName:
        s[NAME_KEY] = calculatedName
        print(f"  + updating `{NAME_KEY}`: (file: {f}, index: {idx})")
        results.kernelNameSet.add(calculatedName)

    s["ProblemType"] = savedProblemType


def _processFilesFactory(logicPath: Path, action: Action) -> Callable:

    if action.UpdateKernelNames:
        results = UpdateKernelNameResults()
        fn = _updateKernelName
        isUpdate = True
    elif action.UpdateBuildKernels:
        results = UpdateBuildKernelResults()
        fn = _updateBuildKernel
        isUpdate = True
    elif action.CheckOnlyCustomKernels or action.CheckAll:
        results = CheckResults()
        fn = _check
        isUpdate = False
    else:
        raise ValueError(f"Action {action} is not implemented.")

    def processFiles(files: List[Path], **kwargs):
        for i, file in enumerate(files):
            yaml = readFile(file, action)
            if yaml:
                info = f"[file: {i+1:02}/{len(files):02}, pid: {int(os.getpid() % 1e3):03}]"
                print1(f"{info} {file.relative_to(logicPath)}")

                for s in yaml[5]:  # Solutions are the 5th index
                    fn(s, file, logicPath, results, **kwargs)

                if isUpdate:
                    writeYAML(file, yaml, explicit_start=False, explicit_end=False)
        return results

    return processFiles


def main():
    jobs, isaInfoMap, logicPath, files, action = setupApp()

    fn = _processFilesFactory(logicPath, action)
    batchSize = len(files) // min(len(files), jobs)
    batches = (files[i : i + batchSize] for i in range(0, len(files), batchSize))

    if action.UpdateBuildKernels:
        fn(files)  # Must be syncronous for proper uniqueness evaluation of kernel names

    if action.UpdateKernelNames:
        ParallelMap2(fn, batches, multiArg=False, procs=jobs, return_as="list")

    if any([action.CheckOnlyCustomKernels, action.CheckAll]):
        fn = functools.partial(fn, isaInfoMap=isaInfoMap, action=action)
        batchSize = len(files) // min(len(files), jobs)
        batches = (files[i : i + batchSize] for i in range(0, len(files), batchSize))

        keep, total = 0, 0
        numBuildKernels, numNames, names = 0, 0, []
        for result in ParallelMap2(fn, batches, multiArg=False, procs=jobs, return_as="list"):
            keep += result.keep
            total += result.total
            numBuildKernels += result.numBuildKernels
            numNames += result.numNames
            names.extend(result.names)

        # Post processing
        rejects = total - keep
        print("------------------------------------------")
        print(f"Total                  {total} solutions")
        print(f"Keep                   {keep} solutions")
        print(f"Reject                 {rejects} solution(s)")
        print("SUCCESS" if rejects == 0 else "FAILURE")

        buildkDiff = abs(numBuildKernels - len(set(names)))
        print("------------------------------------------")
        print(f"Num names (batched)    {numNames}")
        print(f"Unique names           {len(set(names))}")
        print(f"With `{BUILDK_KEY}`     {numBuildKernels}")
        print(f"Difference             {buildkDiff}")
        print("SUCCESS" if buildkDiff == 0 else "FAILURE")

        if rejects > 0 or buildkDiff > 0:
            exit(1)
