(*
    In case the CellContext is not Global, can access via "Global`MakeConsts[...]".
    Can also add the following to the CellProlog config: "$ContextPath = DeleteDuplicates[Prepend[$ContextPath,"Global`"]]"

    Based on https://mathematica.stackexchange.com/questions/31708/creating-a-block-from-a-list-of-rules
    See also my "make const" mathematica notebooks.
*)
MakeConsts[rules_List] := Function[body, Block @@ Join[Apply[Set, Hold[rules], {2}], Hold[body]], HoldAll]
