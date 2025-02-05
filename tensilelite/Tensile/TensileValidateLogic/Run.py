import ray
from pathlib import Path

from Tensile.Common import globalParameters, assignGlobalParameters
from Tensile.LibraryIO import readYAML
from Tensile.Toolchain.Validators import validateToolchain

from .ParseArguments import parseArguments
from .ValidMatrixInstruction import validateMatrixInstruction


def run():
    args = parseArguments()
    cxxCompiler = validateToolchain(args.CxxCompiler)
    assignGlobalParameters({}, cxxCompiler)

    pattern = "**/*.yaml"
    files = Path(args.LogicPath).glob(pattern)
    print(f"Checking logic files with glob {args.LogicPath}/{pattern}")

    if not any([args.CheckMatrixInstruction]):
        print("No checks specified. Exiting.")
        return

    ray.init()

    keep = 0
    total = 0
    print("Checking matrix instructions")
    for file in files:
        if "Experimental" in file.parts:
            continue
        print(f"-> {file}")
        yaml = readYAML(file)
        solutions = yaml[5]  # Solutions are the 5th index
        for s in solutions:
            if args.CheckMatrixInstruction:
                future = validateMatrixInstruction.remote(s, file, globalParameters)
                keep += int(ray.get(future))
                total += 1

    print(f"Total  {total} solutions")
    print(f"Keep   {keep} solutions")
    print(f"Reject {total - keep} solutions")
