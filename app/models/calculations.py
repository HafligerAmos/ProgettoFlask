from typing import Dict, List, Tuple


def compound_growth(
    initial_amount: float,
    returns: List[float],
    monthly_contribution: float = 0.0,
    yearly_contribution: float = 0.0,
) -> List[float]:
    values = [round(initial_amount, 2)]
    current = initial_amount

    for rate in returns:
        current += yearly_contribution
        monthly_rate = (1 + rate) ** (1 / 12) - 1
        for _ in range(12):
            current = (current + monthly_contribution) * (1 + monthly_rate)
        values.append(round(current, 2))

    return values


def calculate_roi(
    initial_amount: float,
    returns: List[float],
    monthly_contribution: float = 0.0,
    yearly_contribution: float = 0.0,
) -> float:
    values = compound_growth(initial_amount, returns, monthly_contribution, yearly_contribution)
    final_value = values[-1]
    years = len(returns)
    total_invested = (
        initial_amount
        + yearly_contribution * years
        + monthly_contribution * 12 * years
    )
    if total_invested == 0:
        return 0.0
    roi = (final_value - total_invested) / total_invested
    return round(roi, 4)


def build_portfolio_series(portfolio_items: List[Dict]) -> Tuple[List[float], List[List[float]]]:
    if not portfolio_items:
        return [], []

    per_asset_series = []
    max_years = 0
    for item in portfolio_items:
        series = compound_growth(
            item["amount"],
            item["returns"],
            item.get("monthly_contribution", 0.0),
            item.get("yearly_contribution", 0.0),
        )
        per_asset_series.append(series)
        max_years = max(max_years, len(series))

    total_series = []
    for idx in range(max_years):
        total = 0.0
        for series in per_asset_series:
            if idx < len(series):
                total += series[idx]
            else:
                total += series[-1]
        total_series.append(round(total, 2))

    return total_series, per_asset_series
