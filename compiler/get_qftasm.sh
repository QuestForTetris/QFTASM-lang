#/bin/sh
a=$(python3 compiler.py $1)
echo "$a" | grep "^\d" | xclip
