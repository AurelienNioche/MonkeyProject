from collections import OrderedDict
from datetime import date
from threading import Event, Thread
from time import time
import json
from os import path
import numpy as np

from data_management.database import Database
from task.ressources import GripManager, ValveManager, TtlManager, \
    GripTracker, Timer, Client, GaugeAnimation
from task.stimuli_finder import StimuliFinder
from utils.utils import log


class Manager(Thread):

    name = "Manager"

    def __init__(self, communicant, queues, shutdown):

        super().__init__()

        self.queues = queues
        self.shutdown = shutdown
        self.communicant = communicant

        self.grip_tracker = GripTracker(
            message_queue=self.queues["manager"],
            change_queue=self.queues["grip_queue"]
        )

        # --------- PROCESS FOR GRIP AND VALVE --- #

        # Get IP address of the RPi
        parameters_folder = path.abspath("{}/../parameters".format(path.dirname(path.abspath(__file__))))
        with open("{}/raspberry_pi.json".format(parameters_folder)) as file:
            rpi_parameters = json.load(file)

        self.client = Client(ip_address=rpi_parameters["ip_address"], port=rpi_parameters["port"])

        self.grip_manager = GripManager(
            grip_value=self.queues["grip_value"], grip_queue=self.queues["grip_queue"],
            client=self.client)

        self.valve_manager = ValveManager(client=self.client)
        self.ttl_manager = TtlManager(client=self.client)

        # -------- PARAMETERS --------- #

        self.parameters = None

        self.task_running = False

        # ------- STIMULI FINDER ------- #

        self.stimuli_finder = StimuliFinder()

        # ------- FOR FUTURE SAVING ---- #
        self.choice = None

        self.gauge_level = 0

        self.stimuli_parameters = {}
        self.to_save = []
        self.error = None

        self.dice_output = 0

        self.current_saving = Event()
        self.data_saved = Event()
        self.waiting_event = Event()

        # -------- TIME & TIMERS ----------- #

        self.timer = Timer(message_queue=self.queues["manager"])
        self.gauge_animation = GaugeAnimation(message_queue=self.queues["manager"])

        self.time_reference = -1

        self.time_reaction = -1
        self.time_movement = -1
        self.time_back_movement = -1
        self.time_inter_trial = -1
        self.time_inter_block = -1
        self.time_fixation = -1
        
        self.time_stamp_grip_onset = -1 
        self.time_stamp_release_grip = -1
        self.time_stamp_cue_onset = -1
        self.time_stamp_cue_contact = -1
        self.time_stamp_result_period_onset = -1
        self.time_stamp_reward_period_onset = -1
        self.time_stamp_inter_trial_interval_onset = -1
        self.time_stamp_inter_block_interval_onset = -1
        
        # ------- TRIAL COUNTERS ------ #

        self.trial_counter = [0, 0]

        self.n_trial_inside_block = 0

        self.n_block = 0

        # ------ STATE MANAGEMENT ---- #
        self.state = ""

        # ------ INIT ------ #

        self.initialize()

    # ------------------------ INIT ------------------------------------- #

    def initialize(self):

        self.grip_tracker.start()
        self.timer.start()
        self.gauge_animation.start()

    def run(self):

        log("Run.", self.name)
        while not self.shutdown.is_set():
            log("Waiting for a message.", self.name)
            message = self.queues["manager"].get()
            self.handle_message(message)

        self.die()

    def die(self):

        log("End program.", self.name)

        if self.current_saving.is_set():
            log("Wait for saving.", self.name)
            self.data_saved.wait()

        self.timer.end()
        self.gauge_animation.end()

        self.grip_tracker.end()
        self.grip_manager.end()
        self.valve_manager.end()
        self.ttl_manager.end()

        self.ask_interface(("close_all_windows",))

        log("I'm dead.", self.name)

    # ------------------------ HANDLE MESSAGE --------------------------- #

    def handle_message(self, message):

        if message[0] == "game":

            command = message[1]

            if command == "choice":

                if self.state == "show_stimuli":
                    self.did_not_release_grip_to_decide()

                elif self.state == "release_grip_to_decide":

                    self.ask_interface(("play_sound", "choice"))

                    side = message[2]

                    if side == "left":
                        log("Choice left.", self.name)
                        self.decide("left")

                    elif side == "right":
                        log("Choice right.", self.name)
                        self.decide("right")

                    else:
                        log("I will raise an exception.", self.name)
                        raise Exception

                else:
                    log("Ignore click on target left because state is not 'show_stimuli'.", self.name)

            elif command == "play":
                log("Play.", self.name)
                self.play_game()

            elif command == "close":
                log("Close game window.", self.name)
                self.end_game()

            else:
                log("ERROR: Message received from GameWindow not understood: '{}'.".format(message), self.name)
                raise Exception("{}: Received message '{}' but did'nt expected anything like that."
                                .format(self.name, message))

        elif message[0] == "grip_tracker":

            command = message[1]
            log("Received from GripTracker: '{}'.".format(command), self.name)

            if command == "release_before_end_of_fixation_time":

                if self.state == "grasp_before_stimuli_display":
                    self.release_before_end_of_fixation_time()

                else:
                    log("Command '{}' ignored (not in the appropriate state)."
                        .format(command), self.name)

            elif command == "grasp_before_stimuli_display":

                if self.state == "wait_for_grasping":
                    self.grasp_before_stimuli_display()

                else:
                    log("Command '{}' ignored (not in the appropriate state)."
                        .format(command), self.name)

            elif command == "release_grip_to_decide":

                if self.state == "show_stimuli":
                    self.release_grip_to_decide()

                else:
                    log("Command '{}' ignored (not in the appropriate state)."
                        .format(command), self.name)

            elif command == "come_back_to_grip_instead_of_deciding":
                if self.state == "release_grip_to_decide":
                    self.come_back_to_grip_instead_of_deciding()

                else:
                    log("Command '{}' ignored (not in the appropriate state)."
                        .format(command), self.name)

            elif command == "show_results":

                if self.state == "decide":
                    self.show_results()

                else:
                    log("Command '{}' ignored (not in the appropriate state)."
                        .format(command), self.name)

            else:
                log("ERROR: Message received from GripTracker not understood: '{}'.".format(message), self.name)
                raise Exception("{}: Received message '{}' but did'nt expected anything like that."
                                .format(self.name, message))

        elif message[0] == "timer":

            command, ts, = message[1:]
            log("Received from Timer: '{}' with and ts '{}'.".format(command, ts), self.name)

            if command == "begin_new_block":

                if self.state == "end_block":
                    self.begin_new_block()

                else:
                    log("Command '{}' ignored (not in the appropriate state)."
                        .format(command), self.name)

            elif command == "show_stimuli":

                if self.state == "grasp_before_stimuli_display":
                    self.show_stimuli()

                else:
                    log("Command '{}' ignored (not in the appropriate state)."
                        .format(command), self.name)

            elif command == "did_not_came_back_to_the_grip":

                if self.state == "decide":
                    self.did_not_came_back_to_the_grip()

                else:
                    log("Command '{}' ignored (not in the appropriate state)."
                        .format(command), self.name)

            elif command == "did_not_take_decision":

                if self.state in ["show_stimuli", "release_grip_to_decide"]:
                    self.did_not_take_decision()

                else:
                    log("Command '{}' ignored (not in the appropriate state)."
                        .format(command), self.name)

            elif command == "inter_trial":

                if self.state == "show_results":
                    self.inter_trial()

                else:
                    log("Command '{}' ignored (not in the appropriate state)."
                        .format(command), self.name)

            elif command == "end_trial":

                if self.state in ["inter_trial", "punishment"]:
                    self.end_trial()

                else:
                    log("Command '{}' ignored (not in the appropriate state)."
                        .format(command), self.name)

            elif command == "inter_block":

                if self.state == "reward":
                    self.inter_block()

                else:
                    log("Command '{}' ignored (not in the appropriate state)."
                        .format(command), self.name)

            elif command == "end_block":

                if self.state == "inter_block":
                    self.end_block()

                else:
                    log("Command '{}' ignored (not in the appropriate state)."
                        .format(command), self.name)

            else:
                log("ERROR: Message received from Timer not understood: '{}'.".format(message), self.name)
                raise Exception("{}: Received message '{}' from Timer but did'nt expected anything like that."
                                .format(self.name, message))

        elif message[0] == "gauge_animation":

            if self.state in ["show_results", "reward"]:

                command, kwargs, = message[1:]

                if command == "set_gauge_quantity":
                    self.set_gauge_quantity(**kwargs)

                else:
                    log("ERROR: Message received from GaugeAnimation not understood: '{}'.".format(message), self.name)
                    raise Exception("{}: Received message '{}' from GaugeAnimation "
                                    "but did'nt expected anything like that."
                                    .format(self.name, message))

            else:
                log("Command '{}' ignored (not in the appropriate state)."
                    .format("gauge_animation"), self.name)

        elif message[0] == "interface":

            command = message[1]
            if command == "close_task":
                log("Interface close task.", self.name)
                self.end_game()

            elif command == "close":
                log("Interface close window.", self.name)
                return

            elif command == "run":

                log("Interface run.", self.name)
                parameters = message[2]
                self.prepare_game(parameters=parameters)
            else:
                log("ERROR: Message received from Interface not understood.", self.name)
                raise Exception("{}: Received message '{}' but did'nt expected anything like that."
                                .format(self.name, message))

        else:
            log("ERROR: Message not understood: '{}'.".format(message), self.name)
            raise Exception("{}: Received message '{}' but did'nt expected anything like that."
                            .format(self.name, message))

    def ask_interface(self, instruction):

        assert type(instruction) == tuple, "Instruction is not in the right type."
        self.queues["interface"].put(instruction)
        self.communicant.signal.emit()


# ------------------------------------ START AND END GAME ---------------------------------------------------------- #

    def prepare_game(self, parameters):

        self.parameters = parameters

        # Show 'trial counter' on interface window
        self.ask_interface(("show_progression_bar", ))

        if self.parameters["fake"]:
            self.ask_interface(("track_fake_grip", ))

        else:

            self.connect_grip_and_valve()

        # Tell to stimuli generator parameters to use
        self.stimuli_finder.set_parameters(
            control_trials_proportion=self.parameters["control_trials_proportion"],
            with_losses_proportion=self.parameters["with_losses_proportion"],
            incongruent_proportion=self.parameters["incongruent_proportion"]
        )

        # Ask interface to show pause screen and trial counter
        self.ask_interface(("prepare_game", ))

        # Reinitialize
        self.to_save = []
        self.trial_counter = [0, 0]
        self.n_block = 0

    def connect_grip_and_valve(self):

        if not self.client.is_connected():

            while not self.shutdown.is_set():
                connected = self.client.establish_connection()
                if connected:
                    break
                else:
                    self.waiting_event.wait(0.5)

            if not self.shutdown.is_set():
                self.valve_manager.start()
                self.grip_manager.start()
                self.ttl_manager.start()

    def play_game(self):

        log("Play game.", self.name)

        # Begin a new block of trials
        self.begin_new_block()

    def end_game(self):

        log("NEW STATE -> End game.", self.name)

        # Update state
        self.state = "end_game"

        # Stop the grip tracker
        self.grip_tracker.cancel()

        # Stop all the timers
        self.timer.cancel(debug="Coming from 'end_game'")
        self.gauge_animation.cancel()

        # Update display on game window
        self.ask_interface(("prepare_next_run", ))

        # Save the session (database)
        if self.parameters and self.parameters["save"]:

            self.save_session()

# ------------------------------------ START AND END BLOCK ---------------------------------------------------------- #

    def begin_new_block(self):

        log("NEW STATE -> Start new block.", self.name)

        # Update state
        self.state = "new_block"

        # Reinitialize
        self.n_trial_inside_block = 0
        self.time_stamp_inter_block_interval_onset = -1
        self.time_inter_block = -1
        self.gauge_level = self.parameters["initial_stock"]

        # Update display of game window
        self.ask_interface(("set_gauge_quantity_and_color", self.gauge_level, "black"))

        # Launch new trial
        self.begin_new_trial()

    def reward(self):

        log("NEW STATE -> Reward.", self.name)

        # Update state
        self.state = "reward"

        # After time for rewarding, launch new block
        reward_time = self.parameters["reward_time"] / 1000
        self.timer.launch(time=reward_time, msg="inter_block")

        # Launch vending animation
        self.venting_gauge_animation()

    def end_block(self):

        # Save trial (on RAM)
        if self.parameters["save"] == 1:
            self.save_trial()

        # Upgrade counter
        self.n_block += 1

        self.begin_new_block()

# ------------------------------------ START AND END TRIAL ---------------------------------------------------------- #

    def begin_new_trial(self):

        log("NEW STATE -> New trial.", self.name)

        # Update state
        self.state = "new_trial"

        # Reinitialize
        self.error = None
        self.time_reaction = -1
        self.time_movement = -1
        self.time_back_movement = -1
        self.time_inter_trial = -1
        self.time_fixation = -1

        self.time_stamp_grip_onset = -1
        self.time_stamp_release_grip = -1
        self.time_stamp_cue_onset = -1
        self.time_stamp_cue_contact = -1
        self.time_stamp_result_period_onset = -1
        self.time_stamp_reward_period_onset = -1
        self.time_stamp_inter_trial_interval_onset = -1

        # Update display on game window
        self.ask_interface(("show_gauge", ))

        # Prepare stimuli for future use
        self.set_stimuli_parameters()

        # Launch next step: wait for the user to grasp the grip
        self.wait_for_grasping()

    def end_trial(self):

        log("NEW STATE -> End of trial.", self.name)

        # Update trial counters
        self.trial_counter[0] += 1
        if self.error is None:

            self.trial_counter[1] += 1  # One trial more without errors
            self.n_trial_inside_block += 1  # Increment the number of made trials inside the same block

        # Update display on graphic interface
        self.ask_interface(("set_trial_counter", self.trial_counter))

        # If no error, continue
        if self.error is None:

            # If it is not the end of the block
            if self.n_trial_inside_block % self.parameters["trials_per_block"]:
                # Save trial (on RAM)
                if self.parameters["save"] == 1:
                    self.save_trial()
                self.begin_new_trial()

            else:
                self.reward()  # Saving will be at the end of the block

        # If there is an error, begin a new block
        else:
            self.end_block()

# ------------------------------------ SUB-STEPS OF TASK ---------------------------------------------------------- #

    def wait_for_grasping(self):

        log("NEW STATE -> Wait for grasping.", self.name)

        # Update state
        self.state = "wait_for_grasping"

        already_hold = self.queues["grip_value"].value == 1

        # If user holds already the grip, go directly to next step
        if already_hold:
            log("Grip already hold by user.", self.name)
            self.grasp_before_stimuli_display()

        # Otherwise wait for him to do it
        else:
            self.grip_tracker.launch(msg="grasp_before_stimuli_display")

    def grasp_before_stimuli_display(self):

        log("NEW STATE -> Grasp before stimuli display.", self.name)

        # Update state
        self.state = "grasp_before_stimuli_display"

        print("*********************** TTL GRASP *******************************")

        if self.n_block == 0 and self.n_trial_inside_block == 0:
            self.time_reference = time()
            self.time_stamp_grip_onset = 0

        else:
            self.time_stamp_grip_onset = time() - self.time_reference

        # Inform recording system
        self.ttl_manager.send_signal()

        # # Observe if the user holds the grip for a certain time, otherwise do what is appropriate
        self.grip_tracker.launch(msg="release_before_end_of_fixation_time")

        # # Launch a new timer: if user holds the grip, show the stimuli
        self.time_fixation = np.random.randint(
            self.parameters["fixation_time"][0], self.parameters["fixation_time"][1]
        ) / 1000

        self.timer.launch(time=self.time_fixation, msg="show_stimuli")

    def show_stimuli(self):

        log("NEW STATE -> Show stimuli.", self.name)

        # Update state
        self.state = "show_stimuli"

        # Stop grip tracker whose purpose was to rise an error if user has release the grip
        self.grip_tracker.cancel()

        print("*********************** TTL STIMULI *******************************")

        self.time_stamp_cue_onset = time() - self.time_reference

        # Inform recording system
        self.ttl_manager.send_signal()

        # Update display on game window
        self.ask_interface(("show_stimuli", ))

        # Launch new timer: after maximum time to decide, if no action took place, do what is appropriated.
        max_decision_time = self.parameters["max_decision_time"] / 1000
        self.timer.launch(msg="did_not_take_decision", time=max_decision_time)

        # # Observe if the user holds the grip for a certain time, otherwise do what is appropriate
        self.grip_tracker.launch(msg="release_grip_to_decide")

    def release_grip_to_decide(self):

        # Update state
        self.state = "release_grip_to_decide"

        log("NEW STATE -> Release grip to decide.", self.name)

        print("*********************** TTL RELEASE GRIP *******************************")

        self.time_stamp_release_grip = time() - self.time_reference

        # Inform recording system
        self.ttl_manager.send_signal()

        self.grip_tracker.launch(msg="come_back_to_grip_instead_of_deciding")

        self.time_reaction = self.time_stamp_release_grip - self.time_stamp_cue_onset

    def decide(self, choice):

        log("NEW STATE -> Decide.", self.name)

        # Update state
        self.state = "decide"

        # Stop previous timer for which the purpose was to raise an error if user did'nt took a decision
        self.timer.cancel()

        # Cancel grip tracker
        self.grip_tracker.cancel()

        print("*********************** TTL DECIDE *******************************")

        self.time_stamp_cue_contact = time() - self.time_reference

        # Inform recording system
        self.ttl_manager.send_signal()

        # Save choice
        self.choice = choice

        # Update display on game window
        self.ask_interface(("show_choice", choice))

        # Launch new timer: limit for coming back to the grip
        max_return_time = self.parameters["max_return_time"] / 1000
        self.timer.launch(msg="did_not_came_back_to_the_grip", time=max_return_time)

        # Launch grip detector: If grip state change, results will be displayed
        self.grip_tracker.launch(msg="show_results")

        # Measure movement time
        self.time_movement = self.time_stamp_cue_contact - self.time_stamp_release_grip

    def show_results(self):

        log("NEW STATE -> Show results.", self.name)

        # Update state
        self.state = "show_results"

        # Stop previous timer whose purpose was to raise an error if user didn't come back
        self.timer.cancel()

        # Prepare results
        self.set_results()

        print("*********************** TTL RESULTS *******************************")

        self.time_stamp_result_period_onset = time() - self.time_reference

        # Inform recording system
        self.ttl_manager.send_signal()

        # Update display on game window
        self.ask_interface(("show_results", ))

        # Launch new timer: after time for displaying results, launch inter-trial
        results_display_time = self.parameters["result_display_time"] / 1000
        self.timer.launch(msg="inter_trial", time=results_display_time)

        # Start animation for filling up the gauge
        self.filling_gauge_animation()

        # Measure time for coming back to the grip
        self.time_back_movement = self.time_stamp_result_period_onset - self.time_stamp_cue_contact

    def inter_trial(self):

        log("NEW STATE -> Inter-trial.", self.name)

        # Update state
        self.state = "inter_trial"

        # Update display on game window
        self.ask_interface(("show_gauge", ))

        if self.parameters["inter_trial_time"][1] > 0:

            # Inform recording system
            print("*********************** TTL INTERTRIAL *******************************")

            self.time_stamp_inter_trial_interval_onset = time() - self.time_reference

            self.ttl_manager.send_signal()

            # Launch new timer: after time for inter-trial, go to end of the trial
            self.time_inter_trial = np.random.randint(
                self.parameters["inter_trial_time"][0],
                self.parameters["inter_trial_time"][1])\
                / 1000

            self.timer.launch(msg="end_trial", time=self.time_inter_trial)

        else:
            self.time_inter_trial = 0
            self.end_trial()

    def inter_block(self):

        log("NEW STATE -> Inter-block.", self.name)

        # Update state
        self.state = "inter_block"

        # Update display on game window
        self.ask_interface(("show_gauge", ))

        if self.parameters["inter_block_time"][1] > 0:

            print("*********************** TTL INTERBLOCK*******************************")

            self.time_stamp_inter_block_interval_onset = time() - self.time_reference

            # Inform recording system
            self.ttl_manager.send_signal()

            # Launch new timer: after time for inter-trial, go to end of the trial
            self.time_inter_block = np.random.randint(
                self.parameters["inter_block_time"][0],
                self.parameters["inter_block_time"][1])\
                / 1000

            self.timer.launch(msg="end_block", time=self.time_inter_block)
        else:
            self.time_inter_block = 0
            self.end_block()

# ----------------------------------------- GAUGE ANIMATION ------------------------------------------------------ #

    def filling_gauge_animation(self):

        results_display_time = self.parameters["result_display_time"] / 1000
        reward = self.stimuli_parameters["{}_x{}".format(self.choice, self.dice_output)]

        if reward > 0:
            sound = "reward"
            sequence = self.gauge_level + np.arange(1, reward + 1)

        elif reward < 0:
            sound = "loss"
            sequence = self.gauge_level + np.arange(-1, reward - 1, -1)

        else:
            sequence = None
            sound = None

        if sequence is not None:
            self.gauge_animation.launch(
                total_time=results_display_time,
                maximum=self.stimuli_finder.maximum_x,
                sound=sound, sequence=sequence, water=False
            )

        self.gauge_level += reward

    def venting_gauge_animation(self):

        print("*********************** TTL VENTING *******************************")

        self.time_stamp_reward_period_onset = time() - self.time_reference

        # Inform recording system
        self.ttl_manager.send_signal()

        self.ask_interface(("set_gauge_color", "blue"))

        reward_time = self.parameters["reward_time"] / 1000

        reward = self.gauge_level

        if reward > 0:
            sequence = self.gauge_level + np.arange(-1, -(reward + 1), -1)

        else:
            sequence = None

        if sequence is not None:
            self.gauge_animation.launch(
                total_time=reward_time,
                maximum=self.stimuli_finder.gauge_maximum,
                sound="reward", sequence=sequence, water=True,
            )

    def set_gauge_quantity(self, **kwargs):

        self.ask_interface(("set_gauge_quantity", kwargs["quantity"], kwargs["sound"]))

        if "water" in kwargs and kwargs["water"] is True:
            if not self.parameters["fake"]:
                self.valve_manager.open(self.parameters["valve_opening_time"])
            else:
                log("FakeValveManager: GIVE WATER.", self.name)


# ----------------------------------------- STIMULI & RESULTS ---------------------------------------------------- #

    def set_stimuli_parameters(self):

        self.stimuli_parameters = self.stimuli_finder.find()

        self.ask_interface(("set_stimuli_parameters", self.stimuli_parameters))

    def set_results(self):

        p = self.stimuli_parameters["{}_p".format(self.choice)]
        r = np.random.random()
        self.dice_output = int(r > p)
        self.ask_interface(("set_dice_output", self.dice_output))

    # ----------------------------------------- ERRORS --------------------------------------------------------------- #

    def punish(self):
        log("NEW STATE -> Punishment.", self.name)

        # Update state
        self.state = "punishment"

        # Update display on game window
        self.ask_interface(("show_black_screen",))

        # After punishment time, go to end of trial
        punishment_time = self.parameters["punishment_time"] / 1000
        self.timer.launch(msg="end_trial", time=punishment_time, debug="Coming from punishment")

    def release_before_end_of_fixation_time(self):
        log("Release grip before the end of the fixation time.", self.name)

        # Cancel timer leading to 'show stimuli'.
        self.timer.cancel(debug="Don't show stimuli")

        self.error = "release before end of fixation time"
        self.punish()

    def did_not_release_grip_to_decide(self):
        log("Did not release grip to decide.", self.name)

        self.grip_tracker.cancel()
        self.timer.cancel()

        self.error = "did not release grip to decide"
        self.punish()

    def come_back_to_grip_instead_of_deciding(self):
        log("Come back to grip instead of deciding.", self.name)

        self.timer.cancel()

        self.error = "come back to grip instead of deciding"
        self.punish()

    def did_not_take_decision(self):
        log("Did not take a decision.", self.name)

        self.grip_tracker.cancel()

        self.error = "too long to take a decision"
        self.punish()

    def did_not_came_back_to_the_grip(self):
        log("Did not came back to the grip.", self.name)

        self.grip_tracker.cancel()

        self.time_back_movement = -1

        self.error = "did not came back to the grip"
        self.punish()


# ------------------------------------- SAVE -------------------------------------------------------------------- #

    def save_trial(self):

        to_save = \
            {
                "error": self.error,
                "choice": self.choice,
                "dice_output": self.dice_output,
                "gauge_level": self.gauge_level,
                "n_trial_inside_block": self.n_trial_inside_block - 1, # Saving function is called after increasing n
                "n_block": self.n_block,
                "time_reaction": int(self.time_reaction * 1000),
                "time_movement": int(self.time_movement * 1000),
                "time_back_movement": int(self.time_back_movement * 1000),
                "time_inter_trial": int(self.time_inter_trial * 1000),
                "time_inter_block": int(self.time_inter_block * 1000),
                "time_fixation": int(self.time_fixation * 1000),
                "time_stamp_grip_onset": int(self.time_stamp_grip_onset * 1000),
                "time_stamp_release_grip": int(self.time_stamp_release_grip * 1000),
                "time_stamp_cue_onset": int(self.time_stamp_cue_onset * 1000),
                "time_stamp_cue_contact": int(self.time_stamp_cue_contact * 1000),
                "time_stamp_result_period_onset": int(self.time_stamp_result_period_onset * 1000),
                "time_stamp_reward_period_onset": int(self.time_stamp_reward_period_onset * 1000),
                "time_stamp_inter_block_interval_onset": int(self.time_stamp_inter_block_interval_onset * 1000),
                "time_stamp_inter_trial_interval_onset": int(self.time_stamp_inter_trial_interval_onset * 1000),
            }
        to_save.update(self.stimuli_parameters)
        self.to_save.append(to_save)

    def save_session(self):

        # In case of trying to end program
        self.data_saved.clear()
        self.current_saving.set()

        log("SAVE SESSION.", self.name)

        self.parameters.pop("save")

        if len(self.to_save) < 1:
            log("No trials to save.", self.name)
            self.current_saving.clear()
            self.data_saved.set()
            return

        else:
            log("{} trials to save.".format(len(self.to_save)), self.name)

        database = Database()
        summary_table_name = "summary"

        # Verify if a summary table exists, otherwise, create it
        if not database.table_exists(summary_table_name):

            columns = OrderedDict()

            # Add columns for date and name of session table
            columns["date"] = str
            columns["session_table"] = str

            # Add a column for every parameter in parameter dic
            for key, value in sorted(self.parameters.items()):
                columns[key] = type(value)
            database.create_table(
                table_name=summary_table_name,
                columns=columns)

            log("Summary table created.", self.name)

        else:
            log("Summary table already exists.", self.name)

        # Create a session table
        log("Create session table.", self.name)
        monkey = self.parameters["monkey"]
        session_table_name = "session_{}_{}".format(str(date.today()).replace("-", "_"), monkey)
        if database.table_exists(table_name=session_table_name):

            log("Session table with name {} already exists.".format(session_table_name), self.name)

            idx = 2
            session_table_name += "({})".format(idx)
            while database.table_exists(table_name=session_table_name):
                log("Session table with name {} already exists.".format(session_table_name), self.name)
                session_table_name = session_table_name.replace("({})".format(idx), "({})".format(idx+1))
                idx += 1

        columns = OrderedDict()
        for key, value in sorted(self.to_save[0].items()):
            columns[key] = type(value)

        database.create_table(
            table_name=session_table_name,
            columns=columns
        )

        log("Session table created with name {}.".format(session_table_name), self.name)

        # Fill summary table
        database.fill_table(summary_table_name, **self.parameters, date=str(date.today()),
                            session_table=session_table_name)

        # Fill session table
        for i in range(len(self.to_save)):
            database.fill_table(session_table_name, **self.to_save[i])

        log("DATA SAVED.", self.name)

        self.current_saving.clear()
        self.data_saved.set()
