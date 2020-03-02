import logging
import os

import pandas as pd
from pandas.core.base import DataError

from decide import data_folder
from decide.data.database import connection, Manager
from decide.results.helpers import list_to_sql_param, handle_data_frame

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)


def write_summary_result(conn, model_run_ids, output_directory):
    sql = """SELECT COUNT(*)   exchanges_count,
           SUM(ea.eu) utility_sum,
           AVG(ea.eu)        utility_avg,
           a.name as         actor,
           m.p
    FROM exchangeactor ea
             JOIN actor a on ea.actor_id = a.id
             JOIN exchange e on ea.id = e.i_id
             JOIN iteration i on e.iteration_id = i.id
             JOIN repetition r on i.repetition_id = r.id
             JOIN modelrun m on r.model_run_id = m.id
    WHERE m.id in (%s)
    GROUP BY a.id, m.p;""" % list_to_sql_param(model_run_ids)

    df = pd.read_sql_query(
        sql=sql,
        con=conn,
        index_col=['actor', 'p'],
    )

    # %%

    file_name = os.path.join(output_directory, 'exchanges_count.{}')

    try:

        handle_data_frame(
            df=pd.pivot_table(df, index=['p'], columns=['actor'], values=['exchanges_count']),
            file_name=file_name,
            title='AVG count of the executed exchanges for a repetition'
        )
    except DataError as ex:
        logging.exception(ex)
        print(ex)
    try:
        handle_data_frame(
            df=pd.pivot_table(df, index=['p'], columns=['actor'], values=['utility_sum']),
            file_name=os.path.join(output_directory, 'expected_utility_sum.{}'),
            title='AVG Sum of the expected utility per repetition'
        )

        handle_data_frame(
            df=pd.pivot_table(df, index=['p'], columns=['actor'], values=['utility_avg']),
            file_name=os.path.join(output_directory, 'expected_utility_avg.{}'),
            title='Average of the expected utility'
        )
    except DataError as ex:
        logging.exception(ex)
        print(ex)


if __name__ == '__main__':
    m = Manager(os.environ.get('DATABASE_URL'))
    m.init_database()

    model_run_id = 1

    write_summary_result(connection, [model_run_id], data_folder)
