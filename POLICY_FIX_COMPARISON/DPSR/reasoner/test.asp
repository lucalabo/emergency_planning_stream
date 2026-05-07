#show p/3.

#show dist_comp_r/3.

#show diff_col_abs/2.

#show n/1.
#show s/1.
#show e/1.
#show w/1.

#show positionPlayer/2.

#show risk_collide/2.

#show ok/2.

#show plantKilled/2.

#show bad_plant/3.

#show diff_row_abs/2.

#show has_future_moves/0.

#show sat/0.

#show dist_comp_c/3.

#show frogKilled/1.

#show activate_planning/0.

#show multi/1.

#show action_taken/4.

#show reached/0.

#show ok/1.

#show penalty_plant/4.

#show active_frog/1.

#show action/4.

#show frog_step/1.

#show not_all_ok/1.

#show is_multi/0.

#show penalty_frog/3.

#show penalty_action/2.

#show good/2.
#show bad/2.

nd_positionPlayer_COUNTMIN20SECONDS(C,R,ND_V0) :- positionPlayer_COUNTMIN20SECONDS(C,R, M), positionPlayer(C,R), ND_V0=( M + 1 ).
p(R,C,T) :- T=AT_now, prow(R,T), pcol_IN1SECONDS(C,T), at_now(-1,AT_now).
 :~ penalty_frog(P,F,T). [P@1,F,T]
dist_comp_r(F,T,DR) :- active_frog(F), frog_step(T), p(R,_,T), frow_now(F,FR), DR=( FR - R ), FR>=R.
diff_col_abs(F,AbsC) :- fcol_now(F,FC), p(PR,PC,AT_now), FC<PC, AbsC=( PC - FC ), at_now(-1,AT_now).
 :- plan_step(T), s(T), w(T).
n(T) | s(T) | e(T) | w(T) :- plan_step(T), activate_planning, not reached.
positionPlayer(C,R) :- p(R,C,AT_now), at_now(-1,AT_now).
risk_collide(T,F) :- dist_comp_r(F,T,DR), dist_comp_c(F,T,DC), at_now(-1,AT_now), Dist=( DR + DC ), K=( T - AT_now ), Dist<=K, Diff=( K - Dist ), Pari=( ( Diff / 2 ) * 2 ), Diff==Pari.
 :- p(R,_,_), R>S, size(S).
ok(T,F) :- active_frog(F), frog_step(T), not risk_collide(T,F), ok(( T - 1 )).
dist_comp_r(F,T,DR) :- active_frog(F), frog_step(T), p(R,_,T), frow_now(F,FR), DR=( R - FR ), R>FR.
nd_p_IN1SECONDS(R,C,T) :- p(R,C,T).
 :- p(R,C,T), p(R1,C1,T), R!=R1.
 :- p(_,C,_), C<0.
 :- not sat.
plantKilled(C,R) :- plantKilled_IN_1SECONDS(C,R).
bad_plant(T,C,R) :- p(R,C,T), plant(C,R), not plantKilled_IN_1SECONDS(C,R).
diff_row_abs(F,AbsR) :- frow_now(F,FR), p(PR,PC,AT_now), FR>=PR, AbsR=( FR - PR ), at_now(-1,AT_now).
p(R,( C + 1 ),( T + 1 )) :- p(R,C,T), e(T), activate_planning.
has_future_moves :- p_IN_1SECONDS(_,_,T), T>AT_now, at_now(-1,AT_now).
p(( R - 1 ),C,( T + 1 )) :- p(R,C,T), n(T), activate_planning.
sat :- reached.
dist_comp_c(F,T,DC) :- active_frog(F), frog_step(T), p(_,C,T), fcol_now(F,FC), DC=( FC - C ), FC>=C.
frogKilled(F) :- frogKilled_IN_1SECONDS(F).
activate_planning :- not has_future_moves.
multi(M) :- positionPlayer(C,R), nd_positionPlayer_COUNTMIN20SECONDS(C,R,M).
 :- p(R,_,_), R<0.
diff_col_abs(F,AbsC) :- fcol_now(F,FC), p(PR,PC,AT_now), FC>=PC, AbsC=( FC - PC ), at_now(-1,AT_now).
diff_row_abs(F,AbsR) :- frow_now(F,FR), p(PR,PC,AT_now), FR<PR, AbsR=( PR - FR ), at_now(-1,AT_now).
action_taken(2,T,C,R) :- p(R,C,T), p(R,( C - 1 ),( T + 1 )).
 :- p(R,C,T), p(R1,C1,T), C!=C1.
reached :- target(C,R), p(R,C,AT_now), at_now(-1,AT_now).
frogKilled(F) :- frow_now(F,R), fcol_now(F,C), p(R,C,AT_now), at_now(-1,AT_now).
ok(T) :- frog_step(T), ok(( T - 1 )), not not_all_ok(T).
p(R,( C - 1 ),( T + 1 )) :- p(R,C,T), w(T), activate_planning.
penalty_plant(Peso,T,C,R) :- bad_plant(T,C,R), my_horizon(H), T1=( T - AT_now ), Peso=( ( H - T1 ) * 10 ), at_now(-1,AT_now).
active_frog(F) :- diff_row_abs(F,DR), diff_col_abs(F,DC), action_radius(R), my_horizon(H), TotalDist=( DR + DC ), TotalDist<=R, not frogKilled_IN_1SECONDS(F).
action(A,S,COL,ROW) :- p(R,C,AT_now), action_radius(Rad), &generate_nearby_actions(C,R,Rad;A,S,COL,ROW), activate_planning, at_now(-1,AT_now).
activate_planning :- active_frog(_).
nd_p_IN1SECONDS(R,C,T) :- p(R,C,T).
ok(AT_now) :- at_now(-1,AT_now).
frog_step(T) :- new_horizon_new(T), my_horizon(H), T>AT_now, T<( AT_now + H ), not reached, at_now(-1,AT_now).
 :- active_frog(F), frog_step(T), risk_collide(T,F), not bad(T,F).
dist_comp_c(F,T,DC) :- active_frog(F), frog_step(T), p(_,C,T), fcol_now(F,FC), DC=( C - FC ), C>FC.
ok(T,F) :- active_frog(F), frog_step(T), bad(T,F).
 :- plan_step(T), n(T), e(T).
 :- p(_,C,_), C>S, size(S).
not_all_ok(T) :- active_frog(F), frog_step(T), not ok(T,F).
 :~ penalty_plant(Peso,T,C,R). [Peso@1,T,C,R]
 :- plan_step(T), e(T), w(T).
is_multi :- multi(_).
 :~ p(R,C,T), p(R,C,T1), T!=T1, multi(M), Peso=( M * 10 ). [Peso@1]
penalty_frog(P,F,T) :- bad(T,F), T1=( T - AT_now ), my_horizon(H), P=( ( H - T1 ) * 5 ), at_now(-1,AT_now).
action_taken(0,T,C,R) :- p(R,C,T), p(( R + 1 ),C,( T + 1 )).
 :- plan_step(T), s(T), e(T).
action_taken(3,T,C,R) :- p(R,C,T), p(R,( C + 1 ),( T + 1 )).
p(R,C,T) :- T=AT_now, at_now(-1,AT_now), nd_p_IN1SECONDS(R,C,T).
 :~ penalty_action(S,T). [S@1,T]
reached :- reached_IN_1SECONDS.
action_taken(1,T,C,R) :- p(R,C,T), p(( R - 1 ),C,( T + 1 )).
nd_p_IN1SECONDS(R,C,T) :- p_IN1SECONDS(R,C,T).
 :- plan_step(T), n(T), w(T).
 :- p(R,C,_), wall(C,R).
plantKilled(C,R) :- plant(C,R), p(R,C,AT_now), at_now(-1,AT_now).
nd_positionPlayer_COUNTMIN20SECONDS(C,R,M) :- positionPlayer_COUNTMIN20SECONDS(C,R, M), not positionPlayer(C,R).
p(( R + 1 ),C,( T + 1 )) :- p(R,C,T), s(T), activate_planning.
sat :- last_step(L), ok(L).
penalty_action(S1,T) :- my_horizon(H), action_taken(A,T,C,R), action(A,B,C,R), multi(M), RankDiff=( 3 - B ), T1=( T - AT_now ), S=( H - T1 ), S1=( ( S * RankDiff ) * M ), at_now(-1,AT_now).
ok(AT_now,F) :- active_frog(F), at_now(-1,AT_now).
penalty_action(S1,T) :- my_horizon(H), action_taken(A,T,C,R), action(A,B,C,R), not is_multi, RankDiff=( 3 - B ), T1=( T - AT_now ), S=( H - T1 ), S1=( S * RankDiff ), at_now(-1,AT_now).
p(R,C,T) :- T>AT_now, not activate_planning, at_now(-1,AT_now), nd_p_IN1SECONDS(R,C,T).
good(T,F) | bad(T,F) :- active_frog(F), frog_step(T).
nd_p_IN1SECONDS(R,C,T) :- p_IN1SECONDS(R,C,T).
 :- plan_step(T), n(T), s(T).
%BK
 
