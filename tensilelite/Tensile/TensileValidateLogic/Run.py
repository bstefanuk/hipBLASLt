import ray
import yaml 
from pathlib import Path

from Tensile.Common import globalParameters, assignGlobalParameters
from Tensile.LibraryIO import readYAML
from Tensile.Toolchain.Validators import validateToolchain

from .ParseArguments import parseArguments
from .ValidMatrixInstruction import validateMatrixInstruction


def run():
    context = ray.init(dashboard_host="0.0.0.0")
    print(f"Started ray with {context}")

    args = parseArguments()
    cxxCompiler = validateToolchain(args.CxxCompiler)
    gp = globalParameters

    gpcache = Path.cwd() / "gpcache.json"
    if gpcache.exists():
        print("AHHH")
        with open(gpcache, "r") as f:
            gp = yaml.load(f, yaml.CSafeLoader)
    else:
        assignGlobalParameters({}, cxxCompiler)
        with open(gpcache, "w") as f:
            yaml.dump(gp, f, yaml.CSafeDumper)

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
        data = readYAML(file)
        solutions = data[5]  # Solutions are the 5th index
        for s in solutions:
            if args.CheckMatrixInstruction:
                future = validateMatrixInstruction.remote(s, file, gp)
                keep += int(ray.get(future))
                total += 1

    print(f"Total  {total} solutions")
    print(f"Keep   {keep} solutions")
    print(f"Reject {total - keep} solutions")
