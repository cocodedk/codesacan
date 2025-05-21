#!/bin/bash
# 1. create & activate dedicated env
source venv/bin/activate
# 2. start server
python code_graph_http.py --host 127.0.0.1 --port 8765
