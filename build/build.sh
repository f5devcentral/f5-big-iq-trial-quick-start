#! /usr/bin/env bash

## Common to AWS and Azure
rm -f ../built/scripts.tar.gz
dos2unix ../scripts/*
# Pack up scripts into an archive
tar cvz ../scripts/* > ../built/scripts.tar.gz

# Get name of current branch, ideally it includes the BIQ version number
branch_name=$(git rev-parse --abbrev-ref HEAD)

## Upload scripts archive
aws s3 cp --acl public-read ../built/scripts.tar.gz "s3://big-iq-quickstart-cf-templates-aws/$branch_name/"

# Copy templates
for f in ../aws/experimental/*.template; do
    aws s3 cp --acl public-read "$f" "s3://big-iq-quickstart-cf-templates-aws/$branch_name/"
done