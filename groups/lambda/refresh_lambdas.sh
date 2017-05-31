#!/usr/bin/env bash

echo "[start] Setup ArmErrorDetector Lambda"
cd ArmErrorDetector
./setup_lambda.py
echo "[end] Setup ArmErrorDetector Lambda"

echo "[start] Setup MasterErrorBrain Lambda"
cd ../MasterBrain
#cd MasterBrain
./setup_lambda.py
echo "[end] Setup MasterErrorBrain Lambda"

echo "[start] Setup MasterErrorDetector Lambda"
cd ../MasterErrorDetector
./setup_lambda.py
echo "[end] Setup MasterErrorDetector Lambda"
