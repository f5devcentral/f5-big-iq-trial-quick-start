BIG-IQ Centralized Management Trial Quick Start - Azure
=======================================================

**Note:** This template uses BIG-IQ 7.0.0

Instructions for Azure
----------------------

To deploy this ARM template in Azure cloud, complete the following steps.

1. To get a BIG-IQ trial license, go to [F5 Cloud Edition Trial](https://f5.com/products/trials/product-trials).

   Select **BIG-IP Cloud Edition - Advanced Web Application Firewall**

2. Enable programmatic deployment for these F5 products:

   * F5 BIG-IQ Virtual Edition - (BYOL) or F5 BIG-IQ Centralized Manager (BYOL): [Navigate to Home > Marketplace > F5 BIG-IQ BYOL > Configure Programmatic Deployment](https://portal.azure.com/#blade/Microsoft_Azure_Marketplace/GalleryFeaturedMenuItemBlade/selectedMenuItemId/home/searchQuery/f5-big-iq/resetMenuId/)

4. Launch the *trial stack* template by right-clicking this button and choosing **Open link in new window**:

   <a href="https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Ff5devcentral%2Ff5-big-iq-trial-quick-start%2F7.0.0%2Fazure%2Fexperimental%2Fazuredeploy.json" target="_blank"><img src="http://azuredeploy.net/deploybutton.png"/></a> (new VNET)
   
   <a href="https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Ff5devcentral%2Ff5-big-iq-trial-quick-start%2F7.0.0%2Fazure%2Fexperimental%2Fazuredeploy-with-exisiting-vnet.json" target="_blank"><img src="http://azuredeploy.net/deploybutton.png"/></a> (existing VNET)
   
5. In the ARM Template, populate this information:

   * Resource group (select existing or create new)
   * Admin user name (default value is **azureuser**)
   * Authentication type (password or ssh key string)
   * Password / sshPublicKey for the BIG-IQ Data Collection Device (DCD) and Centralized Management (CM) instances (you will connect to the instances by using these credentials)
   * BIG-IQ password (management console's password)
   * License keys for CM and DCD
   * BIG-IQ Master Key Passphrase
   * Location (the default is the resource group's location; change if you want to deploy the resources in another location)

6. Accept the terms and conditions and launch the cloud deployment. 

   *Expected time: ~30 min*

7. Open BIG-IQ CM in a web browser by using the public IP address with https, for example: ``https://<public_ip>``

   * Use the username `admin`.
   * Click the **Devices** tab > **BIG-IP DEVICES**. Click on **Add Device(s)**.

8. Start managing BIG-IP devices from BIG-IQ, go to the [BIG-IQ Knowledge Center](https://techdocs.f5.com/en-us/bigiq-7-0-0/managing-big-ip-devices-from-big-iq/device-discovery-and-basic-management.html).

    * Manage your existing BIG-IP(s) on premise (need VPN or Azure Direct Connect) or in the cloud.
    * Don't have BIG-IP yet? stand one up in Azure and use one of the [F5 template](https://github.com/F5Networks/f5-azure-arm-templates)

For more information, go to [the BIG-IQ Centralized Management Knowledge Center](https://support.f5.com/csp/knowledge-center/software/BIG-IQ?module=BIG-IQ%20Centralized%20Management&version=7.0.0).

Security instructions
---------------------

1. F5 strongly recommends that you configure autoshutdown / whitelist the public IP addresses in the network security group you use to access the SSH port of the Azure instances. (This template deploys a network security group with ports 22, 80, and 443 open to the public.)

2. Avoid enabling the `root` account on publicly exposed Azure instances.

Tear down instructions
----------------------

If you want to preserve other resouces in the group, delete only the resources that were created. You can find these resources under **Resource Group** > **Deployments**. Otherwise, you can delete the entire resource group.

Troubleshooting
---------------

1. In the BIG-IQ UI, check the BIG-IQ license on Console Node and Data Collection Device (**System** > **THIS DEVICE** > **Licensing**).
2. In the BIG-IQ CLI, check following logs: /var/log/setup.log, /var/log/restjavad.0.log.
3. In the Azure Marketplace, ensure that programmatic deployment is enabled for F5 products.
4. If you encounter a **MarketPurchaseEligibility** error while deploying the template, check the availability of BIG-IQ.

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
