#!/usr/bin/env python
"""
Run a simple state matrix with extra timers.
It has three states:
- State0: does nothing, jumps to State1 in 100ms.
- State1: turns light on and triggers two extra timers (0.5s and 1s).
          From here ExtraTimer0 will force a transition to State2.
- State2: turns light off.
          From here ExtraTimer1 will force a transition to State0.

NOTES:
1. This example will not work on emulator mode.
2. Run this script from ipython to be able to stop the state machine,
   as instructed at the end.
"""

from taskontrol import smclient

nInputs = 3   # Inputs: see INPUTS in settings/rigsettings,py
nOutputs = 3  # Outputs: see OUTPUTS in settings/rigsettings,py
nExtraTimers = 2  # Two extra timers

#                Ci  Co  Li  Lo  Ri  Ro  Tup  eT0 eT1
stateMatrix = [ [ 0,  0,  0,  0,  0,  0,  1,   0,  0 ] ,
                [ 2,  1,  1,  1,  1,  1,  1,   2,  1 ] ,
                [ 2,  2,  1,  2,  2,  2,  2,   1,  0 ] ]

stateOutputs = [[0,0,0], [1,1,1], [0,0,0]]
stateTimers  = [  0.1,      9 ,      9  ]

extraTimers = [0.5, 1]
triggerStateEachExtraTimer = [1, 1]

sm = smclient.StateMachineClient()

sm.set_sizes(nInputs, nOutputs, nExtraTimers)
sm.set_state_matrix(stateMatrix)
sm.set_state_outputs(stateOutputs)
sm.set_state_timers(stateTimers)

sm.set_extra_timers(extraTimers)
sm.set_extra_triggers(triggerStateEachExtraTimer)

sm.run()

print('If running in interactive mode you can:')
print(' Stop state transitions by typing: sm.stop()')
print(' Close the client by typing: sm.close()')
