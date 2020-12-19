Inputs and outputs
==================

The possible inputs (to generate events) and possible outputs (such as lights) for each system are defined when creating a state transition matrix. In general, the list of inputs and outputs for a rig does not change, so we defined them globally in the ``settings/rigsettings.py`` file.

Below we show how these inputs/outputs can be defined manually or taken from the settings.

*Inputs* are defined by a Python dictionary such as ``{'C':0, 'L':1, 'R':2}`` (for center, left and right detectors), which results in two possible events for each input: ``Cin``, ``Cout``, ``Lin``, ``Lout``, ``Rin``, ``Rout``. In this case ``Cin`` is an event triggered by activating detector C, and ``Cout`` is generated when the detector is deactivated. An additional event (``Tup``) is always created. This event is triggered when the timer corresponding to the current state ends.

*Outputs* are defined by a similar Python dictionary such as ``{'centerValve':0, 'centerLED':1}``. 

When creating an instance of ``StateMatrix``, we can also specify the name of the "readystate". When the system reaches this state, it gives the control back from the state machine to the user interface until ``dispatcherModel.ready_to_start_trial()`` is called.

Here is an example of how this is done in code:

.. code-block:: python
    :linenos:

    from taskontrol import statematrix
    from taskontrol.plugins import templates

    class Paradigm(templates.ParadigmMinimal):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.sm = statematrix.StateMatrix(inputs={'C':0, 'L':1, 'R':2},
                                              outputs={'centerValve':0, 'centerLED':1},
                                              readystate='ready_next_trial')
            # The parent class defines self.dispatcherModel used below.

        def prepare_next_trial(self, nextTrial):
            # -- Set state matrix --
            self.sm.add_state(name='wait_for_event', statetimer=100,
                              transitions={'Cin':'light_on'})
            self.sm.add_state(name='light_on', statetimer=2.0,
                              transitions={'Cin':'light_off', 'Tup':'light_off'},
                              outputsOn=['centerLED'])
            self.sm.add_state(name='light_off', statetimer=0,
                              transitions={'Tup':'ready_next_trial'},
                              outputsOff=['centerLED'])
            self.dispatcherModel.set_state_matrix(self.sm)
            # -- Tell the state machine that we are ready to start --
            self.dispatcherModel.ready_to_start_trial()

    if __name__ == "__main__":
        (app, paradigm) = templates.paramgui.create_app(Paradigm)


Alternatively, we can import rigsettings.py and use the inputs and outputs defined there:

.. code-block:: python
    :linenos:

    from taskontrol import statematrix
    from taskontrol import rigsettings
    from taskontrol.plugins import templates

    class Paradigm(templates.ParadigmMinimal):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.sm = statematrix.StateMatrix(inputs=rigsettings.INPUTS,
                                              outputs=rigsettings.OUTPUTS,
                                              readystate='ready_next_trial')
        # ...lines 10-27 from code above.

You can check `rigsettings_template.py`_, to see what inputs and outputs are defined by default.

.. _rigsettings_template.py: https://github.com/sjara/taskontrol/blob/master/settings/rigsettings_template.py


.. note:: In this example, we import a couple of additional modules (``statematrix`` and ``rigsettings``). In previous examples, these were imported by the ``templates`` module, but here we are using them directly.



  

  


  
