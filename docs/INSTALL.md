
# Installation Instructions
1. Install OS (Jessie-Lite Sept) on three hosts.
    - this demo has been built using Raspberry Pi 3 computers
1. Configure the three hosts to be on the same network and note each host's IP  
1. Execute the following steps from the development machine that contains the `~/mini-fulfillment` repository:
    1. Create the three Greengrass Core **things** and **certificates** in AWS IoT. 
       _Per host_... 
        1. Download and name the certificate and key file pair as follows:
      
            | Filename | Description |
            | :--- | :--- |
            | `cloud.pem.crt` | the GG Core's AWS IoT client certificate - **unique per host** |
            | `cloud.pem.key` | the GG Core's AWS IoT client private key - **unique per host** |
    
        1. Place each pair of files in these directories, respectively.
            - `~/mini-fulfillment/groups/<host_type>/config/certs`
     
        1. Place the `thing_arn`, `cert_arn`, and `thing_name` values for each GG Core 
        in `~/mini-fulfillment/groups/<host_type>/config/cfg.json` 
            ```python
            { 
              "core": {
                "cert_arn": "arn:aws:iot:us-west-2:<account_id>:cert/EXAMPLEEXAMPLEa95f4e32EXAMPLEa888e13EXAMPLEac56337EXAMPLEeed338a",
                "thing_arn": "arn:aws:iot:us-west-2:<account_id>:thing/<device_thing_name>",
                "thing_name": "<device_thing_name>"
            }, ...
            ```
            > The specific **thing** names are not important, but to remain consistent with 
            the host names used in these instructions, one might use: 
            `master-pi-ggc`, `sort_arm-pi-ggc`, and `inv_arm-pi-ggc`
    
    1. Create the Greengrass Device **things** and **certificates** in AWS IoT named 
       and located as follows:
        - `~/mini-fulfillment/groups/master/ggd/certs`
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
        - `~/mini-fulfillment/groups/sort_arm/ggd/certs`
          ```
          GGD_arm.certificate.pem.crt
          GGD_arm.private.key
          GGD_arm.public.key
          GGD_heartbeat.certificate.pem.crt
          GGD_heartbeat.private.key
          GGD_heartbeat.public.key
          ```
        - `~/mini-fulfillment/groups/inv_arm/ggd/certs`
          ```
          GGD_arm.certificate.pem.crt
          GGD_arm.private.key
          GGD_arm.public.key
          GGD_heartbeat.certificate.pem.crt
          GGD_heartbeat.private.key
          GGD_heartbeat.public.key
          ```
    1. For each host, update the placeholder values in each
       `~/mini-fulfillment/groups/<host_type>/ggd/config.py` file with the host 
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
    1. `cd ~/mini-fulfillment/groups/lambda`
    1. `chmod 755 refresh_lambdas.sh`
    1. `./refresh_lambdas.sh`
    1. `cd ~/mini-fullfillment/groups`
    1. Create a Group Private CA and Certificate for each Greengrass Core by 
       executing the following commands:
        ```bash
        $ python cert_setup.py create sort_arm <sort_arm_host_ip_address>
        $ python cert_setup.py create inv_arm <inv_arm_host_ip_address>
        $ python cert_setup.py create master <master_host_ip_address>
        ```
        ..and send them to their destinations with this commands.
        ```bash
        $ ./move_certs.sh
        ```
    1. Download the servo software used by the Greengrass Devices
        ```bash
        $ ./servo_setup.py
        ```
    1. Instantiate the fully-formed Greengrass Groups with the following commands:
        ```bash
        $ ./group_setup.py create arm sort_arm/cfg.json --group_name sort_arm
        $ ./group_setup.py create arm inv_arm/cfg.json --group_name inv_arm
        $ ./group_setup.py create master master/cfg.json --group_name master
        $ ./group_setup.py deploy arm sort_arm/cfg.json
        $ ./group_setup.py deploy arm inv_arm/cfg.json
        $ ./group_setup.py deploy master master/cfg.json
        ```

1. Follow [these instructions](#tbd_link) to install (but not start) Greengrass on each host
1. On each host make a `~/mini-fulfillment` directory
1. Copy the directories from the `gg-mini-fulfillment` repository to each host. Specifically,
    - `mini-fulfillment/groups/sort_arm` to `sort_arm-pi$ ~/mini-fulfillment/groups/sort_arm`
    - `mini-fulfillment/groups/inv_arm` to `inv_arm-pi$ ~/mini-fulfillment/groups/inv_arm`
        - ..and..
    - `mini-fulfillment/groups/master` to `master-pi$ ~/mini-fulfillment/groups/master`
        - ...respectively
1. On each host
    1. `cd ~/mini-fulfillment/<host_type>/`
    1. `chmod 755 all_certs.sh`
    1. `chmod 755 servo_build.sh`
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
