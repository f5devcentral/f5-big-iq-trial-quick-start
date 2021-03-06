#!/usr/bin/env bash
#set -x

echo "Searching for image where name begins with $1"
# e.g. "F5 Networks BYOL BIG-IQ-7.1.0.3.0.0.41, F5 Hourly BIG-IQ-8.0.0-0.0.594"
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