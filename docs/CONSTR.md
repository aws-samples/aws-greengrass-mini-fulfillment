# AWS Mini Fulfillment Center Construction

Welcome to the AWS Mini Fulfillment Construction Documentation. The quickest way to assemble
the various parts to form a complete robot arm is to assemble them in 4 separate sections and
combine them at the intersection points.

## Construction Instructions

Overall the process is:
1) acquire parts from the [Bill of Materials](BOM.md)
1) print 3D parts
1) assemble each arm
1) assemble control box
1) assemble conveyor
1) follow [software installation](INSTALL.md)
1) push green button

## The Arm
The arm's four main parts are in this image:
![4 main parts](img/doc_images/labeled_image.jpg?raw=true)

### The Shoulder

| Image | Instructions | 
| :--- | :--- |
| ![shoulder_01](img/doc_images/shoulder_step1.jpg) | Connect the Servo to the large square spacer using 6 N1 bolts and 6 S3 screws. |
| ![shoulder_02](img/doc_images/shoulder_step2.jpg) | Attach the shoulder piece to the servo fly-wheel. Make sure to include the small spacer between the fly-wheel and shoulder piece. |
| ![shoulder_03](img/doc_images/shoulder_step3.jpg) | When you have completed it, the should should be pointing so that the four holes are on the left side. |


### The Claw

| Image | Instructions | 
| :--- | :--- |
| <img src="img/doc_images/claw_step1.jpg" width="300" style="min-width:300px;"> | Position the servo fly-wheel so that it is pointing downward and use 4 S3 screws to connect the right clamp to the fly-wheel. |
| ![claw_02](img/doc_images/claw_step2.jpg) | On the top side, you’ll need to insert the BU washer through the center hole on the clamp and fasten it to the servo using an S4 screw. |
| ![claw_03](img/doc_images/claw_step3.jpg) | Position the Tibia assembly like shown so that the fly-wheel is pointing to the left and pre-insert 6 N1 bolts as shown. |
| ![claw_04](img/doc_images/claw_step4.jpg) | Return the assembly to the original position and attach the left clamp to the servo using 6 S3 screws. Be sure the N1 bolts line up. |
| ![claw_05](img/doc_images/claw_step5.jpg) | Attach the two camera housing pieces together using an N nut and S3 screw. |
| ![claw_06](img/doc_images/claw_step6.jpg) | Then, use any 2” long screw and bolt to attach the camera housing to the left clamp. |
| ![claw_07](img/doc_images/claw_step7.jpg) | Place 8 N1 bolts into the slotted holes at the flat end of the Tibia and fasten the FP servo mount using 8 S3 screws. |
| ![claw_08](img/doc_images/claw_step8.jpg) | Attach the Claw to the FP04 mount as shown in this photo. Remember to place 4 N1 bolts into the servo slots accordingly and fasten  with S3 screws. |
| ![claw_09](img/doc_images/claw_step9.jpg) | Position the servo at the bottom end of the Tibia as shown so the fly-wheel faces the side with the cable slots. Insert 12 N1 bolts into the servo and fasten with S3 screws. |

### The Femur

| Image | Instructions | 
| :--- | :--- |
| <img src="img/doc_images/femur_step1.jpg" width="300" style="min-width:300px;"> | *Begin the Femur assembly by placing the the piece so that the flat side with the rectangular cut-outs are on top. The servo fly-wheels should be pointing to the left.* |
| <img src="img/doc_images/femur_step2.jpg" width="300" style="min-width:300px;"> | *Each servo will be connected to the Femur using 6 S3 screws on the outer side and 5 on the inner side. Be sure to pre-insert the N1 bolts into the corresponding servo slot.* |
| <img src="img/doc_images/femur_step3.jpg" width="300" style="min-width:300px;"> | *Attach two strips of velcro for the Raspberry Pi to mount onto the Femur.* |


### The Base

| Image | Instructions | 
| :--- | :--- |
| <img src="img/doc_images/base_step1.jpg" width="300" style="min-width:300px;"> | *The base’s front side is marked by the 3 holes, and the back with the flat side. The base will contain a power converter that is attached with velcro.* |
| <img src="img/doc_images/base_step2.jpg" width="300" style="min-width:300px;"> | *Attach the SMPS2DYNAMIXEL power converter mounted to the back with the 3 pins facing up. Note that there are both 3 pins and 4 pins on the power converter.* |
| <img src="img/doc_images/base_step3.jpg" width="300" style="min-width:300px;"> | *Using 4 M3x16mm Flat head screws (equal to SB screws but flat head), mount the shouder assembly to the base. Flat heads are essential or the rotation will be blocked.* |

### Connect at the Joints

| Image | Instructions | 
| :--- | :--- |
| <img src="img/doc_images/connect_step1.jpg" width="300" style="min-width:300px;"> | *Attach the Femur assembly to the Shoulder/Base with the fly-wheel on the servo facing to the left with S3 screws. Use BU-WA washers and an SB screw to fasten the other end of the servo.* |
| <img src="img/doc_images/connect_step2.jpg" width="300" style="min-width:300px;"> | *Use 1 BU-WA washer and SB screw to attach the bottom (or right side when viewing the arm from the back).* |
| <img src="img/doc_images/connect_step3.jpg" width="300" style="min-width:300px;"> | *Use 4 S4 screws to fasten the Claw assembly to the Femur assembly. Note that the S screws are needed due to the extra thickness of the Femur.* |
| <img src="img/doc_images/connect_step4.jpg" width="300" style="min-width:300px;"> | *Attach the Raspberry Pi to the Femur using the velcro strips.* |
| <img src="img/doc_images/connect_step5.jpg" width="300" style="min-width:300px;"> | *When attaching the Claw to the Femur, ensure the direction of the claw is as shown.* |
| <img src="img/doc_images/connect_step6.jpg" width="300" style="min-width:300px;"> | *In general, when connecting the servo to any other part, start with the fly-wheel in the initial state, indicated by the lines in the plastic.* |

### Cables and Power

| Image | Instructions | 
| :--- | :--- |
| <img src="img/doc_images/power_step1.jpg" width="300" style="min-width:300px;"> | *The servos are all daisy chained using the 3P 200mm Robot Cable. Follow the images and connect as shown.* |
| <img src="img/doc_images/power_step2.jpg" width="300" style="min-width:300px;"> | *The cable will usually connect the previous servo on the left, and daisy chain out from the right slot.* |
| <img src="img/doc_images/power_step3.jpg" width="300" style="min-width:300px;"> | *Between the Elbow servo and Shoulder, you’ll need to splice a longer (by 3”) cable.* |
| <img src="img/doc_images/power_step4.jpg" width="300" style="min-width:300px;"> | *From the Elbow, connect to the right servo on the left (in) slot and connect the right (out) slot to the servo on the left.* |
| <img src="img/doc_images/power_step5.jpg" width="300" style="min-width:300px;"> | *From the right slot, connect to the bottom servo on the left slot. The left servo must be the one connected to the bottom.* |
| <img src="img/doc_images/power_step6.jpg" width="300" style="min-width:300px;"> | *The last servo in the daisy chain will connect to the the left servo using the left pin slot. Using the right pin slot connect to the power adapter.* |
| <img src="img/doc_images/power_step7.jpg" width="300" style="min-width:300px;"> | *The power adapter receives the bottom servo connection in the left slot and goes to the serial adapter from the right slot.* |
| <img src="img/doc_images/power_step8.jpg" width="300" style="min-width:300px;"> | *There is only one 3 pin slot on the serial adapter that is connected to the usb port on the Raspberry Pi.* |
| <img src="img/doc_images/power_step9.jpg" width="300" style="min-width:300px;"> | *Note that the switch must be in the up position if using the 3 pin slot.* |

## The Control Box
    <TBD>
