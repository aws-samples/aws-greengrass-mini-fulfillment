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
If you're getting errors when executing:
```
$ python arm_setup.py create <config_file>
...or...
$ python master_setup.py create <config_file>
```
check that the `<config_file> aka. cfg.json` file being used for each host is in 
the original state. The original state will have empty values for: 
`group_arn`, `group_id`, `group_version`, `lambda_list_arn`, `membership_id`, and `membership_list_arn` 

If any of those values are not empty, the `create` function has been run previously. 
  
If you still want to execute the `create` function, prior to executing `create` remove the Group containing the particular host's Greengrass Core. To do this, 
browse to the Greengrass console and delete the Group.

`-=-=-=-=-`
