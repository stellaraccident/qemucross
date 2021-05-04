// ./sysroot/bin/musl-clang -fno-exceptions -stdlib=libc++ -I ./build/libcxx-stage1-install/include/c++/v1 -I ./sysroot/include -L ./build/libcxx-stage1-install/lib -o hello++ hello.cpp -lc++

// Missing rpath and such...
// LD_LIBRARY_PATH=./build/libcxx-stage1-install/lib:./sysroot/lib ./hello++

// Seems to be missing exceptions support in libc++

#include <iostream>

int main(int argc, char **argv) {
  std::cout << "Hello!\n";
  return 0;
}
