#!/usr/bin/env python3

import getpass
import os
import random
import shutil as sh
import subprocess as sp
import sys


def error_out(msg: str) -> None:
    print("error: " + msg)
    sys.exit(1)


if len(sys.argv) < 3:
    error_out("usage: grade.py <assignment> <task>")

assignment = sys.argv[1]
task = sys.argv[2]

grade_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.realpath(os.path.join(grade_dir, "..", ".."))

if getpass.getuser() != "codegrade":
    error_out("This is supposed to run on the codegrade environment.")

os.chdir(base_dir)

home_dir = "/home/codegrade"
handin_dir = os.path.join(home_dir, "student")
student_coco = os.path.join(home_dir, "student-coco")

# Create a fresh student dir.
if os.path.isdir(student_coco):
    sh.rmtree(student_coco)
os.makedirs(student_coco, exist_ok=True)

# Copy the handin into the student coco directory.
assign_dir = os.path.join(student_coco, f"assign{assignment}")
sh.copytree(handin_dir, assign_dir)

# Restore a bunch of files to their original state.
to_replace_list = [
    "framework",
    "assign1/tests",
    "assign2/benchmarks",
    "assign3/tests",
    "assign4/original-src",
    "grade",
    # NOTE: run.py intentionally NOT restored/used anymore
]

for rel in to_replace_list:
    src = os.path.join(base_dir, rel)
    dest = os.path.join(student_coco, rel)

    if os.path.isfile(dest) or os.path.islink(dest):
        os.remove(dest)
    if os.path.isdir(dest):
        sh.rmtree(dest)

    if os.path.isfile(src):
        sh.copy(src, dest)
    else:
        sh.copytree(src, dest)

# We don't know what needs to be executable, so just mark the whole submission.
sp.check_call(["chmod", "-R", "755", student_coco])

# Pick a random grade file name.
grade_file = f"grade-out-{random.randrange(0, 10_000_000)}.json"

# Run grading directly on the VM (no docker, no run.py).
env = os.environ.copy()
env["PRINT_DIFF"] = "1"
env["NOCOLOR"] = "1"
env["GRADE_OUTPUT"] = grade_file

# Important: run ./grade from inside the student's reconstructed workspace
sp.check_call(["./grade", "-a", task], cwd=student_coco, env=env)

# Copy the produced grade JSON to the expected output location.
src_grade_json = os.path.join(student_coco, grade_file)
if not os.path.isfile(src_grade_json):
    error_out(f"expected grade output file not found: {src_grade_json}")

sh.copy(src_grade_json, os.path.join(home_dir, "grade.json"))
