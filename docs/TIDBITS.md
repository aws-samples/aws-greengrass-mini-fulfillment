### GG Tidbits

#### Enable GPIO on Raspberry Pi
Add the following to `/boot/config.txt` in order to enable GPIO on Jessie. 
```
# Enabled GPIO  
enable_uart=1
```
..and this:
```
max_usb_current=1
```
...to provide MAX power to the USB ports

#### Provision USB on Raspberry Pi for optimal use by USB2Dynamixel
Add this to the `/boot/cmdline.txt`
```
dwc_otg.speed=1
```
To limit USB speed to full speed 12Mbps (USB 1.1).

#### Install `screen` on each Raspberry Pi
Execute the command: `sudo apt-get install screen`
Then to run screen with a bash shell: `screen bash`

### Install Dependencies
```bash
sudo apt-get install python-devel
```
..and then using `pip` install:
```bash
sudo pip install -r requirements.txt
```

### Physical Setup
The conveyor should be 14" away from the arm base. 

### Checking Servode comms on a Host
```bash
cd ~/mini-fulfillment/groups/arm/ggd
python -m servo.servode ping [servo_id]
```