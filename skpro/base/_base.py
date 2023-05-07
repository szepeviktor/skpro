# -*- coding: utf-8 -*-
"""Base class and template for regressors and transformers."""
from skbase.base import BaseEstimator as _BaseEstimator
from skbase.base import BaseMetaEstimator as _BaseMetaEstimator
from skbase.base import BaseObject as _BaseObject


class _CommonTags:
    """Mixin for common tag definitions to all estimator base classes."""

    # config common to all estimators
    _config = {}

    _tags = {"estimator_type": "estimator"}


class BaseObject(_CommonTags, _BaseObject):
    """Base class for fittable objects."""


class BaseEstimator(_CommonTags, _BaseEstimator, BaseObject):
    """Base class for fittable objects."""


class BaseMetaEstimator(_CommonTags, _BaseMetaEstimator):
    """Base class for fittable composite meta-objects."""
