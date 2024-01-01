# copyright: skpro developers, BSD-3-Clause License (see LICENSE file)
"""Adapter to sklearn probabilistic regressors."""

__author__ = ["fkiraly"]

import numpy as np
import pandas as pd

from skpro.regression.base import BaseProbaRegressor
from skpro.utils.sklearn import prep_skl_df


class SklearnProbaReg(BaseProbaRegressor):
    """Adapter to sklearn regressors with variance prediction interface.

    Wraps an sklearn regressor that can be queried for variance prediction,
    and constructs an skpro regressor from it.

    The wrapped resgressor must have a ``predict`` with
    a ``return_std`` argument, and return a tuple of ``(y_pred, y_std)``,
    both ndarray of shape (n_samples,) or (n_samples, n_targets).

    Parameters
    ----------
    estimator : sklearn regressor
        Estimator to wrap, must have ``predict`` with ``return_std`` argument.
    """

    _tags = {}

    def __init__(self, estimator):
        self.estimator = estimator
        super().__init__()

    # todo: implement this, mandatory
    def _fit(self, X, y):
        """Fit regressor to training data.

        Writes to self:
            Sets fitted model attributes ending in "_".

        Parameters
        ----------
        X : pandas DataFrame
            feature instances to fit regressor to
        y : pandas DataFrame, must be same length as X
            labels to fit regressor to

        Returns
        -------
        self : reference to self
        """
        from sklearn import clone

        self.estimator_ = clone(self.estimator)
        X_inner = prep_skl_df(X)
        y_inner = prep_skl_df(y)

        if len(y_inner.columns) == 1:
            y_inner = y_inner.iloc[:, 0]
        self.estimator_.fit(X_inner, y_inner)
        return self

    def _predict(self, X):
        """Predict labels for data from features.

        State required:
            Requires state to be "fitted" = self.is_fitted=True

        Accesses in self:
            Fitted model attributes ending in "_"

        Parameters
        ----------
        X : pandas DataFrame, must have same columns as X in `fit`
            data to predict labels for

        Returns
        -------
        y : pandas DataFrame, same length as `X`, same columns as `y` in `fit`
            labels predicted for `X`
        """
        X_inner = prep_skl_df(X)
        y_pred = self.estimator_.predict(X_inner)
        return y_pred

    def _predict_var(self, X):
        """Compute/return variance predictions.

        private _predict_var containing the core logic, called from predict_var

        Parameters
        ----------
        X : pandas DataFrame, must have same columns as X in `fit`
            data to predict labels for

        Returns
        -------
        pred_var : pd.DataFrame
            Column names are exactly those of ``y`` passed in ``fit``.
            Row index is equal to row index of ``X``.
            Entries are variance prediction, for var in col index.
            A variance prediction for given variable and fh index is a predicted
            variance for that variable and index, given observed data.
        """
        X_inner = prep_skl_df(X)
        _, y_std = self.estimator_.predict(X_inner, return_std=True)
        y_std = pd.DataFrame(y_std, index=X.index, columns=X.columns)
        y_var = y_std ** 2
        return y_var

    @classmethod
    def get_test_params(cls, parameter_set="default"):
        """Return testing parameter settings for the estimator.

        Parameters
        ----------
        parameter_set : str, default="default"
            Name of the set of test parameters to return, for use in tests. If no
            special parameters are defined for a value, will return `"default"` set.

        Returns
        -------
        params : dict or list of dict, default = {}
            Parameters to create testing instances of the class
            Each dict are parameters to construct an "interesting" test instance, i.e.,
            `MyClass(**params)` or `MyClass(**params[i])` creates a valid test instance.
            `create_test_instance` uses the first (or only) dictionary in `params`
        """
        from sklearn.linear_model import BayesianRidge
        from sklearn.gaussian_process import GaussianProcessRegressor

        param1 = {"estimator": BayesianRidge()}
        param2 = {"estimator": GaussianProcessRegressor()}

        return [param1, param2]
