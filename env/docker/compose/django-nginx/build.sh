#!/bin/bash

if [[ $1 != "" ]]; then
	  VERSION="$1"
  else
	    VERSION="latest"
fi
echo "version: $VERSION"

# build
docker build -t youngha/django:$VERSION -f Dockerfile .
