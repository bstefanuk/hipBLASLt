import argparse
from pathlib import Path
import yaml
from tqdm import tqdm
import os
import functools

from Tensile.Common import globalParameters, assignGlobalParameters, ParallelMap2
from Tensile.SolutionStructs import Solution
from Tensile.LibraryIO import writeYAML, parseLibraryLogicFile

def load_yaml_files(logic_path):
    yaml_files = list(Path(logic_path).rglob("*.yaml"))
    yaml_contents = []

    for yaml_file in yaml_files:
        with open(yaml_file, 'r') as file:
            content = yaml.safe_load(file)
            yaml_contents.append(content)

    return yaml_contents

def main():
    parser = argparse.ArgumentParser(description="Load YAML files from a specified path.")
    parser.add_argument("logic_path", type=str, help="Path to the directory containing YAML files.")
    args = parser.parse_args()

    assignGlobalParameters({})

    yaml_files = list(Path(args.logic_path).rglob("*.yaml"))
    
    func = functools.partial(parseLibraryLogicFile, archs='all')
    
    library_logics = []
    for library in ParallelMap2(func, yaml_files, "Loading Logics...", return_as="generator_unordered"):
        library_logics.append(library)

    if not library_logics:
        raise ValueError("No YAML files found.")

    solns =     [s for ll in library_logics for s in ll.solutions]
    numSolnsPrior = len(solns)
    solns =  list(dict.fromkeys(solns))
    print(type(solns), len(solns), type(solns[0]), len(solns[0]))
    kernels = [kernel for s in solns for kernel in s.getKernels()]
    print(type(kernels), len(kernels), type(kernels[0]), len(kernels[0]))
    print("Total number of solutions:", len(solns), "removed", numSolnsPrior-len(solns), "duplicates")
    
    kernelMinNaming = Solution.getMinNaming(kernels)
    print("Kernel MIN naming:", kernelMinNaming)
    
    for s in solns:
        s.name = Solution.getNameMin(s.getKernels(), kernelMinNaming)
        # print(name)

    # for i, (logic, filename) in enumerate(library_logics_w_filename):
    #     _, gfxName, _, _, _, lib, _ = logic
        # print(i, filename, gfxName, [(idx, s.name) for idx, s in lib.solutions.items()])

    # Start replacing the correct names
    for yaml_file in tqdm(yaml_files):
        with open(yaml_file, 'r') as file:
            content = yaml.load(file, Loader=yaml.CSafeLoader)
            solutions_content = content[5]
            for i, logic in enumerate(library_logics):
                _, gfxName, _, _, _, lib, filename = logic
                if filename == yaml_file:

                    for idx, s in lib.solutions.items():
                        solutions_content[idx]["SolutionNameMin"] = s.name
                    parts = Path(yaml_file).parts
                    asm_idx = parts.index("asm_full")

                    new_file = Path("..") / "tmp_LOGIC_NEWDIR" / Path(*parts[asm_idx:])
                    new_file.parent.mkdir(parents=True, exist_ok=True)
                    print(new_file)
                    # with open(new_file, 'w') as file:
                    #     yaml.dump(content, file, Dumper=yaml.CSafeDumper, default_flow_style=None)
    
if __name__ == "__main__":
    main()