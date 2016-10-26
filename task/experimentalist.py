from PyQt5 import QtCore
from multiprocessing import Queue
import numpy as np
from threading import Timer
from multiprocessing import Value, Event
from collections import OrderedDict
from task.save import Database
from datetime import date
from task.ressources import GripManager, ValveManager, ConnectionToRaspi, GripTracker, SoundManager


class Experimentalist(QtCore.QThread, QtCore.QObject):

    trigger = QtCore.pyqtSignal()
    # trigger_with_args = QtCore.pyqtSignal(dict)

    def __init__(self, game_window, interface_window, graphic_queue):

        super(Experimentalist, self).__init__()

        self.game_window = game_window
        self.interface_window = interface_window

        self.graphic_queue = graphic_queue

        self.grip_queue = Queue()
        self.grip_value = Value('i')

        self.valve_queue = Queue()

        self.shutdown = Event()

        self.grip_tracker = GripTracker(
            change_queue=self.grip_queue
        )

        # --------- PROCESS FOR GRIP AND VALVE --- #

        self.connection_to_raspi = ConnectionToRaspi(raspi_address='169.254.162.142')

        self.grip_manager = GripManager(
            grip_state=self.grip_value, grip_change=self.grip_queue)

        self.valve_manager = ValveManager(
            valve_opening=self.valve_queue
        )

        # -------- SOUND --------- #

        self.sound_manager = SoundManager(n_sound_thread=8)

        # -------- PARAMETERS --------- #

        self.parameters = None

        self.task_running = False

        # ------- FOR FUTURE SAVING ---- #
        self.choice = None

        self.timer = None

        self.gauge_level = 0

        self.stimuli_parameters = {}
        self.to_save = []
        self.error = None

        self.dice_output = 0

        # ------- TRIAL COUNTERS ------ #

        self.trial_counter = [0, 0]

        self.n_trial_inside_block = 0

        self.n_block = 0

        # ------ INIT ------ #

        self.initialize()

# ------------------------ INIT ------------------------------------- #

    def initialize(self):

        self.grip_tracker.start()
        self.sound_manager.start()

    def run(self):

        print("Experimentalist: Run.")
        # Show graphic interface
        self.command(self.interface_window.show)

        self.wait_for_graphic_msg()

# ----------------------------- GET EVENTS FROM GRAPHIC INTERFACE ----------------------------------------------- #

    def wait_for_graphic_msg(self):

        print("Experimentalist: Wait for graphic msg.")

        graphic_msg = self.graphic_queue.get()

        if graphic_msg[0] == "game_close_window":

            print("Experimentalist: Game close window.")
            self.end_game()

        elif graphic_msg[0] == "interface_close_task":

            print("Experimentalist: Interface close task.")
            self.end_game()

        elif graphic_msg[0] == "interface_close_window":

            print("Experimentalist: Interface close window.")
            self.end_program()
            return

        elif graphic_msg[0] == "interface_run":

            print("Experimentalist: Interface run.")
            # Get parameters from graphic interface
            self.parameters = graphic_msg[1]

            self.prepare_game()

        elif graphic_msg[0] == "game_play":

            print("Experimentalist: Game play.")
            self.play_game()

        elif graphic_msg[0] == "game_left":

            print("Experimentalist: choice left.")
            self.decide("left")

        elif graphic_msg[0] == "game_right":

            print("Experimentalist: choice right.")
            self.decide("right")

        else:
            print("ERROR: msg from graphics not understood.")

        self.wait_for_graphic_msg()

# ------------------------------------------- TOOLS ---------------------------------------------------------- #

    def command(self, function):

        self.trigger.connect(function)
        self.trigger.emit()

# --------------------------------------- END PROGRAM ------------------------------------------------------------ #

    def end_program(self):

        self.grip_tracker.end()
        self.grip_manager.end()
        self.valve_manager.end()
        self.sound_manager.end()
        self.connection_to_raspi.end()
        self.game_window.standalone = True
        self.command(self.game_window.close)
        self.command(self.interface_window.close)

# ------------------------------------ START AND END GAME ---------------------------------------------------------- #

    def prepare_game(self):

        # Show 'trial counter' on interface window
        self.command(self.interface_window.show_progression_bar)

        if self.parameters["fake"]:
            self.game_window.track_fake_grip(queue=self.grip_queue, value=self.grip_value)
        else:
            if not self.connection_to_raspi.is_connected():
                self.connection_to_raspi.connect()
            if not self.valve_manager.isRunning():
                self.valve_manager.start()
            if not self.grip_manager.isRunning():
                self.grip_manager.start()

        # Show 'pause screen' on game window
        self.game_window.current_step = "show_pause_screen"
        self.command(self.game_window.show)

        # Show 'trial counter' on interface window
        self.command(self.interface_window.show_trial_counter)

    def play_game(self):

        print('Experimentalist: PLAY GAME.')

        self.sound_manager.play("start")
        self.to_save = []

        self.n_block = 0

        self.begin_new_block()

    def end_game(self):

        self.grip_tracker.cancel()

        self.command(self.game_window.hide)
        self.game_window.current_step = "show_pause_screen"
        self.command(self.interface_window.prepare_next_run)

        if self.parameters["save"]:

            self.save_session()

# ------------------------------------ START AND END BLOCK ---------------------------------------------------------- #

    def begin_new_block(self):

        print("Experimentalist: Start new block.")

        self.game_window.set_gauge_color(color="black")

        self.n_trial_inside_block = 0

        self.gauge_level = self.parameters["initial_stock"]
        self.game_window.set_gauge_quantity(quantity=self.gauge_level)
        self.begin_new_trial()

    def end_block(self):

        self.n_block += 1

        self.venting_gauge_animation()

        reward_time = self.parameters["reward_time"] / 1000
        inter_trial_time = np.random.randint(
            self.parameters["inter_trial_time"][0], self.parameters["inter_trial_time"][1]) / 1000

        Timer(inter_trial_time+reward_time, self.begin_new_block).start()

# ------------------------------------ START AND END TRIAL ---------------------------------------------------------- #

    def begin_new_trial(self):

        self.game_window.current_step = "show_gauge"

        self.error = None

        self.set_stimuli_parameters()
        self.wait_for_grasping()

    def end_trial(self):

        print("Experimentalist: End of trial.")

        if self.parameters["save"] == 1:
            self.save_trial()

        # Update trial counters
        self.trial_counter[0] += 1
        if self.error is None:

            self.trial_counter[1] += 1
            self.n_trial_inside_block += 1

        else:
            self.n_trial_inside_block = 0

        # Update display on graphic interface
        self.interface_window.trial_counter.set_trial_number(self.trial_counter)

        # If no error, continue
        if self.error is None:

            if self.n_trial_inside_block % self.parameters["trials_per_block"]:
                self.begin_new_trial()
            else:
                self.end_block()
                
        # Otherwise, begin a new block
        else:
            self.begin_new_block()

# ------------------------------------ SUB-STEPS OF TASK ---------------------------------------------------------- #

    def wait_for_grasping(self):

        if self.grip_value.value == 0:

            print("Experimentalist: WAIT FOR GRASPING.")

            self.grip_tracker.launch(
                handling_function=self.grasp_before_stimuli_display,
                msg="Go signal from wait_for_grasping")
        else:
            self.grasp_before_stimuli_display()

    def grasp_before_stimuli_display(self):

        print("Experimentalist: GRASP BEFORE STIMULI DISPLAY.")

        self.grip_tracker.launch(
            handling_function=self.release_before_end_of_fixation_time,
            msg="go signal from grasp before stimuli display")

        fixation_time = np.random.randint(
            self.parameters["fixation_dot_time"][0], self.parameters["fixation_dot_time"][1]) / 1000

        self.timer = Timer(fixation_time, self.show_stimuli)
        self.timer.start()

    def release_before_end_of_fixation_time(self):

        print("Experimentalist: release.")
        self.timer.cancel()

        self.error = "release before end of fixation time"
        self.punish()

    def punish(self):

        print("Experimentalist: PUNISH.")

        self.sound_manager.play("punishment")

        self.game_window.current_step = "show_black_screen"

        punishment_time = self.parameters["punishment_time"] / 1000
        Timer(punishment_time, self.end_trial).start()

    def show_stimuli(self):

        # Stop grip tracker
        self.grip_tracker.cancel()
        self.game_window.current_step = "show_stimuli"

        max_decision_time = self.parameters["max_decision_time"] / 1000
        self.timer = Timer(max_decision_time, self.did_not_take_decision)
        self.timer.start()

    def did_not_take_decision(self):

        print("Experimentalist: did not take a decision.")
        self.error = "too long to take a decision"
        self.punish()

    def decide(self, choice):

        self.sound_manager.play("choice")

        # Stop previous timer
        self.timer.cancel()

        self.choice = choice

        self.game_window.set_choice(choice=choice)

        self.game_window.current_step = "show_choice"

        # Launch new timer
        max_return_time = self.parameters["max_return_time"] / 1000
        self.timer = Timer(max_return_time, self.punish)
        self.timer.start()

        # Launch grip detector
        self.grip_tracker.launch(handling_function=self.show_results, msg="Add results if grip touched")

    def show_results(self):

        # Stop previous timer
        self.timer.cancel()

        # Prepare results
        self.set_results()

        self.game_window.current_step = "show_results"

        self.game_window.set_choice(choice=self.choice)

        results_display_time = self.parameters["result_display_time"] / 1000
        Timer(results_display_time, self.inter_trial).start()

        self.filling_gauge_animation()

    def inter_trial(self):

        self.game_window.current_step = "show_gauge"

        inter_trial_time = np.random.randint(
            self.parameters["inter_trial_time"][0],
            self.parameters["inter_trial_time"][1])\
            / 1000
        Timer(inter_trial_time, self.end_trial).start()

# ----------------------------------------- GAUGE ANIMATION ------------------------------------------------------ #

    def filling_gauge_animation(self):

        results_display_time = self.parameters["result_display_time"] / 1000

        reward = self.stimuli_parameters["{}_x{}".format(self.choice, self.dice_output)]

        time_per_unity = results_display_time / (reward + 1)

        if reward > 0:
            sound = "reward"
            sequence = np.arange(1, reward + 1)

        elif reward < 0:
            sound = "loss"
            sequence = np.arange(1, reward + 1)

        else:
            sequence = []
            sound = None

        for i in sequence:

            Timer(time_per_unity*np.absolute(i), self.set_gauge_quantity,
                  kwargs={"quantity": self.gauge_level + i,
                          "sound": sound}).start()

        self.gauge_level += reward

    def venting_gauge_animation(self):

        self.game_window.set_gauge_color(color="blue")

        reward_time = self.parameters["reward_time"] / 1000

        reward = self.gauge_level

        time_per_unity = reward_time / (reward + 1)

        if reward > 0:

            sequence = np.arange(1, reward + 1)

        else:
            sequence = []

        for i in sequence:

            Timer(time_per_unity*np.absolute(i), self.set_gauge_quantity,
                  kwargs={"quantity": self.gauge_level - i,
                          "sound": "reward"}).start()

    def set_gauge_quantity(self, **kwargs):

        self.game_window.set_gauge_quantity(quantity=kwargs["quantity"])
        self.sound_manager.play(sound=kwargs["sound"])


# ----------------------------------------- STIMULI & RESULTS ---------------------------------------------------- #

    def set_stimuli_parameters(self):

        self.stimuli_parameters = {
            "left_p": 0.25,
            "left_x0": 3,
            "left_x1": 0,
            "left_beginning_angle": 5,
            "right_p": 1,
            "right_x0": 4,
            "right_x1": 0,
            "right_beginning_angle": 140
        }

        self.game_window.set_parameters(self.stimuli_parameters)

    def set_results(self):

        p = self.stimuli_parameters["{}_p".format(self.choice)]
        r = np.random.random()
        self.dice_output = int(r > p)
        self.game_window.set_dice_output(self.dice_output)


# ------------------------------------- SAVE -------------------------------------------------------------------- #

    def save_trial(self):

        to_save = \
            {
                "error": self.error,
                "choice": self.choice,
                "dice_output": self.dice_output,
                "n_trial_inside_block": self.n_trial_inside_block,
                "n_block": self.n_block
            }
        to_save.update(self.stimuli_parameters)
        self.to_save.append(to_save)

    def save_session(self):

        print("Experimentalist: SAVE SESSION.")

        self.parameters.pop("save")

        if len(self.to_save) < 1:
            return

        database = Database()
        summary_table_name = "summary"
        if not database.table_exists(summary_table_name):

            print("Experimentalist: Create new summary table.")

            columns = OrderedDict()
            for key, value in self.parameters.items():
                columns[key] = type(value)
            database.create_table(
                table_name=summary_table_name,
                columns=columns)
        print("Experimentalist: Summary table already exists.")

        print("Experimentalist: Create session table.")
        monkey = self.parameters["monkey"]
        session_table_name = "session_{}_{}".format(str(date.today()).replace("-", "_"), monkey)
        if database.table_exists(table_name=session_table_name):

            print("Experimentalist: Session table with name {} already exists.".format(session_table_name))

            idx = 1
            session_table_name += "_n{}".format(idx)
            while database.table_exists(table_name=session_table_name):
                print("Experimentalist: Session table with name {} already exists.".format(session_table_name))
                session_table_name = session_table_name.replace("n{}".format(idx), "n{}".format(idx+1))
                idx += 1

        print("Experimentalist: I create session table with name {}.".format(session_table_name))

        columns = OrderedDict()
        for key, value in self.to_save[0].items():
            columns[key] = type(value)

        database.create_table(
            table_name=session_table_name,
            columns=columns
        )

        database.fill_table(summary_table_name, **self.parameters)
        for i in range(len(self.to_save)):
            database.fill_table(session_table_name, **self.to_save[i])

        print("Experimentalist: DATA SAVED.")





