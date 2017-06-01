## Startup Master Host `master-pi`
**Start GG Core** -- in `master-pi` Terminal 01 execute:
1. `cd /greengrass`
1. `sudo ./greengrassd start`
You should now see `daemon` in the process list via `top`

**Start GG Devices** -- in `master-pi` Terminal 02 execute:

1. `cd ~/mini-fulfillment/groups/`
1. `chmod 755 master/run_ggd.sh master/stop_ggd.sh`
1. `./master/run_ggd.sh`
**Note:** you should see the white button light turn on

After starting the conveyor devices, to determine success you should see four 
entries in the list of processes, similar to the following:
```
master-pi$ screen -ls
There are screens on:
	8281.web	(11/19/2016 05:53:42 PM)	(Detached)
	8278.heartbeat	(11/19/2016 05:53:42 PM)	(Detached)
	8275.button	(11/19/2016 05:53:42 PM)	(Detached)
	8269.belt	(11/19/2016 05:53:42 PM)	(Detached)
4 Sockets in /var/run/screen/S-pi.
```
To view the output of any of the Greengrass Devices attach to the 
`screen` by using the command `screen -r <pid>`. Example that 
re-attaches to the `web` device process in the above list:
```
screen -r 8281
```
Then remember to detach from the screen using `Ctrl-A, D` not `Ctrl-C`.

If `button` is successful the physical button lights will turn on.
If `belt` is successful you'll see `[btt.__init__] frequency:<value>` in the output.

**Stop GG Devices** -- in a `master-pi` Terminal execute:
1. `cd ~/mini-fulfillment/groups/master`
1. `./stop_ggd.sh`

## Startup Arm Hosts `sort_arm-pi` and `inv_arm-pi`
**Start GG Core** -- in Terminal 01 execute:
1. `cd /greengrass`
1. `sudo ./greengrassd start`
You should now see `daemon` in the process list via `top`

**Start GG Devices** -- in Terminal 02 execute:

1. `cd ~/mini-fulfillment/groups/`
1. `chmod 755 <inv_arm|sort_arm>/run_ggd.sh`
1. `chmod 755 <inv_arm|sort_arm>/stop_ggd.sh`
1. `./<inv_arm|sort_arm>/run_ggd.sh`
1. repeat for the other arm

After starting each arm, to determine success you should see two 
entries in the list of processes, similar to the following:
```
$ screen -ls
There are screens on:
	4961.heartbeat	(19/11/16 18:10:51)	(Detached)
	4958.arm	(19/11/16 18:10:51)	(Detached)
2 Sockets in /var/run/screen/S-pi.
```
To view the output of any of the Greengrass Devices attach to the 
`screen` by using the command `screen -r <pid>`. For example, the following command 
attaches to the `web` device process in the above list:
```
screen -r 8281
```
Then remember to detach from the screen using `Ctrl-A, D`, **not** `Ctrl-C`. 

:warning: – Using `Ctrl-C` will exit the process being viewed.

**Stop GG Devices** -- in a Terminal execute:
1. `cd ~/mini-fulfillment/groups/<inv_arm|sort_arm>/`
1. `./stop_ggd.sh`

## To Start the Demo
Push the **`green`** button to start both robot arms and the conveyor.

## To Stop the Demo
Push the **`red`** button to stop. 

The **`white`** button is a manual override that reverses the direction of the conveyor.
