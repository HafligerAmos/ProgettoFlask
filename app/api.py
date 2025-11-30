from flask import Blueprint, jsonify, request

from .models import Asset, UserAsset
from .models.calculations import build_portfolio_series, calculate_roi, compound_growth

api_bp = Blueprint("api", __name__)


@api_bp.route("/calc-asset", methods=["POST"])
def calc_asset():
    payload = request.get_json() or {}
    asset_name = payload.get("asset")
    initial_amount = float(payload.get("initial_amount", 0))
    monthly_contribution = float(payload.get("monthly_contribution", 0))
    yearly_contribution = float(payload.get("yearly_contribution", 0))

    asset = Asset.query.filter_by(name=asset_name).first()
    if not asset:
        return jsonify({"error": "Asset not found"}), 404

    returns = asset.historical_returns
    base_amount = initial_amount or asset.default_amount
    yearly_values = compound_growth(base_amount, returns, monthly_contribution, yearly_contribution)
    roi_value = calculate_roi(base_amount, returns, monthly_contribution, yearly_contribution)

    return jsonify(
        {
            "yearly_values": yearly_values,
            "roi": roi_value,
        }
    )


@api_bp.route("/calc-portfolio", methods=["POST"])
def calc_portfolio():
    payload = request.get_json() or {}
    user_id = payload.get("user_id")
    portfolio_payload = payload.get("portfolio", [])

    portfolio_items = []

    if user_id:
        user_assets = UserAsset.query.filter_by(user_id=user_id).all()
        for item in user_assets:
            portfolio_items.append(
                {
                    "amount": item.invested_amount,
                    "returns": item.asset.historical_returns,
                    "name": item.asset.name,
                    "percent": item.allocation_percent,
                    "monthly_contribution": item.monthly_contribution,
                    "yearly_contribution": item.yearly_contribution,
                }
            )
    else:
        for entry in portfolio_payload:
            asset = Asset.query.filter_by(name=entry.get("asset")).first()
            if not asset:
                continue
            portfolio_items.append(
                {
                    "amount": entry.get("amount", asset.default_amount),
                    "returns": asset.historical_returns,
                    "name": asset.name,
                    "percent": entry.get("percent", 0),
                    "monthly_contribution": entry.get("monthly_contribution", 0),
                    "yearly_contribution": entry.get("yearly_contribution", 0),
                }
            )

    total_series, per_asset_series = build_portfolio_series(portfolio_items)
    allocation = {}
    invested_total = sum(item["amount"] for item in portfolio_items)
    for item in portfolio_items:
        percent = (item["amount"] / invested_total * 100) if invested_total else 0
        allocation[item["name"]] = round(percent, 2)

    total_contributions = 0.0
    for item in portfolio_items:
        years = len(item["returns"])
        total_contributions += (
            item["amount"]
            + item.get("yearly_contribution", 0) * years
            + item.get("monthly_contribution", 0) * 12 * years
        )
    roi_value = 0.0
    if total_series and total_contributions:
        roi_value = (total_series[-1] - total_contributions) / total_contributions

    return jsonify(
        {
            "yearly_values": total_series,
            "roi": round(roi_value, 4),
            "allocation": allocation,
            "per_asset_series": {
                item["name"]: series for item, series in zip(portfolio_items, per_asset_series)
            },
        }
    )
