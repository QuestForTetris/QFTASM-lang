#/bin/sh
a=$(python3 compiler.py $1)
echo "$a"
if [[ "$OSTYPE" == "darwin"* ]]; then
	echo "$a" | grep "^\d" | pbcopy
else
	echo "$a" | grep "^\d" | xclip
fi
