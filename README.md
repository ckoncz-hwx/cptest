# CherryPy WSGI server load testing

## Setup
```
cd cpserver
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../axios-test
npm i
cd ..
```

## Start server
```
cd cpserver
python cpserver.py --connection_processing_sleep_time 0.2
```

## Start client
```
cd axios-test
node test.js -u http://localhost:8080 -c 50 -s 20
```