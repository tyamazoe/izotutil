#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" IzoT application
    Simple Lamp Switch application to control LEDs and
    buttons on expansiton board connected to GPIO.
"""

# IzoT Device Stack common code used by this application
from izot.examples.common.framework.framework import Framework
from izot.examples.common.framework.framework import FrameworkMenu
from izot.examples.common.framework.framework import ApplicationType
from izot.examples.common.util.util import kbhit

# Import the IzoT Device Stack
import izot.device
import izot.version as version

# IzoT profiles used by this application
from izot.resources.profiles.iotNodeObject import iotNodeObject

# IzoT datapoint
#import izot.resources.datapoints.switch
from izot.resources.profiles.switch import switch
from izot.resources.profiles.lampActuator import lampActuator


DIO_COUNT = 3           # Number of DIOs; can be 1 to 7 with the PiFace
                        # One button/LED pair is reserved for the
                        # Connect LED

# Main IzoT Device Stack EX object
app = None
# Global blocks
switch_fb = None
LampBlock = None

APP_NAME = 'lamp-switch'
APP_DESCRIPTION = 'The IzoT simple Lamp and Switch example application'
APP_TYPE = ApplicationType.OTHER
MAJOR_VERSION = 2

# Define program ID; set the last digit equal to the number of DIOs
PROGRAM_ID = '9F:FF:FF:05:00:0A:A0:0' + str(DIO_COUNT)

# Use GPIO
import RPi.GPIO as GPIO
import time
# GPIO pin number
GP_OUT1 = 4
GP_OUT2 = 17
GP_OUT3 = 22
GP_IN1 = 23
GP_IN2 = 24
GP_IN3 = 25

gpio_in = (GP_IN1, GP_IN2, GP_IN3)
gpio_out = (GP_OUT1, GP_OUT2, GP_OUT3)

def init_gpio():
    print("Initialize GPIO\n")
    # Use GPIO pin num
    GPIO.setmode(GPIO.BCM)
    # Output
    GPIO.setup(GP_OUT1, GPIO.OUT)
    GPIO.output(GP_OUT1, False)
    GPIO.setup(GP_OUT2, GPIO.OUT)
    GPIO.output(GP_OUT2, False)
    GPIO.setup(GP_OUT3, GPIO.OUT)
    GPIO.output(GP_OUT3, False)
    # Input
    GPIO.setup(GP_IN1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(GP_IN2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(GP_IN3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


def worker_check_button_detect_sw(event):
    """
    button detection handler.
    """
    try:
        #print('event: {0}'.format(event))
        if event in gpio_in:
            i = gpio_in.index(event)
            #print('detected {0}'.format(i))

            current_switch_value = switch_fb[i].nvoSwitch.data.value
            current_switch_state = switch_fb[i].nvoSwitch.data.state
            #print('current switch : {0} {1}'.format(current_switch_value, current_switch_state))
            # Turn Off Output
            if current_switch_value > 0 and current_switch_value >= 1:
                print('Turn Off Switch[{0}]'.format(i))
                switch_fb[i].nvoSwitch.data.value = 0.0
                switch_fb[i].nvoSwitch.data.state = 0
            # Turn On Output
            else:
                print('Turn On Switch[{0}]'.format(i))
                switch_fb[i].nvoSwitch.data.value = 100.0
                switch_fb[i].nvoSwitch.data.state = 1
            #print('new switch     : {0} {1}'.format(switch_fb[i].nvoSwitch.data.value, switch_fb[i].nvoSwitch.data.state))
            switch_fb[i].nviSwitchFb.data.value = switch_fb[i].nvoSwitch.data.value
            switch_fb[i].nviSwitchFb.data.state = switch_fb[i].nvoSwitch.data.state
            #logger.info(' Occupancy Sensor Detection Mode Button activated')
    except Exception as e:
        print('Exception occurred when callback button: {}'.format(e))
        #print('Callback exception: {}'.format(e))
        #logger.error('Error collecting button detect sensor reading: {}'.format(e))


def main():
    # Print welcome message
    print('Welcome to the IzoT Lamp & Switch Example Application.')
    #print('Host device: {0}'.format(is_host_device))

    # Initialize the common framework
    print('Initializing...\n')
    framework = Framework(
        APP_NAME, APP_TYPE, APP_DESCRIPTION, PROGRAM_ID
    )
    arguments = framework.arguments     # Get the command line arguments
    global app
    app = framework.app                 # Get the app object

    #
    # Create functional blocks
    #
    # Create Node Object functional block
    app.block(
        profile=iotNodeObject(),
        ext_name='nodeObject'
    )
    # Add in version numbers
    app.node_object.implement('nciDevMajVer')
    app.node_object.implement('nciDevMinVer')
    app.node_object.nciDevMajVer.data = 2
    app.node_object.nciDevMinVer.data = int(version.VERSION[5:])

    # Create lampActuator functional block
    global lamp_fb
    lamp_fb = []
    for i in range(DIO_COUNT):
        lamp_fb.append(app.block(profile=lampActuator(), ext_name = 'LampBlock{0}'.format(i)))

    # Create Switch functional block for button
    global switch_fb
    switch_fb = []
    for i in range(DIO_COUNT):
        switch_fb.append(app.block(profile=switch(), ext_name = 'SwitchBlock{0}'.format(i)))

    for i in range(DIO_COUNT):
        switch_fb[i].implement('nviSwitchFb')


    def find_lamp_fb_index(sender):
        """
        Find function block index
        """
        #print('find_switch_fb_index: {0}'.format(dp_name))
        for i in range(DIO_COUNT):
            if lamp_fb[i].nviLampValue.name == sender.name:
                return i
        return -1


    def on_nvi_lampvalue_updated(sender, arguments):
        """
        Handle updates to the closedSensor's input:
        """
        # copy input fb to output
        #print('Processing new lamp_fb update: {0}'.format(sender))
        i = find_lamp_fb_index(sender)
        if i >= 0:
            try:
                new_lamp_value = lamp_fb[i].nviLampValue.data.value
                new_lamp_state = lamp_fb[i].nviLampValue.data.state
                #print('nviLampValue : {0} {1}'.format(new_lamp_value, new_lamp_state))
                # Turn On/Off LEDs
                if new_lamp_value > 0 and new_lamp_state >= 1:
                    print('Turn On Lamp[{0}]'.format(i))
                    GPIO.output(gpio_out[i], True)
                else:
                    print('Turn Off Lamp[{0}]'.format(i))
                    GPIO.output(gpio_out[i], False)
                # Copy to fb value
                lamp_fb[i].nvoLampValueFb.data.value = new_lamp_value
                lamp_fb[i].nvoLampValueFb.data.state = new_lamp_state
            except Exception as e:
                print('Exception occurred when processing new lux update: {}'.format(sender, e))
        else:
            print('Not Found: {0}'.format(i))

    # Register the input network variable event handlers for lamp
    for i in range(DIO_COUNT):
        #print('add on_nvi_lamp_updated {0}'.format(i))
        lamp_fb[i].nviLampValue.OnUpdate += on_nvi_lampvalue_updated


    def find_switch_fb_index(sender):
        """
        Find function block index
        """
        #print('find_switch_fb_index: {0}'.format(dp_name))
        for i in range(DIO_COUNT):
            if switch_fb[i].nviSwitchFb.name == sender.name:
                return i
        return -1


    def on_nvi_switch_fb_updated(sender, arguments):
        """
        Handle updates to the closedSensor's input:
        """
        # copy input fb to output
        #print('Processing new switch_fb update: {0}'.format(sender))
        i = find_switch_fb_index(sender)
        if i >= 0:
            switch_fb[i].nvoSwitch.data.value = switch_fb[i].nviSwitchFb.data.value
            switch_fb[i].nvoSwitch.data.state = switch_fb[i].nviSwitchFb.data.state
        else:
            print('Not Found: {0}'.format(i))

    # Register the input network variable event handlers for lamp
    for i in range(DIO_COUNT):
        switch_fb[i].nviSwitchFb.OnUpdate += on_nvi_switch_fb_updated

    # Configure and start IzoT application framework
    framework.app_start()

    # Initialize the device name if this is the first run
    # The first run checking must be done after the IzoT app
    # configured and started.
    if framework.app.is_first_run:
        import socket
        device_name = socket.gethostname() + "-" + str(DIO_COUNT) + "Ch-Lamp-Switch"
        print('First run--initialize device name to {0}'.format(device_name))
        if app.node_object:
            app.node_object.cpName.data.name = device_name.encode(
                encoding='UTF-8'
            )

    # Initialize GPIO
    init_gpio()
    # Setup the thread, detect a falling edge on button(channel) specified
    # and debounce it with 200mSec
    for i in range(DIO_COUNT):
        GPIO.add_event_detect(gpio_in[i],
                              GPIO.FALLING,
                              callback=worker_check_button_detect_sw,
                              bouncetime=300)


    # Include the standard framework menu
    framework_menu = FrameworkMenu(framework)

    # Run the application
    done = False
    try:
        while not done:
            # Service the IzoT Device Stack
            app.service(0.100)

            # Test for user input
            if kbhit(0.0):
                done = framework_menu.execute()

    finally:
        # Stop GPIO and IzoT Device Stack
        GPIO.cleanup()
        app.stop()


if __name__ == '__main__':
    main()
