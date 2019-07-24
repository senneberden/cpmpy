# translate expression tree to MiniZinc textual model

from ..expressions import *
from ..variables import *
from ..model_tools.get_variables import get_variables
from . import *

class MiniZincText(SolverInterface):
    # does not do solving itself (you can subclass it)
    # does provide conversion to text model
    def __init__(self):
        self.name = "minizinc_text"

    def solve(self, model):
        print(self.convert(model))

    def convert(self, model):
        modelvars = get_variables(model)
        txt_vars = "% Generated by CPpy\ninclude \"globals.mzn\";\n\n"
        for var in modelvars:
            if isinstance(var, BoolVarImpl):
                txt_vars += "var bool: BV{};\n".format(var.id)
            if isinstance(var, IntVarImpl):
                txt_vars += "var {}..{}: IV{};\n".format(var.lb, var.ub, var.id)

        txt_cons = self.convert_constraints(model.constraints)
        txt_obj  = self.convert_objective(model.objective)
                
        return txt_vars+"\n"+txt_cons+txt_obj

    def convert_constraints(self, cons):
        if cons is None:
            return ""

        # pretty-printing of first-level grouping (if present):
        cons_list = []
        if isinstance(cons, BoolOperator) and cons.name == "and":
            cons_list = cons.elems
        else:
            cons_list = [cons]
        
        # special case for top-level and
        # stick to default outputs for now...
        out = ""
        for con in cons_list:
            out += "constraint {};\n".format(self.convert_expression(con))
        return out+"\n"

    def convert_expression(self, expr):
        if isinstance(expr, np.ndarray):
            return list(expr.flat)

        if isinstance(expr, NumVarImpl):
            return expr # default

        if isinstance(expr, (MathOperator,Comparison)):
            # pretty printing: add () if math or comp
            left_str = self.convert_expression(expr.left)
            if isinstance(expr.left, (MathOperator,Comparison)):
                left_str = "({})".format(left_str)
            right_str = self.convert_expression(expr.right)
            if isinstance(expr.right, (MathOperator,Comparison)):
                right_str = "({})".format(right_str)
            return "{} {} {}".format(left_str, expr.name, right_str)

        if isinstance(expr, WeightedSum):
            elems = [self.convert_expression(e) for e in expr.elems]
            elems_str = "[{}]".format(",".join(map(str,elems)))
            subtype = "int"
            if all(isinstance(v, LogicalExpression) for v in iter(expr.elems)):
                subtype = "bool"
            txt  = "let {{\n      array[int] of int: w={},\n      array[int] of var {}: v={}\n    }} in\n".format(expr.weights, subtype, elems_str)
            txt += "      sum(i in 1..{}) (w[i]*v[i])".format(len(elems))
            return txt
        elif isinstance(expr, Sum):
            elems = [self.convert_expression(e) for e in expr.elems]
            return "sum({})".format(elems)

        if isinstance(expr, BoolOperator):
            name = expr.name
            elems = [self.convert_expression(e) for e in expr.elems]
            if len(elems) == 2:
                if name == 'and': name = "/\\"
                if name == 'or': name = "\\/"
                # xor is xor
                return "{} {} {}".format(elems[0], name, elems[1])

            # n-ary
            if name == 'and': name = 'forall'
            if name == 'xor': name = 'xorall'
            if name == 'or': name = 'exists'
            return "{}({})".format(name, elems)

        if isinstance(expr, GlobalConstraint):
            name = expr.name
            elems = [self.convert_expression(e) for e in expr.elems]

            # special cases:
            # element to array form
            if name == 'element':
                subtype = "int"
                if all(isinstance(v, LogicalExpression) for v in expr.elems[0].flat):
                    subtype = "bool"
                # minizinc is offset 1, which can be problematic for element...
                idx = "{}".format(elems[1])
                if isinstance(elems[1], IntVarImpl) and elems[1].lb == 0:
                    idx = "{}+1".format(idx)
                txt  = "\n    let {{ array[int] of var {}: arr={} }} in\n".format(subtype, elems[0])
                txt += "      arr[{}] = {}".format(idx,elems[2])
                return txt

            args_str = ", ".join(map(str,elems)) # elems are individual args
            return "{}({})".format(name, args_str)

        # default
        return expr # default

    def convert_objective(self, obj):
        if obj is None:
            return "solve satisfy;"
        if not isinstance(obj, Objective):
            raise Exception("Only single objective supported by minizinc_text")

        return "solve {} {};".format(obj.name.lower(),
                                     self.convert_expression(obj.expr))

