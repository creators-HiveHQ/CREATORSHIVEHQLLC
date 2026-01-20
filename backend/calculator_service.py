"""
Calculator Service for Creators Hive HQ
Central Revenue Hub - All money flows through here

Implements:
- Self-Funding Loop: 17_Subscriptions → 06_Calculator
- Financial Analytics (MRR, ARR, churn, LTV)
- Revenue Forecasting
- Expense Tracking & Analysis
- Profit Analysis & Trends
- Creator Revenue Insights
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import logging
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)


class RevenueCategory(str, Enum):
    SUBSCRIPTION = "subscription"
    ONE_TIME = "one_time"
    AFFILIATE = "affiliate"
    SPONSORSHIP = "sponsorship"
    MERCHANDISE = "merchandise"
    SERVICES = "services"
    OTHER = "other"


class ExpenseCategory(str, Enum):
    PLATFORM_FEES = "platform_fees"
    MARKETING = "marketing"
    SOFTWARE = "software"
    EQUIPMENT = "equipment"
    CONTENT_PRODUCTION = "content_production"
    CONTRACTOR = "contractor"
    OTHER = "other"


class FinancialPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class CalculatorService:
    """
    Central Financial Intelligence Hub for Creators Hive HQ.
    Routes all revenue through the Calculator for comprehensive analytics.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        
    # ============== CORE METRICS ==============
    
    async def get_mrr(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate Monthly Recurring Revenue (MRR).
        MRR = Sum of all active subscription revenue per month.
        """
        match_stage = {"source": {"$regex": "Subscription", "$options": "i"}}
        if user_id:
            match_stage["user_id"] = user_id
        
        # Get current month's subscription revenue
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        match_stage["month_year"] = current_month
        
        pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": None,
                "mrr": {"$sum": "$revenue"},
                "subscription_count": {"$sum": 1}
            }}
        ]
        
        result = await self.db.calculator.aggregate(pipeline).to_list(1)
        
        mrr = result[0]["mrr"] if result else 0
        count = result[0]["subscription_count"] if result else 0
        
        # Calculate previous month's MRR for growth
        prev_month = (datetime.now(timezone.utc) - relativedelta(months=1)).strftime("%Y-%m")
        prev_match = {"source": {"$regex": "Subscription", "$options": "i"}, "month_year": prev_month}
        if user_id:
            prev_match["user_id"] = user_id
            
        prev_pipeline = [
            {"$match": prev_match},
            {"$group": {"_id": None, "mrr": {"$sum": "$revenue"}}}
        ]
        prev_result = await self.db.calculator.aggregate(prev_pipeline).to_list(1)
        prev_mrr = prev_result[0]["mrr"] if prev_result else 0
        
        growth = ((mrr - prev_mrr) / prev_mrr * 100) if prev_mrr > 0 else (100 if mrr > 0 else 0)
        
        return {
            "mrr": round(mrr, 2),
            "mrr_previous": round(prev_mrr, 2),
            "mrr_growth_percent": round(growth, 2),
            "active_subscriptions": count,
            "avg_revenue_per_subscription": round(mrr / count, 2) if count > 0 else 0,
            "month": current_month
        }
    
    async def get_arr(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate Annual Recurring Revenue (ARR).
        ARR = MRR × 12
        """
        mrr_data = await self.get_mrr(user_id)
        arr = mrr_data["mrr"] * 12
        prev_arr = mrr_data["mrr_previous"] * 12
        
        return {
            "arr": round(arr, 2),
            "arr_previous": round(prev_arr, 2),
            "arr_growth_percent": mrr_data["mrr_growth_percent"],
            "based_on_mrr": mrr_data["mrr"],
            "projected_year_end": round(arr + (mrr_data["mrr_growth_percent"] / 100 * arr * (12 - datetime.now().month) / 12), 2)
        }
    
    async def get_churn_rate(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate churn rate based on subscription cancellations.
        Churn Rate = (Lost Subscribers / Total Subscribers at Start) × 100
        """
        # Get subscriptions that became inactive in the last 30 days
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        
        # Count churned subscriptions
        churned_query = {
            "status": {"$in": ["cancelled", "expired", "inactive"]},
            "updated_at": {"$gte": thirty_days_ago}
        }
        if user_id:
            churned_query["creator_id"] = user_id
        
        churned = await self.db.creator_subscriptions.count_documents(churned_query)
        
        # Count active subscriptions at start of period
        active_query = {"status": "active"}
        if user_id:
            active_query["creator_id"] = user_id
            
        active_start = await self.db.creator_subscriptions.count_documents(active_query) + churned
        
        churn_rate = (churned / active_start * 100) if active_start > 0 else 0
        retention_rate = 100 - churn_rate
        
        return {
            "churn_rate_percent": round(churn_rate, 2),
            "retention_rate_percent": round(retention_rate, 2),
            "churned_subscriptions": churned,
            "total_at_period_start": active_start,
            "period": "30_days",
            "health_indicator": "excellent" if churn_rate < 3 else "good" if churn_rate < 7 else "concerning" if churn_rate < 15 else "critical"
        }
    
    async def get_ltv(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate Customer Lifetime Value (LTV).
        LTV = ARPU × Average Customer Lifetime
        where Average Customer Lifetime = 1 / Monthly Churn Rate
        """
        mrr_data = await self.get_mrr(user_id)
        churn_data = await self.get_churn_rate(user_id)
        
        arpu = mrr_data["avg_revenue_per_subscription"]
        monthly_churn = churn_data["churn_rate_percent"] / 100
        
        # Average lifetime in months
        avg_lifetime_months = (1 / monthly_churn) if monthly_churn > 0 else 60  # Cap at 5 years
        avg_lifetime_months = min(avg_lifetime_months, 60)
        
        ltv = arpu * avg_lifetime_months
        
        return {
            "ltv": round(ltv, 2),
            "arpu": round(arpu, 2),
            "avg_lifetime_months": round(avg_lifetime_months, 1),
            "monthly_churn_rate": round(monthly_churn * 100, 2),
            "ltv_to_cac_ratio": None,  # Would need CAC data
            "health_indicator": "excellent" if ltv > 500 else "good" if ltv > 200 else "fair" if ltv > 100 else "needs_improvement"
        }
    
    # ============== REVENUE ANALYSIS ==============
    
    async def get_revenue_breakdown(
        self,
        user_id: Optional[str] = None,
        period: str = "monthly",
        months_back: int = 6
    ) -> Dict[str, Any]:
        """
        Get detailed revenue breakdown by source/category over time.
        """
        start_date = (datetime.now(timezone.utc) - relativedelta(months=months_back)).strftime("%Y-%m")
        
        match_stage = {"category": "Income", "month_year": {"$gte": start_date}}
        if user_id:
            match_stage["user_id"] = user_id
        
        pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": {
                    "month": "$month_year",
                    "source": "$source"
                },
                "revenue": {"$sum": "$revenue"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.month": 1}}
        ]
        
        results = await self.db.calculator.aggregate(pipeline).to_list(500)
        
        # Organize by month and source
        by_month = {}
        by_source = {}
        total_revenue = 0
        
        for r in results:
            month = r["_id"]["month"]
            source = r["_id"]["source"] or "Other"
            revenue = r["revenue"]
            total_revenue += revenue
            
            if month not in by_month:
                by_month[month] = {"total": 0, "sources": {}}
            by_month[month]["total"] += revenue
            by_month[month]["sources"][source] = revenue
            
            if source not in by_source:
                by_source[source] = 0
            by_source[source] += revenue
        
        # Calculate percentages
        source_percentages = {
            source: round(rev / total_revenue * 100, 1) if total_revenue > 0 else 0
            for source, rev in by_source.items()
        }
        
        # Top revenue source
        top_source = max(by_source.items(), key=lambda x: x[1])[0] if by_source else None
        
        return {
            "total_revenue": round(total_revenue, 2),
            "by_month": by_month,
            "by_source": {k: round(v, 2) for k, v in by_source.items()},
            "source_percentages": source_percentages,
            "top_revenue_source": top_source,
            "period_analyzed": f"Last {months_back} months",
            "avg_monthly_revenue": round(total_revenue / months_back, 2) if months_back > 0 else 0
        }
    
    async def get_revenue_trends(
        self,
        user_id: Optional[str] = None,
        months_back: int = 12
    ) -> Dict[str, Any]:
        """
        Analyze revenue trends over time.
        """
        start_date = (datetime.now(timezone.utc) - relativedelta(months=months_back)).strftime("%Y-%m")
        
        match_stage = {"category": "Income", "month_year": {"$gte": start_date}}
        if user_id:
            match_stage["user_id"] = user_id
        
        pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": "$month_year",
                "revenue": {"$sum": "$revenue"},
                "transactions": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        results = await self.db.calculator.aggregate(pipeline).to_list(months_back + 1)
        
        if len(results) < 2:
            return {
                "trend": "insufficient_data",
                "data_points": len(results),
                "monthly_data": [{"month": r["_id"], "revenue": r["revenue"]} for r in results]
            }
        
        # Calculate trend
        revenues = [r["revenue"] for r in results]
        first_half_avg = sum(revenues[:len(revenues)//2]) / (len(revenues)//2) if len(revenues) > 1 else 0
        second_half_avg = sum(revenues[len(revenues)//2:]) / (len(revenues) - len(revenues)//2) if len(revenues) > 1 else 0
        
        if second_half_avg > first_half_avg * 1.1:
            trend = "growing"
            trend_strength = "strong" if second_half_avg > first_half_avg * 1.25 else "moderate"
        elif second_half_avg < first_half_avg * 0.9:
            trend = "declining"
            trend_strength = "strong" if second_half_avg < first_half_avg * 0.75 else "moderate"
        else:
            trend = "stable"
            trend_strength = "consistent"
        
        # Calculate MoM growth rates
        growth_rates = []
        for i in range(1, len(revenues)):
            if revenues[i-1] > 0:
                growth = (revenues[i] - revenues[i-1]) / revenues[i-1] * 100
                growth_rates.append(round(growth, 2))
        
        avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0
        
        return {
            "trend": trend,
            "trend_strength": trend_strength,
            "avg_monthly_growth_percent": round(avg_growth, 2),
            "monthly_data": [
                {"month": r["_id"], "revenue": round(r["revenue"], 2), "transactions": r["transactions"]}
                for r in results
            ],
            "highest_month": max(results, key=lambda x: x["revenue"])["_id"] if results else None,
            "lowest_month": min(results, key=lambda x: x["revenue"])["_id"] if results else None,
            "total_analyzed": round(sum(revenues), 2),
            "period": f"Last {months_back} months"
        }
    
    # ============== EXPENSE ANALYSIS ==============
    
    async def get_expense_breakdown(
        self,
        user_id: Optional[str] = None,
        months_back: int = 6
    ) -> Dict[str, Any]:
        """
        Get detailed expense breakdown by category.
        """
        start_date = (datetime.now(timezone.utc) - relativedelta(months=months_back)).strftime("%Y-%m")
        
        match_stage = {"category": "Expense", "month_year": {"$gte": start_date}}
        if user_id:
            match_stage["user_id"] = user_id
        
        pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": {
                    "month": "$month_year",
                    "source": "$source"
                },
                "expenses": {"$sum": "$expenses"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.month": 1}}
        ]
        
        results = await self.db.calculator.aggregate(pipeline).to_list(500)
        
        by_month = {}
        by_category = {}
        total_expenses = 0
        
        for r in results:
            month = r["_id"]["month"]
            category = r["_id"]["source"] or "Other"
            expense = r["expenses"]
            total_expenses += expense
            
            if month not in by_month:
                by_month[month] = {"total": 0, "categories": {}}
            by_month[month]["total"] += expense
            by_month[month]["categories"][category] = expense
            
            if category not in by_category:
                by_category[category] = 0
            by_category[category] += expense
        
        return {
            "total_expenses": round(total_expenses, 2),
            "by_month": by_month,
            "by_category": {k: round(v, 2) for k, v in by_category.items()},
            "top_expense_category": max(by_category.items(), key=lambda x: x[1])[0] if by_category else None,
            "avg_monthly_expenses": round(total_expenses / months_back, 2) if months_back > 0 else 0,
            "period": f"Last {months_back} months"
        }
    
    # ============== PROFIT ANALYSIS ==============
    
    async def get_profit_analysis(
        self,
        user_id: Optional[str] = None,
        months_back: int = 6
    ) -> Dict[str, Any]:
        """
        Comprehensive profit analysis including margins and trends.
        """
        revenue_data = await self.get_revenue_breakdown(user_id, months_back=months_back)
        expense_data = await self.get_expense_breakdown(user_id, months_back=months_back)
        
        total_revenue = revenue_data["total_revenue"]
        total_expenses = expense_data["total_expenses"]
        net_profit = total_revenue - total_expenses
        
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Monthly profit breakdown
        monthly_profit = []
        all_months = set(revenue_data.get("by_month", {}).keys()) | set(expense_data.get("by_month", {}).keys())
        
        for month in sorted(all_months):
            rev = revenue_data.get("by_month", {}).get(month, {}).get("total", 0)
            exp = expense_data.get("by_month", {}).get(month, {}).get("total", 0)
            monthly_profit.append({
                "month": month,
                "revenue": round(rev, 2),
                "expenses": round(exp, 2),
                "profit": round(rev - exp, 2),
                "margin_percent": round((rev - exp) / rev * 100, 1) if rev > 0 else 0
            })
        
        # Health indicators
        if profit_margin >= 40:
            health = "excellent"
        elif profit_margin >= 25:
            health = "healthy"
        elif profit_margin >= 10:
            health = "moderate"
        elif profit_margin >= 0:
            health = "low"
        else:
            health = "loss"
        
        return {
            "total_revenue": round(total_revenue, 2),
            "total_expenses": round(total_expenses, 2),
            "net_profit": round(net_profit, 2),
            "profit_margin_percent": round(profit_margin, 2),
            "monthly_breakdown": monthly_profit,
            "avg_monthly_profit": round(net_profit / months_back, 2) if months_back > 0 else 0,
            "health_indicator": health,
            "expense_to_revenue_ratio": round(total_expenses / total_revenue, 2) if total_revenue > 0 else 0,
            "period": f"Last {months_back} months"
        }
    
    # ============== REVENUE FORECASTING ==============
    
    async def forecast_revenue(
        self,
        user_id: Optional[str] = None,
        months_ahead: int = 3
    ) -> Dict[str, Any]:
        """
        Forecast future revenue based on historical patterns.
        Uses simple linear regression on monthly data.
        """
        # Get historical data
        trends = await self.get_revenue_trends(user_id, months_back=12)
        monthly_data = trends.get("monthly_data", [])
        
        if len(monthly_data) < 3:
            return {
                "forecast": None,
                "error": "Insufficient historical data for forecasting (need at least 3 months)"
            }
        
        # Simple moving average + trend adjustment
        revenues = [m["revenue"] for m in monthly_data]
        
        # Calculate trend
        avg_growth = trends.get("avg_monthly_growth_percent", 0) / 100
        
        # Last 3 month average as base
        base = sum(revenues[-3:]) / 3
        
        forecasts = []
        current_month = datetime.now(timezone.utc)
        
        for i in range(1, months_ahead + 1):
            future_month = (current_month + relativedelta(months=i)).strftime("%Y-%m")
            # Apply growth rate with dampening
            predicted = base * (1 + avg_growth * i * 0.8)  # 0.8 dampening factor
            forecasts.append({
                "month": future_month,
                "predicted_revenue": round(max(0, predicted), 2),
                "confidence": "high" if i <= 1 else "medium" if i <= 2 else "low"
            })
        
        return {
            "forecasts": forecasts,
            "base_amount": round(base, 2),
            "growth_rate_used": round(avg_growth * 100, 2),
            "confidence_interval": {
                "lower_bound_factor": 0.8,
                "upper_bound_factor": 1.2
            },
            "methodology": "Moving average with trend adjustment",
            "data_points_used": len(revenues),
            "note": "Forecasts are estimates based on historical patterns and may vary"
        }
    
    # ============== SELF-FUNDING LOOP ANALYTICS ==============
    
    async def get_self_funding_loop_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of the Self-Funding Loop.
        Shows how subscription revenue flows through the Calculator.
        """
        # Get subscription revenue statistics
        sub_pipeline = [
            {"$match": {"source": {"$regex": "Subscription", "$options": "i"}}},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": "$revenue"},
                "transaction_count": {"$sum": 1},
                "avg_transaction": {"$avg": "$revenue"}
            }}
        ]
        sub_result = await self.db.calculator.aggregate(sub_pipeline).to_list(1)
        
        # Get non-subscription revenue
        other_pipeline = [
            {"$match": {"source": {"$not": {"$regex": "Subscription", "$options": "i"}}, "category": "Income"}},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": "$revenue"},
                "transaction_count": {"$sum": 1}
            }}
        ]
        other_result = await self.db.calculator.aggregate(other_pipeline).to_list(1)
        
        sub_revenue = sub_result[0]["total_revenue"] if sub_result else 0
        sub_count = sub_result[0]["transaction_count"] if sub_result else 0
        sub_avg = sub_result[0]["avg_transaction"] if sub_result else 0
        
        other_revenue = other_result[0]["total_revenue"] if other_result else 0
        other_count = other_result[0]["transaction_count"] if other_result else 0
        
        total_revenue = sub_revenue + other_revenue
        sub_percentage = (sub_revenue / total_revenue * 100) if total_revenue > 0 else 0
        
        # Get active creator subscriptions
        active_subs = await self.db.creator_subscriptions.count_documents({"status": "active"})
        
        return {
            "status": "active",
            "subscription_revenue": {
                "total": round(sub_revenue, 2),
                "transactions": sub_count,
                "avg_per_transaction": round(sub_avg, 2),
                "percentage_of_total": round(sub_percentage, 1)
            },
            "other_revenue": {
                "total": round(other_revenue, 2),
                "transactions": other_count
            },
            "total_platform_revenue": round(total_revenue, 2),
            "active_subscriptions": active_subs,
            "loop_health": "optimal" if sub_percentage > 60 else "healthy" if sub_percentage > 40 else "diversified",
            "description": "All subscription payments automatically create Calculator entries, ensuring complete financial tracking"
        }
    
    # ============== CREATOR-SPECIFIC ANALYTICS ==============
    
    async def get_creator_financial_summary(self, creator_id: str) -> Dict[str, Any]:
        """
        Get comprehensive financial summary for a specific creator.
        """
        # Get creator info
        creator = await self.db.creators.find_one({"id": creator_id}, {"_id": 0})
        if not creator:
            return {"error": "Creator not found"}
        
        # Get subscription status
        subscription = await self.db.creator_subscriptions.find_one(
            {"creator_id": creator_id, "status": "active"},
            {"_id": 0}
        )
        
        # Get MRR for this creator's contributions
        mrr_data = await self.get_mrr(creator_id)
        
        # Get revenue history
        revenue_trends = await self.get_revenue_trends(creator_id, months_back=6)
        
        # Get expense breakdown
        expense_data = await self.get_expense_breakdown(creator_id, months_back=6)
        
        # Profit analysis
        profit_data = await self.get_profit_analysis(creator_id, months_back=6)
        
        return {
            "creator": {
                "id": creator_id,
                "name": creator.get("name"),
                "tier": subscription.get("tier") if subscription else "Free"
            },
            "subscription": {
                "active": subscription is not None,
                "plan_id": subscription.get("plan_id") if subscription else None,
                "current_period_end": subscription.get("current_period_end") if subscription else None
            },
            "financials": {
                "mrr_contribution": mrr_data.get("mrr", 0),
                "total_revenue": revenue_trends.get("total_analyzed", 0),
                "total_expenses": expense_data.get("total_expenses", 0),
                "net_profit": profit_data.get("net_profit", 0),
                "profit_margin": profit_data.get("profit_margin_percent", 0)
            },
            "trends": {
                "revenue_trend": revenue_trends.get("trend", "stable"),
                "avg_monthly_revenue": revenue_trends.get("monthly_data", [{}])[-1].get("revenue", 0) if revenue_trends.get("monthly_data") else 0
            },
            "health_score": profit_data.get("health_indicator", "unknown")
        }
    
    # ============== PLATFORM DASHBOARD ==============
    
    async def get_platform_financial_dashboard(self) -> Dict[str, Any]:
        """
        Get comprehensive platform-wide financial dashboard.
        """
        mrr = await self.get_mrr()
        arr = await self.get_arr()
        churn = await self.get_churn_rate()
        ltv = await self.get_ltv()
        loop_status = await self.get_self_funding_loop_status()
        profit = await self.get_profit_analysis(months_back=3)
        forecast = await self.forecast_revenue(months_ahead=3)
        
        return {
            "key_metrics": {
                "mrr": mrr,
                "arr": arr,
                "churn": churn,
                "ltv": ltv
            },
            "self_funding_loop": loop_status,
            "profit_analysis": profit,
            "revenue_forecast": forecast,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "report_type": "platform_financial_dashboard"
        }


# Singleton instance (initialized in server.py startup)
calculator_service: Optional[CalculatorService] = None
