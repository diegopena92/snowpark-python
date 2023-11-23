#!/usr/bin/env python3
#
# Copyright (c) 2012-2023 Snowflake Computing Inc. All rights reserved.
#

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from snowflake.snowpark.exceptions import SnowparkSQLException


def get_sample_dataframe(session):
    data = [
        ["2023-01-01", 101, 200],
        ["2023-01-02", 101, 100],
        ["2023-01-03", 101, 300],
        ["2023-01-04", 102, 250],
    ]
    return session.create_dataframe(data).to_df(
        "ORDERDATE", "PRODUCTKEY", "SALESAMOUNT"
    )


def test_moving_agg(session):
    """Tests df.transform.moving_agg() happy path."""

    df = get_sample_dataframe(session)

    res = df.transform.moving_agg(
        aggs={"SALESAMOUNT": ["SUM", "AVG"]},
        window_sizes=[2, 3],
        order_by=["ORDERDATE"],
        group_by=["PRODUCTKEY"],
    )

    expected_data = {
        "ORDERDATE": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
        "PRODUCTKEY": [101, 101, 101, 102],
        "SALESAMOUNT": [200, 100, 300, 250],
        "SALESAMOUNT_SUM_2": [200, 300, 400, 250],
        "SALESAMOUNT_AVG_2": [200.0, 150.0, 200.0, 250.0],
        "SALESAMOUNT_SUM_3": [200, 300, 600, 250],
        "SALESAMOUNT_AVG_3": [200.0, 150.0, 200.0, 250.0],
    }
    expected_df = pd.DataFrame(expected_data)
    assert_frame_equal(
        res.order_by("ORDERDATE").to_pandas(), expected_df, check_dtype=False, atol=1e-1
    )


def test_moving_agg_custom_formatting(session):
    """Tests df.transform.moving_agg() with custom formatting of output columns."""

    df = get_sample_dataframe(session)

    def custom_formatter(input_col, agg, window):
        return f"{window}_{agg}_{input_col}"

    res = df.transform.moving_agg(
        aggs={"SALESAMOUNT": ["SUM", "AVG"]},
        window_sizes=[2, 3],
        order_by=["ORDERDATE"],
        group_by=["PRODUCTKEY"],
        col_formatter=custom_formatter,
    )

    expected_data = {
        "ORDERDATE": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
        "PRODUCTKEY": [101, 101, 101, 102],
        "SALESAMOUNT": [200, 100, 300, 250],
        "2_SUM_SALESAMOUNT": [200, 300, 400, 250],
        "2_AVG_SALESAMOUNT": [200.0, 150.0, 200.0, 250.0],
        "3_SUM_SALESAMOUNT": [200, 300, 600, 250],
        "3_AVG_SALESAMOUNT": [200.0, 150.0, 200.0, 250.0],
    }
    expected_df = pd.DataFrame(expected_data)
    assert_frame_equal(
        res.order_by("ORDERDATE").to_pandas(), expected_df, check_dtype=False, atol=1e-1
    )


def test_moving_agg_invalid_inputs(session):
    """Tests df.transform.moving_agg() with invalid window sizes."""

    df = get_sample_dataframe(session)

    with pytest.raises(ValueError) as exc:
        df.transform.moving_agg(
            aggs={"SALESAMOUNT": ["AVG"]},
            window_sizes=[-1, 2, 3],
            order_by=["ORDERDATE"],
            group_by=["PRODUCTKEY"],
        ).collect()
    assert "window_sizes must be a list of integers > 0" in str(exc)

    with pytest.raises(ValueError) as exc:
        df.transform.moving_agg(
            aggs={"SALESAMOUNT": ["AVG"]},
            window_sizes=[0, 2, 3],
            order_by=["ORDERDATE"],
            group_by=["PRODUCTKEY"],
        ).collect()
    assert "window_sizes must be a list of integers > 0" in str(exc)

    with pytest.raises(ValueError) as exc:
        df.transform.moving_agg(
            aggs={"SALESAMOUNT": []},
            window_sizes=[0, 2, 3],
            order_by=["ORDERDATE"],
            group_by=["PRODUCTKEY"],
        ).collect()
    assert "non-empty lists of strings as values" in str(exc)

    with pytest.raises(SnowparkSQLException) as exc:
        df.transform.moving_agg(
            aggs={"SALESAMOUNT": ["INVALID_FUNC"]},
            window_sizes=[1],
            order_by=["ORDERDATE"],
            group_by=["PRODUCTKEY"],
        ).collect()
    assert "Sliding window frame unsupported for function" in str(exc)
