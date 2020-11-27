'''
Extra functions useful at different stages of the paradigm design.
'''

import numpy as np


def find_state_sequence(states, stateSequence):
    '''
    Return an array with the indexes where state transitions are the same as stateSequence
    states is a 1D array of state IDs in the order they occurred.
    stateSequence is a 1D array containing some sequence of states.
    '''
    sequenceStartInd = []
    for ind in range(len(states)-len(stateSequence)+1):
        val = np.all(states[ind:ind+len(stateSequence)] == stateSequence)
        sequenceStartInd.append(val)
    return np.array(sequenceStartInd)


def find_transition(states, prevStateID, nextStateID):
    '''
    Return an array with the indexes of transitions from origEvent to destEvent
    (that is, the index of destEvent that is preceded by origEvent)
    states is a 1D array of state IDs in the order they occurred.
    prevStateID and nextStateID must be integers.

    For a similar method see: extracellpy/loadbehavior.time_of_state_transition
    '''
    prevStateInds = (np.r_[0, states[:-1]] == prevStateID)
    nextStateInds = (states == nextStateID)
    transitionInds = np.flatnonzero(prevStateInds & nextStateInds)
    return transitionInds


def find_event(events, states, eventID, currentStateID):
    '''
    Return an array with the indexes in which eventID occurred while in currentStateID
    events is a 1D array of event IDs in the order they occurred.
    states is a 1D array of state IDs in the order they occurred.
    eventID and currentStateID must be integers.

    For a similar method see: extracellpy/loadbehavior.time_of_state_transition
    '''
    eventInds = (events == eventID)
    currentStateInds = (np.r_[0, states[:-1]] == currentStateID)
    eventInds = np.flatnonzero(eventInds & currentStateInds)
    return eventInds


def append_dict_to_HDF5(h5fileGroup, dictName, dictData, compression=None):
    '''Append a python dictionary to a location/group in an HDF5 file
    that is already open.

    It creates one scalar dataset for each key in the dictionary,
    and it only works for scalar values.

    NOTE: An alternative would be use the special dtype 'enum'
    http://www.h5py.org/docs/topics/special.html
    '''
    dictGroup = h5fileGroup.create_group(dictName)
    for key, val in dictData.items():
        # if isinstance(val, np.array): dtype = val.dtype
        # else: dtype = type(val)
        dtype = type(val)
        dset = dictGroup.create_dataset(key, data=val, dtype=dtype,
                                        compression=compression)
        return dset


def dict_from_HDF5(dictGroup):
    newDict = {}
    for key, val in dictGroup.items():
        newDict[key] = val[()]
        newDict[val[()]] = key
    return newDict


class EnumContainer(dict):
    """
    Container for enumerated variables.

    Useful for non-graphical variables like choice and outcome which take
    a finite set of values, and each value is associated with a label.
    """
    def __init__(self):
        super().__init__()
        self.labels = dict()

    def append_to_file(self, h5file, currentTrial):
        """
        Append data in container to an open HDF5 file.
        """
        if currentTrial < 1:
            raise UserWarning('WARNING: No trials have been completed or ' +
                              'currentTrial not updated.')
        resultsDataGroup = h5file.require_group('resultsData')
        resultsLabelsGroup = h5file.require_group('resultsLabels')
        for key, item in self.items():
            dset = resultsDataGroup.create_dataset(key, data=item[:currentTrial])
        for key, item in self.labels.items():
            # FIXME: Make sure items of self.labels are dictionaries
            dset = append_dict_to_HDF5(resultsLabelsGroup, key, item)
        return dset
