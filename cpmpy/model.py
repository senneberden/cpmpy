#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## model.py
##
"""
    The `Model` class is a lazy container for constraints and an objective function.

    It is lazy in that it only stores the constraints and objective that are added
    to it. Processing only starts when solve() is called, and this does not modify
    the constraints or objective stored in the model.

    A model can be solved multiple times, and constraints can be added to it inbetween
    solve calls.

    See the examples for basic usage, which involves:

    - creation, e.g. `m = Model(cons, minimize=obj)` 
    - solving, e.g. `m.solve()` 
    - optionally, checking status/runtime, e.g. `m.status()` 

    ===============
    List of classes
    ===============
    .. autosummary::
        :nosignatures:

        Model
"""
import copy
import warnings

import numpy as np

from .exceptions import NotSupportedError
from .expressions.core import Expression
from .expressions.variables import NDVarArray
from .expressions.utils import is_any_list
from .solvers.utils import SolverLookup
from .solvers.solver_interface import SolverInterface, SolverStatus, ExitStatus

import pickle

class Model(object):
    """
    CPMpy Model object, contains the constraint and objective expressions
    """

    def __init__(self, *args, minimize=None, maximize=None):
        """
            Arguments of constructor:

            Arguments:
                `*args`: Expression object(s) or list(s) of Expression objects
                `minimize`: Expression object representing the objective to minimize
                `maximize`: Expression object representing the objective to maximize

            At most one of minimize/maximize can be set, if none are set, it is assumed to be a satisfaction problem
        """
        assert ((minimize is None) or (maximize is None)), "can not set both minimize and maximize"
        self.cpm_status = SolverStatus("Model") # status of solving this model, will be replaced

        # init list of constraints and objective
        self.constraints = []
        self.objective_ = None
        self.objective_is_min = None

        if len(args) == 1 and is_any_list(args):
            args = args[0]  # historical shortcut, treat as *args
        # use `__add__()` for typecheck
        if is_any_list(args):
            # add (and type-check) one by one
            for a in args:
                self += a
        else:
            self += args

        # store objective if present
        if maximize is not None:
            self.maximize(maximize)
        if minimize is not None:
            self.minimize(minimize)

        
    def __add__(self, con):
        """
            Add one or more constraints to the model

            .. code-block:: python

                m = Model()
                m += [x > 0]
        """
        if is_any_list(con):
            # catch some beginner mistakes: check that top-level Expressions in the list have Boolean return type
            for elem in con:
                if isinstance(elem, Expression) and not elem.is_bool() and not isinstance(elem, NDVarArray):
                    raise Exception(f"Model error: constraints must be expressions that return a Boolean value, `{elem}` does not.")

            if len(con) == 0:
                # ignore empty list
                return self
            elif len(con) == 1:
                # unpack size 1 list
                con = con[0]

        elif isinstance(con, Expression) and not con.is_bool():
            # catch some beginner mistakes: ensure that a top-level Expression has Boolean return type
            raise Exception(f"Model error: constraints must be expressions that return a Boolean value, `{con}` does not.")

        self.constraints.append(con)
        return self


    def objective(self, expr, minimize):
        """
            Post the given expression to the solver as objective to minimize/maximize

            Arguments:
                expr (Expression):      the CPMpy expression that represents the objective function
                minimize (bool):        whether it is a minimization problem (True) or maximization problem (False)

            'objective()' can be called multiple times, only the last one is stored
        """
        self.objective_ = expr
        self.objective_is_min = minimize

    def has_objective(self):
        return self.objective_ is not None

    def minimize(self, expr):
        """
            Minimize the given objective function

            `minimize()` can be called multiple times, only the last one is stored
        """
        self.objective(expr, minimize=True)

    def maximize(self, expr):
        """
            Maximize the given objective function

            `maximize()` can be called multiple times, only the last one is stored
        """
        self.objective(expr, minimize=False)

    # solver: name of supported solver or any SolverInterface object
    def solve(self, solver=None, time_limit=None, **kwargs):
        """ Send the model to a solver and get the result

        Arguments:
            solver (string or a name in SolverLookup.solvernames() or a SolverInterface class (Class, not object!), optional): 
                name of a solver to use. Run SolverLookup.solvernames() to find out the valid solver names on your system. (default: None = first available solver)
            time_limit (int or float, optional): time limit in seconds

            
        Returns:
            bool: the computed output:

            - True      if a solution is found (not necessarily optimal, e.g. could be after timeout)
            - False     if no solution is found
        """
        if kwargs and solver is None:
            raise NotSupportedError("Specify the solver when using kwargs, since they are solver-specific!")

        if isinstance(solver, SolverInterface):
            # for advanced use, call its constructor with this model
            s = solver(self)
        else:
            s = SolverLookup.get(solver, self)

        # call solver
        ret = s.solve(time_limit=time_limit, **kwargs)
        # store CPMpy status (s object has no further use)
        self.cpm_status = s.status()
        return ret

    def solveAll(self, solver=None, display=None, time_limit=None, solution_limit=None, **kwargs):
        """
            Compute all solutions and optionally display the solutions.

            Delegated to the solver, who might implement this efficiently

            Arguments:
                display:            either a list of CPMpy expressions, OR a callback function, called with the variables after value-mapping
                                    default/None: nothing displayed
                solution_limit:     stop after this many solutions (default: None)

            Returns: number of solutions found
        """
        if kwargs and solver is None:
            raise NotSupportedError("Specify the solver when using kwargs, since they are solver-specific!")

        if isinstance(solver, SolverInterface):
            # for advanced use, call its constructor with this model
            s = solver(self)
        else:
            s = SolverLookup.get(solver, self)

        # call solver
        ret = s.solveAll(display=display,time_limit=time_limit,solution_limit=solution_limit, call_from_model=True, **kwargs)
        # store CPMpy status (s object has no further use)
        self.cpm_status = s.status()
        return ret

    def status(self):
        """
            Returns the status of the latest solver run on this model

            Status information includes exit status (optimality) and runtime.

            Returns:
                an object of :class:`SolverStatus`
        """
        return self.cpm_status

    def objective_value(self):
        """
            Returns the value of the objective function of the latste solver run on this model

            Returns:
                an integer or 'None' if it is not run, or a satisfaction problem
        """
        return self.objective_.value()

    def __repr__(self):
        cons_str = ""
        for c in self.constraints:
            cons_str += "    {}\n".format(c)

        obj_str = ""
        if not self.objective_ is None:
            if self.objective_is_min:
                obj_str = "minimize "
            else:
                obj_str = "maximize "
        obj_str += str(self.objective_)
            
        return "Constraints:\n{}Objective: {}".format(cons_str, obj_str)


    def to_file(self, fname):
        """
            Serializes this model to a ``.pickle`` format

            Arguments:
                fname (FileDescriptorOrPath): Filename of the resulting serialized model
        """
        with open(fname,"wb") as f:
            pickle.dump(self, file=f)


    @staticmethod
    def from_file(fname):
        """
            Reads a Model instance from a binary pickled file

            Returns:
                an object of :class: `Model`
        """
        with open(fname, "rb") as f:
            m = pickle.load(f)
            # bug 158, we should increase the boolvar/intvar counters to avoid duplicate names
            from cpmpy.transformations.get_variables import get_variables_model  # avoid circular import
            vs = get_variables_model(m)
            bv_counter = 0
            iv_counter = 0
            for v in vs:
                if v.name.startswith("BV"):
                    try:
                        bv_counter = max(bv_counter, int(v.name[2:])+1)
                    except:
                        pass
                elif v.name.startswith("IV"):
                    try:
                        iv_counter = max(iv_counter, int(v.name[2:])+1)
                    except:
                        pass
            from cpmpy.expressions.variables import _BoolVarImpl, _IntVarImpl  # avoid circular import
            if (_BoolVarImpl.counter > 0 and bv_counter > 0) or \
                    (_IntVarImpl.counter > 0 and iv_counter > 0):
                warnings.warn(f"from_file '{fname}': contains auxiliary IV*/BV* variables with the same name as already created. Only add expressions created AFTER loadig this model to avoid issues with duplicate variables.")
            _BoolVarImpl.counter = max(_BoolVarImpl.counter, bv_counter)
            _IntVarImpl.counter = max(_IntVarImpl.counter, iv_counter)
            return m

    def copy(self):
        """
            Makes a shallow copy of the model.
            Constraints and variables are shared among the original and copied model (references to the same Expression objects). The /list/ of constraints itself is different, so adding or removing constraints from one model does not affect the other.
        """
        if self.objective_is_min:
            return Model(self.constraints, minimize=self.objective_)
        else:
            return Model(self.constraints, maximize=self.objective_)



    # keep for backwards compatibility
    def deepcopy(self, memodict={}):
        warnings.warn("Deprecated, use copy.deepcopy() instead, will be removed in stable version", DeprecationWarning)
        return copy.deepcopy(self, memodict)
