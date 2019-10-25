import os

import pandas as pd
from decide import data_folder
from decide.data.database import connection, Manager
from decide.results.helpers import list_to_sql_param

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)


def write_summary_result(conn, model_run_ids, output_directory):
    df = pd.read_sql("""
    SELECT
            a.name AS actor,
            i.name as issue,
            AVG(ai.position) as postion,        
            i2.pointer                                AS iteration,
            m.p,
            m.id  
          FROM actorissue ai
            LEFT JOIN issue i ON ai.issue_id = i.id
            LEFT JOIN actor a ON ai.actor_id = a.id
            LEFT JOIN iteration i2 ON ai.iteration_id = i2.id
            LEFT JOIN repetition r ON i2.repetition_id = r.id
            LEFT JOIN modelrun m ON r.model_run_id = m.id            
          WHERE  ai.type = 'before' AND m.id IN(%s)
         GROUP BY m.id, i2.pointer, a.id, i.id;
    """ % list_to_sql_param(model_run_ids),
                     conn,
                     index_col=['issue', 'actor', 'p'],
                     columns=['postion']
                     )

    table = pd.pivot_table(df, index=['issue', 'actor', 'iteration'], columns=['p'], values=['postion'])
    table.to_csv(os.path.join(output_directory, 'issues.csv'))


if __name__ == '__main__':
    m = Manager(os.environ.get('DATABASE_URL'))
    m.init_database()

    model_run_id = 1

    write_summary_result(connection, [model_run_id], data_folder)
