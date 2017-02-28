from multiprocessing import Event, Queue
from threading import Timer, Thread
from PyQt5.QtCore import Qt
from time import time
import queue
import numpy as np
from save.save import BackUp
from collections import OrderedDict


class MyTimer(object):

    def __init__(self, signal):

        super(MyTimer, self).__init__()

        self.signal = signal  # multiprocessing.Queue

        self.end = Event()

        self.interval = None
        self.should_end = None
        self.clock_timer = None

    def start(self, interval, should_end=1):

        self.end.clear()

        self.clock_timer = Timer(interval/1000., self.target)
        self.should_end = should_end
        print("Beginning Timer.")
        self.clock_timer.start()

    def target(self):

        self.end.set()

        if self.should_end == 1:

            self.signal.put(1)

        else:

            self.signal.put(0)
        print("End Timer.")

    def cancel(self):

        self.clock_timer.cancel()

        print("End Timer (cancelled).")


class Check(Thread):

    def __init__(self, launch, shutdown):

        Thread.__init__(self)
        self.shutdown = shutdown
        self.launch = launch
        self.name = np.random.randint(0, 500)

    def run(self):

        print("Checker {}: BEGIN.".format(self.name))

        while not self.shutdown.is_set():
            self.launch.wait()
            if not self.shutdown.is_set():
                self.do_tasks()
                self.launch.clear()

        print("Checker {}: DEAD.".format(self.name))

    def do_tasks(self):

        pass


class CheckGrasping(Check):

    def __init__(self, grip_state, launch, timer, signal, shutdown):
        super(CheckGrasping, self).__init__(launch=launch, shutdown=shutdown)

        self.grip_state = grip_state
        self.timer = timer
        self.signal = signal

    def do_tasks(self):

        print("Beginning CheckGrasping.")
        while not self.timer.end.is_set():

            if self.grip_state.value != 1:

                self.timer.cancel()
                self.signal.put(0)
                break
        print("End CheckGrasping")


class DecisionTracker(Check):

    def __init__(self, choice_queue, choice, timer, signal, launch, shutdown):

        super(DecisionTracker, self).__init__(launch=launch, shutdown=shutdown)

        self.choice_queue = choice_queue
        self.choice = choice

        self.timer = timer
        self.signal = signal

    def do_tasks(self):

        print("Begin DecisionTracker.")

        # Empty choice queue
        while not self.choice_queue.empty():

            self.choice_queue.get()

        while not self.timer.end.is_set():
            try:
                choice = self.choice_queue.get(timeout=1.)
                if choice in ["left", "right"]:
                    self.timer.cancel()
                    self.signal.put(1)
                    self.choice.value = choice.encode()
                    break
            except queue.Empty:
                pass
        self.launch.clear()

        print("End DecisionTracker.")


class ComingBackTracker(Check):

    def __init__(self, grip_change, timer, signal, launch, shutdown):

        super(ComingBackTracker, self).__init__(launch=launch, shutdown=shutdown)

        self.grip_change = grip_change
        self.timer = timer
        self.signal = signal

    def do_tasks(self):

        while not self.grip_change.empty():
            self.grip_change.get()

        print("Begin ComingBackTracker.")

        while not self.timer.end.is_set():

            try:
                change = self.grip_change.get(timeout=1.)
                if change == 1:
                    self.timer.cancel()
                    self.signal.put(1)
                    break
            except queue.Empty:
                pass

        self.launch.clear()

        print("End ComingBackTracker.")


class Experimentalist(Thread):

    def __init__(self,
                 current_frame,
                 grip_state,
                 grip_change,
                 valve_opening,
                 choice_queue,
                 choice,
                 stimuli_parameters,
                 dice_output,
                 sound_instruction,
                 task_parameters_queue,
                 display,
                 general_shutdown,
                 shutdown_event,
                 keys,
                 keyboard_queue,
                 keyboard_queue_for_fake_grip,
                 confirmation_opening_window,
                 trial_queue,
                 graphic_parameters):

        super(Experimentalist, self).__init__()

        self.grip_state = grip_state
        self.grip_change = grip_change
        self.valve_opening = valve_opening

        self.sound_instruction = sound_instruction

        self.task_parameters_queue = task_parameters_queue

        self.task_parameters = None
        self.graphic_parameters = graphic_parameters

        self.shutdown_event = shutdown_event
        self.general_shutdown_event = general_shutdown

        self.current_frame = current_frame

        self.choice_queue = choice_queue
        self.choice = choice
        self.stimuli_parameters = stimuli_parameters

        self.stimuli_parameters_finder = StimuliParametersFinder(stimuli_parameters)

        self.confirmation_opening_window = confirmation_opening_window

        self.keyboard_queue = keyboard_queue
        self.keyboard_queue_for_fake_grip = keyboard_queue_for_fake_grip
        self.keys = keys

        self.trial_queue = trial_queue

        self.trial_n = 0
        self.trial_n_without_errors = 0

        self.trial = 0
        self.trial_error = None
        self.trial_dot_fixation_time = None
        self.trial_decision_time = None
        self.trial_return_time = None
        self.trial_inter_trial_time = None

        self.circle_size = None
        self.dice_output = dice_output

        self.reward_amount = None
        self.condition = None

        self.expected_value = None

        self.data = []

        self.trial_results = OrderedDict()

        self.display = display

        self.signal = Queue()

        self.timer = MyTimer(signal=self.signal)

        self.check_grasping_launcher = Event()
        self.check_grasping = CheckGrasping(
            grip_state=self.grip_state,
            launch=self.check_grasping_launcher,
            shutdown=self.general_shutdown_event,
            signal=self.signal,
            timer=self.timer)

        self.decision_tracker_launcher = Event()
        self.decision_tracker = DecisionTracker(
            choice=self.choice,
            choice_queue=self.choice_queue,
            launch=self.decision_tracker_launcher,
            shutdown=self.general_shutdown_event,
            signal=self.signal,
            timer=self.timer)

        self.coming_back_tracker_launcher = Event()
        self.coming_back_tracker = ComingBackTracker(
            grip_change=self.grip_change,
            launch=self.coming_back_tracker_launcher,
            shutdown=self.general_shutdown_event,
            signal=self.signal,
            timer=self.timer)

    def run(self):

        self.check_grasping.start()
        self.decision_tracker.start()
        self.coming_back_tracker.start()

        while not self.general_shutdown_event.is_set():

            self.reset_trial_count()

            self.task_parameters = self.task_parameters_queue.get()

            if self.task_parameters:

                print("*" * 10)
                print("Experimentalist: Game begins!")
                print("*" * 10)

                self.open_window()

                press_on_start = self.pause()

                if press_on_start:

                    if self.task_parameters["save"] == 1:

                        self.prepare_session_saving()

                    self.graphic_parameters["circle_size"] = self.task_parameters["circle_size"]

                    self.sound_instruction.put("start")

                    while not self.shutdown_event.is_set():

                        print("****** NEW TRIAL ******")

                        self.prepare_trial_saving()

                        self.do_task()

                        if self.task_parameters["save"] == 1:
                            self.save_trial()

                        self.count_trial()

                    if self.task_parameters["save"] == 1:
                        self.save_results()

                else:

                    pass

                print("*" * 10)
                print("Experimentalist: Game ends!")
                print("*" * 10)
                if not self.display.value == 0:
                    self.display.value = 0

        self.close_processes()

        print("Experimentalist: DEAD.")

    def reset_trial_count(self):

        self.trial_n = 0
        self.trial_n_without_errors = 0

        self.trial_queue.put([self.trial_n, self.trial_n_without_errors])

    def count_trial(self):

        self.trial_n += 1
        if self.trial_error == "None":
            self.trial_n_without_errors += 1

        self.trial_queue.put([self.trial_n, self.trial_n_without_errors])

    def prepare_session_saving(self):

        self.data = []
        self.trial = 0

    def prepare_trial_saving(self):

        self.trial += 1

        self.condition = "None"
        self.trial_error = "None"
        self.trial_dot_fixation_time = -1
        self.trial_decision_time = -1
        self.trial_return_time = -1
        self.trial_inter_trial_time = -1

        self.stimuli_parameters_finder.reset()
        self.choice.value = "None".encode()
        self.dice_output.value = "None".encode()

        self.reward_amount = -99

    def save_trial(self):

        self.trial_results["trial"] = self.trial
        self.trial_results["error"] = self.trial_error
        self.trial_results["fixation_dot_time"] = self.trial_dot_fixation_time
        self.trial_results["decision_time"] = self.trial_decision_time
        self.trial_results["return_time"] = self.trial_return_time
        self.trial_results["inter_trial_time"] = self.trial_inter_trial_time
        self.trial_results["choice"] = self.choice.value.decode()
        self.trial_results["dice_output"] = self.dice_output.value.decode()
        self.trial_results["reward_amount"] = self.reward_amount
        self.trial_results["condition"] = self.condition

        for pos, dic in self.stimuli_parameters.items():

            for key, value in dic.items():

                self.trial_results["{}_{}".format(pos, key)] = value

        self.data.append(self.trial_results.copy())

    def save_results(self):

        b = BackUp()

        task_parameters = OrderedDict(sorted(self.task_parameters.items()))

        b.save(task_parameters, self.data[:-1])

    def do_task(self):

        end_phase = self.pre_fixation_dot_phase()

        if end_phase == 1:

            pass

        else:

            self.trial_error = "E1: Grip not held enough time to display the fixation dot."
            print(self.trial_error)
            return 1

        end_phase = self.fixation_dot_phase()

        if end_phase == 1:

            pass

        else:

            self.trial_error = "E2: Grip released to soon."
            print(self.trial_error)
            self.punishment()
            return 1

        end_phase = self.decision_phase()

        if end_phase == 1:

            self.sound_instruction.put("choice")

        else:

            self.trial_error = "E3: Too long for taking a decision."
            print(self.trial_error)
            self.punishment()
            return 1

        end_phase = self.return_phase()

        if end_phase == 1:

            self.rewarding_phase()

        else:

            self.trial_error = "E4: Too long for taking back the grip."
            print(self.trial_error)
            self.punishment()
            self.grip_change.put(None)
            return 1

        self.inter_trial_phase()

        return 0

    def open_window(self):

        while True:

            self.display.value = 1

            try:

                confirmation = self.confirmation_opening_window.get(timeout=1)
                if confirmation:

                    break

            except queue.Empty:

                pass

    def close_processes(self):

        print("Experimentalist close processes...")

        for i in [self.valve_opening, self.grip_change, self.sound_instruction,
                  self.keyboard_queue, self.keyboard_queue_for_fake_grip]:

            i.put(None)

        for i in [self.check_grasping_launcher, self.decision_tracker_launcher, self.coming_back_tracker_launcher]:

            i.set()

    def pause(self):

        self.current_frame.value = "pause".encode()
        while not self.shutdown_event.is_set():

            try:

                k = self.keyboard_queue.get(timeout=0.05)

                if k and k == [1, Qt.Key_Space]:

                    return 1

            except queue.Empty:

                pass

        return 0

    def punishment(self):

        if not self.shutdown_event.is_set():

            self.current_frame.value = "punishment".encode()
            self.sound_instruction.put("punishment")

            Event().wait(self.task_parameters["punishment_time"]/1000.)

    def pre_fixation_dot_phase(self):

        self.current_frame.value = "inter_trial".encode()

        while not self.shutdown_event.is_set():

            if self.grip_state.value == 1:

                end_phase, time_needed = self.launch_timer_and_switch(
                    switch=self.check_grasping_launcher,
                    interval=self.task_parameters["grasping_time"],
                    should_end=1)

                return end_phase

    def fixation_dot_phase(self):

        self.trial_dot_fixation_time = \
            np.random.randint(self.task_parameters["fixation_dot_time"][0],
                              self.task_parameters["fixation_dot_time"][1])

        self.current_frame.value = "fixation_dot".encode()

        end_phase, time_needed = self.launch_timer_and_switch(
                    switch=self.check_grasping_launcher,
                    interval=self.trial_dot_fixation_time,
                    should_end=1)

        return end_phase

    def decision_phase(self):

        self.condition = self.stimuli_parameters_finder.find_stimuli_parameters()

        self.current_frame.value = "stimuli".encode()

        end_phase, time_needed = self.launch_timer_and_switch(
            switch=self.decision_tracker_launcher,
            interval=self.task_parameters["max_decision_time"],
            should_end=0)

        if end_phase == 1:
            self.trial_decision_time = time_needed
        else:
            self.choice_queue.put(None)

        return end_phase

    def return_phase(self):

        self.current_frame.value = "choice".encode()

        end_phase, time_needed = self.launch_timer_and_switch(
            switch=self.coming_back_tracker_launcher,
            interval=self.task_parameters["max_return_time"],
            should_end=0)

        self.grip_change.put(None)

        if end_phase == 1:
            self.trial_return_time = time_needed
        else:
            self.grip_change.put(None)

        return end_phase

    def rewarding_phase(self):

        choice = self.choice.value.decode()

        random_number = np.random.random()
        # print("random", random_number, "p", self.stimuli_parameters[choice]["p"])
        if random_number >= self.stimuli_parameters[choice]["p"]:

            self.dice_output.value = "b".encode()

        else:
            self.dice_output.value = "a".encode()

        if self.dice_output.value.decode() == "a":

            self.reward_amount = self.stimuli_parameters[choice]["q"][0]

        else:

            self.reward_amount = self.stimuli_parameters[choice]["q"][1]

        self.current_frame.value = "result".encode()

        for i in range(int(self.reward_amount)):

            delay = i*(self.task_parameters["valve_opening_time"]/1000.+0.2)
            t = Timer(delay, self.give_reward)
            t.start()

        Event().wait(self.task_parameters["result_display_time"]/1000.)

    def inter_trial_phase(self):

        self.current_frame.value = "inter_trial".encode()

        self.trial_inter_trial_time = \
            np.random.randint(self.task_parameters["inter_trial_time"][0],
                              self.task_parameters["inter_trial_time"][1])
        Event().wait(self.trial_inter_trial_time / 1000.)

    def give_reward(self):

        self.sound_instruction.put("reward")
        self.valve_opening.put(self.task_parameters["valve_opening_time"])

    def launch_timer_and_switch(self, switch, interval, should_end):

        a = time()

        self.timer.start(interval, should_end)

        switch.set()

        end_phase = self.signal.get()

        b = time()

        time_needed = int((b - a) * 1000)

        return end_phase, time_needed


class StimuliParametersFinder(object):

    def __init__(self, stimuli_parameters):

        self.stimuli_parameters = stimuli_parameters
        self.condition = None

        # ------------------------------- #

        # # Uncomment for testing only probabilities
        #
        # self.possible_p = [0.25, 0.5, 0.75]
        # self.possible_q = [1, 2, 3, 4]
        #
        # self.find_stimuli = {"fixed_q": (self.find_stimuli_fixed_q, None)}

        # ------------------------------------- #
        self.possible_p = [0.25, 0.5, 0.75, 1]
        self.possible_q = [1, 2, 3, 4]
        self.find_stimuli = {"fixed_p": (self.find_stimuli_fixed_p, None),
                             "fixed_q": (self.find_stimuli_fixed_q, None),
                             "congruent": (self.find_stimuli_congruent, None)
                             }

        self.expected_values = [-1.25, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1.25]
        for i in self.expected_values:
            self.find_stimuli["incongruent_{}".format(i)] = (self.find_stimuli_incongruent, i)

        # ------------------------------- #

        self.possible_conditions = list(self.find_stimuli.keys())
        self.sides = ["left", "right"]

    def reset(self):

        for i in ["left", "right"]:
            self.stimuli_parameters[i] = \
                {
                    "p": -1,
                    "q": [-99, -99],
                    "beginning_angle": -99
                }

    def find_stimuli_parameters(self):

        np.random.shuffle(self.sides)

        self.condition = np.random.choice(self.possible_conditions)
        f, arg = self.find_stimuli[self.condition]
        if arg is not None:
            f(arg)
        else:
            f()
        return self.condition

    def find_stimuli_fixed_p(self):

        print("FIXED P")

        p = np.random.choice(self.possible_p)
        q = np.random.choice(self.possible_q, size=2, replace=False)

        for i, side in enumerate(self.sides):

            self.stimuli_parameters[side] = \
                {
                    "p": p,
                    "q": [q[i], 0],
                    "beginning_angle": np.random.randint(0, 360)
                }
        return p, q

    def find_stimuli_fixed_q(self):

        print("FIXED Q")

        p = np.random.choice(self.possible_p, size=2, replace=False)
        q = np.random.choice(self.possible_q)

        for i, side in enumerate(self.sides):

            self.stimuli_parameters[side] = \
                {
                    "p": p[i],
                    "q": [q, 0],
                    "beginning_angle": np.random.randint(0, 360)
                }
        return p, q

    def find_stimuli_congruent(self):

        print("CONGRUENT")

        p = np.sort(np.random.choice(self.possible_p, size=2, replace=False))
        q = np.sort(np.random.choice(self.possible_q, size=2, replace=False))

        for i, side in enumerate(self.sides):

            self.stimuli_parameters[side] = \
                {
                    "p": p[i],
                    "q": [q[i], 0],
                    "beginning_angle": np.random.randint(0, 360)
                }
        return p, q

    def find_stimuli_incongruent(self, expected_value):

        print("INCONGRUENT WITH DIFFERENCE IN EXPECTED VALUE OF {} IN (DE)FAVOR OF RISKY OPTION".format(expected_value))

        p = np.sort(np.random.choice(self.possible_p, size=2, replace=False))
        q = np.sort(np.random.choice(self.possible_q, size=2, replace=False))[::-1]

        while p[0]*q[0] - p[1]*q[1] != expected_value:

            p = np.sort(np.random.choice(self.possible_p, size=2, replace=False))
            q = np.sort(np.random.choice(self.possible_q, size=2, replace=False))[::-1]

        for i, side in enumerate(self.sides):

            self.stimuli_parameters[side] = \
                {
                    "p": p[i],
                    "q": [q[i], 0],
                    "beginning_angle": np.random.randint(0, 360)
                }

        return p, q


if __name__ == "__main__":
    pass

