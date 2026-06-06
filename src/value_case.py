"""From cost to decision: CO2 abatement, the SDE++ subsidy, and project NPV/IRR.

LCOE answers "what does a GJ cost to make"; an investment board asks three further
questions this module answers, all in Dutch-market terms:

1. **How much CO2 does it abate?**  Geothermal heat displaces gas-fired heat (a NL
   condensing boiler at ~90 %), net of the grid emissions of the pump/heat-pump
   electricity it consumes.

2. **What subsidy does it need?**  Dutch geothermal heat is financed through
   **SDE++**, which pays the gap between a *base amount* (the project's cost price,
   i.e. our LCOE) and a *correction amount* (the market value of the energy, set by
   the gas price the heat competes with), per GJ, for up to 15 years.  The auction
   ranks projects by **subsidy per tonne CO2 avoided**, so that number — not the raw
   LCOE — is what decides whether the project is fundable.

3. **Does it make money?**  At a heat sales tariff plus the SDE++ top-up, what is the
   equity NPV and IRR?  By construction the LCOE is the price at which the equity IRR
   equals the required return, so this is a faithful extension of the same model — a
   flat tariff equal to the LCOE returns exactly the hurdle rate.
"""

from __future__ import annotations

import numpy as np

# Emission factors (NL, t CO2 per unit).
GAS_EMISSION_T_PER_GJ = 0.0566      # natural gas combustion, ~56.6 kg CO2 / GJ
BOILER_EFFICIENCY = 0.90            # condensing boiler the geothermal displaces
GRID_INTENSITY_T_PER_MWH = 0.30    # NL grid average (declining; sensitivity-worthy)


def co2_abated_t_per_yr(heat_gj: float, elec_mwh: float,
                        boiler_eff: float = BOILER_EFFICIENCY,
                        gas_ef: float = GAS_EMISSION_T_PER_GJ,
                        grid: float = GRID_INTENSITY_T_PER_MWH) -> dict:
    """Net annual CO2 avoided: displaced gas heat minus the geothermal's own grid power."""
    displaced = heat_gj / boiler_eff * gas_ef
    consumed = elec_mwh * grid
    return {"displaced_gas_t": displaced, "geo_power_t": consumed,
            "net_abated_t": displaced - consumed}


def sde_plus(lcoe_base_eur_gj: float, market_ref_eur_gj: float,
             energy_gj: float, sde_years: int = 15) -> dict:
    """SDE++ top-up: (base amount - correction amount) per GJ, while positive.

    base amount   = our LCOE (the cost price the scheme needs to break even).
    correction    = market value of the heat (the gas-equivalent price it competes
                    with); SDE++ only pays the shortfall, capped at the base amount.
    """
    subsidy_per_gj = max(0.0, lcoe_base_eur_gj - market_ref_eur_gj)
    annual = subsidy_per_gj * energy_gj
    return {"subsidy_eur_gj": subsidy_per_gj, "annual_subsidy_eur": annual,
            "total_subsidy_eur": annual * sde_years, "sde_years": sde_years}


def abatement_subsidy_cost_eur_per_t(annual_subsidy_eur: float,
                                     net_abated_t_per_yr: float) -> float:
    """SDE++ ranking metric: subsidy spent per tonne CO2 avoided (EUR/t)."""
    return annual_subsidy_eur / net_abated_t_per_yr if net_abated_t_per_yr else float("nan")


def _npv(rate: float, cashflows) -> float:
    t = np.arange(len(cashflows))
    return float(np.sum(np.asarray(cashflows, float) / (1.0 + rate) ** t))


def irr(cashflows, lo: float = -0.95, hi: float = 2.0, tol: float = 1e-7) -> float:
    """Internal rate of return by bisection (cashflows[0] is the year-0 outflow)."""
    f_lo, f_hi = _npv(lo, cashflows), _npv(hi, cashflows)
    if f_lo * f_hi > 0:
        return float("nan")  # no sign change in the bracket
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        f_mid = _npv(mid, cashflows)
        if abs(f_mid) < tol:
            return mid
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return 0.5 * (lo + hi)


def project_npv_irr(heat_econ: dict, tariff_eur_gj: float,
                    subsidy_eur_gj: float = 0.0, sde_years: int = 15,
                    tax: float = 0.25, equity_return: float = 0.15) -> dict:
    """Equity NPV (at the hurdle rate) and IRR for a heat sales tariff + SDE++ top-up.

    Builds the equity cash flow from the financed model's zero-revenue net cash flow
    (``heat_econ['cashflow']['net_rev_eur']``) plus after-tax revenue at the chosen
    price path. A flat tariff equal to the LCOE (no subsidy) returns the hurdle rate,
    which is the internal consistency check.
    """
    cf = heat_econ["cashflow"]
    years = np.asarray(cf["year"], int)
    energy = np.asarray(cf["energy_gj"], float)
    net_rev = np.asarray(cf["net_rev_eur"], float)         # after-tax, zero revenue
    price = tariff_eur_gj + np.where(years <= sde_years, subsidy_eur_gj, 0.0)
    after_tax_rev = (1.0 - tax) * price * energy
    equity_cf = np.concatenate(([-heat_econ["equity_eur"]], net_rev + after_tax_rev))
    npv = _npv(equity_return, equity_cf)
    return {"equity_npv_eur": npv, "equity_irr": irr(equity_cf),
            "tariff_eur_gj": tariff_eur_gj, "subsidy_eur_gj": subsidy_eur_gj}


def value_summary(market_ref_eur_gj: float = 8.0, tariff_eur_gj: float = 9.0,
                  cfg=None, lifetime_yr: int | None = None) -> dict:
    """End-to-end value case for the recommended Design-A heat product."""
    from src.lcoe import heat_economics
    from src.surface import SchemeConfig
    cfg = cfg or SchemeConfig()
    hc = cfg.heat_case()
    econ = heat_economics(hc, heat_mwth=cfg.heat_delivered_mwth, lifetime_yr=lifetime_yr)
    energy_gj = econ["annual_energy_gj"]
    elec_mwh = cfg.heat_delivered_mwth * hc.heat_loadhours / hc.pump_cop
    lcoe = econ["lcoe_eur_gj"]

    co2 = co2_abated_t_per_yr(energy_gj, elec_mwh)
    sde = sde_plus(lcoe, market_ref_eur_gj, energy_gj, sde_years=hc.fin.term_loan_yr)
    cost_per_t = abatement_subsidy_cost_eur_per_t(sde["annual_subsidy_eur"], co2["net_abated_t"])
    subsidised = project_npv_irr(econ, tariff_eur_gj, sde["subsidy_eur_gj"],
                                 sde_years=hc.fin.term_loan_yr,
                                 tax=hc.fin.tax, equity_return=hc.fin.equity_return)
    unsubsidised = project_npv_irr(econ, tariff_eur_gj, 0.0,
                                   tax=hc.fin.tax, equity_return=hc.fin.equity_return)
    return {
        "lcoe_heat_eur_gj": round(lcoe, 2),
        "market_ref_eur_gj": market_ref_eur_gj,
        "annual_energy_gj": round(energy_gj, 0),
        "annual_elec_mwh": round(elec_mwh, 0),
        "co2_net_abated_t_yr": round(co2["net_abated_t"], 0),
        "sde_subsidy_eur_gj": round(sde["subsidy_eur_gj"], 2),
        "sde_annual_eur": round(sde["annual_subsidy_eur"], 0),
        "sde_abatement_cost_eur_t": round(cost_per_t, 1),
        "tariff_eur_gj": tariff_eur_gj,
        # With SDE++: clears the hurdle. Without: the market tariff alone cannot
        # cover the LCOE, so the equity NPV is negative and break-even needs a
        # tariff = LCOE — which is precisely the gap SDE++ exists to bridge.
        "equity_irr_with_sde": round(subsidised["equity_irr"], 3),
        "equity_npv_with_sde_meur": round(subsidised["equity_npv_eur"] / 1e6, 2),
        "equity_npv_no_sde_meur": round(unsubsidised["equity_npv_eur"] / 1e6, 2),
        "breakeven_tariff_no_sde_eur_gj": round(lcoe, 2),
    }


if __name__ == "__main__":
    for k, v in value_summary().items():
        print(f"  {k:26} = {v}")
