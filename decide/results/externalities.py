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
    sql = """SELECT SUM(e.own)            as own,
           SUM(e.inner_positive) as inner_positive,
           SUM(e.inner_negative) as inner_negative,
           SUM(e.outer_positive) as outer_positive,
           SUM(e.outer_negative) as outer_negative,
           a.name                   actor,
           m.p
    FROM externality e
             JOIN actor a on e.actor_id = a.id
             JOIN iteration i on e.iteration_id = i.id
             JOIN repetition r on i.repetition_id = r.id
             JOIN modelrun m on r.model_run_id = m.id         
    WHERE m.id IN(%s)
    GROUP BY e.actor_id, m.id""" % list_to_sql_param(model_run_ids)

    df = pd.read_sql_query(
        sql,
        con=conn,
        index_col=['p'],
    )

    try:
        handle_data_frame(
            df=pd.pivot_table(df, index=['p'], columns=['actor'], values=['inner_positive']),
            file_name=os.path.join(output_directory, 'externalities_inner_positive.{}'),
            title='Inner positive externalities',
        )
    except DataError as ex:
        logging.exception(ex)
        print(ex)
    try:
        handle_data_frame(
            df=pd.pivot_table(df, index=['p'], columns=['actor'], values=['inner_negative']),
            file_name=os.path.join(output_directory, 'externalities_inner_negative.{}'),
            title='Inner negative externalities',
        )
    except DataError as ex:
        logging.exception(ex)
        print(ex)
    try:

        handle_data_frame(
            df=pd.pivot_table(df, index=['p'], columns=['actor'], values=['outer_positive']),
            file_name=os.path.join(output_directory, 'externalities_outer_positive.{}'),
            title='Outer positive externalities',
        )

    except DataError as ex:
        logging.exception(ex)
        print(ex)
    try:

        handle_data_frame(
            df=pd.pivot_table(df, index=['p'], columns=['actor'], values=['outer_negative']),
            file_name=os.path.join(output_directory, 'externalities_outer_negative.{}'),
            title='Outer negative externalities',
        )

    except DataError as ex:
        logging.exception(ex)
        print(ex)
    try:

        handle_data_frame(
            df=pd.pivot_table(df, index=['p'], columns=['actor'], values=['own']),
            file_name=os.path.join(output_directory, 'externalities_own.{}'),
            title='Own utility sun',
        )
    except DataError as ex:
        logging.exception(ex)
        print(ex)


if __name__ == '__main__':
    m = Manager(os.environ.get('DATABASE_URL'))
    m.init_database()

    model_run_id = 1

    write_summary_result(connection, [model_run_id], data_folder)
