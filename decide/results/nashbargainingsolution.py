import os

import numpy as np
import pandas as pd
from decide import data_folder
from decide.data.database import connection, Manager
from decide.results.helpers import list_to_sql_param


def write_summary_result(conn, model_run_ids, output_directory, ai_type="before"):

    if ai_type == "before":
        x_type = "preference"
    else:
        x_type = "voting"

    df = pd.read_sql("""
    SELECT
      a.p as p,
      a.issue as issue,
      a.iteration as iteration,
      a.repetion as repetion,
      a.numerator / a.denominator AS nbs
    FROM (SELECT
            sum(ai.position * ai.power * ai.salience) AS numerator,
            sum(ai.salience * ai.power)               AS denominator,
            r.pointer                                 AS repetion,
            i2.pointer                                AS iteration,
            m.p,
      i.name as issue
          FROM actorissue ai
            LEFT JOIN issue i ON ai.issue_id = i.id
            LEFT JOIN actor a ON ai.actor_id = a.id
            LEFT JOIN iteration i2 ON ai.iteration_id = i2.id
            LEFT JOIN repetition r ON i2.repetition_id = r.id
            LEFT JOIN modelrun m ON r.model_run_id = m.id        
          WHERE  ai.type = '%s' AND m.id IN (%s)
         GROUP BY m.id,r.id, i2.id, i.id) a
    """ % (ai_type, list_to_sql_param(model_run_ids)),
                     conn,
                     index_col='p',
                     columns=['nbs']
                     )
    try:
        table_avg = pd.pivot_table(df, index=['issue', 'p'], columns=['iteration'], values=['nbs'], aggfunc=np.average)
        table_avg.to_csv(os.path.join(output_directory, f'nbs_average_{x_type}.csv'))
    except Exception as e:
        print(e)

    try:
        table_var = pd.pivot_table(df, index=['issue', 'p'], columns=['iteration'], values=['nbs'], aggfunc=np.var)
        table_var.to_csv(os.path.join(output_directory, f'nbs_variance_{x_type}.csv'))
    except Exception as e:
        print(e)

    sql_2 = """SELECT issue.name, issue.id
FROM issue
INNER JOIN dataset d on issue.data_set_id = d.id
INNER JOIN modelrun m on d.id = m.data_set_id
WHERE m.id IN (%s)
GROUP BY issue.name, issue.id
ORDER BY issue.name""" % list_to_sql_param(model_run_ids)

    cursor = conn.execute_sql(sql=sql_2, params=[])
    issues = cursor.fetchall()

    # %%

    for name, issue_id in issues:
        df = pd.read_sql("""SELECT a.p                         as p,
       a.issue                     as issue,
       a.iteration                 as iteration,
       a.repetion                  as repetion,
       a.numerator / a.denominator AS nbs
FROM (SELECT sum(ai.position * ai.power * ai.salience) AS numerator,
             sum(ai.salience * ai.power)
                                                       AS denominator,
             r.pointer
                                                       AS repetion,
             i2.pointer
                                                       AS iteration,
             m.p,
             i.name                                    as issue
      FROM actorissue ai
               LEFT JOIN issue i ON ai.issue_id = i.id
               LEFT JOIN actor a ON ai.actor_id = a.id
               LEFT JOIN iteration i2 ON ai.iteration_id = i2.id
               LEFT JOIN repetition r ON i2.repetition_id = r.id
               LEFT JOIN modelrun m ON r.model_run_id = m.id
               LEFT JOIN dataset d ON a.data_set_id = d.id
      WHERE ai.type = '%s'
        AND m.id IN(%s)
        AND i.id = %s
      GROUP BY m.id, r.id, i2.id, i.id) a
        """  % (ai_type, list_to_sql_param(model_run_ids), issue_id),
                         conn,
                         index_col='p',
                         columns=['nbs']
                         )

        try:
            table = pd.pivot_table(df, index=['iteration'], columns=['p'], values=['nbs'])
            plt = table.plot()

            plt.set_title(name)
            plt.set_ylim(0, 110)

            lgd = plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)

            plt.figure.savefig(
                os.path.join(output_directory, f'nbs_{name}_{x_type}.png'),
                bbox_extra_artists=(lgd,),
                bbox_inches="tight",
            )
        except Exception as e:
            print(e)


if __name__ == '__main__':
    m = Manager(os.environ.get('DATABASE_URL'))
    m.init_database()

    model_run_ids = [43, 44]

    write_summary_result(connection, model_run_ids, data_folder)
