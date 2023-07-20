#!/bin/bash

mkdir -p .build/lambdas ; cp -r lambda_handlers .build/lambdas
mkdir -p .build/common_layer ; poetry export --without=dev --without-hashes --format=requirements.txt > .build/common_layer/requirements.txt
cdk deploy --app="python ${PWD}/app.py" --require-approval=never
