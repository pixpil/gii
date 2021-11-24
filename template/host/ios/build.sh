
if xcodebuild -target $1 -configuration $2 -sdk $3 ; then
	exit 0
else
	exit 1
fi
