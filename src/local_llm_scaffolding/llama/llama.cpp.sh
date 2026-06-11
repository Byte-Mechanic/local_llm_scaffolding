#!/bin/bash
SCRIPT_DIR="$( cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd )"

LIB_PATH="$SCRIPT_DIR/build/bin"

LD_LIBRARY_PATH="$LIB_PATH:$LD_LIBRARY_PATH" "$LIB_PATH/llama-server" "$@"
