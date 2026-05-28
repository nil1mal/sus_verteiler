% =========================
% MULTI-DAY ASSIGNMENT
% =========================
% In multi mode: each student assigned to exactly one company on exactly one day
1 { assign(S,C) : pref(S,C,_), company_day(C,D) } 1 :- mode("multi"), has_pref(S), day(D), student(S).
1 { assign(S,C) : company(C), company_day(C,D) } 1    :- mode("multi"), student(S), not has_pref(S), day(D).

% Hard constraint: no student may span two days (safety net)
:- mode("multi"), assign(S,C1), assign(S,C2), 
   company_day(C1,D1), company_day(C2,D2), D1 != D2.

% =========================
% ASSIGNMENT (single mode)
% =========================
1 { assign(S,C) : pref(S,C,_) } 1 :- not mode("multi"), has_pref(S).
1 { assign(S,C) : company(C) } 1   :- not mode("multi"), student(S), not has_pref(S).