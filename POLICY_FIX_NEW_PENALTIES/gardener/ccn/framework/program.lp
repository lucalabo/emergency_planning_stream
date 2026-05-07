% external constants: size, prefixes, horizon, high_prio_age, low_prio_age

%%% P_gen %%%
% This section corresponds to the subprogram P_gen described in section
% "ASP Framework" in the main document

% Encode the ranking of the executed action
% The ranking is missing here and dynamically generated and inserted depending
% on the current state of the cache
action_rank(R) :- action(0,A), ranking(A,R).

% inertia and state transition rules for content in cells
cell_content(T+1,C,P) :- action(T,C), C < size, inc_cell(T,P), T=0..horizon-1.
cell_content(T+1,C,P) :- cell_content(T,C,P), not action(T,C), T=0..horizon-1.

% inertia and state transition rules for the age of cells
cell_age(T+1,C,0) :- action(T,C), C < size, cell_age(T,C,A), T=0..horizon-1.
cell_age(T+1,C,A+1) :- not action(T,C), cell_age(T,C,A), T=0..horizon-1.

%%% P_check %%%
% This section corresponds to the subprogram P_check described in section
% "ASP Framework" in the main document
% The guessing rules are missing here and are dynamically generated
% and inserted depending on the instance

% Low Priority Norm is not violated if content is below threshold or not
% low priority
ok_low(T,C) :- cell_age(T,C,A), cell_content(T,C,P), low_prio(P), A <= low_prio_age.
ok_low(T,C) :- cell_content(T,C,P), not low_prio(P).

% High Priority Norm is not violated if content is above threshold or not
% high priority
ok_high(T,C) :- cell_age(T,C,A), cell_content(T,C,P), high_prio(P), A >= high_prio_age.
ok_high(T,C) :- cell_age(T,C,A), cell_content(T,C,P), high_prio(P), A < high_prio_age, action(T, C'), C != C'.
ok_high(T,C) :- cell_content(T,C,P), not high_prio(P).

% Count norm violations in any given time step
ok(T) :- {ok_low(T,C) : C=0..size-1} = size, {ok_high(T,C) : C=0..size-1} = size, ok(T-1).
good_low(T,C) | bad_low(T,C) :- C=0..size-1, T=1..horizon-1.
good_high(T,C) | bad_high(T,C) :- C=0..size-1, T=1..horizon-1.
ok_low(T,C) :- bad_low(T,C).
ok_high(T,C) :- bad_high(T,C).

% saturate to M_sat as described in section "ASP Framework -> Saturation
% technique" in the main document
inc_cell(T,P) :- sat, P=0..prefixes-1, T=1..horizon.
cell_content(T,C,P) :- sat, C=0..size, P=0..prefixes-1, T=1..horizon.

% check saturation criteria
ok(0).
ok_low(0,C) :- C=0..size-1.
ok_high(0,C) :- C=0..size-1.
sat :- ok(horizon-1).
:- not sat.

% Compute penalties for violating norms dependent on age as described in
% section "Experiments->CCN Caching" of the main document
penalty(A, T, C) :- bad_low(T,C), cell_age(T,C,A).
penalty(A, T, C) :- bad_high(T,C), cell_age(T,C,A).

%%% Optimization %%%
% Here (in addition with weak constraints above) we implement the utilitarian
% policy fix described in section "Policy Fixing" in the main document.

% optimize for minimum reward (best action has a reward of 0, higher is worse)
% and minimal penalty
#minimize {S@1,T,C : penalty(S, T, C)}.
#minimize {R@1 : action_rank(R)}.

#show action/2.
#show ranking/2.
#show action_rank/1.

