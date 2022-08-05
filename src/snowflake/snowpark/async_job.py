#
# Copyright (c) 2012-2022 Snowflake Computing Inc. All rights reserved.
#
from enum import Enum
from typing import List

import snowflake.snowpark
from snowflake.connector import SnowflakeConnection
from snowflake.connector.cursor import ResultMetadata
from snowflake.snowpark._internal.utils import result_set_to_iter, result_set_to_rows


class _AsyncDataType(Enum):
    PANDAS = "pandas"
    ROW = "row"
    ITERATOR = "iterator"
    PANDAS_BATCH = "pandas_batch"
    COUNT = "count"
    NO_TYPE = "no_type"


class AsyncJob:
    def __init__(
        self,
        query_id: str,
        query: str,
        conn: SnowflakeConnection,
        result_meta: List[ResultMetadata],
        server_connection: "snowflake.snowpark._internal.server_connection.ServerConnection",
        data_type: _AsyncDataType = _AsyncDataType.ROW,
    ) -> None:
        self.query_id = query_id
        self.query = query
        self._conn = conn
        self._cursor = self._conn.cursor()
        self._data_type = data_type
        self._result_meta = result_meta
        self._server_connection = server_connection

        return

    def is_done(self) -> bool:
        # return a bool value to indicate whether the query is finished
        status = self._conn.get_query_status(self.query_id)
        is_running = self._conn.is_still_running(status)

        return not is_running

    def cancel(self) -> None:
        # stop and cancel current query id
        self._conn._cancel_query(self.query, self.query_id)

    def result(self):
        # return result of the query, in the form of a list of Row object
        self._cursor.get_results_from_sfqid(self.query_id)
        result_data = self._cursor.fetchall()
        if self._data_type == _AsyncDataType.NO_TYPE:
            return None
        elif self._data_type == _AsyncDataType.ROW:
            return result_set_to_rows(result_data, self._result_meta)
        elif self._data_type == _AsyncDataType.ITERATOR:
            return result_set_to_iter(result_data, self._result_meta)
        elif self._data_type == _AsyncDataType.PANDAS:
            return self._server_connection._to_data_or_iter(
                self._cursor, to_pandas=True, to_iter=False
            )["data"]
        elif self._data_type == _AsyncDataType.PANDAS_BATCH:
            return self._server_connection._to_data_or_iter(
                self._cursor, to_pandas=True, to_iter=True
            )["data"]
        elif self._data_type == _AsyncDataType.COUNT:
            return result_data[0][0]
        else:
            raise ValueError(f"{self._data_type} is not a supported data type")
