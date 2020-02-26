def switch(a, b = 3):
    print(a)
    print(b)
    res = (a == b)
    print(res)
    return a == b

def on_input(topic, msg):
    print(msg)
    return switch(msg)

def exec(mqtt_client, input_topic):
    mqtt_client.set_callback(on_input)
    mqtt_client.subscribe(input_topic)
    while True:
        mqtt_client.check_msg()
            