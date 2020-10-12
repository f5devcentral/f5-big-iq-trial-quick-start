#!/usr/bin/env bash
echo "Searching for image where name begins with $1"
# e.g. "F5 Networks BYOL BIG-IQ-7.0.0.1.0.0.6"
regions=$(aws ec2 describe-regions --output text --query 'Regions[*].RegionName')
json=""
for region in $regions; do
    ami=$(aws ec2 describe-images --region $region --filters Name=is-public,Values=true Name=name,Values="$1*" --output json | jq '.Images[] | "\(.ImageId)"' | head -1)
    if [ ! -z "$ami" ]; then
        json="$json,\"$region\": { \"bigiq\": $ami}"
    else
        echo "Unsupported Region: $region (no AMI found)"
    fi
done

json="{ ${json:1} }"
echo $json | jq .