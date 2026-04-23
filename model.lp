% =========================
% ASSIGNMENT
% =========================

% Every student must be assigned to exactly one company
1 { assign(S,C) : pref(S,C,_) } 1 :- has_pref(S).
1 { assign(S,C) : company(C) } 1 :- student(S), not has_pref(S).

% Capacity upper bound
:- capacity(C,Cap), #count { S : assign(S,C) } > Cap.

% Students with preferences can only be assigned to rated companies
:- assign(S,C), has_pref(S), not pref(S,C,_).


% =========================
% RULE 2: Exact student count for specific companies (hard)
% Activated by: exact_count("Company", N).
% =========================
:- exact_count(C,N), #count { S : assign(S,C) } != N.


% =========================
% RULE 3: Max preference rank allowed per company (hard)
% Activated by: max_prio("Company", MaxRank).
% E.g. max_prio("Caritas", 2) => only students with pref rank 1 or 2 may be assigned
% =========================
:- assign(S,C), max_prio(C,MaxP), pref(S,C,Score), Score > MaxP.


% =========================
% HELPERS
% =========================

has_pref(S) :- pref(S,_,_).
no_pref(S)  :- student(S), not has_pref(S).

% Rule 1: resolve effective minimum per company (three-way priority):
%   1. exact_count companies are exempt (genau controls headcount exactly)
%   2. company_min override from the `min` CSV column takes precedence
%   3. global min_per_company default as fallback
effective_min(C, 0)   :- exact_count(C, _).
effective_min(C, M)   :- company_min(C, M), not exact_count(C, _).
effective_min(C, M)   :- min_per_company(M), company(C),
                         not company_min(C, _), not exact_count(C, _).

under_min(C, Diff) :-
    effective_min(C, Min),
    Min > 0,
    company(C),
    Count = #count { S : assign(S,C) },
    Count < Min,
    Diff = Min - Count.

% Rule 4: count how many rank-1 preferences each student has
num_top_prefs(S, N) :- student(S), N = #count { C : pref(S,C,1) }.

% A student is a "sole-top" student if they have exactly one rank-1 preference
sole_top(S, C) :- pref(S,C,1), num_top_prefs(S,1).


% =========================
% OPTIMIZATION
% (higher @priority = evaluated first / harder to violate)
% =========================

% @4 – Student happiness + Company happiness compete at the same level.
%
%   Both goals use @4 so the solver genuinely balances them via weights:
%     - Student:  Score per assignment (1=best, 5=worst)
%     - Company:  Diff * MIN_WEIGHT per missing student below minimum
%
%   Weight ratio determines the trade-off:
%     MIN_WEIGHT = 20  =>  1 missing student = 10 students each dropping 1 rank
%   Tune MIN_WEIGHT up (stricter minima) or down (friendlier to preferences).
%
:~ assign(S,C), pref(S,C,Score). [Score@4, S, C]
:~ under_min(C, Diff). [Diff * 20@4, C]

% @3 – RULE 4: Sole-rank-1 students must preferably get their unique top choice.
%   Students with multiple rank-1 preferences (ambiguous) get no such bonus.
%   Evaluated after the main balance: only breaks ties in favour of sole-top students.
:~ sole_top(S,C), not assign(S,C). [500@3, S]

% @2 – RULE 5: Fill priority companies before others.
%   Activated by: fill_first(Company, Weight).
%   Higher weight => stronger preference to fill that company first.
%   E.g. fill_first(Gesobag,20). fill_first(ABB,10).
%   => Gesobag is filled more aggressively than ABB.
% :~ fill_first(C,W), student(S), pref(S,C,_), not assign(S,C). [W@2, S, C]

% @2 – Strongly discourage assigning to unrated companies
:~ assign(S,C), not pref(S,C,_). [50@2, S, C]

% @2 – Penalise students with no preferences at all
:~ assign(S,_), no_pref(S). [20@2, S]


% =========================
% OUTPUT
% =========================
#show assign/2.