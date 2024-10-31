# import argparse
# from pathlib import Path
# import yaml
# from tqdm import tqdm
# import os
# import functools

# from Tensile.Common import globalParameters, assignGlobalParameters, ParallelMap2
# from Tensile.SolutionStructs import Solution
# from Tensile.LibraryIO import writeYAML, parseLibraryLogicFile

# def load_yaml_files(logic_path):
#     yaml_files = list(Path(logic_path).rglob("*.yaml"))
#     yaml_contents = []

#     for yaml_file in yaml_files:
#         with open(yaml_file, 'r') as file:
#             content = yaml.safe_load(file)
#             yaml_contents.append(content)

#     return yaml_contents

# def main():
#     parser = argparse.ArgumentParser(description="Load YAML files from a specified path.")
#     parser.add_argument("logic_path", type=str, help="Path to the directory containing YAML files.")
#     args = parser.parse_args()

#     assignGlobalParameters({})

#     yaml_files = list(Path(args.logic_path).rglob("*.yaml"))
    
#     func = functools.partial(parseLibraryLogicFile, archs='all')
    
#     library_logics = []
#     for library in ParallelMap2(func, yaml_files, "Loading Logics...", return_as="generator_unordered"):
#         library_logics.append(library)

#     if not library_logics:
#         raise ValueError("No YAML files found.")

#     solns =     [s for ll in library_logics for s in ll.solutions]
#     numSolnsPrior = len(solns)
#     solns =  list(dict.fromkeys(solns))
#     print(type(solns), len(solns), type(solns[0]), len(solns[0]))
#     kernels = [kernel for s in solns for kernel in s.getKernels()]
#     print(type(kernels), len(kernels), type(kernels[0]), len(kernels[0]))
#     print("Total number of solutions:", len(solns), "removed", numSolnsPrior-len(solns), "duplicates")
    
#     kernelMinNaming = Solution.getMinNaming(kernels)
#     print("Kernel MIN naming:", kernelMinNaming)
    
#     for s in solns:
#         s.name = Solution.getNameMin(s.getKernels(), kernelMinNaming)
#         # print(name)

#     # for i, (logic, filename) in enumerate(library_logics_w_filename):
#     #     _, gfxName, _, _, _, lib, _ = logic
#         # print(i, filename, gfxName, [(idx, s.name) for idx, s in lib.solutions.items()])

#     # Start replacing the correct names
#     for yaml_file in tqdm(yaml_files):
#         with open(yaml_file, 'r') as file:
#             content = yaml.load(file, Loader=yaml.CSafeLoader)
#             solutions_content = content[5]
#             for i, logic in enumerate(library_logics):
#                 _, gfxName, _, _, _, lib, filename = logic
#                 if filename == yaml_file:

#                     for idx, s in lib.solutions.items():
#                         solutions_content[idx]["SolutionNameMin"] = Solution.getNameMin(s.getKernels(), kernelMinNaming)
#                         solutions_content[idx]["KernelNameMin"] = Solution.getNameMin(s.getKernels(), kernelMinNaming, True)
#                     parts = Path(yaml_file).parts
#                     asm_idx = parts.index("asm_full")

#                     new_file = Path("..") / "tmp_LOGIC_NEWDIR" / Path(*parts[asm_idx:])
#                     new_file.parent.mkdir(parents=True, exist_ok=True)
#                     print(new_file)
#                     # with open(new_file, 'w') as file:
#                     #     yaml.dump(content, file, Dumper=yaml.CSafeDumper, default_flow_style=None)
    
# if __name__ == "__main__":
#     main()

import argparse
import itertools
import yaml
import warnings
from tqdm import tqdm
from pathlib import Path

from Tensile.Common import assignGlobalParameters, ParallelMap2
from Tensile.SolutionStructs import Solution
from Tensile.LibraryIO import parseLibraryLogicFile

ASM_FULL = "asm_full"
TMP_LOGIC_NEWDIR = "tmp_LOGIC_NEWDIR"

def load_yaml_files(logic_path):
    return list(Path(logic_path).rglob("*.yaml"))

def parse_library_logics(yaml_files):
    fiter = zip(yaml_files, itertools.repeat("all"))
    return list(ParallelMap2(parseLibraryLogicFile, fiter, "Loading Logics...", return_as="generator_unordered"))

def get_unique_solutions(library_logics):
    solutions = [s for ll in library_logics for s in ll.solutions]
    return list(dict.fromkeys(solutions))

def get_kernels(solutions):
    return [kernel for s in solutions for kernel in s.getKernels()]

def update_solution_names(solutions, kernel_min_naming):
    for s in solutions:
        k = s.getKernels()
        assert len(k) == 1
        s.name = Solution.getNameMin(k[0], kernel_min_naming)

def update_yaml_files(yaml_files, library_logics, output_path, kernel_min_naming):
    for yaml_file in tqdm(yaml_files):
        with open(yaml_file, 'r') as file:
            try:
                content = yaml.load(file, Loader=yaml.CSafeLoader)
                solutions_content = content[5]
                update_solutions_content(yaml_file, library_logics, solutions_content, kernel_min_naming)
                new_file = get_new_file_path(yaml_file, output_path)
                with open(new_file, 'w') as file:
                    yaml.dump(content, file, Dumper=yaml.CSafeDumper, default_flow_style=None)
            except Exception as e:
                warnings.warn(f"Error updating {str(yaml_file)}: {e}")

def update_solutions_content(yaml_file, library_logics, solutions_content, kernel_min_naming):
    for logic in library_logics:
        _, _, _, _, _, lib, filename = logic
        if filename == yaml_file:
            for idx, s in lib.solutions.items():
                try:
                    solutions_content[idx]["SolutionNameMin"] = Solution.getNameMin(s.getKernels(), kernel_min_naming)
                    solutions_content[idx]["KernelNameMin"] = Solution.getNameMin(s.getKernels(), kernel_min_naming, True)
                except IndexError:
                    warnings.warn("idx {idx} out of range of library size {lib_size}... skipping,\n  offending file: {filename}")

def get_new_file_path(yaml_file, output_path):
    parts = Path(yaml_file).parts
    asm_idx = parts.index(ASM_FULL)
    new_file = Path(output_path) / TMP_LOGIC_NEWDIR / Path(*parts[asm_idx:])
    new_file.parent.mkdir(parents=True, exist_ok=True)
    return new_file


def main():
    parser = argparse.ArgumentParser(description="Load YAML files from a specified path.")
    parser.add_argument("--logic-path", "-l", type=str, help="Path to the directory containing YAML files.")
    parser.add_argument("--output-path", "-o", type=str, help="Directory where YAML files are written to.")
    args = parser.parse_args()

    assignGlobalParameters({})

    yaml_files = load_yaml_files(args.logic_path)
    library_logics = parse_library_logics(yaml_files)

    if not library_logics:
        raise ValueError("No YAML files found.")

    solutions = get_unique_solutions(library_logics)
    print(f"Total number of solutions: {len(solutions)}, removed {len(solutions) - len(set(solutions))} duplicates")

    kernels = get_kernels(solutions)
    print(f"Total number of kernels: {len(kernels)}")

    kernel_min_naming = Solution.getMinNaming(kernels)
    # print(f"Kernel MIN naming: {kernel_min_naming}")

    update_yaml_files(yaml_files, library_logics, args.output_path, kernel_min_naming)

if __name__ == "__main__":
    main()