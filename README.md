## The Greengrass mini-fulfillment center demo 

At re:Invent 2016 AWS Greengrass was introduced to the world. This miniature 
fulfillment center demonstration was used to display what could be done with 
Greengrass when announced. It has since been upgraded to use the publicly available 
version of Greengrass.
 
A [video](https://youtu.be/XQQjX8GTEko?t=27m27s) was taken of the completed and 
operational Greengrass-based miniature fulfillment center demo in action at re:Invent.

All the artifacts, code, and instructions to make this demo are now 
available in this repo. We look forward to seeing what you'll do with it.

### Directory Structure
```
aws-greengrass-mini-fulfillment/
  +- docs/
  |  +- BOM.md       -- the bill of materials necessary for construction
  |  +- CONSTR.md    -- instructions for physical construction
  |  +- INSTALL.md   -- instructions for software installation
  |  +- OPERATE.md   -- instructions for operation of the demo
  |  +- TIDBITS.md   -- tiny pieces of setup information that might be helpful
  |  +- TROUBLE.md   -- troubleshooting of install and operation
  |
  +- groups/
  |  +- lambda/      -- the Lambda functions to be used in the GGCores
  |  +- master/      -- the directory of the `master` Greengrass group 
  |  |  +- certs/    -- the group AWS IoT and local certs to be copied to Core
  |  |  +- ggd/      -- the Greengrass Devices that will be run on the Host
  |  |     +- certs/ -- the client certs used by GG devices
  |  |     +- flask/ -- where the web GG device gets files to serve
  |  |     +- servode/ -- the servo communications libraries 
  |  |
  |  +- sort_arm/    -- the directory of the `inv_arm` Greengrass group
  |  |  +- certs/    -- the group AWS IoT and local certs to be copied to Core
  |  |  +- ggd/      -- the Greengrass Devices that will be run on the Host
  |  |     +- certs/ -- the client certs used by GG devices
  |  |     +- servode/ -- the servo communications libraries 
  |  |
  |  +- inv_arm/     -- the directory of the `sort_arm` Greengrass group
  |  |  +- certs/    -- the group AWS IoT and local certs to be copied to Core
  |  |  +- ggd/      -- the Greengrass Devices that will be run on the Host
  |  |     +- certs/ -- the client certs used by GG devices
  |  |     +- servode/ -- the servo communications libraries 
  |
  +- models/         -- the 3d printing models used to make this demo
  + LICENSE
  + README.md -- this file
  + requirements.txt
  + TIDBITS.md
```

After following the [installation instructions](docs/INSTALL.md), each directory 
contains all the files necessary to support one of the three Demo groups' hosts. 
There are three Greengrass Groups named: 

| Group | Host Name | Description |
| :---: | :---: | :--- |
| `master` | `master-pi` | contains both the Conveyor Belt devices and the Master Core |
| `sort_arm` | `sort_arm-pi` | contains the Sorting Arm devices and the Sort Arm Core |
| `inv_arm` | `inv_arm-pi` | contains the Inventory Arm devices and the Inventory Arm Core |

The demo behavior is broken into the concept of a series of simple control stages 
organized by Group. Those stages are:

| Group | Control Stages |
| :--- | :--- |
| **Sorting** | `... > Home > Finding > Pickup > Sorting > Home > ...` |
| **Master** | `..conveyor direction..` |
| **Inventory** | `... > Home > Finding > Pickup > Shipping > Home > ...` |

As shown in the video above, even with these simple stages the interaction between 
the three Groups displays complex, cohesive, and coordinated behaviors.

This is possible because the whole system is modeled as a collection of micro-services. 
Those micro-services then leverage high-speed local messaging to enable communication 
within and between groups, as well as transactional state control using local device 
shadows. 

The high-level, local architecture of the demo is:
![mini-fulfillment demo architecture](docs/img/demo-architecture.png)

### Master/Conveyor Host
There are five processes on this host:
- the Master Greengrass Core
- the `heartbeat` Greengrass Device (GGD) process
- the `bridge` GGD process
- the `belt` GGD process -- manages the conveyor belt servo
- the `button` GGD process -- manages the button box's red, green, and white control buttons
- the `web` GGD process

Within the Master Core, these are the Lambda functions:
- `MasterErrorDetector` -- this function monitors local telemetry and detects any error states
- `MasterBrain` -- this function monitors the fabric of telemetry coming from the 
  bridges and the local GGDs. This function will decide what to do with respect 
  to current telemetry and errors in the system

There is a web visualization on this host. If one browses to: `<master_ip>:8000` a 
visualization that reads data from the Master Core can be seen. 

### Sorting Arm Host
There are three processes on this host:
- the Sorting Arm Greengrass Core
- the `heartbeat` Greengrass Device (GGD) process
- the `arm` GGD process

Within the Sort Arm Core, this is the Lambda function:
- `ArmErrorDetector` -- this function monitors local telemetry and detects any error states

### Inventory Arm Host
There are three processes on this host:
- the Inventory Arm Greengrass Core
- the `heartbeat` Greengrass Device (GGD) process
- the `arm` GGD process

Within the Inventory Arm Core, this is the Lambda function:
- `ArmErrorDetector` -- this function monitors local telemetry and detects any error states

## DIY
If you'd like to build a copy of this demo yourself you'll want to read both 
the [installation instructions](docs/INSTALL.md) and the 
[construction instructions](docs/CONSTR.md).

## Special Thanks
[Brett Francis](https://github.com/brettf) and [Todd Varland](https://github.com/toddvarland) would like to thank the following. Without their 
help and existence we simply would not have made it.

    The Francis Family, The Varland Family, ROBOTIS, Pretty Lights, Sigur Ros, 
    Flume - Insanity, Amazon.com, HBO Silicon Valley, The Greengrass Developers
