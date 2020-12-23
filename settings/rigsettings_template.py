"""
This script defines the parameters of the system, including the names
of inputs and outputs, the type of state machine and sound server,
the serial/USB ports used, and the data directories.

*This file is a template, do not modify it.* Make a copy of this file
and name it 'rigsettings.py'. Modify this new file to define the
appropriate settings for your rig.
"""

__version__ = '0.3'

#: Operating system
OS = 'ubuntu2004'


#: ======== State machine and ports ========

#: Type of state machine. Either 'arduino_due', 'emulator' or 'dummy'
STATE_MACHINE_TYPE = 'emulator'
#STATE_MACHINE_TYPE = 'arduino_due'
#STATE_MACHINE_TYPE = 'dummy'

#: Make the emulator print details
EMULATOR_VERBOSE = True

#: Serial port for the state machine.
STATE_MACHINE_PORT = '/dev/arduinoDueProgramming'
#STATE_MACHINE_PORT = '/dev/ttyACM0'

#: Serial port for triggering sounds.
SOUND_TRIGGER_PORT = '/dev/arduinoDueNative'
#SOUND_TRIGGER_PORT = '/dev/ttyACM1'

#: Serial port for the wheelsensor
WHEEL_SENSOR_PORT = None
#WHEEL_SENSOR_PORT = 'dev/arduinoUNO'


#: ======== Sound subsystem ========

#: Type of sound server. Either 'jack' or 'pygame'
SOUND_SERVER = 'pygame'
#SOUND_SERVER = 'jack'

#: Type of sound card. Find this name by running: aplay -l
SOUND_CARD_NAME = 'PCH'

#: Computer volume level for sound presentation [0-100%]
SOUND_VOLUME_LEVEL = 82

#: Files that define the calibration of speakers
SPEAKER_CALIBRATION_SINE = None
#SPEAKER_CALIBRATION_SINE = '/home/jarauser/src/taskontrol/settings/speaker_calibration_sine.h5'
SPEAKER_CALIBRATION_CHORD = None
#SPEAKER_CALIBRATION_CHORD = '/home/jarauser/src/taskontrol/settings/speaker_calibration_chord.h5'
SPEAKER_CALIBRATION_NOISE = None
#SPEAKER_CALIBRATION_NOISE = '/home/jarauser/src/taskontrol/settings/speaker_calibration_noise.h5'

#: Settings for sending sync signals through one channel of the sound card
SOUND_SYNC_CHANNEL = None
#SOUND_SYNC_CHANNEL = 0
SYNC_SIGNAL_AMPLITUDE = 0.1
SYNC_SIGNAL_FREQUENCY = 500


#: ======== Data paths ========

DATA_DIR = '/data/behavior/'
REMOTE_DIR = None #'/mnt/jarahubdata/'

DEFAULT_PARAMSFILE = './params.py'


#: ======== Inputs and output ========

#: Name for each input line. They must match the state machine.
INPUTS = {
    'C'  :0,
    'L'  :1,
    'R'  :2,
}

#: Name for each output line. They must match the state machine.
OUTPUTS = {
    'centerWater':0,
    'centerLED'  :1,
    'leftWater'  :2,
    'leftLED'    :3,
    'rightWater' :4,
    'rightLED'   :5,
    'stim1'      :6,
    'stim2'      :7,
    'outBit0'    :8,
    'outBit1'    :9
}
