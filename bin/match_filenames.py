#!/usr/bin/env python3
import itertools as it
import os
import re
import shutil
import sys
from collections import defaultdict
from enum import Enum
from os.path import join
from typing import Iterable, Collection, Sequence, Dict, List, Tuple, Set, TypeVar, Type

import click


# mapping from a class to a list of files contained in that class
EquivalenceClasses = Dict[str, List[str]]


class PathContent(object):
    def __init__(self, path: str, filenames: Collection[str], equivalence_classes: EquivalenceClasses) -> None:
        """
        Params:
            path: directory or file path
            filenames: List of files contained in this directory or file
            equivalence_classes: Equivalence classes contained in this directory or file
        """
        self.path = path
        self.filenames = filenames
        self.classes = equivalence_classes
        # sets of equivalence classes (the keys)
        # to be set later, but would be nicer to keep this class immutable though..
        self.difference: Set[str] = set()
        self.duplicates: Set[str] = set()


def classify(paths_and_patterns: Sequence[Tuple[str, str]]) -> List[PathContent]:
    """
    Take list of (path, pattern) tuples and sort the files in path into equivalence classes based on the regex pattern.
    Args:
        path:
            Can be a directory or a file containing lines of text
        pattern:
            A regular expression whose matches define equivalence classes. If there are subgroups, concatenate those to
            define the class. If there is no match, use the whole filename.
    Returns:
        A list of PathContent objects, one for each paths_and_patterns
    """
    path_contents = []

    for path, pattern in paths_and_patterns:
        is_dir = os.path.isdir(path)
        if is_dir:
            filenames = os.listdir(path)
            path = path.rstrip("/")
        else:
            with open(path, "r") as f:
                filenames = [l for l in f.read().split("\n") if l]

        try:
            equivalence_classes = classify_list(filenames, pattern)
        except re.error as e:
            print("Error: Invalid regular expression '{}':\n{}".format(pattern, e))
            sys.exit(-1)

        path_contents.append(PathContent(path, filenames, equivalence_classes))

    return path_contents


def classify_list(strings: Collection[str], pattern: str) -> EquivalenceClasses:
    """
    Sort each string into a class based on the regular expression pattern.
    Args:
        string:
            List of strings
        pattern:
            A regular expression whose matches define equivalence classes. If there are subgroups, concatenate those to
            define the class. If there is no match, use the whole filename.
    Returns:
        A mapping from class to filenames belonging to that class
    """
    equivalence_classes: EquivalenceClasses = defaultdict(list)
    for string in strings:
        match = re.search(pattern, string)
        if not match:
            class_ = string
        elif len(match.groups()) == 0:
            class_ = match.group(0)
        else:
            class_ = "".join(match.groups())

        equivalence_classes[class_].append(string)
    return equivalence_classes


T = TypeVar('T')
def flatten(list_of_lists: Iterable[Iterable[T]]) -> Iterable[T]:
    return it.chain.from_iterable(list_of_lists)


def copy_files(path: str, target_files: Collection[str], all_files: Collection[str], suffix: str) -> None:
    target = path + suffix
    print("Copying {}/{} files from '{}' to '{}'".format(len(target_files), len(all_files), path, target))

    if os.path.isdir(path):
        os.makedirs(target, exist_ok=True)
        for file in target_files:
            shutil.copy(join(path, file), target)
    else:
        with open(target, "w") as f:
            f.write("\n".join(sorted(target_files)))


def move_files(path: str, target_files: Collection[str], all_files: Collection[str], suffix: str) -> None:
    target = path + suffix
    print("Moving {}/{} files from '{}' to '{}'".format(len(target_files), len(all_files), path, target))

    if os.path.isdir(path):
        os.makedirs(target, exist_ok=True)
        for file in target_files:
            shutil.move(join(path, file), target)
    else:
        with open(target, "w") as f:
            f.write("\n".join(sorted(target_files)))
        with open(path, "w") as f:
            remaining = set(all_files) - set(target_files)
            f.write("\n".join(sorted(remaining)))


def remove_files(path: str, target_files: Collection[str], all_files: Collection[str]) -> None:
    print("Removing {}/{} files in '{}'".format(len(target_files), len(all_files), path))

    if os.path.isdir(path):
        for file in target_files:
            os.remove(join(path, file))
    else:
        with open(path, "w") as f:
            remaining = set(all_files) - set(target_files)
            f.write("\n".join(sorted(remaining)))


def print_list(lines: Collection[str], verbose: bool, limit: int = 20) -> None:
    if not lines:
        return
    if verbose or len(lines) <= limit:
        print("\n".join(list(lines)))
    else:
        print("\n".join(list(lines)[:limit]))
        print("...")


class Target(Enum):
    NONE = "none"
    DIFF = "diff"
    INT = "int"
    DUP = "dup"


class Operation(Enum):
    NONE = "none"
    CP = "cp"
    MV = "mv"
    RM = "rm"


def format_enum_values(enum: Type[Enum]) -> str:
    return "[{}]".format("|".join(e.value for e in enum))


@click.command()
@click.option("-p", "--path_and_pattern", type=click.Tuple([click.Path(exists=True), str]), multiple=True, required=True,
              help="(path, pattern) tuple. path can be a directory or a text file. pattern is a regular "
                   "expression whose matches define equivalence classes. If there are subgroups, use those. If there "
                   "is no match, use the whole filename to define a class.")
@click.option("-t", "--target", metavar=format_enum_values(Target), type=Target, default=Target.NONE.value,
              help="Which files to operate on, the intersection, the difference, or duplicates.", show_default=True)
@click.option("-o", "--operation", metavar=format_enum_values(Operation), type=Operation, default=Operation.NONE.value,
              help="Which operation to perform on the target files. 'cp' and 'mv' will copy/move them to a separate "
                   "directory/file called '<path>_<target>'.",  show_default=True)
@click.option("-v", "--verbose", is_flag=True,
              help="List all files.")
def main(path_and_pattern: Sequence[Tuple[str, str]], target: Target, operation: Operation, verbose: bool) -> None:
    """
    Find all files (equivalence classes) that are present in all directories (the "intersection"), the remaining ones
    (the "difference") or the "duplicates" and do something with them. Can be used to make different directories match,
    to make them distinct or to remove duplicates.

    For finding duplicates the order of the '-p' options matters. The first path won't have duplicates, the second one
    will have the classes that were already present in the first as duplicates, the third one the ones form the first
    and second, etc.

    \b
    Example:
        For two directories with the following files:
        images/
            a.jpg a.xml.jpg b.jpg b.xml.jpg
        masks/
            a.tif b.tif c.tif
        The following can be used to find the files (or equivalence classes) that are not contained in both (c.tif):
            match_filenames.py -p images '([^.]+)\..+' -p masks '(.+)\.tif'
    """
    if operation != Operation.NONE and target == Target.NONE:
        print("Error: Need to specify a target if operation is not 'none'")
        sys.exit(-1)


    # classify the contents of a directory or file, and calculate intersection etc
    path_contents = classify(path_and_pattern)
    class_sets = [set(c.classes.keys()) for c in path_contents]
    intersection = set.intersection(*class_sets)

    processed_classes: Set[str] = set()
    for content in path_contents:
        classes_keys = set(content.classes.keys())
        content.difference = classes_keys - intersection
        content.duplicates = processed_classes & classes_keys
        processed_classes |= classes_keys


    # print files and statistics
    if target in [Target.INT, Target.NONE]:
        print("int: equivalence classes present in all directories ({}):".format(len(intersection)))
        print_list(intersection, verbose)
        print()

    if target in [Target.DIFF, Target.NONE]:
        print("diff: Equivalence classes not present in the intersection:")
        for content in path_contents:
            print("{} ({}):".format(content.path, len(content.difference)))
            print_list(content.difference, verbose)
            print()

    if target in [Target.DUP, Target.NONE]:
        print("dup: Equivalence classes already present in an earlier directory:")
        for content in path_contents:
            print("{} ({}):".format(content.path, len(content.duplicates)))
            print_list(content.duplicates, verbose)
            print()


    # do an operation on the target files/lines
    if operation == Operation.NONE:
        return

    print("Operating on:", target.value)
    for content in path_contents:
        if target == Target.INT:
            target_classes = intersection
        elif target == Target.DIFF:
            target_classes = content.difference
        elif target == Target.DUP:
            target_classes = content.duplicates
        else:
            assert False

        target_files = list(flatten(content.classes[c] for c in target_classes))
        suffix = "_" + target.value

        if target_files:
            if operation == Operation.CP:
                copy_files(content.path, target_files, content.filenames, suffix)
            elif operation == Operation.MV:
                move_files(content.path, target_files, content.filenames, suffix)
            elif operation == Operation.RM:
                remove_files(content.path, target_files, content.filenames)


if __name__ == '__main__':
    main()
