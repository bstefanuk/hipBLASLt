import ray
import yaml 
from pathlib import Path

from Tensile.Common import globalParameters, assignGlobalParameters
from Tensile.LibraryIO import readYAML
from Tensile.Toolchain.Validators import validateToolchain

from .ParseArguments import parseArguments
from .ValidMatrixInstruction import validateMatrixInstruction

def getParams(cxxCompiler):
    gp = globalParameters

    gpcache = Path.cwd() / "gpcache.yaml"
    if gpcache.exists():
        with open(gpcache, "r") as f:
            gp = yaml.load(f, yaml.CSafeLoader)
    else:
        assignGlobalParameters({}, cxxCompiler)
        with open(gpcache, "w") as f:
            yaml.dump(gp, f, yaml.CSafeDumper)

    return gp

def run():

    args = parseArguments()
    cxxCompiler = validateToolchain(args.CxxCompiler)
    gp = getParams(cxxCompiler)

    logicPath = Path(args.LogicPath)
    pattern = "**/*.yaml"
    files = logicPath.glob(pattern)
    print(f"Checking logic files with glob {args.LogicPath}/{pattern}")

    if not any([args.CheckMatrixInstruction]):
        print("No checks specified. Exiting.")
        exit(0)

    context = ray.init(dashboard_host="0.0.0.0", num_cpus=32)
    print(f"Started ray with {context}")

    keep = 0
    total = 0
    for file in files:
        if "Experimental" in file.parts:
            continue
        print(f"-> {file.relative_to(logicPath)}")
        data = readYAML(file)
        solutions = data[5]  # Solutions are the 5th index
        for s in solutions:
            if args.CheckMatrixInstruction:
                total += 1
                try:
                    future = validateMatrixInstruction.remote(s, file.relative_to(logicPath), gp)
                    ray.get(future)
                except AssertionError as e:
                    print(f"X> Rejecting {file.relative_to(logicPath)}: {e}")
                    continue
                keep += 1
    ray.shutdown()

    rejects = total - keep
    print(f"Total  {total} solutions")
    print(f"Keep   {keep} solutions")
    print(f"Reject {rejects} solutions")

    if rejects > 0:
        exit(1)



