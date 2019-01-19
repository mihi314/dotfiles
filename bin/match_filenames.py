#!/usr/bin/env python3
import re
import os
from os.path import join
from collections import defaultdict
import itertools as it
import shutil

import click


def classify(paths_and_patterns):
    """
    Take list of (path, pattern) tuples and sort the files in path into equivalence classes based on the regexp pattern.
    path:
        Can be a directory or a file containing lines of text
    pattern:
        A regular expression whose matches define equivalence classes. If there are subgroups, use those. If there is
        no match, use the whole filename to define a class.
    """
    all_classes = {}
    all_files = {}

    for path, pattern in paths_and_patterns:
        is_dir = os.path.isdir(path)
        if is_dir:
            filenames = os.listdir(path)
            path = path.rstrip("/")
        else:
            with open(path, "r") as f:
                filenames = [l for l in f.read().split("\n") if l]

        equivalence_classes = classify_list(filenames, pattern)

        all_classes[path] = equivalence_classes
        all_files[path] = filenames

    return all_classes, all_files


def classify_list(filenames, pattern):
    # sort each filename into a class
    # and generate a mapping from class to filenames belonging to that class
    equivalence_classes = defaultdict(list)
    for filename in filenames:
        # todo: add nicer error message when the regexp is invalid
        match = re.search(pattern, filename)
        if not match:
            class_ = filename
        elif len(match.groups()) == 0:
            class_ = match.group(0)
        else:
            class_ = "".join(match.groups())

        equivalence_classes[class_].append(filename)
    return equivalence_classes


def flatten(list_of_lists):
    return it.chain.from_iterable(list_of_lists)


def move_files(path, diff_files, all_files, suffix):
    target = path + suffix
    print("Moving {}/{} files from '{}' to '{}'".format(len(diff_files), len(all_files), path, target))

    if os.path.isdir(path):
        for file in diff_files:
            os.makedirs(target, exist_ok=True)
            shutil.move(join(path, file), target)
    else:
        with open(target, "w") as f:
            f.write("\n".join(sorted(diff_files)))
        with open(path, "w") as f:
            remaining = set(all_files) - set(diff_files)
            f.write("\n".join(sorted(remaining)))


def delete_files(path, diff_files, all_files):
    print("Deleting {}/{} files in '{}'".format(len(diff_files), len(all_files), path))

    if os.path.isdir(path):
        for file in diff_files:
            os.remove(join(path, file))
    else:
        with open(path, "w") as f:
            remaining = set(all_files) - set(diff_files)
            f.write("\n".join(sorted(remaining)))


def print_list(lines, verbose, limit=20):
    if not lines:
        return
    if verbose or len(lines) <= limit:
        print("\n".join(list(lines)))
    else:
        print("\n".join(list(lines)[:limit]))
        print("...")


@click.command()
@click.option("-p", "--path_and_pattern", type=click.Tuple([click.Path(exists=True), str]), multiple=True, required=True,
              help="(path, pattern) tuple. path can be a directory or a text file. pattern is a regular "
                   "expression whose matches define equivalence classes. If there are subgroups, use those. If there "
                   "is no match, use the whole filename to define a class.")
@click.option("-t", "--target", type=click.Choice(["diff", "int"]), default="diff",
              help="whether to do move/delete on the difference or the intersection (default: diff)")
@click.option("--delete", is_flag=True,
              help="whether to delete the difference or intersection")
@click.option("--move", is_flag=True,
              help="whether to move the difference or intersection to a separate folder/file called "
                   "${path}_diff/${path}_int")
@click.option("-v", "--verbose", is_flag=True,
              help="list all files")
def main(path_and_pattern, target, delete, move, verbose):
    """
    Find all files (equivalence classes) that are present in all directories (the "intersection") and do something with
    them or the remaining ones (the "difference"). Can be used to make the different directories match, or to make them
    distinct.
    """
    assert not (delete and move)

    all_classes, all_files = classify(path_and_pattern)
    class_sets = [set(c.keys()) for c in all_classes.values()]
    intersection = set.intersection(*class_sets)

    print("int: equivalence classes present in all directories ({}):".format(len(intersection)))
    print_list(intersection, verbose)
    print()
    print("diff: Equivalence classes present only in some directories:")

    for path, classes in all_classes.items():
        difference = set(classes.keys()) - intersection
        print("{} ({}):".format(path, len(difference)))
        print_list(difference, verbose)

        if target == "diff":
            target_classes = difference
            suffix = "_diff"
        else:
            target_classes = intersection
            suffix = "_int"
        target_files = list(flatten(classes[c] for c in target_classes))

        if move and target_files:
            move_files(path, target_files, all_files[path], suffix)

        if delete and target_files:
            delete_files(path, target_files, all_files[path])

        print()


if __name__ == '__main__':
    main()
