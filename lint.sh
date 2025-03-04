#!/bin/bash
echo "Running yapf to format the code"
yapf -i -p -vv --exclude=.venv --exclude=.build --exclude=cdk.out --exclude=.git -r .
echo "Using isort to order python imports"
isort --skip-glob=".venv" \
      --extend-skip-glob="cdk.out" \
      --extend-skip-glob=".build" \
      .
echo "Using pylint to lint the code"
pylint --rcfile .pylintrc --jobs 4 --py-version 3.12 --ignore=".venv,cdk.out,.build" .
