import argparse

from model.helpers.csvParser import Parser


def parse_arguments():
	parser = argparse.ArgumentParser(description="This program accepts input with a dot (.) as decimal separator. \n"
												 "Parameters:\n{0} is for defining an actor,\n"
												 "{1} for an issue,\n"
												 "{2} for actor values for each issue.\n"
												 "We expect for {2} the following order in values: "
												 "actor, issue, position, salience, power".format(Parser.cA, Parser.cP,
																								  Parser.cD))
	parser.add_argument('--model',
						help='The type of the model. The options are "equal" for the Equal Gain model and '
							 '"random" for the RandomRate model ',
						default='equal', type=str)

	parser.add_argument('--rounds', help='The number of round the model needs to be executed', default=10, type=int)
	parser.add_argument('--input', help='The location of the csv input file. ', default="data/data_short.csv", type=str)
	parser.add_argument('--output', help='Output directory ', default="data/output/data_short/", type=str)

	return parser.parse_args()