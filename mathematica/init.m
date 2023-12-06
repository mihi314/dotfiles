(*
    In case the CellContext is not Global, can access via "Global`MakeConsts[...]".
    Can also add the following to the CellProlog config: "$ContextPath = DeleteDuplicates[Prepend[$ContextPath,"Global`"]]"

    Based on https://mathematica.stackexchange.com/questions/31708/creating-a-block-from-a-list-of-rules
    See also my "make const" mathematica notebooks.
*)
SetAttributes[EvaluateOneStep, HoldAll]
EvaluateOneStep[expr_] := Module[{P},
    P = (P = Return[#, TraceScan] &) &;
    TraceScan[P, expr, TraceDepth -> 1]
]

SetAttributes[MakeConsts, HoldAll]
MakeConsts[rules_List] := Function[body, Block @@ Join[
    Replace[Hold[rules], {(a_ -> b_) :> (a = b), (a_ :> b_) :> (a := b)}, {2}],
    Hold[body]
], HoldAll]
MakeConsts[symbol_] := Function[body, EvaluateOneStep[symbol] /. _[x_] :> MakeConsts[x][body], HoldAll]
