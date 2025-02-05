import math
import ray
from pathlib import Path
from warnings import warn

from Tensile.Common import IsaVersion

MI_KEY: str = "MatrixInstruction"
MI_ENABLED_KEY: str = "EnableMatrixInstruction"

validMFMA = {}
validMFMA["H"] = [[32, 32, 4, 2], [32, 32, 8, 1], [16, 16, 4, 4], [16, 16, 16, 1], [4, 4, 4, 16]]
validMFMA["S"] = [[32, 32, 1, 2], [32, 32, 2, 1], [16, 16, 1, 4], [16, 16, 4, 1], [4, 4, 1, 16]]
validMFMA["B"] = [[32, 32, 2, 2], [32, 32, 4, 1], [16, 16, 2, 4], [16, 16, 8, 1], [4, 4, 2, 16]]
validMFMA["4xi8"] = [
    [32, 32, 4, 2],
    [32, 32, 8, 1],
    [16, 16, 4, 4],
    [16, 16, 16, 1],
    [4, 4, 4, 16],
    [32, 32, 16, 1],
    [16, 16, 32, 1],
]
validMFMA["D"] = [[16, 16, 4, 1], [4, 4, 4, 4]]
validMFMA["B1k"] = [[32, 32, 4, 2], [32, 32, 8, 1], [16, 16, 4, 4], [16, 16, 16, 1], [4, 4, 4, 16]]
validMFMA["C"] = validMFMA["S"]
validMFMA["Z"] = validMFMA["D"]
validMFMA["I8"] = [
    [32, 32, 4, 2],
    [32, 32, 8, 1],
    [16, 16, 4, 4],
    [16, 16, 16, 1],
    [4, 4, 4, 16],
] + [[32, 32, 16, 1], [16, 16, 32, 1]]
validMFMA["X"] = [[32, 32, 4, 1], [16, 16, 8, 1]]
validMFMA["F8"] = [[32, 32, 16, 1], [16, 16, 32, 1]]
validMFMA["B8"] = validMFMA["F8"]
validMFMA["F8B8"] = validMFMA["F8"]
validMFMA["B8F8"] = validMFMA["F8"]
validMFMA["F8N"] = [[32, 32, 16, 1], [16, 16, 32, 1]]
validMFMA["B8N"] = validMFMA["F8N"]
validMFMA["F8B8N"] = validMFMA["F8N"]
validMFMA["B8F8N"] = validMFMA["F8N"]
validWMMA = [
    [16, 16, 16, 1],
]
validTT = 32
validMFMA["_format9"] = []

for MFMA in [
    validMFMA["H"],
    validMFMA["S"],
    validMFMA["B"],
    validMFMA["D"],
    validMFMA["X"],
    validMFMA["F8N"],
    validWMMA,
]:
    for MI in MFMA:
        for bm in range(int(math.log(MI[3], 2)) + 1):
            for tt0 in range(1, validTT + 1):
                for tt1 in range(1, validTT + 1):
                    for wave_m in range(3):
                        for wave_n in range(3):
                            validMFMA["_format9"].append(
                                [MI[0], MI[1], MI[2], MI[3], 2**bm, tt0, tt1, 2**wave_m, 2**wave_n]
                            )
validMatrixInstructions = (
    [[], [-1]]
    + validMFMA["H"]
    + validMFMA["S"]
    + validMFMA["B"]
    + validMFMA["D"]
    + validMFMA["B1k"]
    + validMFMA["X"]
)
validMatrixInstructions = validMatrixInstructions + validMFMA["_format9"]

validSMFMA = {}
validSMFMA["H"] = [[32, 32, 16, 1], [16, 16, 32, 1]]
validSMFMA["B"] = [[32, 32, 16, 1], [16, 16, 32, 1]]
validSMFMA["4xi8"] = [[32, 32, 32, 1], [16, 16, 64, 1]]
validSMFMA["I8"] = validSMFMA["4xi8"]
validSMFMA["F8"] = [[32, 32, 32, 1], [16, 16, 64, 1]]
validSMFMA["B8"] = validSMFMA["F8"]
validSMFMA["F8B8"] = validSMFMA["F8"]
validSMFMA["B8F8"] = validSMFMA["F8"]
validSMFMA["F8N"] = [[32, 32, 32, 1], [16, 16, 64, 1]]
validSMFMA["B8N"] = validSMFMA["F8N"]
validSMFMA["F8B8N"] = validSMFMA["F8N"]
validSMFMA["B8F8N"] = validSMFMA["F8N"]
validSMFMA["_format9"] = []
for SMFMA in [validSMFMA["H"], validSMFMA["B"], validSMFMA["4xi8"], validSMFMA["F8N"]]:
    for MI in SMFMA:
        for bm in range(int(math.log(MI[3], 2)) + 1):
            for tt0 in range(1, validTT + 1):
                for tt1 in range(1, validTT + 1):
                    for wave_m in range(3):
                        for wave_n in range(3):
                            validSMFMA["_format9"].append(
                                [MI[0], MI[1], MI[2], MI[3], 2**bm, tt0, tt1, 2**wave_m, 2**wave_n]
                            )
validSparseMatrixInstructions = validSMFMA["H"] + validSMFMA["B"] + validSMFMA["4xi8"]
validMatrixInstructions = (
    validMatrixInstructions + validSparseMatrixInstructions + validSMFMA["_format9"]
)


@ray.remote
def validateMatrixInstruction(solution: dict, filepath: Path, params: dict):
    keep = True
    if MI_KEY not in solution:
        warn(f"{MI_KEY} not in solution: file: {filepath}, index: {solution['SolutionIndex']}")
        keep = False

    if MI_ENABLED_KEY not in solution:
        warn(
            f"{MI_ENABLED_KEY} not in solution: file: {filepath}, index: {solution['SolutionIndex']}"
        )
        keep = False

    if solution[MI_KEY] == [] and solution[MI_ENABLED_KEY] == True:
        warn(
            f"{MI_KEY} is empty but {MI_ENABLED_KEY} is True: file: {filepath}, index: {solution['SolutionIndex']}"
        )
        keep = False

    isa = IsaVersion(solution["ISA"])
    miFull = solution[MI_KEY]
    miEnabled = solution[MI_ENABLED_KEY]

    if miFull not in validMatrixInstructions:
        warn(
            f"Matrix instruction is not valid: file: {filepath}, index: {solution['SolutionIndex']}"
        )
        keep = False

    if len(solution[MI_KEY]) == 9:
        mi = [miFull[0], miFull[1], miFull[2], miFull[3]]
        waves = miFull[7] * miFull[8]
        miwg0 = miFull[4] * miFull[0] * miFull[7]  # Matrix instruction work group 0
        miwg1 = waves * wfsize // miwg0

        wfsize = solution["WavefrontSize"]
        isSparse = solution["ProblemType"]["Sparse"]
        miDataType = (
            solution["ProblemType"]["DataType"]
            if (not solution["EnableF32XdlMathOp"])
            else solution["ProblemType"]["F32XdlMathOp"]
        )

        assert solution["WorkGroup"] == [miwg0, miwg1]

        if not isSparse:
            if params["AsmCaps"][isa]["HasMFMA"]:
                if not (miDataType.toChar() in validMFMA and mi in validMFMA[miDataType.toChar()]):
                    if not (miDataType.isBFloat16() and mi in validMFMA["B1k"]):
                        warn(f"Matrix instruction {mi} not valid for DataType {miDataType}")
                        keep = False
            elif params["AsmCaps"][isa]["HasWMMA"]:
                if mi not in validWMMA:
                    warn(f"Matrix instruction {mi} not valid for DataType {miDataType}")
                    keep = False
        else:
            if not (miDataType.toChar() in validSMFMA and mi in validSMFMA[miDataType.toChar()]):
                warn(f"Sparse matrix instruction {mi} not valid for DataType {miDataType}")
                keep = False

        if (not params["AsmCaps"][isa]["HasMFMA"]) and params["AsmCaps"][isa][
            "HasWMMA"
        ]:
            if isa[0] == 10 or isa[0] == 11:
                assert solution["MIInputPerThread"] == solution["MatrixInstruction"][2]

        assert solution["MFMA_BF16_1K"] == False

        # Check MIBlock
        assert solution["MIBlock"][0] == mi[0]
        assert solution["MIBlock"][1] == mi[1]
        assert solution["MIBlock"][2] == mi[2]
        assert solution["MIBlock"][3] == mi[3]
        assert solution["MIBlock"][4] == min(miwg0 // mi[0], mi[3])
        assert solution["MIBlock"][5] == mi[3] // solution["MIBlock"][4]

        # Check MIWaveGroup
        assert solution["MIWaveGroup"][0] == min((miwg0 // mi[0]) // solution["MIBlock"][4], waves)
        assert solution["MIWaveGroup"][1] == waves // solution["MIWaveGroup"][0]

        # Check MIWaveTile
        assert solution["MIWaveTile"][0] == mi[5]
        assert solution["MIWaveTile"][1] == mi[6]

        # Check MIInputPerThread
        assert solution["MIInputPerThread"] == (
            solution["MatrixInstruction"][0]
            * solution["MatrixInstruction"][2]
            * solution["MatrixInstruction"][3]
            // solution["WavefrontSize"]
        )

        sparseA = (
            False
            if not solution["ProblemType"]["Sparse"]
            else False if solution["ProblemType"]["Sparse"] == 2 else True
        )
        sparseB = (
            False
            if not solution["ProblemType"]["Sparse"]
            else True if solution["ProblemType"]["Sparse"] == 2 else False
        )
        assert solution["MIInputPerThreadA"] == (
            solution["MIInputPerThread"] if not sparseA else solution["MIInputPerThread"] // 2
        )
        assert solution["MIInputPerThreadB"] == (
            solution["MIInputPerThread"] if not sparseB else solution["MIInputPerThread"] // 2
        )
        assert solution["MIInputPerThreadMetadata"] == (
            solution["MIInputPerThread"]
            if not solution["ProblemType"]["Sparse"]
            else solution["MIInputPerThread"] // 8
        )

        assert miEnabled == True
    elif miFull != [] and len(miFull) == 4:
        assert miEnabled == True
    else:
        assert miEnabled == False

    return keep
