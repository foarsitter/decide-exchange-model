import os
import threading
import tkinter as tk
import xml.etree.cElementTree as ET
from datetime import datetime
from queue import Queue
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk

import decimal

from model.base import AbstractModel
from model.helpers import csvparser
from model.helpers.helpers import ModelLoop
from model.observers.exchanges_writer import ExchangesWriter
from model.observers.externalities import Externalities
from model.observers.issue_development import IssueDevelopment
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


class ScrolledWindow(tk.Frame):
    """
    1. Master widget gets scrollbars and a canvas. Scrollbars are connected
    to canvas scrollregion.

    2. self.scrollwindow is created and inserted into canvas

    Usage Guideline:
    Assign any widgets as children of <ScrolledWindow instance>.scrollwindow
    to get them inserted into canvas

    __init__(self, parent, canv_w = 400, canv_h = 400, *args, **kwargs)
    docstring:
    Parent = master of scrolled window
    canv_w - width of canvas
    canv_h - height of canvas

    """

    def __init__(self, parent, canv_w=400, canv_h=400, *args, **kwargs):
        """
        Parent = master of scrolled window
        canv_w - width of canvas
        canv_h - height of canvas
       """
        super().__init__(parent, *args, **kwargs)

        self.parent = parent

        # creating a scrollbars
        self.xscrlbr = ttk.Scrollbar(self.parent, orient='horizontal')
        self.xscrlbr.grid(column=0, row=1, sticky='ew', columnspan=2)
        self.yscrlbr = ttk.Scrollbar(self.parent)
        self.yscrlbr.grid(column=1, row=0, sticky='ns')
        # creating a canvas
        self.canv = tk.Canvas(self.parent)
        self.canv.config(relief='flat',
                         width=10,
                         heigh=10, bd=2)
        # placing a canvas into frame
        self.canv.grid(column=0, row=0, sticky='nsew')
        # accociating scrollbar comands to canvas scroling
        self.xscrlbr.config(command=self.canv.xview)
        self.yscrlbr.config(command=self.canv.yview)

        # creating a frame to inserto to canvas
        self.scrollwindow = ttk.Frame(self.parent)

        self.canv.create_window(0, 0, window=self.scrollwindow, anchor='nw')

        self.canv.config(xscrollcommand=self.xscrlbr.set,
                         yscrollcommand=self.yscrlbr.set,
                         scrollregion=(0, 0, 100, 100))

        self.yscrlbr.lift(self.scrollwindow)
        self.xscrlbr.lift(self.scrollwindow)
        self.scrollwindow.bind('<Configure>', self._configure_window)
        # TODO: fix scrolling window
        # self.scrollwindow.bind('<Enter>', self._bound_to_mousewheel)
        # self.scrollwindow.bind('<Leave>', self._unbound_to_mousewheel)

        return

    def _bound_to_mousewheel(self, event):
        self.canv.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.canv.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canv.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _configure_window(self, event):
        # update the scrollbars to match the size of the inner frame
        size = (self.scrollwindow.winfo_reqwidth(), self.scrollwindow.winfo_reqheight())
        self.canv.config(scrollregion='0 0 %s %s' % size)
        if self.scrollwindow.winfo_reqwidth() != self.canv.winfo_width():
            # update the canvas's width to fit the inner frame
            self.canv.config(width=self.scrollwindow.winfo_reqwidth())
        if self.scrollwindow.winfo_reqheight() != self.canv.winfo_height():
            # update the canvas's width to fit the inner frame
            self.canv.config(height=self.scrollwindow.winfo_reqheight())


class CSVFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.row_pointer = 0

        self.scrolled_window = ScrolledWindow(parent, 400, 400)

    def create_grid_table(self, model: 'AbstractModel', issues):

        # an actor has only a name

        self.create_heading(["Actors"])
        self.create_row([x.name for x in model.actors.values()])

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

        for key, actor_issues in model.actor_issues.items():
            for actor_issue in actor_issues.values():
                self.create_row(
                    [actor_issue.actor_name, actor_issue.issue_name, int(actor_issue.position), actor_issue.salience,
                     actor_issue.power])

    def create_row(self, values):

        for __, value in enumerate(values):
            tk.Label(self.scrolled_window.scrollwindow, text=value, relief=tk.GROOVE).grid(row=self.row_pointer,
                                                                                           column=__,
                                                                                           sticky=tk.W + tk.E)

        self.row_pointer += 1

    def create_heading(self, values):

        for __, value in enumerate(values):
            tk.Label(self.scrolled_window.scrollwindow, text=value, relief=tk.GROOVE, font="Verdana 10 bold").grid(
                row=self.row_pointer, column=__, sticky=tk.W + tk.E)

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
        self.repetitions = tk.IntVar()
        self.repetitions.set(1)

        self.salience_weight = tk.DoubleVar()
        self.salience_weight.set(0.4)

        self.randomized_value = tk.DoubleVar()
        self.randomized_value.set(0.1)

        self.fixed_weight = tk.DoubleVar()
        self.fixed_weight.set(0.1)

        self.voting_positions = tk.IntVar()
        self.voting_positions.set(0)

        # load settings from xml file
        self.load_settings()

        row = self.row()
        self.label("Help", row=row)
        self.label("https://github.com/foarsitter/decide-exchange-model", row=row, column=1)
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
        self.label("Negotiation rounds", row=row)
        self.E1 = ttk.Entry(parent, textvariable=self.iterations)
        self.E1.grid(row=row, column=1, sticky=tk.W)

        self.entry_row("Model repetitions", self.repetitions)

        row = self.row()
        self.label("Exchange type", row=row)
        r1 = ttk.Radiobutton(parent, text="Equal Exchange Rate", variable=self.model, value="equal")
        r1.grid(row=row, column=1, sticky=tk.W)

        r2 = ttk.Radiobutton(parent, text="Random Exchange Rate", variable=self.model, value="random")
        r2.grid(row=self.row(), column=1, sticky=tk.W)

        self.entry_row("Randomized equal gain value", self.randomized_value)
        self.entry_row("Salience Weight", self.salience_weight)
        self.entry_row("Fixed Weight", self.fixed_weight)

        row = self.row()
        self.label("", row=row)
        self.run_btn = ttk.Checkbutton(parent, text="Show voting positions", variable=self.voting_positions)
        self.run_btn.grid(row=row, column=1, sticky=tk.W)

        row = self.row()
        self.label("", row=row)
        self.run_btn = ttk.Button(parent, text="Run", command=self.run_model)
        self.run_btn.grid(row=row, column=1, sticky=tk.W)

        self.progress_dialog = None

    def progress_bar(self, maximum):

        self.counter.set(0)
        self.progress_dialog = tk.Toplevel(self.parent)
        tk.Label(self.progress_dialog, text="Progress").pack(side=tk.TOP)

        ttk.Progressbar(self.progress_dialog, orient="horizontal", length=400, mode="determinate",
                        variable=self.counter, maximum=maximum).pack(side=tk.TOP)

        center(self.progress_dialog)

    def input(self):
        dialog = tk.filedialog.askopenfile()

        if dialog:
            self.input_file.set(dialog.name)

            model = AbstractModel()

            from model.helpers import csvparser
            csv_parser = csvparser.CsvParser(model)

            model = csv_parser.read(self.input_file.get())

            table = CSVFrame(tk.Toplevel())
            table.create_grid_table(model, model.issues)

    def output(self):
        selected_dir = filedialog.askdirectory(initialdir=self.output_dir)

        if selected_dir and not os.path.isdir(selected_dir):
            os.makedirs(selected_dir)

        self.output_dir.set(selected_dir)

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

            try:
                for elm in ET.parse("model-settings.xml").getroot():
                    if elm.tag in self.__dict__:
                        self.__dict__[elm.tag].set(elm.text)
            except ET.ParseError:
                print('Invalid xml')

    def entry_row(self, label, text_variable):

        row = self.row()
        self.label(label, row=row)
        self.E1 = ttk.Entry(self.parent, textvariable=text_variable)
        self.E1.grid(row=row, column=1, sticky=tk.W)

    def to_xml(self):

        element = ET.Element("model-settings")

        ignore = ["counter"]

        for key, value in self.__dict__.items():
            if isinstance(value, tk.Variable) and key not in ignore:
                child = ET.Element(key)
                try:
                    child.text = str(value.get())
                except tk.TclError:
                    child.text = str('')
                element.append(child)

        return element

    def run_model(self):

        if not self.input_file.get():
            messagebox.showinfo("Error", "No input file selected")
            return

        self.save_settings()

        t = threading.Thread(target=self.run)
        t.start()
        self.periodic_call()

        self.progress_bar(int(self.iterations.get()))

    def run(self):

        start_time = datetime.now()

        if self.model.get() == "equal":
            from model.equalgain import EqualGainModel as Model
            try:
                model = Model(randomized_value=decimal.Decimal(self.randomized_value.get()))
            except tk.TclError:
                model = Model(randomized_value=None)
        else:
            from model.randomrate import RandomRateModel as Model
            model = Model()

        # The event handlers for logging and writing the results to the disk.
        model.data_set_name = self.input_file.get().split("/")[-1].split(".")[0]

        if self.model.get() == 'equal':
            model_name = 'equal-' + str(round(self.randomized_value.get(), 2))
        else:
            model_name = 'random'

        output_directory = os.path.join(self.output_dir.get(), model.data_set_name, model_name)

        event_handler = Observable(model_ref=model, output_directory=output_directory)
        event_handler.log(message="Start calculation at {0}".format(start_time))

        csv_parser = csvparser.CsvParser(model_ref=model)

        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)

        Externalities(event_handler)
        ExchangesWriter(event_handler)
        IssueDevelopment(event_handler)

        event_handler.log(message="Parsed file {0}".format(self.input_file.get()))

        event_handler.before_repetitions()  # TODO FIX ARGS argument

        for repetition in range(int(self.repetitions.get())):

            model = csv_parser.read(self.input_file.get())

            model_loop = ModelLoop(model, event_handler, repetition)

            event_handler.before_iterations(repetition)

            for iteration_number in range(int(self.iterations.get())):

                if not self.interrupt:
                    model_loop.loop()
                    self.queue.put(iteration_number)
                else:
                    print("interrupted")
                    break

            event_handler.after_iterations(repetition)
        event_handler.after_repetitions()

        event_handler.log(message="Finished in {0}".format(datetime.now() - start_time))

        self.stop_periodic_call()

        messagebox.showinfo("Finished", "The model has finished executing {0} rounds.".format(self.iterations.get()))

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

    root.title("Decide Exchange Model (Equal Exchange Rate)")

    root.mainloop()
