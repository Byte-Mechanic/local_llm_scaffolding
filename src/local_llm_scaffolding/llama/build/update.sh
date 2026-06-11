SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd $SCRIPT_DIR
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp/
# Replace from here-
HIPCXX="$(hipconfig -l)/clang" HIP_PATH="$(hipconfig -R)" \
  cmake -S . -B build -DGGML_HIP=ON -DGPU_TARGETS=gfx1030 -DCMAKE_BUILD_TYPE=Release
# -to here with your custom build settings.
cmake --build build --target llama-server --config Release -j $(nproc)
cd ..
mv llama.cpp/build/bin/* bin/
rm -rf llama.cpp/
