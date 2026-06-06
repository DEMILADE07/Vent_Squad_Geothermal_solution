"""Levelised cost of energy — a faithful Python re-build of the TNO workbook,
extended to the hybrid heating + cooling design.

Why re-build it in code rather than just editing the spreadsheet?  Because the
deck needs sensitivities (the tornado) and the bonus pipeline needs to drive the
LCOE programmatically.  The risk in re-building is drift from the published
model, so the module is gated: ``validate_reference()`` reproduces the stock
workbook's heat case to 5.769 EUR/GJ before any of our numbers are trusted.

The TNO LCOE is *not* "total cost / total energy".  It is a financed, after-tax,
levelised break-even price: the heat price (EUR/GJ) at which the discounted
after-tax cash flows plus the upfront equity are exactly recovered, discounting
at the required equity return.  Wells are part debt / part equity, depreciated
linearly, and taxed.  That financing structure — not the raw thermodynamics — is
what sets the headline number.

References reconstructed from LCOE.xlsx (sheets Input_Output, CFheat):
- well cost  = scaling * (0.2*d^2 + 700*d + 250000) * 1e-6   [mln EUR / well]
- heat MWth  = eff * flow_Ls * Cp * rho * dT * 1e-9          [TNO L/s convention]
- LCOE       = (equity - NPV(net cashflow)) / NPV((1-tax)*energy), both @ equity return
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np

# ---------------------------------------------------------------------------
# TNO workbook fluid properties (Input_Output!K4, K5).  These differ from the
# deliverability module's values (1000 kg/m3, 4180 J/kgK): the workbook assumes a
# saline Rotliegend brine.  We keep the workbook's own constants here so the
# heat-from-flow formula reproduces the published reference exactly.
# ---------------------------------------------------------------------------

CP_WATER_J_KGK = 4250.0
RHO_WATER_KG_M3 = 1078.0
HORIZON_YEARS = 40  # the workbook's cash-flow grid runs 40 yr; lifetime caps it


# ---------------------------------------------------------------------------
# Financing block (shared by heat and cooling LCOE)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Financing:
    """Project finance assumptions (TNO Input_Output defaults)."""
    loan_rate: float = 0.06         # D57 interest on debt
    equity_return: float = 0.15     # D58 required return on equity = discount rate
    equity_share: float = 0.20      # D59
    debt_share: float = 0.80        # D60
    tax: float = 0.25               # D61
    term_loan_yr: int = 15          # D63
    depreciation_yr: int = 15       # D64
    inflation: float = 0.0          # D56


def _annuity(principal: float, rate: float, n_years: int, horizon: int):
    """Per-year interest and principal repayment of a level annuity loan.

    Reproduces Excel IPMT/PPMT (positive principal in, negative payments out).
    Returns two arrays of length ``horizon`` indexed by year 1..horizon (index 0
    is year 1); zero after the loan term.
    """
    interest = np.zeros(horizon)
    principal_pay = np.zeros(horizon)
    if principal <= 0 or n_years <= 0:
        return interest, principal_pay
    payment = principal * rate / (1.0 - (1.0 + rate) ** (-n_years))
    balance = principal
    for i in range(min(n_years, horizon)):
        intr = balance * rate
        prin = payment - intr
        interest[i] = -intr           # cash out
        principal_pay[i] = -prin
        balance -= prin
    return interest, principal_pay


def financed_lcoe(capex_mln: float, annual_opex_eur: float, annual_energy_gj: float,
                  fin: Financing, lifetime_yr: int,
                  reinvest: dict[int, float] | None = None,
                  horizon: int = HORIZON_YEARS) -> dict:
    """The TNO financed, after-tax, levelised cost of energy.

    capex_mln          total investment, million EUR (year 0).
    annual_opex_eur    positive fixed+variable O&M per operating year. Scalar
                       (flat) or a per-year array of length ``horizon``.
    annual_energy_gj   energy delivered per operating year (GJ). Scalar (flat) or
                       a per-year array of length ``horizon`` — the latter is how a
                       thermal-decline profile (src/reservoir_thermal.py) enters.
    reinvest           {year: EUR} periodic reinvestment (e.g. pump workovers),
                       cash-out, applied as a positive magnitude.
    Returns a dict with the LCOE (EUR/GJ) and the NPV building blocks.
    """
    invest = capex_mln * 1e6
    equity = fin.equity_share * invest
    loan_share = fin.debt_share * invest
    interest, principal_pay = _annuity(loan_share, fin.loan_rate, fin.term_loan_yr, horizon)

    years = np.arange(1, horizon + 1)
    operating = years <= lifetime_yr
    energy_arr = np.broadcast_to(np.asarray(annual_energy_gj, float), (horizon,))
    opex_arr = np.broadcast_to(np.asarray(annual_opex_eur, float), (horizon,))
    energy_gj = np.where(operating, energy_arr, 0.0)
    opex = np.where(operating, -opex_arr, 0.0)

    reinvest_arr = np.zeros(horizon)
    for yr, eur in (reinvest or {}).items():
        if 1 <= yr <= horizon:
            reinvest_arr[yr - 1] -= eur

    infl = (1.0 + fin.inflation) ** (years - 1)
    gross_rev = infl * (opex + reinvest_arr)          # income = 0 when solving LCOE
    deprec = np.where(years <= fin.depreciation_yr, -invest / fin.depreciation_yr, 0.0)
    taxable = gross_rev + deprec + interest
    tax_credit = -fin.tax * taxable
    loan_charge = interest + principal_pay
    net_rev = gross_rev + loan_charge + tax_credit
    energy_after_tax = (1.0 - fin.tax) * energy_gj

    disc = (1.0 + fin.equity_return) ** years
    npv_net_rev = float(np.sum(net_rev / disc))
    npv_energy = float(np.sum(energy_after_tax / disc))
    lcoe = (equity - npv_net_rev) / npv_energy if npv_energy else float("nan")

    return {
        "lcoe_eur_gj": lcoe,
        "capex_mln": capex_mln,
        "equity_eur": equity,
        "npv_net_rev_eur": npv_net_rev,
        "npv_energy_gj": npv_energy,
        "annual_energy_gj": annual_energy_gj,
        "annual_opex_eur": annual_opex_eur,
        "cashflow": {
            "year": years,
            "energy_gj": energy_gj,
            "gross_rev_eur": gross_rev,
            "depreciation_eur": deprec,
            "interest_eur": interest,
            "loan_charge_eur": loan_charge,
            "tax_credit_eur": tax_credit,
            "net_rev_eur": net_rev,
        },
    }


# ---------------------------------------------------------------------------
# Geothermal heat side (TNO direct-heat block, re-parameterised)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HeatCase:
    """Inputs for the geothermal heat LCOE.  Defaults = TNO reference case."""
    flowrate_ls: float = 50.0          # total surface flow, L/s
    ah_depth_m: float = 1800.0         # along-hole depth per well
    t_prod_c: float = 93.7             # production (reservoir) temperature
    t_outlet_c: float = 93.7           # top of usable range (= Tx for direct heat)
    t_reinject_c: float = 35.0
    n_wells: int = 2
    heat_loadhours: float = 6000.0
    well_cost_scaling: float = 1.5
    stim_cost_mln_per_well: float = 0.0
    pump_cost_mln: float = 0.3         # one pump set; workover every 5 yr
    heat_plant_invest_keur_mwth: float = 150.0
    om_fixed_rate: float = 0.01        # of (heat + subsurface) capex
    electricity_price_eur_mwh: float = 150.0
    pump_cop: float = 27.0             # MWth/MWe to drive the pumps
    direct_heat_efficiency: float = 1.0
    fin: Financing = field(default_factory=Financing)


def well_cost_mln(depth_m: float, scaling: float) -> float:
    """TNO drilling cost (mln EUR / well), polynomial in along-hole depth."""
    return scaling * (0.2 * depth_m ** 2 + 700.0 * depth_m + 250_000.0) * 1e-6


def heat_mwth_from_flow(flow_ls: float, t_hot_c: float, t_cold_c: float,
                        efficiency: float = 1.0) -> float:
    """Thermal power (MWth) in the TNO L/s convention (= eff*Q*Cp*rho*dT*1e-9)."""
    return efficiency * flow_ls * CP_WATER_J_KGK * RHO_WATER_KG_M3 * (t_hot_c - t_cold_c) * 1e-9


def heat_economics(c: HeatCase, heat_mwth: float | None = None,
                   mwth_profile=None, lifetime_yr: int | None = None) -> dict:
    """Capex / opex / LCOE for the geothermal heat product.

    If ``heat_mwth`` is given it overrides the flow-derived value — this is how we
    drive the LCOE from the Monte-Carlo P50 deliverability rather than a nominal
    flow rate.  An effective flow rate consistent with that MWth is reported back.

    ``mwth_profile`` (per-year MWth, length ``horizon``) lets a thermal-decline
    profile (src/reservoir_thermal.py) drive a *time-varying* delivered energy:
    capex and the nameplate sizing stay set by ``heat_mwth``, while annual energy
    and the variable (pumping) O&M scale with the declining per-year MWth; fixed
    O&M stays on the nameplate.  Omit it for the flat reference behaviour.

    ``lifetime_yr`` overrides the economic life (default = loan term); the asset
    can deliver energy beyond the 15-yr loan, which lowers LCOE.
    """
    if heat_mwth is None:
        heat_mwth = heat_mwth_from_flow(c.flowrate_ls, c.t_outlet_c, c.t_reinject_c,
                                        c.direct_heat_efficiency)
        flow_ls = c.flowrate_ls
    else:
        dt = c.t_outlet_c - c.t_reinject_c
        denom = c.direct_heat_efficiency * CP_WATER_J_KGK * RHO_WATER_KG_M3 * dt * 1e-9
        flow_ls = heat_mwth / denom if denom else float("nan")

    life = c.fin.term_loan_yr if lifetime_yr is None else lifetime_yr

    drill = well_cost_mln(c.ah_depth_m, c.well_cost_scaling)
    subsurface_capex = (c.stim_cost_mln_per_well + drill) * c.n_wells + c.pump_cost_mln
    heat_capex = c.heat_plant_invest_keur_mwth * heat_mwth / 1000.0
    capex_mln = subsurface_capex + heat_capex

    om_var_eur_mwh = c.electricity_price_eur_mwh / c.pump_cop          # D22 / D46
    om_fixed_keur_mwth = c.om_fixed_rate * (heat_capex + subsurface_capex) * 100.0  # D45
    om_fixed_eur = heat_mwth * om_fixed_keur_mwth * 1000.0            # nameplate, flat

    if mwth_profile is None:
        annual_energy_gj = heat_mwth * c.heat_loadhours * 3.6
        annual_opex = heat_mwth * c.heat_loadhours * om_var_eur_mwh + om_fixed_eur
    else:
        mw = np.asarray(mwth_profile, float)                          # per-year MWth
        annual_energy_gj = mw * c.heat_loadhours * 3.6
        annual_opex = mw * c.heat_loadhours * om_var_eur_mwh + om_fixed_eur

    # pump workover every 5 yr within the loan/operating window
    reinvest = {yr: c.pump_cost_mln * 1e6 for yr in range(5, c.fin.term_loan_yr + 1, 5)}

    res = financed_lcoe(capex_mln, annual_opex, annual_energy_gj, c.fin,
                        lifetime_yr=life, reinvest=reinvest)
    res.update({
        "product": "heat",
        "heat_mwth": heat_mwth,
        "flow_ls": flow_ls,
        "drill_mln_per_well": drill,
        "subsurface_capex_mln": subsurface_capex,
        "heat_capex_mln": heat_capex,
        "loadhours": c.heat_loadhours,
        "lifetime_yr": life,
        "declined": mwth_profile is not None,
    })
    return res


# ---------------------------------------------------------------------------
# Reference validation gate
# ---------------------------------------------------------------------------

REFERENCE_LCOE_EUR_GJ = 5.769049045858562  # Input_Output!D70


def validate_reference(tol: float = 1e-3) -> float:
    """Reproduce the stock TNO heat case; raise if we have drifted from 5.769."""
    lcoe = heat_economics(HeatCase())["lcoe_eur_gj"]
    if abs(lcoe - REFERENCE_LCOE_EUR_GJ) > tol:
        raise AssertionError(
            f"LCOE engine drifted from TNO reference: got {lcoe:.6f}, "
            f"expected {REFERENCE_LCOE_EUR_GJ:.6f} EUR/GJ")
    return lcoe


# ---------------------------------------------------------------------------
# Cooling side — Design A (ATES + electric heat pump in chiller mode)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CoolingCase:
    """Inputs for the cooling LCOE (Design A: seasonal ATES + trim heat pump).

    Cooling is delivered mostly by circulating cold water banked in the ATES cold
    well over winter; an electric heat pump in chiller mode trims the summer peak.
    The effective system COP is therefore high (free stored cold + a little
    electric lift), which is the whole economic argument for ATES over an
    absorption chiller that burns the geothermal heat we are trying to sell.
    """
    cooling_mwth: float = 5.0
    cooling_loadhours: float = 2000.0      # cooling is summer-peaky, not baseload
    ates_pairs: int = 4                    # warm/cold well pairs
    ates_capex_mln_per_pair: float = 0.7   # shallow ATES doublet + HX (NL range 0.5-0.8)
    ates_throughput_mwth_per_pair: float = 1.5
    ates_round_trip_eff: float = 0.70
    chiller_capex_keur_mwth: float = 120.0  # trim heat-pump / chiller plant
    # Blended COP: ATES supplies most cold at COP ~25 (circulation only); an
    # electric heat pump trims the summer peak at COP ~4.5.  ~70/30 split -> ~10.
    system_cop_cooling: float = 10.0        # delivered cold per electric input
    electricity_price_eur_mwh: float = 150.0
    om_fixed_rate: float = 0.02             # cooling kit O&M, fraction of capex
    fin: Financing = field(default_factory=Financing)


def cooling_economics(c: CoolingCase) -> dict:
    """Capex / opex / LCOE for the cooling product (Design A)."""
    ates_capex = c.ates_pairs * c.ates_capex_mln_per_pair
    chiller_capex = c.chiller_capex_keur_mwth * c.cooling_mwth / 1000.0
    capex_mln = ates_capex + chiller_capex

    cooling_mwhth = c.cooling_mwth * c.cooling_loadhours
    elec_mwh = cooling_mwhth / c.system_cop_cooling
    elec_opex = elec_mwh * c.electricity_price_eur_mwh
    om_fixed = c.om_fixed_rate * capex_mln * 1e6
    annual_opex = elec_opex + om_fixed
    annual_energy_gj = cooling_mwhth * 3.6

    res = financed_lcoe(capex_mln, annual_opex, annual_energy_gj, c.fin,
                        lifetime_yr=c.fin.term_loan_yr)
    res.update({
        "product": "cool",
        "cooling_mwth": c.cooling_mwth,
        "ates_pairs": c.ates_pairs,
        "ates_capex_mln": ates_capex,
        "chiller_capex_mln": chiller_capex,
        "elec_mwh": elec_mwh,
        "elec_opex_eur": elec_opex,
        "loadhours": c.cooling_loadhours,
        "ates_supply_mwth": c.ates_pairs * c.ates_throughput_mwth_per_pair,
    })
    return res


@dataclass(frozen=True)
class AbsorptionCoolingCase:
    """Design B cooling: LiBr/H2O absorption chiller driven by geothermal heat.

    The chiller makes cold from heat (COP_th ~0.7), so 5 MWth of cooling needs
    ~7 MWth of driving heat — heat that Design A would instead sell.  We price
    that driving heat at the heat LCOE as an internal transfer cost, which is the
    fair way to expose the trade-off: cold made from heat is only cheap if the
    heat is otherwise worthless, and on this marginal-economics reservoir it is
    not.
    """
    cooling_mwth: float = 5.0
    cooling_loadhours: float = 2000.0
    cop_th: float = 0.7                     # thermal COP of the absorption chiller
    chiller_capex_keur_mwth: float = 250.0  # absorption chillers are capex-heavy
    parasitic_cop: float = 25.0             # electric COP for pumps/fans only
    electricity_price_eur_mwh: float = 150.0
    om_fixed_rate: float = 0.02
    fin: Financing = field(default_factory=Financing)


def cooling_economics_absorption(c: AbsorptionCoolingCase,
                                 heat_lcoe_eur_gj: float) -> dict:
    """Capex / opex / LCOE for Design B cooling (absorption chiller)."""
    chiller_capex = c.chiller_capex_keur_mwth * c.cooling_mwth / 1000.0
    capex_mln = chiller_capex

    cooling_mwhth = c.cooling_mwth * c.cooling_loadhours
    driving_heat_mwhth = cooling_mwhth / c.cop_th
    driving_heat_gj = driving_heat_mwhth * 3.6
    heat_transfer_cost = driving_heat_gj * heat_lcoe_eur_gj      # opportunity cost
    elec_mwh = cooling_mwhth / c.parasitic_cop
    elec_opex = elec_mwh * c.electricity_price_eur_mwh
    om_fixed = c.om_fixed_rate * capex_mln * 1e6
    annual_opex = elec_opex + om_fixed + heat_transfer_cost
    annual_energy_gj = cooling_mwhth * 3.6

    res = financed_lcoe(capex_mln, annual_opex, annual_energy_gj, c.fin,
                        lifetime_yr=c.fin.term_loan_yr)
    res.update({
        "product": "cool_absorption",
        "cooling_mwth": c.cooling_mwth,
        "chiller_capex_mln": chiller_capex,
        "driving_heat_mwth": c.cooling_mwth / c.cop_th,
        "driving_heat_gj": driving_heat_gj,
        "heat_transfer_cost_eur": heat_transfer_cost,
        "elec_mwh": elec_mwh,
        "loadhours": c.cooling_loadhours,
    })
    return res


def hybrid_summary(heat: HeatCase, cool: CoolingCase,
                   heat_mwth: float | None = None) -> dict:
    """Combined heat + cool view: per-product LCOE and a blended system LCOE.

    Cost allocation: the geothermal doublets and heat surface plant are charged
    entirely to heat (they exist to sell heat); the ATES wells, chiller plant and
    cooling electricity are charged entirely to cooling.  No shared cost is split,
    so neither product is cross-subsidised — the LCOEs stand on their own.
    """
    h = heat_economics(heat, heat_mwth=heat_mwth)
    k = cooling_economics(cool)
    total_capex = h["capex_mln"] + k["capex_mln"]
    total_energy = h["npv_energy_gj"] + k["npv_energy_gj"]
    blended = ((h["lcoe_eur_gj"] * h["npv_energy_gj"]
                + k["lcoe_eur_gj"] * k["npv_energy_gj"]) / total_energy
               if total_energy else float("nan"))
    return {
        "heat": h,
        "cool": k,
        "lcoe_heat_eur_gj": h["lcoe_eur_gj"],
        "lcoe_cool_eur_gj": k["lcoe_eur_gj"],
        "lcoe_blended_eur_gj": blended,
        "total_capex_mln": total_capex,
    }


if __name__ == "__main__":  # smoke check
    print(f"TNO reference reproduced: {validate_reference():.4f} EUR/GJ")
