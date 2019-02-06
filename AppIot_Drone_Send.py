#!/usr/bin/python

import os
import sys
import time
import requests

if len(sys.argv) != 10:
    print("ERROR: Require sensor data to post.")
    print("Sensor data order: OperatingStatus Longitude Latitude Altitude Speed CameraOnOff RemainingBattery RemainingFlight CommandString")
    sys.exit(1)

def post_data(sensor_id, sensor_value, gateway_id, sensor_type):
    
    # TestTruck from the APP IoT 2.0 Gateway ticket.
# Ottawa FirstRespondorDrone Gateway Lwm2m
    httpSAS = 'SharedAccessSignature sr=https%3a%2f%2fiotabusinesslab.servicebus.windows.net%2fdatacollectoroutbox%2fpublishers%2fbe481468-caea-466e-9e4c-999476e5e727%2fmessages&sig=kuMAh8XzNExLq3RikpqbsurJqhrJGOEcD0Vv7KnlDhk%3d&se=4701689911&skn=SendAccessPolicy'

    #
    # Get current time in seconds. (works with or without trailing milliseconds)
    time_now = int(time.time())
    #
    # Create http body with sensor data.
    # {
    # "bu":"default-unit",
    # "e":[
    #   {
    #     "n":"[Endpoint]/[ObjectID]/[InstanceID]/[ResourceID]", (TestTruckDevice/3303/0/5700)
    #     "u":"default-unit",
    #     "v":null,   (Numeric Value)
    #     "bv":false, (Boolean Value) 
    #     "sv":null,  (String Value)
    #     "t":1538546399 (Timestamp in Seconds)
    #   }
    #   ]
    # }
    if sensor_type == "v":
      print("found int or float")
      sensor_data = '{"bu":"default-unit","e":[{"n":"%s","u":"default-unit","v":%s,"bv":null,"sv":null,"t":%s}]}' % (sensor_id, sensor_value, time_now)
    elif sensor_type == "sv":
      print("found string")
      sensor_data = '{"bu":"default-unit","e":[{"n":"%s","u":"default-unit","v":null,"bv":null,"sv":"%s","t":%s}]}' % (sensor_id, sensor_value, time_now)
    elif sensor_type == "bv":
      print("found boolean")
      sensor_data = '{"bu":"default-unit","e":[{"n":"%s","u":"default-unit","v":null,"bv":%s,"sv":null,"t":%s}]}' % (sensor_id, sensor_value, time_now)
    else:  # taken as default for now
      sensor_data = '{"bu":"default-unit","e":[{"n":"%s","u":"default-unit","v":%s,"bv":null,"sv":null,"t":%s}]}' % (sensor_id, sensor_value, time_now)

    #
    # Create headers (http://docs.appiot.io/?page_id=43134)
    headers = { 'DataCollectorId': gateway_id,
                'Authorization': httpSAS,
                'PayloadType': 'application/senml+json',
                'Content-Type': 'application/json' }

    return(headers,sensor_data)

###############################################################################
def run(OperatingStatus_Value, Longitude_Value, Latitude_Value, Altitude_Value, Speed_Value, CameraOnOff_Value, RemainingBattery_Value, RemainingFlight_Value, CommandString_Value):
    # First Respondor Drone Gateway From APP IoT
    gateway_id = 'be481468-caea-466e-9e4c-999476e5e727'


    # APP IoT Mailbox URL for passing in sensor data.
    url = 'https://iotabusinesslab.servicebus.windows.net/datacollectoroutbox/publishers/%s/messages' % (gateway_id)

    # Sensor that we have defined in APP IoT.
    sensors = { "OperatingStatus_Value":"EricssonOneOttawaFirstRespondorDroneDevice/3348/0/5547",
                "Longitude_Value":"EricssonOneOttawaFirstRespondorDroneDevice/6/0/1",
                "Latitude_Value":"EricssonOneOttawaFirstRespondorDroneDevice/6/0/0",
                "Altitude_Value":"EricssonOneOttawaFirstRespondorDroneDevice/6/0/2",
                "Speed_Value":"EricssonOneOttawaFirstRespondorDroneDevice/6/0/6",
                "Timestamp_Value":"EricssonOneOttawaFirstRespondorDroneDevice/6/0/5",
                "CameraOnOff_Value":"EricssonOneOttawaFirstRespondorDroneDevice/3342/0/5500",
                "RemainingBattery_Value":"EricssonOneOttawaFirstRespondorDroneDevice/3320/0/5700",
                "RemainingFlight_Value":"EricssonOneOttawaFirstRespondorDroneDevice/3340/0/5538",
                "CommandString_Value":"EricssonOneOttawaFirstRespondorDroneDevice/3348/0/5750" }

    # Associate command-line inputs with target sensor.
    sensor_inputs = { "OperatingStatus_Value":[OperatingStatus_Value,"v"], "Longitude_Value":[Longitude_Value,"v"],
                      "Latitude_Value":[Latitude_Value,"v"], "Altitude_Value":[Altitude_Value,"v"],
                      "Speed_Value":[Speed_Value,"v"], "Timestamp_Value":[int(time.time()),"v"],
                      "CameraOnOff_Value":[CameraOnOff_Value,"bv"], "RemainingBattery_Value":[RemainingBattery_Value,"v"],
                      "RemainingFlight_Value":[RemainingFlight_Value,"v"], "CommandString_Value":[CommandString_Value,"sv"] }
    # sensor.items() for python 3.X
    for sensor_name,sensor_id in sensors.iteritems():

        sensor_value = sensor_inputs[sensor_name][0]
        sensor_type = sensor_inputs[sensor_name][1]
        (header_data, sensor_data) = post_data(sensor_id, sensor_value, gateway_id, sensor_type) 
        response = requests.post(url, data=sensor_data, headers=header_data)
        
        if str(response.status_code) != "201":
            print("Error: Post Response: "+ str(response.status_code))
            sys.exit(1)

        print("Posted %s: %s" % (sensor_name, sensor_data))
        print("Post Response Status: " + str(response.status_code))
