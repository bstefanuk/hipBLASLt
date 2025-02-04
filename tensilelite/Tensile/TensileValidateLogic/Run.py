<<<<<<< Updated upstream
import os, sys

parentdir = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", ".."))
print(parentdir)
sys.path.append(parentdir)

=======
>>>>>>> Stashed changes
from pathlib import Path

from Tensile.Common import assignGlobalParameters
from Tensile.LibraryIO import readYAML
<<<<<<< Updated upstream

from Tensile.TensileValidateLogic.ParseArguments import parseArguments
from Tensile.TensileValidateLogic.ValidMatrixInstruction import validateMatrixInstruction


if __name__ == "__main__":
    args = parseArguments()

    assignGlobalParameters({}, args.CxxCompiler)

    keep = 0
    total = 0
    for file in Path(args.LogicPath).glob("**/*.yaml"):
        if "Experimental" in file.parts:
            continue
        print(f"   -> Reading {file}")
        yaml = readYAML(file)
        solutions = yaml[5]  # Solutions are the 5th index
        startingSolutions = len(solutions)
        for s in solutions:
            keep += int(validateMatrixInstruction(s))
            total += 1
=======
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
                keep += int(validateMatrixInstruction(s, file))
                total += 1
>>>>>>> Stashed changes

    print(f"Total  {total} solutions")
    print(f"Keep   {keep} solutions")
    print(f"Reject {total - keep} solutions")
