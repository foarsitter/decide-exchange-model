import sqlite3
from collections import defaultdict

conn = sqlite3.connect('/home/jelmert/PycharmProjects/decide-exchange-model/data/output/decide-data.db')


# conn = sqlite3.connect('/home/jelmert/PycharmProjects/decide-exchange-model/decide/kopenhagen_without_ties.db')


def average_per_issue():
    avg_sql = """
SELECT
  m.p,
  a.name AS actor,
  i.name AS issue,
  AVG(ai.position)
FROM actorissue ai
  LEFT JOIN actor a ON ai.actor_id = a.id
  LEFT JOIN issue i ON ai.issue_id = i.id
  LEFT JOIN iteration i2 ON ai.iteration_id = i2.id
  LEFT JOIN repetition r ON i2.repetition_id = r.id
  LEFT JOIN modelrun m ON r.model_run_id = m.id
WHERE ai.type = 'before' and i2.pointer = 9
GROUP BY a.id, i.id, m.id;
"""

    params = ()

    c = conn.cursor()

    c.execute(avg_sql, params)

    issue_averages = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

    issue_var = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    issue_var_count = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

    # sum all the rows
    for row in c:
        p, actor, issue, avg = row

        p = '{:.2f}'.format(p)

        issue_averages[actor][issue][p] += avg

    sql = """
SELECT
  m.p,  
  a.name AS actor,
  i.name     AS issue,
  ai.position 
FROM actorissue ai
  LEFT JOIN actor a ON ai.actor_id = a.id
  LEFT JOIN issue i ON ai.issue_id = i.id
  LEFT JOIN iteration i2 ON ai.iteration_id = i2.id
  LEFT JOIN repetition r ON i2.repetition_id = r.id
  LEFT JOIN modelrun m ON r.model_run_id = m.id
WHERE ai.type = 'before' and i2.pointer = 9 ORDER BY m.p;
    """

    c.execute(sql, params)

    # calculate the distance
    for row in c:
        p, actor, issue, position = row

        p = '{:.2f}'.format(p)

        avg = issue_averages[p][actor][issue]

        issue_var_count[actor][issue][p] += pow(position - avg, 2)

    for actor, issues in issue_var_count.items():

        for issue, ps in issues.items():

            for p, value in ps.items():
                var_count = issue_averages[actor][issue][p]

                issue_var[actor][issue][p] = var_count / 7298

    for actor, issues in issue_var.items():
        print(actor)
        for issue, ps in issues.items():
            print(issue)
            for p, value in ps.items():
                var = value
                avg = issue_averages[actor][issue][p]

                print('{} {} {}'.format(p, avg, var))


def externalities():
    pass
#
#
# if __name__ == "__main__":
#     # average_per_issue()
#     import matplotlib.pyplot as plt
#
#     fig = plt.figure()
#     fig.suptitle('No axes on this figure')
#
#     fig, ax_lst = plt.subplots(2, 2)
#
#     plt.show()
