#!/usr/bin/env bash

echo "[start] Create ArmErrorDetector Lambda"
python setup_lambda.py create ArmErrorDetector/cfg_lambda.json
echo "[end] Create ArmErrorDetector Lambda"

echo "[start] Create MasterBrain Lambda"
python setup_lambda.py create MasterBrain/cfg_lambda.json
echo "[end] Create MasterBrain Lambda"

echo "[start] Create MasterErrorDetector Lambda"
python setup_lambda.py create MasterErrorDetector/cfg_lambda.json
echo "[end] Create MasterErrorDetector Lambda"
