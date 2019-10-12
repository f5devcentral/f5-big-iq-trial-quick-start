BIG-IQ Centralized Management Trial Quick Start - AWS
=====================================================

**Note:** This template uses BIG-IQ 7.0.0

Instructions for AWS
--------------------

To deploy this CFT in AWS, complete the following steps.

**Note:** This template is not supported in the Paris region and in AWS GovCloud.

1. To get a BIG-IQ trial license, go to [F5 Cloud Edition Trial](https://f5.com/products/trials/product-trials).

   Select **BIG-IP Cloud Edition - Advanced Web Application Firewall**

2. Subscribe and accept the Terms and Conditions for these F5 products:

   * [F5 BIG-IQ Virtual Edition - (BYOL)](https://aws.amazon.com/marketplace/pp/B00KIZG6KA)

3. Launch the *trial stack* template by right-clicking this button and choosing **Open link in new window**:

   <a href="https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=F5-BIG-IQ-Trial&templateURL=https:%2F%2Fs3.amazonaws.com%2Fbig-iq-quickstart-cf-templates-aws%2F7.0.0%2Fbigiq-cm-dcd-pair.template" target="_blank"><img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png"/></a> (new VPC)

   <a href="https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=F5-BIG-IQ-Trial&templateURL=https:%2F%2Fs3.amazonaws.com%2Fbig-iq-quickstart-cf-templates-aws%2F7.0.0%2Fbigiq-cm-dcd-pair-existing-vpc.template" target="_blank"><img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png"/></a> (existing VPC)

4. In the CloudFormation Template (CFT), populate this information:

   * Stack name (must be fewer than 25 characters)
   * Subnet
   * If you did not do it previously, accept the BIG-IQ license terms by visiting the URLs specified,
   clicking **Continue to Subscribe**, and accepting terms
   * BIG-IQ Centralized Management (CM) License Key (from F5 trial **BIG-IQ Console Node**)
   * BIG-IQ Data Collection Device (DCD) License Key (from F5 trial **BIG-IQ Data Collection Device**)
   * BIG-IQ Master Key Passphrase
   * SSH Key (your AWS key pair name)

   *Expected time: ~5 min*

5. Open the [EC2 console](https://console.aws.amazon.com/ec2/v2/home) and wait until the BIG-IQ instances are fully deployed.

   * Instance State: running
   * Status Checks: 2/2 checks passed

   *Expected time: ~5 min*

6. Use admin user and your AWS SSH key to SSH into the BIG-IQ DCD instance, then execute the following commands:

   ```
   # bash
   # /config/cloud/setup-dcd.sh
   ```

   * When prompted, enter a password for BIG-IQ. You will use this same password again on the BIG-IQ CM instance. [Details on prohibited characters](https://support.f5.com/csp/article/K2873).
   * Let the scripts finish before moving to the next step.

   *Expected time: ~2 min*

7. Use admin user and your AWS SSH key to SSH into the BIG-IQ CM instance, then execute the following commands:

   ```
   # bash
   # /config/cloud/setup-cm.sh
   ```

   * The password must match the password you used on the BIG-IQ DCD instance in the previous step.
   * Let the scripts finish before moving to the next step.

   *Expected time: ~5 min*

8. Open BIG-IQ CM in a web browser by using the public IP address with https, for example: ``https://<public_ip>``

   * Use the username `admin`.
   * Click the **Devices** tab > **BIG-IP DEVICES**. Click on **Add Device(s)**.

9. Start managing BIG-IP devices from BIG-IQ, go to the [BIG-IQ Knowledge Center](https://techdocs.f5.com/en-us/bigiq-7-0-0/managing-big-ip-devices-from-big-iq/device-discovery-and-basic-management.html).

    * Manage your existing BIG-IP(s) on premise (need VPN or AWS Direct Connect) or in the cloud.
    * Don't have BIG-IP yet? stand one up in AWS and use one of the [F5 template](https://github.com/F5Networks/f5-aws-cloudformation)

For more information, go to [the BIG-IQ Centralized Management Knowledge Center](https://support.f5.com/csp/knowledge-center/software/BIG-IQ?module=BIG-IQ%20Centralized%20Management&version=7.0.0).


Security instructions
---------------------

1. F5 strongly recommends that you configure autoshutdown / whitelist the public IP addresses in the network security group you use to access the SSH port of the AWSinstances. (This template deploys a network security group with ports 22, 80, and 443 open to the public.)

2. Avoid enabling the `root` account on publicly exposed AWS instances.

Tear down instructions
----------------------

Open the [Cloud Formation Console](https://console.aws.amazon.com/cloudformation/) and delete the stack.

*Expected time: ~10 min*

Troubleshooting
---------------

1.	In the BIG-IQ UI, check the BIG-IQ license on the Console Node and Data Collection Device (**System** > **THIS DEVICE** > **Licensing**)..
2.	In the BIG-IQ CLI, check the following logs: /var/log/setup.log, /var/log/restjavad.0.log.
3.	In AWS Marketplace, ensure you have subscribed and accepted the terms for F5 products.
4.	In AWS CFT Console, check the CFT status, make sure it is COMPLETED.
5.	In AWS IAM Console, confirm the Access Key has the necessary permissions.

### Copyright

Copyright 2014-2020 F5 Networks Inc.

### License

#### Apache V2.0

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations
under the License.

#### Contributor License Agreement

Individuals or business entities who contribute to this project must have
completed and submitted the [F5 Contributor License Agreement](http://f5-openstack-docs.readthedocs.io/en/latest/cla_landing.html).
