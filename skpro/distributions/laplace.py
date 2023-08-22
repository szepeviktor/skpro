# -*- coding: utf-8 -*-
# copyright: sktime developers, BSD-3-Clause License (see LICENSE file)
"""Normal/Gaussian probability distribution."""

__author__ = ["fkiraly"]

import numpy as np
import pandas as pd
from scipy.special import erf, erfinv

from skpro.distributions.base import BaseDistribution


class Laplace(BaseDistribution):
    """Laplace distribution.

    Parameters
    ----------
    mean : float or array of float (1D or 2D)
        mean of the distribution
    scale : float or array of float (1D or 2D), must be positive
        scale parameter of the distribution, same as standard deviation / sqrt(2)
    index : pd.Index, optional, default = RangeIndex
    columns : pd.Index, optional, default = RangeIndex

    Example
    -------
    >>> from skpro.distributions.normal import Normal

    >>> n = Laplace(mu=[[0, 1], [2, 3], [4, 5]], scale=1)
    """

    _tags = {
        "capabilities:approx": ["pdfnorm"],
        "capabilities:exact": ["mean", "var", "energy", "pdf", "log_pdf", "cdf", "ppf"],
        "distr:measuretype": "continuous",
    }

    def __init__(self, mu, scale, index=None, columns=None):

        self.mu = mu
        self.scale = scale
        self.index = index
        self.columns = columns

        # todo: untangle index handling
        # and broadcast of parameters.
        # move this functionality to the base class
        self._mu, self._scale = self._get_bc_params()
        shape = self._mu.shape

        if index is None:
            index = pd.RangeIndex(shape[0])

        if columns is None:
            columns = pd.RangeIndex(shape[1])

        super().__init__(index=index, columns=columns)

    def _get_bc_params(self):
        """Fully broadcast parameters of self, given param shapes and index, columns."""
        to_broadcast = [self.mu, self.scale]
        if hasattr(self, "index") and self.index is not None:
            to_broadcast += [self.index.to_numpy().reshape(-1, 1)]
        if hasattr(self, "columns") and self.columns is not None:
            to_broadcast += [self.columns.to_numpy()]
        bc = np.broadcast_arrays(*to_broadcast)
        return bc[0], bc[1]

    def mean(self):
        r"""Return expected value of the distribution.

        Let :math:`X` be a random variable with the distribution of `self`.
        Returns the expectation :math:`\mathbb{E}[X]`

        Returns
        -------
        pd.DataFrame with same rows, columns as `self`
        expected value of distribution (entry-wise)
        """
        mean_arr = self._mu
        return pd.DataFrame(mean_arr, index=self.index, columns=self.columns)

    def var(self):
        r"""Return element/entry-wise variance of the distribution.

        Let :math:`X` be a random variable with the distribution of `self`.
        Returns :math:`\mathbb{V}[X] = \mathbb{E}\left(X - \mathbb{E}[X]\right)^2`

        Returns
        -------
        pd.DataFrame with same rows, columns as `self`
        variance of distribution (entry-wise)
        """
        sd_arr = self._scale / np.sqrt(2)
        return pd.DataFrame(sd_arr, index=self.index, columns=self.columns) ** 2

    def pdf(self, x):
        """Probability density function."""
        d = self.loc[x.index, x.columns]
        pdf_arr = np.exp(-np.abs((x.values - d.mu) / d.scale))
        pdf_arr = pdf_arr / (2 * d.scale)
        return pd.DataFrame(pdf_arr, index=x.index, columns=x.columns)

    def log_pdf(self, x):
        """Logarithmic probability density function."""
        d = self.loc[x.index, x.columns]
        lpdf_arr = -np.abs((x.values - d.mu) / d.scale)
        lpdf_arr = lpdf_arr - np.log(2 * d.scale)
        return pd.DataFrame(lpdf_arr, index=x.index, columns=x.columns)

    def cdf(self, x):
        """Cumulative distribution function."""
        d = self.loc[x.index, x.columns]
        sgn_arr = np.sign(x.values - d.mu)
        exp_arr = np.exp(-np.abs((x.values - d.mu) / d.scale))
        cdf_arr = 0.5 + 0.5 * sgn_arr * (1 - exp_arr)
        return pd.DataFrame(cdf_arr, index=x.index, columns=x.columns)

    def ppf(self, p):
        """Quantile function = percent point function = inverse cdf."""
        d = self.loc[p.index, p.columns]
        sgn_arr = np.sign(p.values - d.mu)
        icdf_arr = d.mu - d.scale * sgn_arr * np.log(1 - 2 * np.abs(p.values - 0.5))
        return pd.DataFrame(icdf_arr, index=p.index, columns=p.columns)

    @classmethod
    def get_test_params(cls, parameter_set="default"):
        """Return testing parameter settings for the estimator."""
        params1 = {"mu": [[0, 1], [2, 3], [4, 5]], "scale": 1}
        params2 = {
            "mu": 0,
            "scale": 1,
            "index": pd.Index([1, 2, 5]),
            "columns": pd.Index(["a", "b"]),
        }
        return [params1, params2]
