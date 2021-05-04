// ./sysroot/bin/musl-clang -static -O2 -fno-exceptions -fno-rtti -stdlib=libc++ -I ./build/libcxx-stage1-install/include/c++/v1 -I ./sysroot/include -L ./build/libcxx-stage1-install/lib -o hello++ hello.cpp -lc++ -lcxxrt

// If building dynamic...
// Missing rpath and such...
// LD_LIBRARY_PATH=./build/libcxx-stage1-install/lib:./sysroot/lib ./hello++

// Seems to be missing exceptions support in libc++

#include <iostream>

int main(int argc, char **argv) {
  std::cout << "Hello!\n";
  return 0;
}
