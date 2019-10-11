#! /usr/bin/env bash

## Common to AWS and Azure
rm -f ../built/scripts.tar.gz
#dos2unix ../scripts/*
# Pack up scripts into an archive
tar cvz ../scripts/* > ../built/scripts.tar.gz

## AWS CFT
fname="bigiq-cm-dcd-pair.template"
output_dir="../aws/experimental/"
template_output="$output_dir$fname"
# Get name of current branch, ideally it includes the BIQ version number
branch_name=$(git rev-parse --abbrev-ref HEAD)

## Upload scripts archive
aws s3 cp --acl public-read ../built/scripts.tar.gz "s3://big-iq-quickstart-cf-templates-aws/$branch_name/"

# Compile template file
#./big-iq-master-aws-cft.py --branch $branch_name > $template_output

# Copy templates
for f in ../aws/experimental/*.template; do
    aws s3 cp --acl public-read "$f" "s3://big-iq-quickstart-cf-templates-aws/$branch_name/"
done

#aws s3 cp --acl public-read aws/experimental/bigiq-cm-dcd-pair.template "s3://big-iq-quickstart-cf-templates-aws/7.0.0/"
#aws s3 cp --acl public-read aws/experimental/bigiq-cm-dcd-pair-existing-vpc.template "s3://big-iq-quickstart-cf-templates-aws/7.0.0/"