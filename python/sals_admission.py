"""Causal one-step priority admission using the candidate PPRC static envelope.

This is not a voltage-stability certificate. A command window only covers
events after observation. A producer handshake or an always-held reserve is
needed if the physical event can precede that observation.
"""
from pprc_two_stage import Parameters, continuous_power_limit


def admit(vbat, nondeferrable_upper_A, requests, *, coverage_valid,
          margin=.95, p=Parameters()):
    """requests: {name: (present requested amps, priority)}, high priority first.

    coverage_valid is an externally established event contract, not a guess
    derived from a Monte Carlo failure rate. False fails closed on deferrables
    and explicitly refuses to certify mandatory demand.
    """
    if not 0<margin<=1 or nondeferrable_upper_A<0:
        raise ValueError('Require 0<margin<=1 and nonnegative mandatory bound')
    if any(current<0 or priority<0 for current,priority in requests.values()):
        raise ValueError('Requests and priorities must be nonnegative')
    budget=margin*continuous_power_limit(vbat,p)/p.vref
    mandatory_feasible=nondeferrable_upper_A<=budget
    allowance={name:0. for name in requests}
    if coverage_valid and mandatory_feasible:
        available=budget-nondeferrable_upper_A
        for name,(request,priority) in sorted(requests.items(),key=lambda item:-item[1][1]):
            if priority==0: continue
            allowance[name]=min(request,available)
            available-=allowance[name]
    return dict(allowance_A=allowance,load_budget_A=budget,
                mandatory_deficit_A=max(0.,nondeferrable_upper_A-budget),
                coverage_valid=bool(coverage_valid),
                static_admission_feasible=bool(coverage_valid and mandatory_feasible),
                voltage_safety_verified=False)
