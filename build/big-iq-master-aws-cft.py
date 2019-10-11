#! /usr/bin/env python3
import argparse
from os import listdir
from os.path import isfile, join
from pathlib import Path

import troposphere
from troposphere import (Base64, FindInMap, GetAtt, Join,
                         Output, Parameter, Ref, cloudformation)
from troposphere.cloudformation import *
from troposphere.ec2 import *
from troposphere.elasticloadbalancing import (HealthCheck, Listener,
                                              LoadBalancer)

def parse_args ():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--branch",
        required=True,
        help="Please provide output of `git rev-parse --abbrev-ref HEAD`"
    )

    return parser.parse_args()

SCRIPT_PATH = "../scripts/"
# Files which configure the BIG-IQ instances

def generate_pwd_prompt (prompt_text, var_name):
    return (
        'read -s -p "' + prompt_text + '" v1 \n'
        'echo \n'
        'read -s -p "Re-enter ' + prompt_text + '" ' + var_name + ' \n'
        'while [ "$v1" != "$' + var_name + '" ]; do \n'
        '    echo \n'
        '    echo "Entries did not match, try again" \n'
        '    echo \n'
        '    read -s -p "' + prompt_text + '" v1 \n'
        '    echo \n'
        '    read -s -p "Re-enter ' + prompt_text + '" ' + var_name + ' \n'
        'done \n'
        'echo'
    )

def define_instance_init_files (t, args):
    init_files_map = {}

    # Download scripts archive from raw.gh and extract
    download_and_extract_scripts = (
        "mkdir -p /config/cloud \n"
        "cd /config/cloud \n"
        "curl https://s3.amazonaws.com/big-iq-quickstart-cf-templates-aws/" + args.branch + "/scripts.tar.gz > scripts.tar.gz \n"
        "tar --strip-components=1 -xvzf scripts.tar.gz \n"
    )

    return {
        "cm": InitFiles({
            "/config/cloud/setup-cm.sh": InitFile(
                mode = "000755",
                owner = "root",
                group = "root",
                content = Join("\n", [
                    # This script is run in root context
                    "#!/usr/bin/env bash",
                    generate_pwd_prompt('BIG-IQ Password [Alphanumerics only]: ', 'BIG_IQ_PWD'),
                    'nohup /config/cloud/setup-cm-background.sh "$BIG_IQ_PWD" &> /var/log/setup.log < /dev/null &',
                    "echo 'tail -f /var/log/setup.log in order to monitor setup progress'",
                    "echo;"
                    "echo 'Make sure you follow Teardown instructions from the GitHub repository once you are done with your testing.'"
                ])
            ),
            "/config/cloud/setup-cm-background.sh": InitFile(
                mode = "000755",
                owner = "root",
                group = "root",
                content = Join("\n", [
                    # This script is run in root context
                    "#!/usr/bin/env bash",
                    download_and_extract_scripts,
                    'BIG_IQ_PWD="$1"',
                    "mount -o remount,rw /usr",
                    # Run configuration
                    Join(" ", [
                        "/config/cloud/configure-bigiq.py --LICENSE_KEY",
                        Ref(t.parameters["licenseKey1"]),
                        "--MASTER_PASSPHRASE",
                        Ref(t.parameters["masterPassphrase"]),
                        "--TIMEOUT_SEC 1200"
                    ]),
                    # Wait for restart to take effect, should be unnecessary since the setup wizard has resequenced to
                    # only set startup true after the restart has taken place
                    "sleep 10",
                    Join(" ", [
                        "/config/cloud/add-dcd.py --DCD_IP_ADDRESS",
                        GetAtt("BigIqDcdEth0", "PrimaryPrivateIpAddress"),
                        Join(" ", [
                            '--DCD_PWD "$BIG_IQ_PWD"',
                            "--DCD_USERNAME admin"
                        ])
                    ]),
                    "chmod +x /config/cloud/import-as3-templates.sh",
                    "/config/cloud/import-as3-templates.sh",
                    Join("", [
                        "tmsh modify auth user admin",
                        ' password "$BIG_IQ_PWD"',
                        " && tmsh save sys config"
                    ]),
                    Join(" ", [
                        "/config/cloud/activate-dcd-services.py --SERVICES asm",
                        "--DCD_IP_ADDRESS",
                        GetAtt("BigIqDcdEth0", "PrimaryPrivateIpAddress")
                    ]),
                    "set-basic-auth on" # The calls within require identity gleaned from a login
                ])
            )
        }),
        "dcd": InitFiles({
            "/config/cloud/setup-dcd.sh": InitFile(
                mode = "000755",
                owner = "root",
                group = "root",
                content = Join("\n", [
                    "#!/usr/bin/env bash",
                    generate_pwd_prompt('BIG-IQ Password [Alphanumerics only]: ', 'BIG_IQ_PWD'),
                    'nohup /config/cloud/setup-dcd-background.sh "$BIG_IQ_PWD" &> /var/log/setup.log < /dev/null &',
                    "echo 'tail -f /var/log/setup.log in order to monitor setup progress'"
                ])
            ),
            "/config/cloud/setup-dcd-background.sh": InitFile(
                mode = "000755",
                owner = "root",
                group = "root",
                content = Join("\n", [
                    "#!/usr/bin/env bash",
                    download_and_extract_scripts,
                    "/config/cloud/wait-for-rjd.py",
                    'BIG_IQ_PWD="$1"',
                    Join("", [
                        "tmsh modify auth user admin",
                        ' password "$BIG_IQ_PWD"',
                        " && tmsh save sys config && set-basic-auth on"
                    ]),
                    Join(" ", [
                        "/config/cloud/configure-bigiq.py --LICENSE_KEY",
                        Ref(t.parameters["licenseKey2"]),
                        "--MASTER_PASSPHRASE",
                        Ref(t.parameters["masterPassphrase"]),
                        "--TIMEOUT_SEC 1200",
                        "--NODE_TYPE DCD"
                    ])
                ])
            )
        })
    }

def define_instance_metadata (t, args, is_cm_instance=True):
    init_files_map = define_instance_init_files(t, args)
    return Metadata(
        Init({
            "config": InitConfig(
                files = init_files_map["cm"] if is_cm_instance else init_files_map["dcd"]
            )
        })
    )

def define_metadata (t):
    t.add_metadata({
        "Version": "1.0.0",
        "AWS::CloudFormation::Interface": define_interface()
    })

# Define the AWS::CloudFormation::Interface for the template
def define_interface ():
    return {
            "ParameterGroups": [
                {
                    "Label": {
                        "default": "NETWORKING CONFIGURATION"
                    },
                    "Parameters": [
                        "vpcCidrBlock",
                        "subnet1CidrBlock",
                        "subnet1Az"
                    ]
                }, {
                    "Label": {
                        "default": "Accept BIG-IQ Terms and Conditions: https://aws.amazon.com/marketplace/pp/B00KIZG6KA"
                    },
                    "Parameters": [ ]
                }, {
                    "Label": {
                        "default": "BIG-IQ CONFIGURATION"
                    },
                    "Parameters": [
                        "bigIqPassword",
                        "bigIqAmi",
                        "licenseKey1",
                        "licenseKey2",
                        "masterPassphrase",
                        "instanceType",
                        "restrictedSrcAddress",
                        "sshKey"
                    ]
                }
            ],
            "ParameterLabels": define_param_labels()
        }

# Define the AMI mappings per region for BIG-IQ
def define_mappings (t):
    t.add_mapping("AmiRegionMap", {
        "eu-north-1": {
        "bigiq": "ami-ae9913d0"
        },
        "ap-south-1": {
        "bigiq": "ami-0102bd6934987f9b4"
        },
        "eu-west-2": {
        "bigiq": "ami-02fa9c0cf70261667"
        },
        "eu-west-1": {
        "bigiq": "ami-046af572233671cec"
        },
        "ap-northeast-2": {
        "bigiq": "ami-0379bc3d5fbd5d2b6"
        },
        "ap-northeast-1": {
        "bigiq": "ami-03b922910324db7aa"
        },
        "sa-east-1": {
        "bigiq": "ami-054f641e417cb06d7"
        },
        "ca-central-1": {
        "bigiq": "ami-0190f71dcb9cc1f9f"
        },
        "ap-southeast-1": {
        "bigiq": "ami-00db427a9fb8bd623"
        },
        "ap-southeast-2": {
        "bigiq": "ami-0916a14783f29fb52"
        },
        "eu-central-1": {
        "bigiq": "ami-01fcae3ec9761cff5"
        },
        "us-east-1": {
        "bigiq": "ami-09cd0faf029ac7746"
        },
        "us-east-2": {
        "bigiq": "ami-08ae7e928d8bda90a"
        },
        "us-west-1": {
        "bigiq": "ami-05e14d844b0b28686"
        },
        "us-west-2": {
        "bigiq": "ami-033094a3b2f492fae"
        }
    })

# Define the parameter labels for the AWS::CloudFormation::Interface
def define_param_labels ():
    return {
        "bigIqPassword": {
            "default": "BIG-IQ Admin Password"
        },
        "bigIqAmi": {
            "default": "BIG-IQ AMI"
        },
        "masterPassphrase": {
            "default": "BIG-IQ Master Key Passphrase"
        },
        "imageName": {
            "default": "Image Name"
        },
        "instanceType": {
            "default": "AWS Instance Size"
        },
        "licenseKey1": {
            "default": "BIG-IQ CM License Key"
        },
        "licenseKey2": {
            "default": "BIG-IQ DCD License Key"
        },
        "vpcCidrBlock": {
            "default": "VPC CIDR Block"
        },
        "restrictedSrcAddress": {
            "default": "Source Address(es) for SSH Access"
        },
        "sshKey": {
            "default": "SSH Key"
        },
        "subnet1Az": {
            "default": "Subnet AZ1"
        },
        "subnet1CidrBlock": {
            "default": "Subnet 1 CIDR Block"
        }
    }

# Define the template parameters and constraints
def define_parameters (t):
    t.add_parameter(Parameter("instanceType",
        AllowedValues = [
            "m4.2xlarge", "m4.4xlarge", "m4.8xlarge"
        ],
        ConstraintDescription = "Must be a valid EC2 instance type for BIG-IQ",
        Default = "m4.2xlarge",
        Description = "Size of the F5 BIG-IQ Virtual Instance",
        Type = "String"
    ))
    t.add_parameter(Parameter("licenseKey1",
        ConstraintDescription = "Verify your F5 BYOL regkey.",
        Description = "F5 BIG-IQ CM license key",
        MaxLength = 255,
        MinLength = 1,
        Type = "String"
    ))
    t.add_parameter(Parameter("licenseKey2",
        ConstraintDescription = "Verify your F5 BYOL regkey.",
        Description = "F5 BIG-IQ DCD license key",
        MaxLength = 255,
        MinLength = 1,
        Type = "String"
    ))
    t.add_parameter(Parameter("masterPassphrase",
        ConstraintDescription = "Verify your Master Key Passphrase 16-characters min.",
        Description = "F5 BIG-IQ Master Key Passphrase",
        Default = "Thisisthemasterkey#1234",
        MaxLength = 255,
        MinLength = 1,
        Type = "String"
    ))
    t.add_parameter(Parameter("vpcCidrBlock",
        AllowedPattern = "(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})/(\\d{1,2})",
        ConstraintDescription = "Must be a valid IP CIDR range of the form x.x.x.x/x.",
        Default = "10.1.0.0/16",
        Description = " The CIDR block for the VPC",
        MaxLength = 18,
        MinLength = 9,
        Type = "String"
    ))
    t.add_parameter(Parameter("restrictedSrcAddress",
        AllowedPattern = "(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})/(\\d{1,2})",
        ConstraintDescription = "Must be a valid IP CIDR range of the form x.x.x.x/x.",
        Description = " The IP address range used to SSH and access managment GUI on the EC2 instances",
        Default = "0.0.0.0/0",
        MaxLength = 18,
        MinLength = 9,
        Type = "String"
    ))
    t.add_parameter(Parameter("sshKey",
        Description = "Key pair for accessing the instance",
        Type = "AWS::EC2::KeyPair::KeyName"
    ))
    t.add_parameter(Parameter("subnet1Az",
        Description = "Name of an Availability Zone in this Region",
        Type = "AWS::EC2::AvailabilityZone::Name"
    ))
    t.add_parameter(Parameter("subnet1CidrBlock",
        AllowedPattern = "(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})/(\\d{1,2})",
        ConstraintDescription = "Must be a valid IP CIDR range of the form x.x.x.x/x.",
        Default = "10.1.1.0/24",
        Description = " The CIDR block for the first subnet which is compatible with the VPC CIDR block",
        MaxLength = 18,
        MinLength = 9,
        Type = "String"
    ))

# Define the networking components for the stack
# VPC, two subnets, security group, classic ELB, IGW etc
def define_networking (t):
    t.add_resource(
        VPC(
            "VPC",
            CidrBlock = Ref(t.parameters["vpcCidrBlock"]),
            InstanceTenancy = "default",
            EnableDnsSupport = True,
            EnableDnsHostnames = False,
            Tags = troposphere.cloudformation.Tags(
                Name = Join(" ", ["BIG-IQ VPC:", Ref("AWS::StackName")])
            )
        )
    )

    t.add_resource(
        Subnet(
            "Subnet1",
            CidrBlock = Ref(t.parameters["subnet1CidrBlock"]),
            VpcId = Ref(t.resources["VPC"]),
            AvailabilityZone = Ref(t.parameters["subnet1Az"]),
            Tags = Tags(
                Name = Join(" ", ["BIG-IQ Subnet 1:", Ref("AWS::StackName")])
            )
        )
    )

    t.add_resource(RouteTable(
        "RouteTable1",
        VpcId = Ref(t.resources["VPC"]),
        Tags = Tags(
            Name = Join(" ", ["BIG-IQ Route Table 1:", Ref("AWS::StackName")])
        )
    ))

    t.add_resource(RouteTable(
        "RouteTable2",
        VpcId = Ref(t.resources["VPC"]),
        Tags = Tags(
            Name = Join(" ", ["BIG-IQ Route Table 2:", Ref("AWS::StackName")])
        )
    ))

    t.add_resource(SubnetRouteTableAssociation(
        "Subnet1RouteTableAssociation",
        SubnetId = Ref(t.resources["Subnet1"]),
        RouteTableId = Ref(t.resources["RouteTable1"])
    ))

    t.add_resource(InternetGateway(
        "IGW",
        Tags = Tags(
            Name = Join(" ", ["BIG-IQ Internet Gateway:", Ref("AWS::StackName")])
        )
    ))

    t.add_resource(VPCGatewayAttachment(
        "IGWAttachment",
        VpcId = Ref(t.resources["VPC"]),
        InternetGatewayId = Ref(t.resources["IGW"])
    ))

    t.add_resource(Route(
        "Route1Default",
        DestinationCidrBlock = "0.0.0.0/0",
        RouteTableId = Ref(t.resources["RouteTable1"]),
        GatewayId = Ref(t.resources["IGW"])
    ))

    t.add_resource(Route(
        "Route2Default",
        DestinationCidrBlock = "0.0.0.0/0",
        RouteTableId = Ref(t.resources["RouteTable2"]),
        GatewayId = Ref(t.resources["IGW"])
    ))

    t.add_resource(NetworkAcl(
        "VPCAcl",
        VpcId = Ref(t.resources["VPC"])
    ))

    t.add_resource(SecurityGroup(
        "SecurityGroup",
        GroupName = Join(" ",["BIG-IQ SG:", Ref("AWS::StackName")]),
        GroupDescription = "vpc-sg",
        VpcId = Ref(t.resources["VPC"]),
        SecurityGroupIngress = [
            SecurityGroupRule(
                IpProtocol = "tcp",
                FromPort = "443",
                ToPort = "443",
                CidrIp = "0.0.0.0/0"
            ),
            SecurityGroupRule(
                IpProtocol = "tcp",
                FromPort = "80",
                ToPort = "80",
                CidrIp = "0.0.0.0/0"
            ),
            SecurityGroupRule(
                IpProtocol = "tcp",
                FromPort = "22",
                ToPort = "22",
                CidrIp = "0.0.0.0/0"
            ),
            SecurityGroupRule(
                IpProtocol = "tcp", # TODO Determine actual ports which should be open
                FromPort = "1",
                ToPort = "65356",
                CidrIp = Ref(t.parameters["vpcCidrBlock"])
            )
        ]
    ))

# Define the BIQ ec2 instances, there is a centralized management and data collection device
def define_ec2_instances (t, args):
    t.add_resource(EIP(
        "CmElasticIp",
        Domain = "vpc"
    ))

    t.add_resource(EIP(
        "DcdElasticIp",
        Domain = "vpc"
    ))

    t.add_resource(NetworkInterface(
        "BigIqCmEth0",
        Description = "BIG-IQ CM Instance Management IP",
        GroupSet = [ Ref(t.resources["SecurityGroup"]) ],
        SubnetId = Ref("Subnet1")
    ))

    t.add_resource(NetworkInterface(
        "BigIqDcdEth0",
        Description = "BIG-IQ DCD Instance Management IP",
        GroupSet = [ Ref(t.resources["SecurityGroup"]) ],
        SubnetId = Ref("Subnet1")
    ))

    bd_mappings = [
            BlockDeviceMapping(
                DeviceName = "/dev/xvda",
                Ebs = EBSBlockDevice(
                    DeleteOnTermination = True,
                    VolumeType = "gp2"
                )
            )
        ]

    t.add_resource(Instance(
        "BigIqCm",
        # Kick off cfn-init b/c BIG-IP doesn't run this automatically
        UserData=Base64(Join("", [
                "#!/bin/bash\n",
                "/opt/aws/apitools/cfn-init-1.4-0.amzn1/bin/cfn-init -v -s ",
                Ref("AWS::StackId"), " -r ",
                "BigIqCm",
                " --region ", Ref("AWS::Region"),
                "\n"
            ]
        )),
        Metadata = define_instance_metadata(t, args),
        ImageId = FindInMap("AmiRegionMap", Ref("AWS::Region"), "bigiq"),
        InstanceType =  Ref(t.parameters["instanceType"]),
        KeyName = Ref(t.parameters["sshKey"]),
        NetworkInterfaces =  [
            NetworkInterfaceProperty(
                DeviceIndex =  "0",
                NetworkInterfaceId =  Ref(t.resources["BigIqCmEth0"])
            ),
            NetworkInterfaceProperty(
                DeleteOnTermination =  True,
                Description =  "BIG-IQ CM Instance Management IP",
                DeviceIndex =  "1",
                GroupSet =  [ Ref(t.resources["SecurityGroup"]) ],
                SubnetId = Ref(t.resources["Subnet1"])
            )
        ],
        Tags = Tags(
            Name = Join(" ", [
                        "Big-IQ CM:",
                        Ref("AWS::StackName")
                    ])
        ),
        BlockDeviceMappings = bd_mappings
    ))

    t.add_resource(Instance(
        "BigIqDcd",
        # Kick off cfn-init b/c BIG-IP doesn't run this automatically
        UserData=Base64(Join("", [
                "#!/bin/bash\n",
                "/opt/aws/apitools/cfn-init-1.4-0.amzn1/bin/cfn-init -v -s ",
                Ref("AWS::StackId"), " -r ",
                "BigIqDcd",
                " --region ", Ref("AWS::Region"),
                "\n"
            ]
        )),
        Metadata = define_instance_metadata(t, args, is_cm_instance=False),
        ImageId = FindInMap("AmiRegionMap", Ref("AWS::Region"), "bigiq"),
        InstanceType =  Ref(t.parameters["instanceType"]),
        KeyName = Ref(t.parameters["sshKey"]),
        NetworkInterfaces =  [
            NetworkInterfaceProperty(
                DeviceIndex =  "0",
                NetworkInterfaceId =  Ref(t.resources["BigIqDcdEth0"])
            ),
            NetworkInterfaceProperty(
                DeleteOnTermination =  True,
                Description =  "BIG-IQ DCD Instance Management IP",
                DeviceIndex =  "1",
                GroupSet =  [ Ref(t.resources["SecurityGroup"]) ],
                SubnetId = Ref(t.resources["Subnet1"])
            )
        ],
        Tags = Tags(
            Name = Join(" ", [
                        "Big-IQ DCD:",
                        Ref("AWS::StackName")
                    ])
        ),
        BlockDeviceMappings = bd_mappings
    ))

    t.add_resource(EIPAssociation(
        "CmEipAssociation",
        AllocationId = GetAtt("CmElasticIp", "AllocationId"),
        NetworkInterfaceId = Ref("BigIqCmEth0")
    ))

    t.add_resource(EIPAssociation(
        "DcdEipAssociation",
        AllocationId = GetAtt("DcdElasticIp", "AllocationId"),
        NetworkInterfaceId = Ref("BigIqDcdEth0")
    ))


# Define all the resources for this stack
def define_resources (t, args):
    define_networking(t)
    define_ec2_instances(t, args)

# Define the stack outputs
def define_outputs (t):
    t.add_output(Output("BigIqCmExternalInterfacePrivateIp",
        Description = "Internally routable IP of the public interface on BIG-IQ",
        Value = GetAtt(
                    "BigIqCmEth0",
                    "PrimaryPrivateIpAddress"
                )
    ))
    t.add_output(Output("BigIqCmInstanceId",
        Description = "Instance Id of BIG-IQ in Amazon",
        Value = Ref(t.resources["BigIqCm"])
    ))
    t.add_output(Output("BigIqCmEipAddress",
        Description = "IP address of the management port on BIG-IQ",
        Value = Ref(t.resources["CmElasticIp"])
    ))
    t.add_output(Output("BigIqCmManagementInterface",
        Description = "Management interface ID on BIG-IQ",
        Value = Ref(t.resources["BigIqCmEth0"])
    ))
    t.add_output(Output("BigIqCmUrl",
        Description = "BIG-IQ CM Management GUI",
        Value = Join("", ["https://", GetAtt("BigIqCm", "PublicIp")])
    ))
    t.add_output(Output("availabilityZone1",
        Description = "Availability Zone",
        Value = GetAtt("BigIqCm", "AvailabilityZone")
    ))


# Build the template in logical order (hopefully) by just the top level tags
def main ():
    args = parse_args()
    t = troposphere.Template()
    define_mappings(t)
    define_metadata(t)
    define_parameters(t)
    define_resources(t, args)
    define_outputs(t)

    print(t.to_json())

if __name__ == '__main__':
    main()
