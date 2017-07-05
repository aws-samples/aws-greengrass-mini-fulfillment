## The Greengrass mini-fulfillment center example 

At re:Invent 2016 AWS Greengrass was introduced to the world. This miniature 
fulfillment center demonstration was used to display what could be done with 
Greengrass when announced. It has since been upgraded to use the publicly available 
version of [Greengrass](https://aws.amazon.com/greengrass/).
 
A [video](https://youtu.be/XQQjX8GTEko?t=27m27s) was taken of the completed and 
operational Greengrass-based miniature fulfillment center, a.k.a. "dual robot arm demo" 
in action at re:Invent. Since re:Invent this demo and example has continued to 
evolve and it has been the seed for [other demos](https://youtu.be/dpatdO2uPCA). 

The artifacts, example code, and instructions to construct this demo are now 
available in this repo. We look forward to seeing what you'll do with it.

#### Directory Structure
```
aws-greengrass-mini-fulfillment/
  +- docs/
  |  +- BOM.md       -- the bill of materials necessary for construction
  |  +- CONSTR.md    -- instructions for physical construction (TODO)
  |  +- INSTALL.md   -- instructions for software installation
  |  +- OPERATE.md   -- instructions for operation of the demo
  |  +- TIDBITS.md   -- tiny pieces of setup information that might be helpful
  |  +- TROUBLE.md   -- troubleshooting of install and operation
  |
  +- groups/
  |  +- inv_arm/     -- the directory of the `inv_arm` Greengrass group
  |  |  +- certs/    -- the group AWS IoT and local certs to be copied to Core
  |  |  +- ggd/      -- the Greengrass Devices that will be run on the Host
  |  |     +- certs/ -- the client certs used by GG devices
  |  |     +- servo/ -- the servo communications libraries 
  |  | 
  |  +- lambda/      -- the Lambda functions used in the Greengrass groups
  |  |
  |  +- master/      -- the directory of the `master` Greengrass group 
  |  |  +- certs/    -- the group AWS IoT and local certs to be copied to Core
  |  |  +- ggd/      -- the Greengrass Devices that will be run on the Host
  |  |     +- certs/ -- the client certs used by GG devices
  |  |     +- flask/ -- where the web GG device gets files to serve
  |  |     +- servo/ -- the servo communications libraries 
  |  |
  |  +- sort_arm/    -- the directory of the `sort_arm` Greengrass group
  |     +- certs/    -- the group AWS IoT and local certs to be copied to Core
  |     +- ggd/      -- the Greengrass Devices that will be run on the Host
  |        +- certs/ -- the client certs used by GG devices
  |        +- servo/ -- the servo communications libraries 
  |
  +- models/         -- the models used to 3D print components of this demo
  + LICENSE
  + README.md -- this file
  + requirements.txt
```

After following the [installation instructions](docs/INSTALL.md), each directory 
contains all the files necessary to support one of the three Demo groups' hosts. 
There are three Greengrass Groups named: 

| Group | Host Name | Description |
| :---: | :---: | :--- |
| `inv_arm` | `inv_arm-pi` | contains the Inventory Arm devices and the Inventory Arm Core |
| `master` | `master-pi` | contains both the Conveyor Belt devices and the Master Core |
| `sort_arm` | `sort_arm-pi` | contains the Sorting Arm devices and the Sort Arm Core |

The demo behavior is broken into the concept of a series of simple control stages 
organized by Group. Those stages are:

| Group | Control Stages |
| :--- | :--- |
| **Inventory Arm** | `... > Home > Finding > Pickup > Shipping > Home > ...` |
| **Master** | `..conveyor direction..` |
| **Sorting Arm** | `... > Home > Finding > Pickup > Sorting > Home > ...` |

As shown in the video above, even with these simple stages the interaction between 
the three Groups displays complex, cohesive, and coordinated behaviors.

This is possible because the whole system is modeled as a collection of micro-services. 
Those micro-services then leverage high-speed local messaging to enable communication 
within and between groups, as well as transactional state control using local device 
shadows. 

The high-level, local architecture of the demo is:
![mini-fulfillment demo architecture](docs/img/demo-architecture.png)

#### Master/Conveyor Host
There are six processes on this host:
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

There is a web visualization on this host. If one browses to: `<master_ip>:5000` a 
visualization that reads data from the Master Core can be seen. 

#### Inventory Arm Host
There are three processes on this host:
- the Inventory Arm Greengrass Core
- the `heartbeat` Greengrass Device (GGD) process
- the `arm` GGD process

Within the Inventory Arm Core, this is the Lambda function:
- `ArmErrorDetector` -- this function monitors local telemetry and detects any error states

#### Sorting Arm Host
There are three processes on this host:
- the Sorting Arm Greengrass Core
- the `heartbeat` Greengrass Device (GGD) process
- the `arm` GGD process

Within the Sort Arm Core, this is the Lambda function:
- `ArmErrorDetector` -- this function monitors local telemetry and detects any error states


#### Noteworthy Files
There are some noteworthy files in the repository that centralize a fair amount 
of work around the instantiation of this demonstration.
- `groups/group_setup.py` – performs all provisioning of each host's Greengrass Group. 
This file has three commands that are useful when instantiating this demo and that  
demonstrate the use of the Greengrass REST APIs.
    - `create <host_type> <config_file>` – creates a Greengrass Group for a given 
    host type and configuration file. Also stores all of the provisioning 
    artifacts (i.e. `GroupID`, `CoreDefinitionId`, etc.) in the local configuration file.
    - `deploy <host_type> <config_file>` – deploys a previously provisioned 
    Greengrass Group
    - `clean_all <config_file>` – cleans up the entirety of an **un-deployed** 
    Greengrass Group and the locally stored provisioning artifacts.
- `groups/cert_setup.py` – creates a Certificate Authority (CA) and server certificate 
for use locally on each host. These protect communication between the Greengrass 
Core and Greengrass Devices.
- `groups/servo_setup.py` – prepares the servo manufacturer's communication library 
for use on a Raspberry Pi with the Raspbian OS.

## DIY
If you'd like to build a copy of this demo yourself you'll want to read both 
the [installation instructions](docs/INSTALL.md) and the 
[construction instructions](docs/CONSTR.md).

## Special Thanks
[Brett Francis](https://github.com/brettf) and [Todd Varland](https://github.com/toddvarland) would like to thank the following. Without their 
help and existence we simply would not have made this demo.

> **The Francis Family, The Varland Family, [ROBOTIS](https://github.com/ROBOTIS-GIT/DynamixelSDK), [Servode](https://github.com/brettf/servode), Pretty Lights, 
 Sigur Ros, Flume - Insanity, Amazon.com, HBO Silicon Valley, The [Greengrass](https://aws.amazon.com/greengrass/) Developers**
