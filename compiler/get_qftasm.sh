#/bin/sh
a=$(python3 compiler.py $1)
echo "$a"
if [[ "$OSTYPE" == "darwin"* ]]; then
	echo -n "$a" | grep "^\d*\." | pbcopy
else
	echo -n "$a" | grep "^\d*\." | xclip
fi
