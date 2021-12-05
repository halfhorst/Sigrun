#!/bin/sh

python build_lambda_zip.py

RESPONSE=$?
if [ $RESPONSE != 0 ]
then
    echo "Failed to build lambda zip."
    return RESPONSE;
fi

cdk deploy --all
