% =========================
% ASSIGNMENT
% =========================

% Every student must be assigned
1 { assign(S,C) : pref(S,C,_) } 1 :- has_pref(S).
1 { assign(S,C) : company(C) } 1 :- student(S), not has_pref(S).
% 1 { assign(S,C) : company(C) } 1 :- student(S).

% Capacity constraint
:- capacity(C,Cap), #count { S : assign(S,C) } > Cap.
:- assign(S,C), has_pref(S), not pref(S,C,_).

% =========================
% HELPERS
% =========================

has_pref(S) :- pref(S,_,_).
no_pref(S) :- student(S), not has_pref(S).


% =========================
% OPTIMIZATION
% =========================

% Prefer high scores (5 best)
:~ assign(S,C), pref(S,C,Score). [ (6-Score)@1, S, C ]

% Strongly discourage assigning to unrated companies
:~ assign(S,C), not pref(S,C,_). [50@2, S, C]

% Penalize students with no preferences
:~ assign(S,_), no_pref(S). [20@3, S]


% =========================
% OUTPUT
% =========================
#show assign/2.