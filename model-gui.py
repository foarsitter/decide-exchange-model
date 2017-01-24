import os
import tkFileDialog
import tkSimpleDialog

os.system("python3 /home/jelmert/PycharmProjects/equal-gain-python/model.py -h")

input_file = tkFileDialog.askopenfile().name
output_dir = tkFileDialog.askdirectory()
rounds = tkSimpleDialog.askinteger("Enther the numbers of rounds", "Number of rounds:")
model_type = "equal"

os.system('python3 /home/jelmert/PycharmProjects/equal-gain-python/model.py --input "{0}" --output "{1}" --rounds {2} --model {3}'.format(input_file, output_dir, rounds, model_type))
