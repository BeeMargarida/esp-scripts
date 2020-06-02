import urequests

def log_to_logstash(data):
    print('Sending data to Logstash. Data:', data)
    try:
        response = urequests.post(
            "http://logstash:9600",
            json=data
        )
        print(response.status_code, response.reason, response.text)
    except OSError as e:
        print('Error sending data to Logstash:', e)