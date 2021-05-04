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


class Config:
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

    # Environment.
    environ = os.environ.copy()
    if "CC" in environ: del environ["CC"]
    if "CXX" in environ: del environ["CXX"]
    if "LD" in environ: del environ["LD"]
    self.environ = environ


@add_action
def build_musl(args):
  c = Config(args)
  print("--- Configure MUSL ---")
  subprocess.check_call([
    os.path.join(c.musl_src_dir, "configure"),
    f"--srcdir={c.musl_src_dir}",
    f"--prefix={c.sysroot_dir}",
    #f"--syslibdir={p.syslib_dir}",
    #"--disable-static",
    "--disable-shared",
  ], cwd=c.musl_build_dir, env=c.environ)
  print("--- MUSL Configure Complete ---")
  print(f"--- Building MUSL (jobs={args.j})---")
  subprocess.check_call([
    "make",
    f"-j{args.j}",
  ], cwd=c.musl_build_dir, env=c.environ)
  print(f"--- Installing MUSL ---")
  subprocess.check_call([
    "make", "install",
  ], cwd=c.musl_build_dir, env=c.environ)


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
