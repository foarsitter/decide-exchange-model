import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

from decide import input_folder

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)

conn = sqlite3.connect("C:\\Users\\jelme\\PycharmProjects\\decide-exchange-model\\data\\output\\decide-data_1.db")

df = pd.read_sql("""
SELECT  
    a.p as p,
    a.issue as issue,  
    a.repetion || '-' || a.iteration as pointer, 
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
        LEFT JOIN dataset d ON a.data_set_id = d.id
      WHERE  ai.type = 'before' AND i2.pointer = 9 AND d.id = ? 
     GROUP BY m.id,r.id, i2.id, i.id) a
""",
                 conn,
                 params=(1,),
                 index_col=['p'],
                 columns=['issue']
                 )


for p in sorted(set(df.index)):
    x = df.loc[p].pivot(index='pointer', columns='issue', values='nbs').cov().round(5)

    x.to_csv(input_folder + '/test_{}.csv'.format(p))