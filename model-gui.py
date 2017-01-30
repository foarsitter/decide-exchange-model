import os
import tkinter as tk
import xml.etree.cElementTree as ET
from _datetime import datetime
from tkinter import filedialog
from tkinter import ttk

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


class MainApplication(tk.Frame):
    GRID_COLUMN = 0
    GRID_ROW = 0

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        # variable used
        self.input_file = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.model = tk.StringVar()
        self.iterations = tk.StringVar()

        self.load_settings()
        row = self.row()
        self.label("Select input file", row=row)
        self.input_btn = ttk.Button(parent, text="Input file", command=self.input)
        self.input_btn.grid(row=row, column=1, sticky=tk.W)
        tk.Label(parent, textvariable=self.input_file).grid(row=self.row(), column=1, sticky=tk.W)

        row = self.row()
        self.label("Output directory", row=row)
        self.output_btn = tk.Button(parent, text="Output directory", command=self.output)
        self.output_btn.grid(row=row, column=1, sticky=tk.W)
        tk.Label(parent, textvariable=self.output_dir).grid(row=self.row(), column=1, sticky=tk.W)

        row = self.row()
        self.label("Iterations", row=row)
        self.E1 = tk.Entry(parent, textvariable=self.iterations)
        self.E1.grid(row=row, column=1, sticky=tk.W)

        row = self.row()
        self.label("Model Type", row=row)
        r1 = tk.Radiobutton(parent, text="Equal Gain", variable=self.model, value="equal")
        r1.grid(row=row, column=1, sticky=tk.W)

        r2 = tk.Radiobutton(parent, text="Random Rate", variable=self.model, value="random")
        r2.grid(row=self.row(), column=1, sticky=tk.W)

        self.run = tk.Button(parent, text="Run", command=self.run)
        self.run.grid(row=self.row(), column=1, sticky=tk.E)

        self.progress_bar = ttk.Progressbar(self.parent, orient="horizontal", length=100, mode="determinate")
        self.progress_bar.grid(row=self.row(), column=0, columnspan=2, sticky=tk.E+tk.W)

    def input(self):
        dialog = tk.filedialog.askopenfile()

        if dialog:
            self.input_file.set(dialog.name)

    def output(self):
        dir = filedialog.askdirectory(initialdir=self.output_dir)

        if not os.path.isdir(dir):
            os.makedirs(dir)

        self.output_dir.set(dir)

    def run(self):
        print("run")
        print(self.E1.get())
        print(self.input_file)
        print(self.output_dir)
        print(self.serialize())

        self.save_settings()
        self.run_model()

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
        tk.Label(self.parent, text=text).grid(row=row, column=column, sticky=tk.W)

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

        for key, value in self.__dict__.items():
            if isinstance(value, tk.Variable):
                child = ET.Element(key)
                child.text = value.get()
                element.append(child)

        return element

    def run_model(self):

        if self.model.get() == "equal":
            from model.equalgain import EqualGainModel as Model
        else:
            from model.randomrate import RandomRateModel as Model

        # The event handlers for logging and writing the results to the disk.
        eventHandler = Observable()
        Logger(eventHandler)
        po = ProgressObserver(eventHandler)

        po.progressbar = self.progress_bar
        po.step_size = 100 / int(self.iterations.get())

        startTime = datetime.now()

        eventHandler.notify(Observable.LOG, message="Start calculation at {0}".format(startTime))

        model = Model()

        from model.helpers import csvParser
        csvParser = csvParser.Parser(model)

        data_set_name = os.path.join(self.output_dir.get(), self.input_file.get().split("/")[-1].split(".")[0])

        model = csvParser.read(self.input_file.get())

        Externalities(eventHandler, model, data_set_name)
        ExchangesWriter(eventHandler, model, data_set_name)
        HistoryWriter(eventHandler, model, data_set_name)
        InitialExchanges(eventHandler)
        eventHandler.notify(Observable.LOG, message="Parsed file {0}".format(self.input_file.get()))

        model_loop = ModelLoop(model, eventHandler)

        for iteration_number in range(int(self.iterations.get())):
            model_loop.loop()
            self.parent.update_idletasks()

        eventHandler.notify(Observable.CLOSE, model=self.model)
        eventHandler.notify(Observable.LOG, message="Finished in {0}".format(datetime.now() - startTime))


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)

    root.minsize(width=500, height=500)
    center(root)

    root.title("Model")
    root.mainloop()
