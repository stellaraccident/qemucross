#!/usr/bin/python

import argparse
import multiprocessing
import os
import shutil
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
    self.libcxxrt_src_dir = os.path.join(self.repo_dir, "external", "libcxxrt")
    self.libunwind_src_dir = os.path.join(self.repo_dir, "external", "libunwind")
    self.llvm_src_dir = os.path.join(self.repo_dir, "external", "llvm-project")
    self.musl_src_dir = os.path.join(self.repo_dir, "external", "musl")

    # Build directories.
    self.libcxxrt_build_dir = os.path.join(self.repo_dir, "build", "libcxxrt")
    os.makedirs(self.libcxxrt_build_dir, exist_ok=True)
    self.libunwind_build_dir = os.path.join(self.repo_dir, "build", "libunwind")
    os.makedirs(self.libunwind_build_dir, exist_ok=True)
    self.llvm_build_dir = os.path.join(self.repo_dir, "build", "llvm")
    os.makedirs(self.llvm_build_dir, exist_ok=True)
    self.musl_build_dir = os.path.join(self.repo_dir, "build", "musl")
    os.makedirs(self.musl_build_dir, exist_ok=True)

    # Installation paths.
    self.sysroot_dir = os.path.join(self.repo_dir, "sysroot")
    os.makedirs(self.sysroot_dir, exist_ok=True)
    self.syslib_dir = os.path.join(self.sysroot_dir, "lib")
    os.makedirs(self.syslib_dir, exist_ok=True)

    # libcxx stage1 - built against libcxxrt
    self.libcxx_stage1_build_dir = os.path.join(self.repo_dir, "build", "libcxx-stage1")
    os.makedirs(self.libcxx_stage1_build_dir, exist_ok=True)
    self.libcxx_stage1_install_dir = os.path.join(self.repo_dir, "build", "libcxx-stage1-install")
    os.makedirs(self.libcxx_stage1_install_dir, exist_ok=True)

    # Environment.
    environ = os.environ.copy()
    if "CC" in environ: del environ["CC"]
    if "CXX" in environ: del environ["CXX"]
    if "LD" in environ: del environ["LD"]
    if "CFLAGS" in environ: del environ["CFLAGS"]
    if "CXXFLAGS" in environ: del environ["CXXFLAGS"]
    if "LDFLAGS" in environ: del environ["LDFLAGS"]
    environ["CC"] = "clang"
    environ["CXX"] = "clang++"
    environ["CFLAGS"] = "-fPIC"
    environ["CXXFLAGS"] = "-fPIC"
    environ["LDFLAGS"] = ""
    self.environ = environ

    # Sysroot setup.
    self.symlink_sysroot("/usr/include/linux", "include/linux")
    self.symlink_sysroot("/usr/include/asm-generic", "include/asm")
    self.symlink_sysroot("/usr/include/asm-generic", "include/asm-generic")

  def symlink_sysroot(self, src_path, dest_path):
    dest_path = os.path.join(self.sysroot_dir, dest_path)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    if not os.path.exists(dest_path):
      print(f"SYMLINK {src_path} -> {dest_path}")
      os.symlink(src_path, dest_path)

  def cflag(self, flag):
    self.environ["CFLAGS"] += f" {flag}"
    self.environ["CXXFLAGS"] += f" {flag}"

  def ldflag(self, flag):
    self.environ["LDFLAGS"] += f" {flag}"

  def use_musl(self):
    self.environ["CC"] = f"{self.sysroot_dir}/bin/musl-clang"
    self.environ["CXX"] = self.environ["CC"]
    self.cflag("-Wno-unused-command-line-argument")
    print("--- USING MUSL ---")
    print(self.environ)


@add_action
def build_musl(args):
  c = Config(args)
  print("--- Configure MUSL ---")
  subprocess.check_call([
    os.path.join(c.musl_src_dir, "configure"),
    f"--srcdir={c.musl_src_dir}",
    f"--prefix={c.sysroot_dir}",
    #"--disable-static",
    f"--syslibdir={c.syslib_dir}",
    #"--disable-shared",
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


@add_action
def build_libunwind(args):
  c = Config(args)
  c.use_musl()
  # Why??? Needed to find stdatomic.h for libunwind.
  self.cflag("-I/usr/lib/llvm-10/lib/clang/10.0.0/include")
  env = dict(c.environ)
  print("--- Autogen libunwind ---")
  subprocess.check_call([
    os.path.join(c.libunwind_src_dir, "autogen.sh"),
  ], cwd=c.libunwind_src_dir, env={"NOCONFIGURE": "TRUE"})
  print("--- Configure libunwind ---")
  subprocess.check_call([
    os.path.join(c.libunwind_src_dir, "configure"),
    f"--prefix={c.sysroot_dir}",
    "--disable-shared",  # Tries to link against gcc_s
    "--disable-tests",   # Tries to link against gcc_s
  ], cwd=c.libunwind_build_dir, env=env)
  print("--- Build libunwind ---")
  subprocess.check_call([
    "make", "install",
    f"-j{args.j}",
  ], cwd=c.libunwind_build_dir, env=env)


@add_action
def build_libcxxrt(args):
  c = Config(args)
  c.use_musl()
  env = dict(c.environ)
  env["CC"] = f"{c.environ['CC']} -fPIC"
  env["CXX"] = f"{c.environ['CXX']} -fPIC"
  print("--- libcxxrt Configure ---")
  subprocess.check_call([
    "cmake", c.libcxxrt_src_dir,
    "-DCMAKE_BUILD_TYPE=Release",
  ], cwd=c.libcxxrt_build_dir, env=env)
  print("--- libcxxrt make ---")
  subprocess.check_call([
    "make", f"-j{args.j}",
  ], cwd=c.libcxxrt_build_dir, env=env)
  shutil.copy(os.path.join(c.libcxxrt_build_dir, "lib", "libcxxrt.a"),
      os.path.join(c.sysroot_dir, "lib"))
  shutil.copy(os.path.join(c.libcxxrt_build_dir, "lib", "libcxxrt.so"),
      os.path.join(c.sysroot_dir, "lib"))


@add_action
def build_libcxx_stage1(args):
  c = Config(args)
  c.use_musl()
  print("--- libcxxrt stage1 Configure ---")
  subprocess.check_call([
    "cmake", f"{c.llvm_src_dir}/libcxx",
    "-DCMAKE_BUILD_TYPE=Release",
    "-DLIBCXX_CXX_ABI=libcxxrt",
    f"-DLIBCXX_CXX_ABI_INCLUDE_PATHS={c.libcxxrt_src_dir}/src",
    f"-DCMAKE_INSTALL_PREFIX={c.libcxx_stage1_install_dir}",
    #"-DLIBCXX_ENABLE_LOCALIZATION=OFF",
    "-DLIBCXX_HAS_MUSL_LIBC=ON",
    "-DLIBCXX_ENABLE_FILESYSTEM=OFF",
  ], cwd=c.libcxx_stage1_build_dir, env=c.environ)
  print("--- libcxx make ---")
  subprocess.check_call([
    "make", f"-j{args.j}", "install",
  ], cwd=c.libcxx_stage1_build_dir, env=c.environ)


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
