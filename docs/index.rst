CPMpy: Constraint Programming and Modeling in Python
====================================================

Constraint Programming is a methodology for solving combinatorial optimisation problems like assignment problems or covering, packing and scheduling problems. Problems that require searching over discrete decision variables.

CPMpy is a Constraint Programming and Modeling library in Python, based on numpy, with direct solver access. Key features are:

* Easy to integrate with machine learning and visualisation libraries, because decision variables are numpy arrays.
* Solver-independent: transparently translating to CP, MIP, SMT and SAT solvers
* Incremental solving and direct access to the underlying solvers
* And much more...

.. toctree::
   :maxdepth: 1
   :caption: Usage

   modeling

.. _supported-solvers:

Supported solvers
-----------------

CPMpy can translate to many different solvers, and even provides direct access to them.

.. list-table::
   :header-rows: 1

   * - **Solver**
     - **Technology**
     - **Installation**
     - **Assumption interface?**
     - **Notes**
   * - :doc:`OR-Tools <api/solvers/ortools>`
     - CP-SAT
     - pip
     - Yes
     - Assumptions NOT incremental! Every solve starts from scratch
   * - :doc:`Choco <api/solvers/choco>`
     - CP
     - pip
     - No
     - 
   * - :doc:`GCS <api/solvers/gcs>`
     - CP
     - pip
     - No
     - Supports proof logging
   * - :doc:`MiniZinc <api/solvers/minizinc>`
     - CP
     - pip + local install
     - No
     - Communicates through textfiles
   * - :doc:`Z3 <api/solvers/z3>`
     - SMT
     - pip
     - Yes
     - 
   * - :doc:`CP Optimizer <api/solvers/cpo>`
     - CP
     - pip + local install + (aca.) license
     - No
     - 
   * - :doc:`Gurobi <api/solvers/gurobi>`
     - ILP
     - pip + (aca.) license
     - No
     - 
   * - :doc:`Exact <api/solvers/exact>`
     - Pseudo-Boolean
     - pip (only Linux, Win(py>3.10))
     - Yes
     - Manual installation on Mac possible
   * - :doc:`PySAT <api/solvers/pysat>`
     - SAT
     - pip
     - Yes
     - Only Boolean variables (CPMpy transformation incomplete)
   * - :doc:`PySDD <api/solvers/pysdd>`
     - SAT Counter
     - pip
     - Yes
     - Knowledge compiler, only Boolean variables (CPMpy transformation incomplete)

Different solvers excell at different problems. Try multiple!

* Our rule-of-thumb ordering when *solving* a problem: OrTools > Gurobi > Exact > Others
* Our rule-of-thumb ordering when *explaining* a problem: Exact > Z3 > OrTools > Others


To make clear how well supported and tested these solvers are, we work with a tiered classification:

* Tier 1 solvers: passes all internal tests, passes our bigtest suit, will be fuzztested in the near future
    - "ortools" the OR-Tools CP-SAT solver
    - "pysat" the PySAT library and its many SAT solvers ("pysat:glucose4", "pysat:lingeling", etc)

* Tier 2 solvers: passes all internal tests, might fail on edge cases in bigtest
    - "minizinc" the MiniZinc modeling system and its many solvers ("minizinc:gecode", "minizinc:chuffed", etc)
    - "z3" the SMT solver and theorem prover
    - "gurobi" the MIP solver
    - "PySDD" a Boolean knowledge compiler
    - "exact" the Exact integer linear programming solver
    - "choco" the Choco constraint solver
    - "gcs" the Glasgow Constraint Solver
    - "cpo" the CP Optimizer solver

* Tier 3 solvers: they are work in progress and live in a pull request
    - "scip" the SCIP Optimisation Suite (open source MIP solver)
    - "cplex" the CPLEX solver (commercial MIP solver)

We hope to upgrade many of these solvers to higher tiers, as well as adding new ones. Reach out on github if you want to help out.


.. toctree::
   :maxdepth: 1
   :caption: Advanced guides:

   how_to_debug
   multiple_solutions
   unsat_core_extraction
   developers
   adding_solver

Open Source
-----------

Source code and bug reports at https://github.com/CPMpy/cpmpy

CPMpy has the open-source `Apache 2.0 license <https://github.com/cpmpy/cpmpy/blob/master/LICENSE>`_ and is run as an open-source project. All discussions happen on Github, even between direct colleagues, and all changes are reviewed through pull requests.

**Join us!** We welcome any feedback and contributions. You are also free to reuse any parts in your own project. A good starting point to contribute is to add your models to the examples folder.


Are you a solver developer? We are keen to integrate solvers that have a python API on pip. If this is the case for you, or if you want to discuss what it best looks like, do contact us!


.. toctree::
   :maxdepth: 1
   :caption: API documentation:

   api/expressions
   api/model
   api/solvers
   api/transformations
   api/tools
