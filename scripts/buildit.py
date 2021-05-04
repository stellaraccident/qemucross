#!/usr/bin/python

import argparse
import multiprocessing
import os
import subprocess
import sys

ACTIONS = dict()
def add_action(f):
  ACTIONS[f.__name__] = f
  return f


class Paths:
  def __init__(self, args):
    self.repo_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    # Source paths.
    self.musl_src_dir = os.path.join(self.repo_dir, "external", "musl")
    self.llvm_src_dir = os.path.join(self.repo_dir, "external", "llvm-project")

    # Build directories.
    self.musl_build_dir = os.path.join(self.repo_dir, "build", "musl")
    os.makedirs(self.musl_build_dir, exist_ok=True)
    self.llvm_build_dir = os.path.join(self.repo_dir, "build", "llvm")
    os.makedirs(self.llvm_build_dir, exist_ok=True)

    # Installation paths.
    self.sysroot_dir = os.path.join(self.repo_dir, "sysroot")
    os.makedirs(self.sysroot_dir, exist_ok=True)
    self.syslib_dir = os.path.join(self.sysroot_dir, "lib")
    os.makedirs(self.syslib_dir, exist_ok=True)


@add_action
def build_musl(args):
  p = Paths(args)
  print("--- Configure MUSL ---")
  subprocess.check_call([
    os.path.join(p.musl_src_dir, "configure"),
    f"--srcdir={p.musl_src_dir}",
    f"--prefix={p.sysroot_dir}",
    f"--syslibdir={p.syslib_dir}",
    "--disable-static",
  ], cwd=p.musl_build_dir)
  print("--- MUSL Configure Complete ---")
  print(f"--- Building MUSL (jobs={args.j})---")
  subprocess.check_call([
    "make",
    f"-j{args.j}",
  ], cwd=p.musl_build_dir)
  print(f"--- Installing MUSL ---")
  subprocess.check_call([
    "make", "install",
  ], cwd=p.musl_build_dir)


def main(args):
  action = ACTIONS.get(args.action)
  if action is None:
    raise ValueError(f"Unsupported 'action' argument: {args.action}")
  action(args)


def create_argument_parser():
  parser = argparse.ArgumentParser(description="Main build script")
  parser.add_argument("action")
  parser.add_argument("-j", type=int, default=multiprocessing.cpu_count(),
    help="Number of parallel jobs")
  return parser


if __name__ == "__main__":
  args = create_argument_parser().parse_args()
  main(args)
