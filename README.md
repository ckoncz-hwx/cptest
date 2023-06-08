# CherryPy WSGI server load testing

## Setup
Python 3.9 is required (Python 3.11 is known not to work).
```
python3.9 -m venv venv; \
source venv/bin/activate; \
pip install -r requirements.txt; \
cd axios-test; \
npm i; \
cd ..
```

## Start server
```
python cpserver.py --connection_processing_sleep_time 0.2
```

## Start client
```
cd axios-test
node test.js -u http://127.0.0.1:8080 -c 100 -s 20
```