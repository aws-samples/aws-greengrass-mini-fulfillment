
# Installation Instructions
1. Install OS (Jessie-Lite Sept) on three hosts.
    - this demo has been built using Raspberry Pi 3 computers
1. Configure the three hosts to be on the same network and note each host's IP  
1. On each host make a `~/mini-fulfillment` directory
1. Back on your development machine, execute the following steps.
    1. [Install](http://docs.aws.amazon.com/cli/latest/userguide/installing.html) 
    the AWS CLI and [configure](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html) 
    it with [Administrator](http://docs.aws.amazon.com/IAM/latest/UserGuide/getting-started_create-admin-group.html) 
    credentials.   
    1. Clone this git repo into a directory `~/aws-greengrass-mini-fulfillment/`
        - Example: `git clone https://github.com/awslabs/aws-greengrass-mini-fulfillment.git ~/aws-greengrass-mini-fulfillment`
        > **Note**: All subsequent instructions assume the developer's local copy of 
        this repository is in `~/aws-greengrass-mini-fulfillment/` if you chose 
        another directory, remember to take that into account throughout these 
        instructions. 
    1. From the top of the repository at `~/aws-greengrass-mini-fulfillment/`:
        - Install a virtual environment: `virtualenv venv --python=python2.7`
        - Activate the virtual environment: `source venv/bin/activate`
        - Execute: `pip install -r requirements.txt`
    1. [Create](http://docs.aws.amazon.com/iot/latest/developerguide/thing-registry.html) 
    the three Greengrass Core **things** and attach 
    [certificates](http://docs.aws.amazon.com/iot/latest/developerguide/managing-device-certs.html) 
    in AWS IoT. Specifically, to create the Greengrass Cores for this example:  
        ```bash
        $ cd ~/aws-greengrass-mini-fulfillment/groups
        $ ./group_setup.py create-core --thing-name sort_arm-core --config-file ./arm/sort_arm/cfg.json --cert-dir ./arm/sort_arm
        $ ./group_setup.py create-core --thing-name inv_arm-core --config-file ./arm/inv_arm/cfg.json --cert-dir ./arm/inv_arm
        $ ./group_setup.py create-core --thing-name master-core --config-file ./master/cfg.json --cert-dir ./master/certs
        ```
        > Note: You can see the details of each created Core recorded in the 
        `cfg.json` files used above in the `create-core` command. Example: 
        ```json
        {
          "core": {
            "cert_arn": "arn:aws:iot:us-west-2:EXAMPLE_ACCT:cert/EXAMPLE10bEXAMPLE34e3a3ac96f3903d040fcca1f7b6e83aba15d95a631622b",
            "cert_id": "EXAMPLE10bEXAMPLE34e3a3ac96f3903d040fcca1f7b6e83aba15d95a631622b",
            "thing_arn": "arn:aws:iot:us-west-2:EXAMPLE_ACCT:thing/sort_arm-core",
            "thing_name": "sort_arm-core"
          },...
        ``` 
    1. Download the `root-ca` file used by all three cores to communicate with 
    the AWS cloud. Then copy that `root-ca` to the proper directories:
        ```bash
        $ cd ~/aws-greengrass-mini-fulfillment/groups
        $ curl -o root-ca.pem https://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem
        $ echo arm/sort_arm arm/sort_arm/ggd_certs | xargs -n 1 cp root-ca.pem
        $ echo arm/inv_arm arm/inv_arm/ggd_certs | xargs -n 1 cp root-ca.pem
        $ echo master/certs master/ggd/certs | xargs -n 1 cp root-ca.pem
        $ rm root-ca.pem
        ```
    1. Create the Greengrass Device **things** and **certificates** in AWS IoT 
        as follows:
        ```bash
        $ ./group_setup.py create-devices --thing-names '[GGD_arm,GGD_heartbeat]' --config-file ./arm/sort_arm/cfg.json --cert-dir ./arm/sort_arm/ggd_certs
        $ ./group_setup.py create-devices --thing-names '[GGD_arm,GGD_heartbeat]' --config-file ./arm/inv_arm/cfg.json --cert-dir ./arm/inv_arm/ggd_certs
        $ ./group_setup.py create-devices --thing-names '[GGD_belt,GGD_bridge,GGD_heartbeat,GGD_web]' --config-file ./master/cfg.json --cert-dir ./master/ggd/certs
        ```
        > Note: You can see the details of each create Device recorded in the 
        `cfg.json` files used above in the `create-devices` command. Example:
        ```json
          ...
          "devices": {
            "GGD_arm": {
              "cert_arn": "arn:aws:iot:us-west-2:EXAMPLE_ACCT:cert/EXAMPLEba1EXAMPLE32b63db0d3a830b7874dcb791cc045ad9bc7c64a058c87e",
              "cert_id": "EXAMPLEba1EXAMPLE32b63db0d3a830b7874dcb791cc045ad9bc7c64a058c87e",
              "thing_arn": "arn:aws:iot:us-west-2:EXAMPLE_ACCT:thing/GGD_arm",
              "thing_name": "GGD_arm"
            },...
        ```
    1. Create the Greengrass Group's Lambda functions
        ```bash
        $ ./lambda_setup.py create lambda/MasterBrain/cfg_lambda.json
        $ ./lambda_setup.py create lambda/MasterErrorDetector/cfg_lambda.json
        $ ./lambda_setup.py create lambda/ArmErrorDetector/cfg_lambda.json
        ```
    1. Associate the Lambda functions with the proper Greengrass Groups
        ```bash
        $ ./group_setup.py associate-lambda ./arm/sort_arm/cfg.json ./lambda/ArmErrorDetector/cfg_lambda.json
        $ ./group_setup.py associate-lambda ./arm/inv_arm/cfg.json ./lambda/ArmErrorDetector/cfg_lambda.json
        $ ./group_setup.py associate-lambda ./master/cfg.json ./lambda/MasterBrain/cfg_lambda.json
        $ ./group_setup.py associate-lambda ./master/cfg.json ./lambda/MasterErrorDetector/cfg_lambda.json
        ```
    1. Download and prep the servo software used by the Greengrass Devices
        ```bash
        $ ./servo_setup.py
        ```
    1. Instantiate the fully-formed Greengrass Groups with the following commands:
        ```bash
        $ ./group_setup.py create arm ./arm/sort_arm/cfg.json --group_name sort_arm
        $ ./group_setup.py create arm ./arm/inv_arm/cfg.json --group_name inv_arm
        $ ./group_setup.py create master ./master/cfg.json --group_name master
        $ ./group_setup.py deploy ./sort_arm/cfg.json
        $ ./group_setup.py deploy ./inv_arm/cfg.json
        $ ./group_setup.py deploy ./master/cfg.json
        ```
1. Follow [these instructions](http://docs.aws.amazon.com/greengrass/latest/developerguide/what-is-gg.html) 
   to install (but not provision or start) Greengrass on each host.
1. Copy the directories from the developer local `aws-greengrass-mini-fulfillment` repository 
   to each of the three Raspberry Pi hosts. Specifically,
    - `~/aws-greengrass-mini-fulfillment/groups/arm` to `sort_arm-pi$ ~/mini-fulfillment/groups/arm`
    - `~/aws-greengrass-mini-fulfillment/groups/arm` to `inv_arm-pi$ ~/mini-fulfillment/groups/arm`
    - `~/aws-greengrass-mini-fulfillment/groups/master` to `master-pi$ ~/mini-fulfillment/groups/master`
1. On the `master` host
    1. `cd ~/mini-fulfillment/groups/master/`
    1. `pip install -r requirements.txt` - **Note** you might need to use `sudo`
        > **Note** it can take some time to install `numpy`
    1. `chmod 755 cp_certs.sh servo_build.sh start_master.sh stop_master.sh`
    1. Make the Dynamixel SDK by executing `./servo_build.sh`
    1. Execute `cp_certs.sh`. This will copy the host's certs into the 
       necessary GG Core location.
1. On the `sort_arm` host
    1. `cd ~/mini-fulfillment/groups/arm/`
    1. `pip install -r requirements.txt` - **Note** you might need to use `sudo`
    1. `chmod 755 cp_sort_arm_certs.sh servo_build.sh start_sort_arm.sh stop_arm.sh`
    1. Make the Dynamixel SDK by executing `./servo_build.sh`
    1. Execute `./cp_sort_arm_certs.sh`. This will copy the host's certs into the 
       necessary GG Core location.
1. On the `inv_arm` host
    1. `cd ~/mini-fulfillment/groups/arm/`
    1. `pip install -r requirements.txt` - **Note** you might need to use `sudo`
    1. `chmod 755 cp_inv_arm_certs.sh servo_build.sh start_inv_arm.sh stop_arm.sh`
    1. Make the Dynamixel SDK by executing `./servo_build.sh`
    1. Execute `./cp_inv_arm_certs.sh`. This will copy the host's certs into the 
       necessary GG Core location.
1. Using [the operation instructions](OPERATE.md) start the GG Cores and Devices in the following order:
    1. Start the `master` GG Core
    1. Start the `sort_arm` GG Core and the `sort_arm` GG Devices
    1. Start the `inv_arm` GG Core and the `inv_arm` GG Devices
    1. Start the `master` GG Devices
    
    :white_check_mark: at this point in time you should see the `master` host button box's white button light turn on.
1. Use the physical **`green`** and **` red`** buttons to **start** and **stop** the demo, respectively.
> **Note:** If you experience trouble, checkout the [troubleshooting](TROUBLE.md) doc

##### Instantiation of Greengrass Groups is now complete

`-=-=-=-=-`
