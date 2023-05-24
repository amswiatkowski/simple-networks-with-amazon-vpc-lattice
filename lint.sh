#!/bin/bash
echo "Using flake8 to lint the code"
flake8 cdk/* tests/* lambda_handlers/* --exclude patterns='build,cdk.json,cdk.context.json,.yaml'
echo "Using isort to order python imports"
isort ${PWD}
