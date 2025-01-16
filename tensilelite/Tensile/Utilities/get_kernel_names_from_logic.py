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
from copy import deepcopy
import itertools
import re
import yaml
import warnings
from tqdm import tqdm
from pathlib import Path

from Tensile.Common import assignGlobalParameters, ParallelMap2
from Tensile.SolutionStructs import Solution
from Tensile.LibraryIO import parseLibraryLogicFile
from Tensile.Utilities.RequiredParameters import getRequiredParametersFull, getRequiredParametersMin

ASM_FULL = "hipblaslt_asm_small"
TMP_LOGIC_NEWDIR = "NEW_TENSILE_LOGIC"


def load_yaml_files(logic_path):
    return list(Path(logic_path).rglob("*.yaml"))


def parse_library_logics(yaml_files):
    fiter = zip(yaml_files, itertools.repeat("all"))
    return list(
        ParallelMap2(
            parseLibraryLogicFile, fiter, "Loading Logics...", return_as="generator_unordered"
        )
    )


def get_unique_solutions(library_logics):
    solutions = [s for ll in library_logics for s in ll.solutions]
    return list(dict.fromkeys(solutions))


def get_kernels(solutions):
    return [kernel for s in solutions for kernel in s.getKernels()]


def update_yaml_files(yaml_files, library_logics, output_path):
    for yaml_file in tqdm(yaml_files):
        with open(yaml_file, "r") as file:
            # try:
            content = yaml.load(file, Loader=yaml.CSafeLoader)
            solutions_content = content[5]
            exact_logic_content = content[7]
            for logic in library_logics:
                # print("type------logic------", type(logic))
                if logic.srcFile == yaml_file:
                    # print("Logic solutions:", logic.solutions)
                    for sol_idx, sol in enumerate(logic.solutions):
                        try:
                            # print("type------2", type(sol), sol, dir(sol))
                            update_solutions(solutions_content, sol_idx, sol)
                        except IndexError:
                            warnings.warn(
                                "idx {idx} out of range of library size {lib_size}... skipping,\n  offending file: {filename}"
                            )

            # keep_sol = set()
            # del_sol_idx = set()
            # for idx, s in enumerate(solutions_content):
            #     if s["SolutionPseudoNameMin"] not in keep_sol:
            #         keep_sol.add(s["SolutionPseudoNameMin"])
            #     else:
            #         del_sol_idx.add(idx)

            # print(f"Total number of solutions: {len(solutions_content)}, with {len(del_sol_idx)} marked for removal")

            # solutions_content_copy = deepcopy(solutions_content)
            # for sol in solutions_content_copy:
            #     if sol["SolutionIndex"] in del_sol_idx:
            #         solutions_content.remove(sol)

            # exact_logic_content_copy = deepcopy(exact_logic_content)
            # for exact_logic in exact_logic_content_copy:
            #     problem, idx_list = exact_logic
            #     idx = idx_list[0]
            #     if idx in del_sol_idx:
            #         exact_logic_content.remove(exact_logic)

            new_file = get_new_file_path(yaml_file, output_path)
            with open(new_file, "w") as file:
                yaml.dump(content, file, Dumper=yaml.CSafeDumper, default_flow_style=None)
            # except Exception as e:
            #     warnings.warn(f"Error updating {str(yaml_file)}: {e}")


def update_solutions(solutions_content, idx, s):
    k = s.getKernels()
    assert len(k) == 1
    k = k[0]
    solutions_content[idx]["KernelNameMin"] = Solution.getNameMin(k, getRequiredParametersMin(), True, recompute=True)
    solutions_content[idx]["SolutionNameMin"] = Solution.getNameMin(k, getRequiredParametersFull(), recompute=True)
    solutions_content[idx]["SolutionPseudoNameMin"] = Solution.getNameMin(Solution.getKeyNoInternalArgs(k), getRequiredParametersFull(), recompute=True)


def get_new_file_path(yaml_file, output_path):
    parts = Path(yaml_file).parts
    asm_idx = parts.index(ASM_FULL)
    new_file = Path(output_path) / TMP_LOGIC_NEWDIR / Path(*parts[asm_idx:])
    new_file.parent.mkdir(parents=True, exist_ok=True)
    return new_file


def main():
    parser = argparse.ArgumentParser(description="Load YAML files from a specified path.")
    parser.add_argument(
        "--logic-path", "-l", type=str, help="Path to the directory containing YAML files."
    )
    parser.add_argument(
        "--output-path", "-o", type=str, help="Directory where YAML files are written to."
    )
    args = parser.parse_args()

    assignGlobalParameters({})

    yaml_files = load_yaml_files(args.logic_path)
    library_logics = parse_library_logics(yaml_files)

    if not library_logics:
        raise ValueError("No YAML files found.")

    solutions = get_unique_solutions(library_logics)
    print(
        f"Total number of solutions: {len(solutions)}, removed {len(solutions) - len(set(solutions))} duplicates"
    )

    kernels = get_kernels(solutions)
    print(f"Total number of kernels: {len(kernels)}")

    update_yaml_files(yaml_files, library_logics, args.output_path)


if __name__ == "__main__":
    main()
