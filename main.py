# coding=utf-8
from multiprocessing import Queue, Value, Event, Manager
from PyQt5.QtWidgets import QApplication
import sys
from ressources.ressources import FakeValveManager, \
    FakeGripManager, ValveManager, GripManager, ConnectionToRaspi, Sound
from graphics.graphics import WindowManager
from parametrisation.parametrisation import Interface
from experimentation.experimentation import Experimentalist
from ctypes import c_char_p


if __name__ == "__main__":

    '''
    Create objects shared by all the processes
    '''

    current_frame = Value(c_char_p)

    u_screen = Queue()

    g_change = Queue()
    g_state = Value('i')

    v_opening = Queue()

    s_instruction = Queue()

    choice_queue = Queue()

    choice = Value(c_char_p)
    dice_output = Value(c_char_p)

    task_parameters = Queue()

    manager = Manager()

    keys_list = manager.list([])
    k_queue_for_grip = Queue()
    k_queue_for_experimentalist = Queue()

    stimuli_parameters = manager.dict()
    graphic_parameters = manager.dict()

    opening_window = Queue()

    display = Value('i')
    display.value = -1

    shutdown = Event()
    general_shutdown_event = Event()

    trial_queue = Queue()

    '''
    Decide if you want to use real material of keyboard instead
    '''
    fake = 0

    if fake:

        grip_manager = FakeGripManager(
            keyboard_queue=k_queue_for_grip,
            grip_state=g_state,
            grip_change=g_change,
            shutdown_event=general_shutdown_event)

        valve_manager = FakeValveManager(
            valve_opening=v_opening,
            shutdown_event=general_shutdown_event)

    else:

        c = ConnectionToRaspi()

        grip_manager = GripManager(
            grip_state=g_state,
            grip_change=g_change,
            shutdown_event=general_shutdown_event)

        valve_manager = ValveManager(
            valve_opening=v_opening,
            shutdown_event=general_shutdown_event)

    '''
    Prepare a task manager and a process for sound
    '''

    experimentalist = Experimentalist(
        grip_state=g_state,
        grip_change=g_change,
        valve_opening=v_opening,
        current_frame=current_frame,
        choice_queue=choice_queue,
        choice=choice,
        stimuli_parameters=stimuli_parameters,
        dice_output=dice_output,
        sound_instruction=s_instruction,
        task_parameters_queue=task_parameters,
        display=display,
        general_shutdown=general_shutdown_event,
        shutdown_event=shutdown,
        keys=keys_list,
        keyboard_queue=k_queue_for_experimentalist,
        keyboard_queue_for_fake_grip=k_queue_for_grip,
        confirmation_opening_window=opening_window,
        trial_queue=trial_queue,
        graphic_parameters=graphic_parameters)

    sound_manager = Sound(
        sound_instruction=s_instruction,
        shutdown_event=general_shutdown_event)

    '''
    Start all non graphics processes
    '''

    # noinspection PyUnresolvedReferences
    grip_manager.start()
    # noinspection PyUnresolvedReferences
    valve_manager.start()
    sound_manager.start()
    experimentalist.start()

    '''
    Start graphics processes
    '''

    app = QApplication(sys.argv)

    interface = Interface(
        parameters_values=task_parameters,
        shutdown_event=shutdown,
        general_shutdown=general_shutdown_event,
        trial_queue=trial_queue)

    window_manager = WindowManager(
        current_frame=current_frame,
        choice_queue=choice_queue,
        choice=choice,
        stimuli_parameters=stimuli_parameters,
        dice_output=dice_output,
        shutdown_event=shutdown,
        general_shutdown_event=general_shutdown_event,
        display=display,
        sound_instructions=s_instruction,
        keyboard_queues=[k_queue_for_grip, k_queue_for_experimentalist],
        keys=keys_list,
        confirmation_opening_window=opening_window,
        graphic_parameters=graphic_parameters)

    sys.exit(app.exec_())
