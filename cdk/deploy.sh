#!/bin/sh

poetry run python build_lambda_zip.py

RESPONSE=$?
if [ $RESPONSE != 0 ]
then
    echo "Failed to build lambda zip."
    return RESPONSE;
fi

poetry run cdk deploy --all

