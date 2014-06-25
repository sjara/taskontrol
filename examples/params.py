'''
Define parameters for different subjects
'''

test000 = {'targetDuration':0.2, 'targetIntensityMode':'fixed',
           'targetMaxIntensity':80,
           'highFreq':2100, 'midFreq':1400,'lowFreq':1000, 'trialsPerBlock':3,
           'punishSoundAmplitude':0.1} #, 'outcomeMode':'simulated'

test001 = {'delayToTarget':0.333, 'value1':88, 'value2':99}
test002 = {'value1':77, 'value2':88, 'value3':99}


sidesDirectMode = {'outcomeMode':'sides_direct', 'delayToTargetMean':0, 'delayToTargetHalfRange':0,
                   'currentBlock':'mid_boundary'}
directMode = {'outcomeMode':'direct', 'delayToTargetMean':0, 'delayToTargetHalfRange':0,
                   'currentBlock':'mid_boundary'}
increaseDelayMode = {'outcomeMode':'on_next_correct', 'delayToTargetMean':0, 'delayToTargetHalfRange':0,
                   'currentBlock':'mid_boundary', 'automationMode':'increase_delay', 'targetDuration':0.05,'targetMaxIntensity':80,'lowFreq':4000,'highFreq':13000}

#onNextCorrectMode = {'outcomeMode':'on_next_correct', 'delayToTargetMean':0.2, 'delayToTargetHalfRange':0.05,
#                   'currentBlock':'mid_boundary', 'targetDuration':0.1,'targetMaxIntensity':80,'lowFreq':4000,'highFreq':13000}
#onNextCorrectMode = {'currentBlock':'mid_boundary','lowFreq':3000,'highFreq':16000}
onNextCorrectMode = {'currentBlock':'low_boundary','trialsPerBlock':1000}


switchBlocksMode = {'punishTimeError':4}

test011 = switchBlocksMode.copy()
test011.update({'subject':'test011','experimenter':'santiago'})

test012 = switchBlocksMode.copy()
test012.update({'subject':'test012','experimenter':'santiago'})

test013 = switchBlocksMode.copy()
test013.update({'subject':'test013','experimenter':'santiago'})

test014 = switchBlocksMode.copy()
test014.update({'subject':'test014','experimenter':'santiago'})

test015 = switchBlocksMode.copy()
test015.update({'subject':'test015','experimenter':'santiago'})

test016 = switchBlocksMode.copy()
test016.update({'subject':'test016','experimenter':'santiago'})

test017 = switchBlocksMode.copy()
test017.update({'subject':'test017','experimenter':'santiago'})

test018 = switchBlocksMode.copy()
test018.update({'subject':'test018','experimenter':'santiago'})

test019 = switchBlocksMode.copy()
test019.update({'subject':'test019','experimenter':'santiago', 'currentBlock':'low_boundary', 'trialsPerBlock':1000})

test020 = switchBlocksMode.copy()
test020.update({'subject':'test020','experimenter':'santiago'})


test050 = onNextCorrectMode.copy()
test050.update({'subject':'test050','experimenter':'santiago'})

test051 = onNextCorrectMode.copy()
test051.update({'subject':'test051','experimenter':'santiago'})

test052 = onNextCorrectMode.copy()
test052.update({'subject':'test052','experimenter':'santiago'})

test053 = onNextCorrectMode.copy()
test053.update({'subject':'test053','experimenter':'santiago'})

test054 = onNextCorrectMode.copy()
test054.update({'subject':'test054','experimenter':'santiago'})

test055 = onNextCorrectMode.copy()
test055.update({'subject':'test055','experimenter':'santiago'})

test056 = onNextCorrectMode.copy()
test056.update({'subject':'test056','experimenter':'santiago'})

test057 = onNextCorrectMode.copy()
test057.update({'subject':'test057','experimenter':'santiago'})

test058 = onNextCorrectMode.copy()
test058.update({'subject':'test058','experimenter':'santiago'})

test059 = onNextCorrectMode.copy()
test059.update({'subject':'test059','experimenter':'santiago'})

