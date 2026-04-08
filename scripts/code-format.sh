#!/bin/bash

poetry run black -t py310 -l 88 $(find . -name "*.py")

# Remove trailing whitespace in all .py files
find . -name "*.py" -exec sed -i 's/[[:space:]]*$//' {} \;
