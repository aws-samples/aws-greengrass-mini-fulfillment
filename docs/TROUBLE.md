## Troubleshooting
#### An arm does not start
- If `arm.py` does not start, simply exits, or shows this error:
```
 SE:[Errno 111] Connection refused
Traceback (most recent call last):
  File "./arm.py", line 324, in <module>
    initialize()
  File "./arm.py", line 76, in initialize
    raise EnvironmentError("connection to GG Core MQTT failed.")
EnvironmentError: connection to GG Core MQTT failed.
```
...please ensure you have executed `sudo /greengrass/greengrassd start`.

#### Has everything stopped?
To ensure nothing is running you can execute the following and expect 
the subsequent output.
```
$ screen -ls
No Sockets found in /var/run/screen/S-pi.
```

#### IP addresses change
If the IP addresses change for some reason:
1. Do a Lan Scan to find the three Raspberry Pi 3's
2. Take note of each host's new IP
3. Update the files on each host to reflect the new IP addresses. Specifically:
```
~/mini-fulfillment/master/ggd/config.py
~/mini-fulfillment/inv_arm/ggd/config.py
~/mini-fulfillment/sort_arm/ggd/config.py
```

#### Getting errors when Creating Cores
If you're getting errors when executing any of the `create` group commands:
```
$ ./group_setup.py create sort_arm <config_file>
...
```
check that the `<config_file>` aka. `cfg.json` file being used for each host is in 
the original state. The original state will have empty values for: 
`group_arn`, `group_id`, `group_version`, `lambda_list_arn`, `membership_id`, and `membership_list_arn` 

If any of those values are not empty, the `create` function has been run previously. 
  
If you still want to execute the `create` function, prior to executing `create` remove the Group containing the particular host's Greengrass Core. To do this, 
browse to the Greengrass console and delete the Group.

#### Getting errors when a Greengrass Core is launched
If you're getting the following error when executing `$ sudo /greengrass/ggc/core/greengrassd start`
```
Setting up greengrass daemon
Validating execution environment
Found cgroup subsystem: cpu
Found cgroup subsystem: cpuacct
Found cgroup subsystem: blkio
Found cgroup subsystem: memory
Found cgroup subsystem: devices
Found cgroup subsystem: freezer
Found cgroup subsystem: net_cls

Starting greengrass daemon
Greengrass daemon 20301 failed to start
thing name is unresolved, error: Certificate hash not found in cores list. ThingName is unresolved
```
Then the Greengrass Core was used previously with a different Thing and Certificate. Either re-install the 
Greengrass Core software from scratch, or edit the `/greengrass/ggc/deployment/group/group.json` back to an unused state, as follows:
```json
{
    "Version": "test group version",
    "Devices": [],
    "Cores": [],
    "GroupDefinitions": {
        "Logging": {
            "Content": [
                {
                    "Component": "GreengrassSystem",
                    "Level": "DEBUG",
                    "Type": "FileSystem",
                    "Space": 128
                }
            ]
        },
        "Lambdas": {
            "ref": null,
            "Content": []
        },
        "Subscriptions": {
            "ref": null,
            "Content": []
        },
        "ShadowSync": {
            "ref": null,
            "Content": []
        }
    },
    "Region": null
}

```  
`-=-=-=-=-`
