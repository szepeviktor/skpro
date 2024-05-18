# copyright: skpro developers, BSD-3-Clause License (see LICENSE file)
"""I.i.d. sample from a distribution."""

__author__ = ["fkiraly"]

import numpy as np
import pandas as pd
from scipy.special import erf, erfinv

from skpro.distributions.base import BaseDistribution


class IID(BaseDistribution):
    r"""An i.i.d. sample of a given distribution.

    Constructed with a scalar or row distribution.

    Broadcasts to an i.i.d. sample based on index and columns.

    If ``distribution`` is scalar, broadcasts across index and columns.

    If ``distribution`` is a row distribution, ``columns`` must be
    same number of rows if passed; broadcasts across index.

    Parameters
    ----------
    distribution : skpro distribution - scalar, or shape (1, d)
        mean of the normal distribution
    index : pd.Index, optional, default = RangeIndex
    columns : pd.Index, optional, default = RangeIndex

    Example
    -------
    >>> import pandas as pd
    >>> from skpro.distributions.compose import IID
    >>> from skpro.distributions.normal import Normal

    >>> n = Normal(mu=0, sigma=1)
    >>> index = pd.Index([1, 2, 4, 6])
    >>> n_iid = IID(n, index=index)
    """

    _tags = {
        "capabilities:approx": ["pdfnorm"],
        "capabilities:exact": ["mean", "var", "energy", "pdf", "log_pdf", "cdf", "ppf"],
        "distr:measuretype": "continuous",
        "distr:paramtype": "parametric",
    }

    def __init__(self, distribution, index=None, columns=None):
        self.distibution = distribution

        dist_scalar = distribution.ndim == 0
        dist_cols = distribution.columns

        # set _bc_cols - do we broadcast rows?
        if dist_scalar:
            self._bc_cols = True
        else:  # not dist_scalar
            if distribution.shape[1] == 1 and columns is not None:
            self._bc_cols = True

        # what is the index of self?
        if not dist_scalar and index is None:
            index = distribution.index
            assert len(index) == 1
        if dist_scalar and index is None:
            index = pd.RangeIndex(1)
        # else index is what was passed

        # what are columns of self?
        if dist_scalar and columns is None:
            columns = pd.RangeIndex(1)
        if not dist_scalar:
            if columns is None:
                columns = dist_cols
            if not len(dist_cols) == 1 and columns is not None:
                assert len(dist_cols) == len(columns)

        super().__init__(index=index, columns=columns)

    def _mean(self):
        """Return expected value of the distribution.

        Returns
        -------
        2D np.ndarray, same shape as ``self``
            expected value of distribution (entry-wise)
        """
        return self._bc_params["mu"]

    def _var(self):
        r"""Return element/entry-wise variance of the distribution.

        Returns
        -------
        2D np.ndarray, same shape as ``self``
            variance of the distribution (entry-wise)
        """
        return self._bc_params["sigma"] ** 2

    def _pdf(self, x):
        """Probability density function.

        Parameters
        ----------
        x : 2D np.ndarray, same shape as ``self``
            values to evaluate the pdf at

        Returns
        -------
        2D np.ndarray, same shape as ``self``
            pdf values at the given points
        """
        mu = self._bc_params["mu"]
        sigma = self._bc_params["sigma"]

        pdf_arr = np.exp(-0.5 * ((x - mu) / sigma) ** 2)
        pdf_arr = pdf_arr / (sigma * np.sqrt(2 * np.pi))
        return pdf_arr

    def _log_pdf(self, x):
        """Logarithmic probability density function.

        Parameters
        ----------
        x : 2D np.ndarray, same shape as ``self``
            values to evaluate the pdf at

        Returns
        -------
        2D np.ndarray, same shape as ``self``
            log pdf values at the given points
        """
        mu = self._bc_params["mu"]
        sigma = self._bc_params["sigma"]

        lpdf_arr = -0.5 * ((x - mu) / sigma) ** 2
        lpdf_arr = lpdf_arr - np.log(sigma * np.sqrt(2 * np.pi))
        return lpdf_arr

    def _cdf(self, x):
        """Cumulative distribution function.

        Parameters
        ----------
        x : 2D np.ndarray, same shape as ``self``
            values to evaluate the cdf at

        Returns
        -------
        2D np.ndarray, same shape as ``self``
            cdf values at the given points
        """
        mu = self._bc_params["mu"]
        sigma = self._bc_params["sigma"]

        cdf_arr = 0.5 + 0.5 * erf((x - mu) / (sigma * np.sqrt(2)))
        return cdf_arr

    def _ppf(self, p):
        """Quantile function = percent point function = inverse cdf.

        Parameters
        ----------
        p : 2D np.ndarray, same shape as ``self``
            values to evaluate the ppf at

        Returns
        -------
        2D np.ndarray, same shape as ``self``
            ppf values at the given points
        """
        mu = self._bc_params["mu"]
        sigma = self._bc_params["sigma"]

        icdf_arr = mu + sigma * np.sqrt(2) * erfinv(2 * p - 1)
        return icdf_arr

    def _energy_self(self):
        r"""Energy of self, w.r.t. self.

        :math:`\mathbb{E}[|X-Y|]`, where :math:`X, Y` are i.i.d. copies of self.

        Private method, to be implemented by subclasses.

        Returns
        -------
        2D np.ndarray, same shape as ``self``
            energy values w.r.t. the given points
        """
        sigma = self._bc_params["sigma"]
        energy_arr = 2 * sigma / np.sqrt(np.pi)
        if energy_arr.ndim > 0:
            energy_arr = np.sum(energy_arr, axis=1)
        return energy_arr

    def _energy_x(self, x):
        r"""Energy of self, w.r.t. a constant frame x.

        :math:`\mathbb{E}[|X-x|]`, where :math:`X` is a copy of self,
        and :math:`x` is a constant.

        Private method, to be implemented by subclasses.

        Parameters
        ----------
        x : 2D np.ndarray, same shape as ``self``
            values to compute energy w.r.t. to

        Returns
        -------
        2D np.ndarray, same shape as ``self``
            energy values w.r.t. the given points
        """
        mu = self._bc_params["mu"]
        sigma = self._bc_params["sigma"]

        cdf = self.cdf(x)
        pdf = self.pdf(x)
        energy_arr = (x - mu) * (2 * cdf - 1) + 2 * sigma**2 * pdf
        if energy_arr.ndim > 0:
            energy_arr = np.sum(energy_arr, axis=1)
        return energy_arr

    @classmethod
    def get_test_params(cls, parameter_set="default"):
        """Return testing parameter settings for the estimator."""
        # array case examples
        params1 = {"mu": [[0, 1], [2, 3], [4, 5]], "sigma": 1}
        params2 = {
            "mu": 0,
            "sigma": 1,
            "index": pd.Index([1, 2, 5]),
            "columns": pd.Index(["a", "b"]),
        }
        # scalar case examples
        params3 = {"mu": 1, "sigma": 2}
        return [params1, params2, params3]
