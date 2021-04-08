# Servode
An ode to Python code that uses Servos ([ROBOTIS](https://github.com/ROBOTIS-GIT/DynamixelSDK) first)

## Usage
### As a library
When using Servode as a library use a single ServoProtocol instance per 
connected servo bus. One ServoProtocol can be shared across threads.

To connect a Servo and read a register (example: `present_position`):
```python
with ServoProtocol() as sp:
    servo = Servo(sp=sp, servo_id=1)
    # to read a value
    value = servo['present_position']
```

To connect a Servo and write a register (example: `goal_position`):
```python
with ServoProtocol() as sp:
    servo = Servo(sp=sp, servo_id=1)
    # to read a value
    servo['goal_position'] = 128
```

To connect a group of servos and write values to a register (example: `goal_position`):
```python
with ServoProtocol() as sp:
    sg = ServoGroup()
    sg['base'] = Servo(sp, 10)
    sg['elbow'] = Servo(sp, 11)
    sg['wrist'] = Servo(sp, 12),
    sg['claw'] = Servo(sp, 13)

   sg.write("goal_position", [
        100,  # first servo value
        200,  # second servo value
        330,  # third servo value
        400   # fourth servo value
    ])
```

### From the command-line
To read a register from one servo:
```
$ ./servode.py read_register --sid 10
2016-11-04 06:01:42,582|servode |INFO: Read register: 'present_position'
2016-11-04 06:01:42,587|servode |INFO: Servo:10 value:497
```
To read a register from two servos:
```
$ ./servode.py read_register --sid 10 --sid 11
2016-11-04 06:01:42,582|servode |INFO: Read register: 'present_position'
2016-11-04 06:01:42,587|servode |INFO: Servo:10 value:497
2016-11-04 06:01:42,589|servode |INFO: Servo:11 value:102
```
To write a value to a register on one servo:
```
$ ./servode.py write_register goal_position 490 --sid 10
2016-11-04 06:23:28,716|servode |INFO: Servo:10 wrote value:490 to register:goal_position
```
To write a value to a register on two servos:
```
$ ./servode.py write_register goal_position 490 --sid 10 --sid 11
2016-11-04 06:24:11,614|servode |INFO: Servo:10 wrote value:490 to register:goal_position
2016-11-04 06:24:11,616|servode |INFO: Servo:11 wrote value:490 to register:goal_position
```
## Installation

1. Download the latest [ROBOTIS SDK](https://github.com/ROBOTIS-GIT/DynamixelSDK/releases)
2. Change to the directory where `servode.py` resides
3. Un-tar the ROBOTIS SDK:

    ```
    #example
    tar -xvf ~/download/dir/of/DynamixelSDK-#.#.#.tar
    ```  
4. Copy the dynamixel python functions to the directory where `servode.py` resides

    ```
    # example
    cp DynamixelSDK-#.#.#.tar/python/dynamixel_functions_py/dynamixel_functions.py .
     ```
5. Edit `dynamixel_functions.py` to use the CDLL for your OS. 
    - Example CDLL edit for Raspbian Jessie: 
    ```python
        ...snip...
        from ctypes import cdll
        # dxl_lib = cdll.LoadLibrary("../../c/build/win32/output/dxl_x86_c.dll") # for windows 32bit
        # dxl_lib = cdll.LoadLibrary("../../c/build/win64/output/dxl_x64_c.dll") # for windows 64bit
        # dxl_lib = cdll.LoadLibrary("../../c/build/linux32/libdxl_x86_c.so")    # for linux 32bit
        # dxl_lib = cdll.LoadLibrary("../../c/build/linux64/libdxl_x64_c.so")    # for linux 64bit
        dxl_lib = cdll.LoadLibrary("DynamixelSDK-3.4.1/c/build/linux_sbc/libdxl_sbc_c.so")    # for linux 32bit sbc
        ...snip...

    ```
