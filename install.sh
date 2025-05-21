#!/bin/bash

python3 -m venv venv
source venv/bin/activate.fish
pip install -r requirements.txt
docker compose build
docker compose up -d
