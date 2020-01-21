# -*- coding: utf-8 -*-
import visa
from time import sleep

CHANNELS = {
    'A': 1,
    'B': 2,
    'C': 3,
    'REAR': 4,
    'INTREF': 6
}
TRIGGER_SOURCES = {
    'A': 'EXT1',
    'B': 'EXT2',
    'REAR': 'EXT4',
}

class CNT90:
    device = None
    batch_size = None

    def __init__(self, address=None):
        self.connect_to_device(address)

    def connect_to_device(self, address):
        rm = visa.ResourceManager()
        print(rm.list_resources())
    
        found = False
        for address in [address, *rm.list_resources()]:
            try:
                print('trying to connect to', address)
                device = rm.open_resource(address)
                print('Connection successful! Checking whether it is the correct device.')
                assert 'CNT-9' in device.query('*IDN?')
                print('It is! The device address is', address)
                found = True
                break
            except:
                pass

        if not found:
            raise Exception("""
                Unable to connect.
                If you are on Linux, you need to install via pip:
                    - pyvisa-py
                    - pyusb

                Then you have to do:
                    sudo groupadd usbusers
                    sudo usermod -a -G usbusers USERNAME
                    nano  /etc/udev/rules.d/99-com.rules

                    add the following line:

                    SUBSYSTEM=="usb", MODE="0666", GROUP="usbusers"

                    save the changes:

                    /etc/init.d/udev  restart

                    reboot

                This tutorial is taken from https://stackoverflow.com/questions/52256123/unable-to-get-full-visa-address-that-includes-the-serial-number
            """)
        
        self.device = device

        # clear state
        self.write('*CLS')

        # increase timeout to prevent errors with large datasets, in ms
        self.device.timeout = 120000

        # how many entries of the buffer can be transmitted with one query?
        self.batch_size = int(self.read('FORM:SMAX?'))

    def read(self, cmd):
        """Read the output of a command"""
        return self.device.query(cmd).rstrip('\n')

    def read_buffer(self):
        """Read out the entire device buffer"""
        data = []

        # loop until the buffer was completely read out
        while True:
            new = [
                float(n)
                for n in self.read(':FETC:ARR? MAX').split(',')
                if n
            ]
            data += new

            if len(new) < self.batch_size:
                break

        return data

    def write(self, cmd):
        """Send one or multiple commands to the device"""
        if isinstance(cmd, (tuple, list)):
            self.device.write(';'.join(cmd))
        else:
            self.device.write(cmd)

    def abort(self):
        """Abort the current command"""
        self.write(':ABORT')

    def frequency_measurement(self, channel, duration, sampling_freq,
                              trigger_source=None, wait=True):
        try:
            channel_idx = CHANNELS[channel]
        except ValueError:
            raise Exception('Invalid channel %s, valid values are %s' % (channel, list(CHANNELS.keys())))

        repetitions = duration * sampling_freq
        measurement_time = 1.0 / sampling_freq

        self.write([
            # set output format to ascii
            'FORM ASC',
            # set channel number and number of repetitions
            ':CONF:ARR:FREQ %d,(@%d)' % (repetitions, channel_idx),
            # disable continuous mode
            ':INIT:CONT OFF',
            # set measurement time
            ':ACQ:APER %f' % measurement_time,
        ])

        if trigger_source:
            self.write([
                'ARM:SOUR %s' % TRIGGER_SOURCES[trigger_source],
                'ARM:SLOP POS'
            ])

        # start the measurement (or wait for trigger)
        self.write(':INIT')

        if wait:
            return self.wait_and_return()

    def wait_and_return(self):
        while not self.command_done:
            sleep(0.1)

        data = self.read_buffer()
        if len(data) == 1:
            return data[0]
        return data

    @property
    def command_done(self):
        """Check whether the device has finished the last command"""
        return self.read('*OPC?') == '1'

