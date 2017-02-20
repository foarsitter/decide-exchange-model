import os
import threading
import tkinter as tk
import xml.etree.cElementTree as ET
from datetime import datetime
from queue import Queue
from tkinter import filedialog
from tkinter import ttk

from model.base import AbstractModel
from model.helpers.helpers import ModelLoop
from model.observers.exchanges_writer import ExchangesWriter
from model.observers.externalities import Externalities
from model.observers.history_writer import HistoryWriter
from model.observers.initial_exchanges import InitialExchanges
from model.observers.logger import Logger
from model.observers.observer import Observable, Observer


def center(toplevel):
    toplevel.update_idletasks()
    w = toplevel.winfo_screenwidth()
    h = toplevel.winfo_screenheight()
    size = tuple(int(_) for _ in toplevel.geometry().split('+')[0].split('x'))
    x = w / 2 - size[0] / 2
    y = h / 2 - size[1] / 2
    toplevel.geometry("%dx%d+%d+%d" % (size + (x, y)))


class ProgressObserver(Observer):
    progressbar = None
    step_size = 10

    def update(self, observable, notification_type, **kwargs):
        if notification_type == Observable.FINISHED_ROUND:
            self.progressbar["value"] += self.step_size


class CSVFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.row_pointer = 0

        sizex = 800
        sizey = 600
        posx = 100
        posy = 100
        self.parent.geometry("%dx%d+%d+%d" % (sizex, sizey, posx, posy))

        self.canvas = tk.Canvas(self.parent)

        myscrollbar = tk.Scrollbar(self.parent, orient="vertical", command=self.canvas.yview)
        myscrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=myscrollbar.set)

        self.canvas.pack(side="left")

    def create_grid_table(self, model: AbstractModel, issues):

        # an actor has only a name

        self.create_heading(["Actors"])
        self.create_row(model.Actors.values())

        self.create_row([""])

        self.create_heading(["Issues"])
        self.create_heading(["Name", "Lower", "Upper"])
        for issue in issues.values():
            self.create_row([issue.name, issue.lower, issue.upper])

        # an issue has a name, lower and upper

        self.row_pointer += 1
        self.create_row([""])
        self.create_heading(["Actor issues"])
        # an actor issues has an actor, issue, position, and power
        self.create_heading(["Actor", "issue", "position", "salience", "power"])

        for key, actor_issues in model.ActorIssues.items():
            for actor_issue in actor_issues.values():
                self.create_row([actor_issue.actor_name, actor_issue.issue_name, int(actor_issue.position), actor_issue.salience, actor_issue.power])

    def create_row(self, values):

        for __, value in enumerate(values):
            tk.Label(self.canvas, text=value, relief=tk.GROOVE).grid(row=self.row_pointer, column=__, sticky=tk.W + tk.E)

        self.row_pointer += 1

    def create_heading(self, values):

        for __, value in enumerate(values):
            tk.Label(self.canvas, text=value, relief=tk.GROOVE, font="Verdana 10 bold").grid(row=self.row_pointer, column=__, sticky=tk.W + tk.E)

        self.row_pointer += 1


class MainApplication(tk.Frame):
    GRID_COLUMN = 0
    GRID_ROW = 0

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.parent = parent
        self.queue = Queue()
        self.interrupt = False
        self.tid = None

        # variable used
        self.input_file = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.model = tk.StringVar()
        self.model.set("equal")
        self.iterations = tk.StringVar()
        self.iterations.set(10)
        self.counter = tk.IntVar()

        # load settings from xml file
        self.load_settings()

        # layout
        row = self.row()
        self.label("Select input file", row=row)
        self.input_btn = ttk.Button(parent, text="Input file", command=self.input)
        self.input_btn.grid(row=row, column=1, sticky=tk.W)
        tk.Label(parent, textvariable=self.input_file).grid(row=self.row(), column=1, sticky=tk.W)

        row = self.row()
        self.label("Output directory", row=row)
        self.output_btn = ttk.Button(parent, text="Output directory", command=self.output)
        self.output_btn.grid(row=row, column=1, sticky=tk.W)
        tk.Label(parent, textvariable=self.output_dir).grid(row=self.row(), column=1, sticky=tk.W)

        row = self.row()
        self.label("Iterations", row=row)
        self.E1 = ttk.Entry(parent, textvariable=self.iterations)
        self.E1.grid(row=row, column=1, sticky=tk.W)

        row = self.row()
        self.label("Exchange type", row=row)
        r1 = ttk.Radiobutton(parent, text="Equal Exchange Rate", variable=self.model, value="equal")
        r1.grid(row=row, column=1, sticky=tk.W)

        r2 = ttk.Radiobutton(parent, text="Random Exchange Rate", variable=self.model, value="random")
        r2.grid(row=self.row(), column=1, sticky=tk.W)

        row = self.row()
        self.label("", row=row)
        self.run_btn = ttk.Button(parent, text="Run", command=self.run_model)
        self.run_btn.grid(row=row, column=1, sticky=tk.W)

        self.progress_dialog = None

    def progress_bar(self, maximum):

        self.counter.set(0)
        self.progress_dialog = tk.Toplevel(self.parent)
        tk.Label(self.progress_dialog, text="Download Bar").pack(side=tk.TOP)

        ttk.Progressbar(self.progress_dialog, orient="horizontal", length=400, mode="determinate", variable=self.counter, maximum=maximum).pack(side=tk.TOP)

        center(self.progress_dialog)

    def input(self):
        dialog = tk.filedialog.askopenfile()

        if dialog:
            self.input_file.set(dialog.name)

            model = AbstractModel()

            from model.helpers import csvParser
            csv_parser = csvParser.Parser(model)

            data_set_name = os.path.join(self.output_dir.get(), self.input_file.get().split("/")[-1].split(".")[0])

            model = csv_parser.read(self.input_file.get())

            table = CSVFrame(tk.Toplevel())
            table.create_grid_table(model, csv_parser.issues)

    def output(self):
        selected_dir = filedialog.askdirectory(initialdir=self.output_dir)

        if selected_dir and not os.path.isdir(selected_dir):
            os.makedirs(selected_dir)

        self.output_dir.set(selected_dir)

    def model_type(self):
        print(self.model.get())

    @staticmethod
    def col():
        ret = MainApplication.GRID_COLUMN
        MainApplication.GRID_COLUMN += 1
        return ret

    @staticmethod
    def row():
        ret = MainApplication.GRID_ROW
        MainApplication.GRID_ROW += 1
        return ret

    def label(self, text, row, column=0):
        tk.Label(self.parent, text=text).grid(row=row, column=column, sticky=tk.W, padx=20, pady=20)

    def serialize(self):
        return ET.tostring(self.to_xml())

    def save_settings(self):
        tree = ET.ElementTree(self.to_xml())
        tree.write("model-settings.xml")

    def load_settings(self):

        if os.path.isfile("model-settings.xml"):

            for elm in ET.parse("model-settings.xml").getroot():

                if elm.tag in self.__dict__:
                    self.__dict__[elm.tag].set(elm.text)

    def to_xml(self):

        element = ET.Element("model-settings")

        ignore = ["counter"]

        for key, value in self.__dict__.items():
            if isinstance(value, tk.Variable) and key not in ignore:
                child = ET.Element(key)
                child.text = value.get()
                element.append(child)

        return element

    def run_model(self):

        if not self.input_file.get():
            tk.me

        self.save_settings()

        t = threading.Thread(target=self.run)
        t.start()
        self.periodic_call()

        self.progress_bar(int(self.iterations.get()))

    def run(self):

        if self.model.get() == "equal":
            from model.equalgain import EqualGainModel as Model
        else:
            from model.randomrate import RandomRateModel as Model

        # The event handlers for logging and writing the results to the disk.
        event_handler = Observable()
        Logger(event_handler)

        start_time = datetime.now()

        event_handler.notify(Observable.LOG, message="Start calculation at {0}".format(start_time))

        model = Model()

        from model.helpers import csvParser
        csv_parser = csvParser.Parser(model)

        data_set_name = os.path.join(self.output_dir.get(), self.input_file.get().split("/")[-1].split(".")[0])

        model = csv_parser.read(self.input_file.get())

        Externalities(event_handler, model, data_set_name)
        ExchangesWriter(event_handler, model, data_set_name)
        HistoryWriter(event_handler, model, data_set_name)
        InitialExchanges(event_handler, model, data_set_name)
        event_handler.notify(Observable.LOG, message="Parsed file {0}".format(self.input_file.get()))

        model_loop = ModelLoop(model, event_handler)

        for iteration_number in range(int(self.iterations.get())):

            if not self.interrupt:
                model_loop.loop()
                self.queue.put(iteration_number)
            else:
                print("interrupted")
                break

        event_handler.notify(Observable.CLOSE, model=self.model)
        event_handler.notify(Observable.LOG, message="Finished in {0}".format(datetime.now() - start_time))

        self.stop_periodic_call()

    def prog_bar_update(self, value):
        self.counter.set(value + 1)

    def process_queue(self):
        while self.queue.qsize():
            try:
                value = self.queue.get(0)
                self.prog_bar_update(value)
            except Queue.Empty:
                pass

    def periodic_call(self):
        self.process_queue()
        self.tid = self.parent.after(100, self.periodic_call)

    def stop_periodic_call(self):
        self.parent.after_cancel(self.tid)
        self.progress_dialog.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)

    center(root)

    root.title("Decide Exchange Model")

    root.mainloop()