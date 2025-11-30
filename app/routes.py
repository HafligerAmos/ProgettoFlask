from datetime import datetime
from pathlib import Path

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .models import Asset, UserAsset, recalculate_allocations
from .models.calculations import build_portfolio_series, calculate_roi, compound_growth
from .models.charts import (
    generate_multi_asset_chart,
    generate_portfolio_chart,
    generate_single_asset_chart,
)
from . import db
from .config import Config

main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET", "POST"])
def index():
    roi_result = None
    yearly_values = []
    featured_assets = Asset.query.limit(4).all()

    if request.method == "POST":
        initial_amount = float(request.form.get("initial_amount", 0))
        yearly_rate = float(request.form.get("yearly_rate", 0)) / 100
        years = int(request.form.get("years", 1))
        returns = [yearly_rate for _ in range(years)]
        yearly_values = compound_growth(initial_amount, returns)
        roi_result = calculate_roi(initial_amount, returns)

    return render_template(
        "index.html",
        roi_result=roi_result,
        yearly_values=yearly_values,
        featured_assets=featured_assets,
    )


@main_bp.route("/portfolio", methods=["GET", "POST"])
@login_required
def portfolio():
    assets = Asset.query.all()

    if request.method == "POST":
        form_type = request.form.get("form_type", "create")
        invested_amount = float(request.form.get("invested_amount", 0) or 0)
        monthly_contribution = float(request.form.get("monthly_contribution") or 0)
        yearly_contribution = float(request.form.get("yearly_contribution") or 0)

        if form_type == "update":
            user_asset_id = request.form.get("user_asset_id")
            user_asset = UserAsset.query.filter_by(id=user_asset_id, user_id=current_user.id).first()
            if not user_asset:
                flash("Investment not found", "danger")
                return redirect(url_for("main.portfolio"))
            user_asset.invested_amount = invested_amount
            user_asset.monthly_contribution = monthly_contribution
            user_asset.yearly_contribution = yearly_contribution
            db.session.commit()
            recalculate_allocations(current_user.id)
            flash("Investment updated", "success")
            return redirect(url_for("main.portfolio"))

        asset_id = request.form.get("asset_id")
        if not asset_id:
            flash("Select an asset", "danger")
            return redirect(url_for("main.portfolio"))

        try:
            asset_id_int = int(asset_id)
        except (TypeError, ValueError):
            flash("Invalid asset", "danger")
            return redirect(url_for("main.portfolio"))

        user_asset = UserAsset.query.filter_by(user_id=current_user.id, asset_id=asset_id_int).first()
        if user_asset:
            flash("Asset already in your portfolio. Adjust it directly in the cards below.", "warning")
            return redirect(url_for("main.portfolio"))

        user_asset = UserAsset(
            user_id=current_user.id,
            asset_id=asset_id_int,
            invested_amount=invested_amount,
            monthly_contribution=monthly_contribution,
            yearly_contribution=yearly_contribution,
        )
        db.session.add(user_asset)
        db.session.commit()
        recalculate_allocations(current_user.id)
        flash("Asset added to portfolio", "success")
        return redirect(url_for("main.portfolio"))

    user_assets = (
        UserAsset.query.filter_by(user_id=current_user.id).all() if current_user.is_authenticated else []
    )
    totals = {
        "invested": sum(asset.invested_amount for asset in user_assets),
        "monthly": sum(asset.monthly_contribution for asset in user_assets),
        "yearly": sum(asset.yearly_contribution for asset in user_assets),
    }

    return render_template("portfolio.html", assets=assets, user_assets=user_assets, totals=totals)


@main_bp.post("/portfolio/<int:user_asset_id>/delete")
@login_required
def delete_investment(user_asset_id):
    user_asset = UserAsset.query.filter_by(id=user_asset_id, user_id=current_user.id).first()
    if not user_asset:
        abort(404)
    db.session.delete(user_asset)
    db.session.commit()
    recalculate_allocations(current_user.id)
    flash("Investment removed. Re-add the asset if you wish to set it up again.", "info")
    return redirect(url_for("main.portfolio"))


@main_bp.route("/charts")
@login_required
def charts():
    user_assets = UserAsset.query.filter_by(user_id=current_user.id).all()
    if not user_assets:
        flash("Add at least one asset to your portfolio to unlock insights.", "warning")
        return redirect(url_for("main.portfolio"))

    chart_dir = Path(Config.CHART_OUTPUT_DIR)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")

    portfolio_items = []
    asset_charts = []
    asset_insights = []
    for index, user_asset in enumerate(user_assets):
        asset = user_asset.asset
        returns = asset.historical_returns
        portfolio_items.append(
            {
                "amount": user_asset.invested_amount,
                "returns": returns,
                "name": asset.name,
                "monthly_contribution": user_asset.monthly_contribution,
                "yearly_contribution": user_asset.yearly_contribution,
            }
        )
        values = compound_growth(
            user_asset.invested_amount,
            returns,
            user_asset.monthly_contribution,
            user_asset.yearly_contribution,
        )
        asset_chart_path = chart_dir / f"asset_{asset.id}_{timestamp}.png"
        generate_single_asset_chart(values, asset.name, str(asset_chart_path))
        asset_charts.append(asset_chart_path.name)
        years = len(returns)
        total_contrib = (
            user_asset.invested_amount
            + user_asset.monthly_contribution * 12 * years
            + user_asset.yearly_contribution * years
        )
        best_year = max(returns)
        worst_year = min(returns)
        asset_insights.append(
            {
                "chart": asset_chart_path.name,
                "title": asset.name,
                "details": [
                    f"{asset.name} compounds {years} curated annual data points blended with a €{user_asset.monthly_contribution:,.0f} monthly plan and €{user_asset.yearly_contribution:,.0f} yearly top-up.",
                    f"Entry level: €{user_asset.invested_amount:,.2f} deployed today with cumulative contributions of €{total_contrib:,.2f}. The curve currently targets €{values[-1]:,.2f} by year {years}.",
                    f"Momentum: best recorded season prints {(best_year * 100):.1f}% while the defensive scenario sits at {(worst_year * 100):.1f}%. The line in the chart mirrors those swings.",
                    "Pricing note: these simulations assume execution at internal model prices; adjust once live quotes are connected.",
                    "Catalysts: recurring cash-in maintains slope even during pullbacks, helping the strategy buy lows and smooth drawdowns.",
                ],
                "collapse_id": f"assetInfo{index}",
            }
        )

    total_series, per_asset_series = build_portfolio_series(portfolio_items)

    portfolio_chart_path = chart_dir / f"portfolio_{current_user.id}_{timestamp}.png"
    multi_chart_path = chart_dir / f"multi_{current_user.id}_{timestamp}.png"

    generate_portfolio_chart(total_series, str(portfolio_chart_path))
    generate_multi_asset_chart(per_asset_series, [item["name"] for item in portfolio_items], str(multi_chart_path))

    total_contributions = sum(
        item["amount"]
        + item["monthly_contribution"] * 12 * len(item["returns"])
        + item["yearly_contribution"] * len(item["returns"])
        for item in portfolio_items
    )
    ending_value = total_series[-1] if total_series else 0
    horizon = len(total_series) - 1 if total_series else 0
    top_asset_index = (
        max(range(len(per_asset_series)), key=lambda idx: per_asset_series[idx][-1]) if per_asset_series else 0
    )
    top_asset_name = portfolio_items[top_asset_index]["name"] if portfolio_items else ""

    portfolio_insight = {
        "chart": portfolio_chart_path.name,
        "title": "Portfolio growth",
        "details": [
            f"Total contributions across strategies amount to €{total_contributions:,.2f}; projected value reaches €{ending_value:,.2f} over {horizon} years.",
            "Curve steepness reflects combined momentum of every asset plus the recurring capital that keeps compounding even in flat markets.",
            f"Largest lift currently comes from {top_asset_name}, which drives most of the upside in the latest chart segment.",
            "Risk management tip: rebalance when allocation drifts >5pp from target to lock in profits before new deploys.",
        ],
        "collapse_id": "portfolioInsight",
    }

    multi_insight = {
        "chart": multi_chart_path.name,
        "title": "Multi-asset overlay",
        "details": [
            "Each colored line mirrors a specific asset’s compounding path so you can spot dispersion instantly.",
            "Crossovers highlight when a defensive sleeve (bonds/real estate) outperforms the aggressive bets, suggesting tactical shifts.",
            "Use this view during client reviews: it explains visually why diversification smooths drawdowns.",
        ],
        "collapse_id": "multiInsight",
    }

    return render_template(
        "charts.html",
        portfolio_chart=portfolio_chart_path.name,
        multi_chart=multi_chart_path.name,
        asset_charts=asset_charts,
        asset_insights=asset_insights,
        portfolio_insight=portfolio_insight,
        multi_insight=multi_insight,
    )
