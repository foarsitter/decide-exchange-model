# The old format
# import xml.etree.ElementTree as ET
# import csv
#
# tree = ET.parse('verkiezing 2012.xdf')
# root = tree.getroot()
#
# with open('data/verkiezing 2012.csv', 'w', newline='') as csvfile:
#     writer = csv.writer(csvfile, delimiter=';')
#
#     dataset = root.find('dataset')
#     issues = []
#     actors = []
#     actor_issues = []
#
#     # /	ID	Full name
#     writer.writerow(["#/", "ID", "Full name"])
#
#     for actor in dataset.findall('actor'):
#         writer.writerow(["#A", actor.get('name'), actor.get('name')])
#
#     # /	ID	Full name
#     writer.writerow(["#/", "ID", "Full name"])
#
#     for issue in dataset.findall('issue'):
#         writer.writerow(["#P", issue.get('key'), issue.get('key')])
#
#     # /	actor	issue	position	salience	power
#     writer.writerow(["#/", "actor", "issue", "position", "salience", "power"])
#
#     for actor in dataset.findall('actor'):
#         actor_name = actor.get('name')
#
#         for actor_issue in actor.findall('actorIssueLink'):
#             issue = actor_issue.get('issueRef')
#             salience = actor_issue.get('salience')
#             power = actor_issue.get('power')
#             position = actor_issue.get('position')
#             if float(salience) > 0:
#                 writer.writerow(["#D", actor_name, issue, position, salience, power])
#
#
# # print(issues)
