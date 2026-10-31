## ----step1, results = "hide", message = FALSE---------------------------------
library(EpiModel)
set.seed(12345)

nw <- network_initialize(n = 500)

formation <- ~edges + concurrent + degrange(from = 4)
target.stats <- c(175, 110, 0)
coef.diss <- dissolution_coefs(
  dissolution = ~offset(edges),
  duration = 50   # mean partnership duration in time steps
)

est <- netest(nw, formation, target.stats, coef.diss, verbose = FALSE)

## ----step2, results = "hide"--------------------------------------------------
dx <- netdx(est, nsims = 5, nsteps = 500, verbose = FALSE)

## ----step3, results = "hide"--------------------------------------------------
param <- param.net(inf.prob = 0.4, act.rate = 2, rec.rate = 0.05)
init <- init.net(i.num = 10)
control <- control.net(type = "SIS", nsims = 5, nsteps = 500, verbose = FALSE)

sim <- netsim(est, param, init, control)
