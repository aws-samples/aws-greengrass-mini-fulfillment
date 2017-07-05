#!/usr/bin/env python

# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not
# use this file except in compliance with the License. A copy of the License is
# located at
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

import os
import shutil
import errno
import zipfile
import requests

dl_name = "dxl_v3_4_3.zip"
url = "https://github.com/ROBOTIS-GIT/DynamixelSDK/archive/3.4.3.zip"
arm_dir = "arm/ggd/servo"
master_dir = "master/ggd/servo"

print("[begin] Downloading Dynamixel SDK: {0}".format(url))
r = requests.get(url, stream=True)
with open(dl_name, 'wb') as f:
    for chunk in r.iter_content(chunk_size=512):
        if chunk:   # filter out keep-alive new chunks
            f.write(chunk)
r.close()
print("[end] Download complete.")


def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

make_sure_path_exists(arm_dir)
make_sure_path_exists(master_dir)

print("[begin] Unzipping download {0}".format(dl_name))
with zipfile.ZipFile(dl_name, 'r') as z:
    z.extractall(os.curdir)
    print("...extracted to: {0}".format(os.curdir))
print("[end] Unzipped download")

print("[begin] Configure Dynamixel for Raspbian.")
dxl_python_file = os.curdir + '/DynamixelSDK-3.4.3/python/dynamixel_functions_py/dynamixel_functions.py'
win_match = r'dxl_lib = cdll.LoadLibrary("../../c/build/win32/output/dxl_x86_c.dll")'
win_after = r'# dxl_lib = cdll.LoadLibrary("../../c/build/win32/output/dxl_x86_c.dll")'
sbc_match = r'# dxl_lib = cdll.LoadLibrary("../../c/build/linux_sbc/libdxl_sbc_c.so")'
sbc_imp   = 'import os\n'
sbc_path  = 'dir_path = os.path.dirname(os.path.realpath(__file__))\n'
sbc_after = 'dxl_lib = cdll.LoadLibrary(dir_path + "/DynamixelSDK-3.4.3/c/build/linux_sbc/libdxl_sbc_c.so")'
out_fname = "dxl_funcs_py.tmp"
print("...finding lib strings...")
with open(dxl_python_file) as f:
    with open(out_fname, "w") as out:
        for line in f:
            if line.find(win_match) >= 0:
                out.write(line.replace(win_match, win_after))
            elif line.find(sbc_match) >= 0:
                out.write(sbc_imp)
                out.write(sbc_path)
                out.write(line.replace(sbc_match, sbc_after))
            else:
                out.write(line)

print("...replaced lib strings in temp dynamixel_functions.py.")
print("...copying Dynamixel directory...")
try:
    shutil.copytree(os.curdir + '/DynamixelSDK-3.4.3',
                    os.curdir + '/' + master_dir + '/DynamixelSDK-3.4.3')
    shutil.copytree(os.curdir + '/DynamixelSDK-3.4.3',
                    os.curdir + '/' + arm_dir + '/DynamixelSDK-3.4.3')
except OSError as ose:
    print("...ERROR copying Dynamixel directory:{0}".format(ose))
    exit(1)

print("...copied Dynamixel directory into ggd directories.")
print("...copying modified dynamixel_functions.py")
try:
    shutil.copy(out_fname,
                os.curdir + '/' + master_dir + '/dynamixel_functions.py')
    shutil.copy(out_fname,
                os.curdir + '/' + arm_dir + '/dynamixel_functions.py')
except OSError as ose:
    print("...ERROR copying modified dynamixel_functions.py:{0}".format(ose))
    exit(1)

print("...copied modified dynamixel_functions.py into ggd directories.")
print("[end] Configured Dynamixel for Raspbian.")

print("[begin] Cleaning up.")
os.remove(out_fname)
print("...removed temp dynamixel_functions.py.")
shutil.rmtree(os.curdir + '/DynamixelSDK-3.4.3')
print("...removed expanded Dynamixel SDK")
os.remove(dl_name)
print("...removed downloaded Dynamixel SDK")

print("[end] Cleaned up")
