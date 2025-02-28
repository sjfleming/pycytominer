"""
Miscellaneous utility functions
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
from pycytominer.cyto_utils.features import (
    infer_cp_features,
    convert_compartment_format_to_list,
)

default_metadata_file = os.path.join(
    os.path.dirname(__file__), "..", "data", "metadata_feature_dictionary.txt"
)


def get_default_compartments():
    """Returns default compartments.

    Returns
    -------
    list of str
        Default compartments.

    """

    return ["cells", "cytoplasm", "nuclei"]


def check_compartments(compartments):
    """Checks if the input compartments are noncanonical compartments.

    Parameters
    ----------
    compartments : list of str
        Input compartments.

    Returns
    -------
    None
        Nothing is returned.

    """

    default_compartments = get_default_compartments()

    compartments = convert_compartment_format_to_list(compartments)

    non_canonical_compartments = []
    for compartment in compartments:
        if compartment not in default_compartments:
            non_canonical_compartments.append(compartment)

    if len(non_canonical_compartments) > 0:
        warn_str = "Non-canonical compartment detected: {x}".format(
            x=", ".join(non_canonical_compartments)
        )
        warnings.warn(warn_str)


def load_known_metadata_dictionary(metadata_file=default_metadata_file):
    """From a tab separated text file (two columns: ["compartment", "feature"]), load
    previously known metadata columns per compartment.

    Parameters
    ----------
    metadata_file : str, optional
        File location of the metadata text file. Uses a default dictionary if you do not specify.

    Returns
    -------
    dict
        Compartment (keys) mappings to previously known metadata (values).

    """

    metadata_dict = {}
    with open(metadata_file) as meta_fh:
        next(meta_fh)
        for line in meta_fh:
            compartment, feature = line.strip().split("\t")
            compartment = compartment.lower()
            if compartment in metadata_dict:
                metadata_dict[compartment].append(feature)
            else:
                metadata_dict[compartment] = [feature]

    return metadata_dict


def check_correlation_method(method):
    """Confirm that the input method is currently supported.

    Parameters
    ----------
    method : str
        The correlation metric to use.

    Returns
    -------
    str
        Correctly formatted correlation method.

    """

    method = method.lower()
    avail_methods = ["pearson", "spearman", "kendall"]
    assert method in avail_methods, "method {} not supported, select one of {}".format(
        method, avail_methods
    )

    return method


def check_aggregate_operation(operation):
    """Confirm that the input operation for aggregation is currently supported.

    Parameters
    ----------
    operation : str
        Aggregation operation to provide.

    Returns
    -------
    str
        Correctly formatted operation method.

    """

    operation = operation.lower()
    avail_ops = ["mean", "median"]
    assert (
        operation in avail_ops
    ), "operation {} not supported, select one of {}".format(operation, avail_ops)

    return operation


def check_consensus_operation(operation):
    """Confirm that the input operation for consensus is currently supported.

    Parameters
    ----------
    operation: str
        Consensus operation to provide.

    Returns
    -------
    str
        Correctly formatted operation method.

    """

    operation = operation.lower()
    avail_ops = ["modz"]  # All aggregation operations are also supported
    try:
        operation = check_aggregate_operation(operation)
    except AssertionError:
        assert (
            operation in avail_ops
        ), "operation {} not supported, select one of {} or see aggregate.py".format(
            operation, avail_ops
        )

    return operation


def check_fields_of_view_format(fields_of_view):
    """Confirm that the input fields of view is valid.

    Parameters
    ----------
    fields_of_view : list of int
        List of integer fields of view.

    Returns
    -------
    str or list of int
        Correctly formatted fields_of_view variable.

    """

    if fields_of_view != "all":
        if isinstance(fields_of_view, list):
            if all(isinstance(x, int) for x in fields_of_view):
                return fields_of_view
            else:
                try:
                    return list(map(int, fields_of_view))
                except ValueError:
                    raise TypeError(
                        f"Variables of type int expected, however some of the input fields of view are not integers."
                    )
        else:
            raise TypeError(
                f"Variable of type list expected, however type {type(fields_of_view)} was passed."
            )
    else:
        return fields_of_view


def check_fields_of_view(data_fields_of_view, input_fields_of_view):
    """Confirm that the input list of fields of view is a subset of the list of fields of view in the image table.

    Parameters
    ----------
    data_fields_of_view : list of int
        Fields of view in the image table.
    input_fields_of_view : list of int
        Input fields of view.

    Returns
    -------
    None
        Nothing is returned.

    """

    try:
        assert len(
            list(np.intersect1d(data_fields_of_view, input_fields_of_view))
        ) == len(input_fields_of_view)
    except AssertionError:
        raise ValueError(
            "Some of the input fields of view are not present in the image table."
        )


def get_pairwise_correlation(population_df, method="pearson"):
    """Given a population dataframe, calculate all pairwise correlations.

    Parameters
    ----------
    population_df : pandas.core.frame.DataFrame
        Includes metadata and observation features.
    method : str, default "pearson"
        Which correlation matrix to use to test cutoff.
    Returns
    -------
    list of str
        Features to exclude from the population_df.

    """

    # Check that the input method is supported
    method = check_correlation_method(method)

    # Get a symmetrical correlation matrix
    data_cor_df = population_df.corr(method=method)

    # Create a copy of the dataframe to generate upper triangle of zeros
    data_cor_natri_df = data_cor_df.copy()

    # Replace upper triangle in correlation matrix with NaN
    data_cor_natri_df = data_cor_natri_df.where(
        np.tril(np.ones(data_cor_natri_df.shape), k=-1).astype(np.bool)
    )

    # Acquire pairwise correlations in a long format
    # Note that we are using the NaN upper triangle DataFrame
    pairwise_df = data_cor_natri_df.stack().reset_index()
    pairwise_df.columns = ["pair_a", "pair_b", "correlation"]

    return data_cor_df, pairwise_df
