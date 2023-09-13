"""Automated tests based on the skbase test suite template."""
import numbers
import types
from copy import deepcopy
from inspect import getfullargspec, signature

import joblib
import numpy as np
import pandas as pd
from skbase.testing import TestAllObjects as _TestAllObjects
from skbase.testing.utils.inspect import _get_args
from skbase.utils import deep_equals

from skpro.registry import OBJECT_TAG_LIST
from skpro.utils.git_diff import is_class_changed
from skpro.utils.random_state import set_random_state

# whether to test only estimators from modules that are changed w.r.t. main
# default is False, can be set to True by pytest --only_changed_modules True flag
ONLY_CHANGED_MODULES = False


class PackageConfig:
    """Contains package config variables for test classes."""

    # class variables which can be overridden by descendants
    # ------------------------------------------------------

    # package to search for objects
    # expected type: str, package/module name, relative to python environment root
    package_name = "skpro"

    # list of object types (class names) to exclude
    # expected type: list of str, str are class names
    exclude_objects = "ClassName"  # exclude classes from extension templates

    # list of valid tags
    # expected type: list of str, str are tag names
    valid_tags = OBJECT_TAG_LIST


class BaseFixtureGenerator:
    """Base class for fixture generation, overrides skbase object retrieval."""

    def _all_objects(self):
        """Retrieve list of all object classes of type self.object_type_filter."""
        obj_list = super()._all_objects()

        # this setting ensures that only estimators are tested that have changed
        # in the sense that any line in the module is different from main
        if ONLY_CHANGED_MODULES:
            obj_list = [obj for obj in obj_list if is_class_changed(obj)]

        return obj_list


class TestAllObjects(PackageConfig, BaseFixtureGenerator, _TestAllObjects):
    """Generic tests for all objects in the mini package."""

    # override this due to reserved_params index, columns, in the BaseDistribution class
    # index and columns params behave like pandas, i.e., are changed after __init__
    def test_constructor(self, object_class):
        """Check that the constructor has sklearn compatible signature and behaviour.

        Based on sklearn check_estimator testing of __init__ logic.
        Uses create_test_instance to create an instance.
        Assumes test_create_test_instance has passed and certified create_test_instance.

        Tests that:
        * constructor has no varargs
        * tests that constructor constructs an instance of the class
        * tests that all parameters are set in init to an attribute of the same name
        * tests that parameter values are always copied to the attribute and not changed
        * tests that default parameters are one of the following:
            None, str, int, float, bool, tuple, function, joblib memory, numpy primitive
            (other type parameters should be None, default handling should be by writing
            the default to attribute of a different name, e.g., my_param_ not my_param)
        """
        msg = "constructor __init__ should have no varargs"
        assert getfullargspec(object_class.__init__).varkw is None, msg

        estimator = object_class.create_test_instance()
        assert isinstance(estimator, object_class)

        # Ensure that each parameter is set in init
        init_params = _get_args(type(estimator).__init__)
        invalid_attr = set(init_params) - set(vars(estimator)) - {"self"}
        assert not invalid_attr, (
            "Estimator %s should store all parameters"
            " as an attribute during init. Did not find "
            "attributes `%s`." % (estimator.__class__.__name__, sorted(invalid_attr))
        )

        # Ensure that init does nothing but set parameters
        # No logic/interaction with other parameters
        def param_filter(p):
            """Identify hyper parameters of an estimator."""
            return p.name != "self" and p.kind not in [p.VAR_KEYWORD, p.VAR_POSITIONAL]

        init_params = [
            p
            for p in signature(estimator.__init__).parameters.values()
            if param_filter(p)
        ]

        params = estimator.get_params()

        test_params = object_class.get_test_params()
        if isinstance(test_params, list):
            test_params = test_params[0]
        test_params = test_params.keys()

        init_params = [param for param in init_params if param.name not in test_params]

        for param in init_params:
            assert param.default != param.empty, (
                "parameter `%s` for %s has no default value and is not "
                "set in `get_test_params`" % (param.name, estimator.__class__.__name__)
            )
            if type(param.default) is type:
                assert param.default in [np.float64, np.int64]
            else:
                assert type(param.default) in [
                    str,
                    int,
                    float,
                    bool,
                    tuple,
                    type(None),
                    np.float64,
                    types.FunctionType,
                ]

            reserved_params = object_class.get_class_tag("reserved_params", [])
            if param.name not in reserved_params:
                param_value = params[param.name]
                if isinstance(param_value, np.ndarray):
                    np.testing.assert_array_equal(param_value, param.default)
                elif bool(
                    isinstance(param_value, numbers.Real) and np.isnan(param_value)
                ):
                    # Allows to set default parameters to np.nan
                    assert param_value is param.default, param.name
                else:
                    assert param_value == param.default, param.name

    # same here, reserved_params need to be dealt with
    def test_set_params_sklearn(self, object_class):
        """Check that set_params works correctly, mirrors sklearn check_set_params.

        Instead of the "fuzz values" in sklearn's check_set_params,
        we use the other test parameter settings (which are assumed valid).
        This guarantees settings which play along with the __init__ content.
        """
        from skbase.testing.utils.deep_equals import deep_equals

        estimator = object_class.create_test_instance()
        test_params = object_class.get_test_params()
        if not isinstance(test_params, list):
            test_params = [test_params]

        reserved_params = object_class.get_class_tag(
            "reserved_params", tag_value_default=[]
        )

        for params in test_params:
            # we construct the full parameter set for params
            # params may only have parameters that are deviating from defaults
            # in order to set non-default parameters back to defaults
            params_full = object_class.get_param_defaults()
            params_full.update(params)

            msg = f"set_params of {object_class.__name__} does not return self"
            est_after_set = estimator.set_params(**params_full)
            assert est_after_set is estimator, msg

            def unreserved(params):
                return {p: v for p, v in params.items() if p not in reserved_params}

            est_params = estimator.get_params(deep=False)
            is_equal, equals_msg = deep_equals(
                unreserved(est_params), unreserved(params_full), return_msg=True
            )
            msg = (
                f"get_params result of {object_class.__name__} (x) does not match "
                f"what was passed to set_params (y). "
                f"Reason for discrepancy: {equals_msg}"
            )
            assert is_equal, msg


class TestAllEstimators(PackageConfig, _TestAllObjects):
    """Package level tests for all sktime estimators, i.e., objects with fit."""

    def test_fit_updates_state(self, object_instance, scenario):
        """Check fit/update state change."""
        # Check that fit updates the is-fitted states
        attrs = ["_is_fitted", "is_fitted"]

        estimator = object_instance
        object_class = type(object_instance)

        msg = (
            f"{object_class.__name__}.__init__ should call "
            f"super({object_class.__name__}, self).__init__, "
            "but that does not seem to be the case. Please ensure to call the "
            f"parent class's constructor in {object_class.__name__}.__init__"
        )
        assert hasattr(estimator, "_is_fitted"), msg

        # Check is_fitted attribute is set correctly to False before fit, at init
        for attr in attrs:
            assert not getattr(
                estimator, attr
            ), f"Estimator: {estimator} does not initiate attribute: {attr} to False"

        fitted_estimator = scenario.run(object_instance, method_sequence=["fit"])

        # Check is_fitted attributes are updated correctly to True after calling fit
        for attr in attrs:
            assert getattr(
                fitted_estimator, attr
            ), f"Estimator: {estimator} does not update attribute: {attr} during fit"

    def test_fit_returns_self(self, object_instance, scenario):
        """Check that fit returns self."""
        fit_return = scenario.run(object_instance, method_sequence=["fit"])
        assert (
            fit_return is object_instance
        ), f"Estimator: {object_instance} does not return self when calling fit"

    def test_fit_does_not_overwrite_hyper_params(self, object_instance, scenario):
        """Check that we do not overwrite hyper-parameters in fit."""
        estimator = object_instance
        set_random_state(estimator)

        # Make a physical copy of the original estimator parameters before fitting.
        params = estimator.get_params()
        original_params = deepcopy(params)

        # Fit the model
        fitted_est = scenario.run(object_instance, method_sequence=["fit"])

        # Compare the state of the model parameters with the original parameters
        new_params = fitted_est.get_params()
        for param_name, original_value in original_params.items():
            new_value = new_params[param_name]

            # We should never change or mutate the internal state of input
            # parameters by default. To check this we use the joblib.hash function
            # that introspects recursively any subobjects to compute a checksum.
            # The only exception to this rule of immutable constructor parameters
            # is possible RandomState instance but in this check we explicitly
            # fixed the random_state params recursively to be integer seeds.
            msg = (
                "Estimator %s should not change or mutate "
                " the parameter %s from %s to %s during fit."
                % (estimator.__class__.__name__, param_name, original_value, new_value)
            )
            # joblib.hash has problems with pandas objects, so we use deep_equals then
            if isinstance(original_value, (pd.DataFrame, pd.Series)):
                assert deep_equals(new_value, original_value), msg
            else:
                assert joblib.hash(new_value) == joblib.hash(original_value), msg
