
# Installation Instructions
1. Install OS (Jessie-Lite Sept) on three hosts.
    - this demo has been built using Raspberry Pi 3 computers
1. Configure the three hosts to be on the same network and note each host's IP  
1. Back on your development machine, execute the following steps.
    1. Clone this git repo into directory `~/aws-greengrass-mini-fulfillment/`
    > **Note**: All subsequent instructions assume the local repository is in 
    `~/aws-greengrass-mini-fulfillment/` if you chose another directory, remember 
    to take that into account. 
    1. **Per host** [create](http://docs.aws.amazon.com/iot/latest/developerguide/thing-registry.html) 
    the three Greengrass Core things and attach 
    [certificates](http://docs.aws.amazon.com/iot/latest/developerguide/managing-device-certs.html) 
    in AWS IoT.  
        1. Download and name the certificate and key file pair as follows:
      
            | Filename | Description |
            | :--- | :--- |
            | `cloud.pem.crt` | the GG Core's AWS IoT client certificate - **unique cert per host** |
            | `cloud.pem.key` | the GG Core's AWS IoT client private key - **unique key per host** |
            | `cloud.public.pem.key` | the GG Core's AWS IoT client public key - **unique key per host, unused in this example** |
    
        1. Place each pair of files in these directories, respectively.
            - `~/aws-greengrass-mini-fulfillment/groups/<host_type>/config/certs`
     
        1. Place the `thing_arn`, `cert_arn`, and `thing_name` values for each host's 
        GG Core in `~/aws-greengrass-mini-fulfillment/groups/<host_type>/config/cfg.json` 
            ```python
            { 
              "core": {
                "cert_arn": "arn:aws:iot:us-west-2:<account_id>:cert/EXAMPLEEXAMPLEa95f4e32EXAMPLEa888e13EXAMPLEac56337EXAMPLEeed338a",
                "thing_arn": "arn:aws:iot:us-west-2:<account_id>:thing/<device_thing_name>",
                "thing_name": "<device_thing_name>"
            }, ...
            ```
            > The specific **thing** names are not important, but to remain consistent 
            with the host names used in these instructions, one might use: 
            `master-pi-ggc`, `sort_arm-pi-ggc`, and `inv_arm-pi-ggc`
    
    1. Create the Greengrass Device **things** and **certificates** in AWS IoT named 
       and located as follows:
        - `~/aws-greengrass-mini-fulfillment/groups/master/ggd/certs`
          ```
          GGD_belt.certificate.pem.crt
          GGD_belt.private.key
          GGD_belt.public.key
          GGD_bridge.certificate.pem.crt
          GGD_bridge.private.key
          GGD_bridge.public.key
          GGD_heartbeat.certificate.pem.crt
          GGD_heartbeat.private.key
          GGD_heartbeat.public.key
          GGD_web.certificate.pem.crt
          GGD_web.private.key
          GGD_web.public.key
          ```
        - `~/aws-greengrass-mini-fulfillment/groups/sort_arm/ggd/certs`
          ```
          GGD_arm.certificate.pem.crt
          GGD_arm.private.key
          GGD_arm.public.key
          GGD_heartbeat.certificate.pem.crt
          GGD_heartbeat.private.key
          GGD_heartbeat.public.key
          ```
        - `~/aws-greengrass-mini-fulfillment/groups/inv_arm/ggd/certs`
          ```
          GGD_arm.certificate.pem.crt
          GGD_arm.private.key
          GGD_arm.public.key
          GGD_heartbeat.certificate.pem.crt
          GGD_heartbeat.private.key
          GGD_heartbeat.public.key
          ```
    1. For each host, update the placeholder values in each
       `~/aws-greengrass-mini-fulfillment/groups/<host_type>/ggd/config.py` file with the host 
       IPs noted earlier. 
        - Example:
        ```python
          master_core_ip = "xx.xx.xx.xx"  # << placeholder
          master_core_port = 8883
          sort_arm_ip = "yy.yy.yy.yy"     # << placeholder
          sort_arm_port = 8883
          inv_arm_ip = "zz.zz.zz.zz"      # << placeholder
          inv_arm_port = 8883
        ```
    1. From the top of the repository at `~/aws-greengrass-mini-fulfillment/`:
        - Install a virtual environment: `virtualenv venv --python=python2.7`
        - Activate the virtual environment: `source venv/bin/activate`
        - Execute: `pip install -r requirements.txt`
    1. `cd ~/aws-greengrass-mini-fulfillment/groups/lambda`
    1. `chmod 755 create_lambdas.sh`
    1. `./create_lambdas.sh`
    1. `cd ~/aws-greengrass-mini-fulfillment/groups`
    1. Using the IP addresses you noted earlier, create a Group Private CA and 
       Certificate for each Greengrass Core by executing the following commands:
        ```bash
        $ python cert_setup.py create sort_arm <sort_arm_host_ip_address>
        $ python cert_setup.py create inv_arm <inv_arm_host_ip_address>
        $ python cert_setup.py create master <master_host_ip_address>
        ```
        ..and send them to their destinations with this command.
        ```bash
        $ ./move_certs.sh
        ```
    1. Download and prep the servo software used by the Greengrass Devices
        ```bash
        $ ./servo_setup.py
        ```
    1. Instantiate the fully-formed Greengrass Groups with the following commands:
        ```bash
        $ ./group_setup.py create sort_arm/cfg.json arm --group_name sort_arm
        $ ./group_setup.py create inv_arm/cfg.json arm --group_name inv_arm
        $ ./group_setup.py create master master/cfg.json master --group_name master
        $ ./group_setup.py deploy sort_arm/cfg.json arm
        $ ./group_setup.py deploy inv_arm/cfg.json arm
        $ ./group_setup.py deploy master/cfg.json master
        ```

1. Follow [these instructions](#tbd_link) to install (but not start) Greengrass on each host
1. On each host make a `~/aws-greengrass-mini-fulfillment` directory
1. Copy the directories from the `aws-greengrass-mini-fulfillment` repository to each host. Specifically,
    - `~/aws-greengrass-mini-fulfillment/groups/sort_arm` to `sort_arm-pi$ ~/mini-fulfillment/groups/sort_arm`
    - `~/aws-greengrass-mini-fulfillment/groups/inv_arm` to `inv_arm-pi$ ~/mini-fulfillment/groups/inv_arm`
        - ..and..
    - `~/aws-greengrass-mini-fulfillment/groups/master` to `master-pi$ ~/mini-fulfillment/groups/master`
        - ...respectively
1. On each host
    1. `cd ~/mini-fulfillment/groups/<host_type>/`
    1. `chmod 755 all_certs.sh run_ggd.sh servo_build.sh stop_ggd.sh`
    1. Make the Dynamixel SDK by executing `./servo_build.sh`
    1. Execute `all_certs.sh`. This will copy the host's certs into the 
       necessary GG Core location.
1. Using [these instructions](OPERATE.md) start the GG Cores and Devices in the following order:
    1. Start the `master` GG Core
    1. Start the `sort_arm` GG Core and the `sort_arm` GG Devices
    1. Start the `inv_arm` GG Core and the `inv_arm` GG Devices
    1. Start the `master` GG Devices
    
    :white_check_mark: at this point in time you should see the `master` host button box's white button light turn on.
1. Use the physical **`green`** and **` red`** buttons to **start** and **stop** the demo, respectively.
> **Note:** If you experience trouble, checkout the [troubleshooting](TROUBLE.md) doc

##### Instantiation of Greengrass Groups is now complete

`-=-=-=-=-`
