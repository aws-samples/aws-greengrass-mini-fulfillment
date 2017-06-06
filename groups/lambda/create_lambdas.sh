#!/usr/bin/env bash

echo "[start] Create ArmErrorDetector Lambda"
python setup_lambda.py create ArmErrorDetector/lambda_cfg.json
echo "[end] Create ArmErrorDetector Lambda"

echo "[start] Create MasterBrain Lambda"
python setup_lambda.py create MasterBrain/lambda_cfg.json
echo "[end] Create MasterBrain Lambda"

echo "[start] Create MasterErrorDetector Lambda"
python setup_lambda.py create MasterErrorDetector/lambda_cfg.json
echo "[end] Create MasterErrorDetector Lambda"
