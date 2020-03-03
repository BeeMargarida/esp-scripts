mqtt_client = None
input_topic = "data"
output_topic = "results"
done = False

def switch(a, b=3):
    print(a)
    print(b)
    res = (a == b)
    print(res)
    return a == b


def on_input(topic, msg):
    global done
    res = switch(msg)
    mqtt_client.publish(output_topic, '%s' % res)
    done = True


def exec(mqtt_c):
    global mqtt_client

    mqtt_client = mqtt_c
    mqtt_client.set_callback(on_input)
    mqtt_client.subscribe(input_topic)

    while done == False:
        mqtt_client.check_msg()

    return
