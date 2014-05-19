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

test050 = sidesDirectMode.copy()
test050.update({'subject':'test050','experimenter':'santiago'})

test051 = sidesDirectMode.copy()
test051.update({'subject':'test051','experimenter':'santiago'})

test052 = sidesDirectMode.copy()
test052.update({'subject':'test052','experimenter':'santiago'})

test053 = sidesDirectMode.copy()
test053.update({'subject':'test053','experimenter':'santiago'})

test054 = sidesDirectMode.copy()
test054.update({'subject':'test054','experimenter':'santiago'})

test055 = sidesDirectMode.copy()
test055.update({'subject':'test055','experimenter':'santiago'})

test056 = sidesDirectMode.copy()
test056.update({'subject':'test056','experimenter':'santiago'})

test057 = sidesDirectMode.copy()
test057.update({'subject':'test057','experimenter':'santiago'})

test058 = sidesDirectMode.copy()
test058.update({'subject':'test058','experimenter':'santiago'})

test059 = sidesDirectMode.copy()
test059.update({'subject':'test059','experimenter':'santiago'})

