"""
Pattern Export Service (Module A5)
Allows Premium+ creators to export pattern analysis data.
Supports JSON and CSV formats with filtering options.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import uuid
import json
import csv
import io
import hashlib

logger = logging.getLogger(__name__)


class PatternExportService:
    """
    Service for exporting pattern analysis data for Premium+ creators.
    Provides data in JSON and CSV formats with various filtering options.
    """
    
    # Tier access configuration
    ALLOWED_TIERS = ["premium", "elite"]
    
    def __init__(self, db, feature_gating=None, pattern_insights_service=None):
        self.db = db
        self.feature_gating = feature_gating
        self.pattern_insights_service = pattern_insights_service
    
    async def has_access(self, creator_id: str) -> Dict[str, Any]:
        """
        Check if creator has access to pattern export (Premium+ only).
        Returns access status and upgrade info if needed.
        """
        if not self.feature_gating:
            return {"has_access": True, "tier": "unknown"}
        
        tier, features = await self.feature_gating.get_creator_tier(creator_id)
        tier_value = tier.value if hasattr(tier, 'value') else tier
        
        has_access = tier_value in self.ALLOWED_TIERS
        
        return {
            "has_access": has_access,
            "tier": tier_value,
            "upgrade_needed": not has_access,
            "upgrade_message": "Upgrade to Premium to unlock pattern export functionality" if not has_access else None,
            "upgrade_url": "/creator/subscription" if not has_access else None
        }
    
    async def get_export_options(self, creator_id: str) -> Dict[str, Any]:
        """
        Get available export options for a creator.
        Returns format options, filter options, and current data availability.
        """
        access = await self.has_access(creator_id)
        if not access["has_access"]:
            return {
                "access_denied": True,
                "upgrade_message": access["upgrade_message"],
                "upgrade_url": access["upgrade_url"]
            }
        
        # Get current pattern count
        pattern_data = await self._gather_pattern_data(creator_id)
        
        return {
            "access_denied": False,
            "tier": access["tier"],
            "formats": [
                {"id": "json", "name": "JSON", "description": "Structured data format, ideal for developers"},
                {"id": "csv", "name": "CSV", "description": "Spreadsheet-compatible format, ideal for analysis"}
            ],
            "filters": {
                "categories": ["all", "success", "risk", "timing", "growth", "engagement", "platform", "content"],
                "confidence_levels": ["all", "high", "medium", "low"],
                "date_ranges": ["all", "7d", "30d", "90d", "1y"],
                "include_options": ["patterns", "recommendations", "trends", "feedback"]
            },
            "data_availability": {
                "total_patterns": len(pattern_data.get("patterns", [])),
                "total_recommendations": len(pattern_data.get("recommendations", [])),
                "has_trends": bool(pattern_data.get("trends")),
                "has_feedback": bool(pattern_data.get("feedback")),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        }
    
    async def export_patterns(
        self,
        creator_id: str,
        export_format: str = "json",
        categories: List[str] = None,
        confidence_level: str = "all",
        date_range: str = "all",
        include_recommendations: bool = True,
        include_trends: bool = True,
        include_feedback: bool = False
    ) -> Dict[str, Any]:
        """
        Export pattern data in the specified format.
        Returns exported data or error information.
        """
        # Check access
        access = await self.has_access(creator_id)
        if not access["has_access"]:
            return {
                "success": False,
                "access_denied": True,
                "upgrade_message": access["upgrade_message"],
                "upgrade_url": access["upgrade_url"]
            }
        
        # Validate format
        if export_format not in ["json", "csv"]:
            return {"success": False, "error": "Invalid format. Supported: json, csv"}
        
        # Gather all pattern data
        pattern_data = await self._gather_pattern_data(creator_id)
        
        # Apply filters
        filtered_data = await self._apply_filters(
            pattern_data,
            categories=categories,
            confidence_level=confidence_level,
            date_range=date_range,
            include_recommendations=include_recommendations,
            include_trends=include_trends,
            include_feedback=include_feedback
        )
        
        # Add export metadata
        export_metadata = {
            "export_id": f"EXP-{uuid.uuid4().hex[:8].upper()}",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "exported_by": creator_id,
            "format": export_format,
            "filters_applied": {
                "categories": categories or ["all"],
                "confidence_level": confidence_level,
                "date_range": date_range,
                "include_recommendations": include_recommendations,
                "include_trends": include_trends,
                "include_feedback": include_feedback
            },
            "record_counts": {
                "patterns": len(filtered_data.get("patterns", [])),
                "recommendations": len(filtered_data.get("recommendations", [])),
                "trends": len(filtered_data.get("trends", {})),
                "feedback_entries": len(filtered_data.get("feedback", []))
            }
        }
        
        # Generate export content
        if export_format == "json":
            export_content = await self._generate_json_export(filtered_data, export_metadata)
        else:
            export_content = await self._generate_csv_export(filtered_data, export_metadata)
        
        # Calculate checksum for data integrity
        checksum = hashlib.sha256(export_content.encode()).hexdigest()[:16]
        
        # Log the export
        await self._log_export(creator_id, export_metadata, checksum)
        
        return {
            "success": True,
            "export_id": export_metadata["export_id"],
            "format": export_format,
            "content": export_content,
            "content_type": "application/json" if export_format == "json" else "text/csv",
            "filename": f"pattern_export_{export_metadata['export_id']}.{export_format}",
            "checksum": checksum,
            "record_counts": export_metadata["record_counts"],
            "exported_at": export_metadata["exported_at"]
        }
    
    async def get_export_history(self, creator_id: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get export history for a creator.
        Returns list of previous exports with metadata.
        """
        access = await self.has_access(creator_id)
        if not access["has_access"]:
            return {
                "access_denied": True,
                "upgrade_message": access["upgrade_message"]
            }
        
        exports = await self.db.pattern_export_log.find(
            {"creator_id": creator_id},
            {"_id": 0}
        ).sort("exported_at", -1).limit(limit).to_list(limit)
        
        return {
            "exports": exports,
            "total": len(exports),
            "access_denied": False
        }
    
    async def get_export_preview(
        self,
        creator_id: str,
        categories: List[str] = None,
        confidence_level: str = "all",
        date_range: str = "all"
    ) -> Dict[str, Any]:
        """
        Get a preview of what would be exported without generating the full export.
        Useful for UI to show counts and sample data.
        """
        access = await self.has_access(creator_id)
        if not access["has_access"]:
            return {
                "access_denied": True,
                "upgrade_message": access["upgrade_message"]
            }
        
        # Gather data
        pattern_data = await self._gather_pattern_data(creator_id)
        
        # Apply filters
        filtered_data = await self._apply_filters(
            pattern_data,
            categories=categories,
            confidence_level=confidence_level,
            date_range=date_range,
            include_recommendations=True,
            include_trends=True,
            include_feedback=False
        )
        
        # Get sample patterns (first 3)
        sample_patterns = filtered_data.get("patterns", [])[:3]
        
        # Category breakdown
        category_counts = {}
        for p in filtered_data.get("patterns", []):
            cat = p.get("category", "unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Confidence breakdown
        confidence_counts = {"high": 0, "medium": 0, "low": 0}
        for p in filtered_data.get("patterns", []):
            level = p.get("confidence_level", "medium")
            if level in confidence_counts:
                confidence_counts[level] += 1
        
        return {
            "access_denied": False,
            "preview": {
                "total_patterns": len(filtered_data.get("patterns", [])),
                "total_recommendations": len(filtered_data.get("recommendations", [])),
                "category_breakdown": category_counts,
                "confidence_breakdown": confidence_counts,
                "sample_patterns": sample_patterns,
                "has_actionable": any(p.get("actionable") for p in filtered_data.get("patterns", [])),
                "estimated_file_size": self._estimate_file_size(filtered_data)
            }
        }
    
    # ============== PRIVATE METHODS ==============
    
    async def _gather_pattern_data(self, creator_id: str) -> Dict[str, Any]:
        """Gather all pattern-related data for a creator."""
        data = {
            "patterns": [],
            "recommendations": [],
            "trends": {},
            "feedback": []
        }
        
        # Get patterns from the pattern insights service if available
        if self.pattern_insights_service:
            try:
                patterns_result = await self.pattern_insights_service.get_creator_patterns(creator_id, limit=100)
                if not patterns_result.get("access_denied"):
                    data["patterns"] = patterns_result.get("patterns", [])
                
                recs_result = await self.pattern_insights_service.get_pattern_recommendations(creator_id)
                if not recs_result.get("access_denied"):
                    data["recommendations"] = recs_result.get("recommendations", [])
                
                trends_result = await self.pattern_insights_service.get_pattern_trends(creator_id, days=90)
                if not trends_result.get("access_denied"):
                    data["trends"] = trends_result.get("trends", {})
            except Exception as e:
                logger.error(f"Error getting patterns from service: {e}")
        
        # Get stored patterns from database
        stored_patterns = await self.db.creator_patterns.find(
            {"creator_id": creator_id},
            {"_id": 0}
        ).to_list(100)
        
        # Merge stored patterns with generated ones
        existing_ids = {p.get("pattern_id") for p in data["patterns"]}
        for sp in stored_patterns:
            if sp.get("pattern_id") not in existing_ids:
                data["patterns"].append(sp)
        
        # Get feedback
        feedback = await self.db.pattern_feedback.find(
            {"creator_id": creator_id},
            {"_id": 0}
        ).to_list(100)
        data["feedback"] = feedback
        
        return data
    
    async def _apply_filters(
        self,
        data: Dict[str, Any],
        categories: List[str] = None,
        confidence_level: str = "all",
        date_range: str = "all",
        include_recommendations: bool = True,
        include_trends: bool = True,
        include_feedback: bool = False
    ) -> Dict[str, Any]:
        """Apply filters to the pattern data."""
        filtered = {"patterns": [], "recommendations": [], "trends": {}, "feedback": []}
        
        # Filter patterns
        patterns = data.get("patterns", [])
        
        # Category filter
        if categories and "all" not in categories:
            patterns = [p for p in patterns if p.get("category") in categories]
        
        # Confidence filter
        if confidence_level != "all":
            patterns = [p for p in patterns if p.get("confidence_level") == confidence_level]
        
        # Date filter
        if date_range != "all":
            cutoff = self._get_date_cutoff(date_range)
            patterns = [
                p for p in patterns
                if p.get("discovered_at", "") >= cutoff.isoformat()
            ]
        
        filtered["patterns"] = patterns
        
        # Include recommendations if requested
        if include_recommendations:
            recs = data.get("recommendations", [])
            # Filter recommendations to match pattern categories
            if categories and "all" not in categories:
                recs = [r for r in recs if r.get("category") in categories]
            filtered["recommendations"] = recs
        
        # Include trends if requested
        if include_trends:
            trends = data.get("trends", {})
            # Filter trends to match categories
            if categories and "all" not in categories:
                filtered["trends"] = {k: v for k, v in trends.items() if k in categories}
            else:
                filtered["trends"] = trends
        
        # Include feedback if requested
        if include_feedback:
            filtered["feedback"] = data.get("feedback", [])
        
        return filtered
    
    def _get_date_cutoff(self, date_range: str) -> datetime:
        """Get cutoff date for filtering."""
        now = datetime.now(timezone.utc)
        
        if date_range == "7d":
            return now - timedelta(days=7)
        elif date_range == "30d":
            return now - timedelta(days=30)
        elif date_range == "90d":
            return now - timedelta(days=90)
        elif date_range == "1y":
            return now - timedelta(days=365)
        else:
            return datetime.min.replace(tzinfo=timezone.utc)
    
    async def _generate_json_export(
        self,
        data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> str:
        """Generate JSON export content."""
        export_doc = {
            "metadata": metadata,
            "data": {
                "patterns": data.get("patterns", []),
                "recommendations": data.get("recommendations", []),
                "trends": data.get("trends", {}),
                "feedback": data.get("feedback", [])
            },
            "summary": {
                "total_patterns": len(data.get("patterns", [])),
                "categories": list(set(p.get("category") for p in data.get("patterns", []))),
                "high_confidence_count": len([p for p in data.get("patterns", []) if p.get("confidence_level") == "high"]),
                "actionable_count": len([p for p in data.get("patterns", []) if p.get("actionable")])
            }
        }
        
        return json.dumps(export_doc, indent=2, default=str)
    
    async def _generate_csv_export(
        self,
        data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> str:
        """Generate CSV export content."""
        output = io.StringIO()
        
        # Write metadata section
        output.write("# PATTERN EXPORT\n")
        output.write(f"# Export ID: {metadata['export_id']}\n")
        output.write(f"# Exported At: {metadata['exported_at']}\n")
        output.write(f"# Total Patterns: {metadata['record_counts']['patterns']}\n")
        output.write(f"# Total Recommendations: {metadata['record_counts']['recommendations']}\n")
        output.write("\n")
        
        # Patterns section
        patterns = data.get("patterns", [])
        if patterns:
            output.write("## PATTERNS\n")
            pattern_writer = csv.writer(output)
            pattern_writer.writerow([
                "Pattern ID", "Category", "Title", "Description", 
                "Confidence", "Confidence Level", "Actionable",
                "Recommended Action", "Discovered At"
            ])
            
            for p in patterns:
                pattern_writer.writerow([
                    p.get("pattern_id", ""),
                    p.get("category", ""),
                    p.get("title", ""),
                    p.get("description", ""),
                    f"{p.get('confidence', 0) * 100:.1f}%",
                    p.get("confidence_level", ""),
                    "Yes" if p.get("actionable") else "No",
                    p.get("recommended_action", ""),
                    p.get("discovered_at", "")
                ])
            
            output.write("\n")
        
        # Recommendations section
        recommendations = data.get("recommendations", [])
        if recommendations:
            output.write("## RECOMMENDATIONS\n")
            rec_writer = csv.writer(output)
            rec_writer.writerow([
                "Recommendation ID", "Category", "Title", "Action",
                "Impact", "Effort", "Priority"
            ])
            
            for r in recommendations:
                rec_writer.writerow([
                    r.get("id", ""),
                    r.get("category", ""),
                    r.get("title", ""),
                    r.get("action", ""),
                    r.get("impact", ""),
                    r.get("effort", ""),
                    r.get("priority", "")
                ])
            
            output.write("\n")
        
        # Trends summary section
        trends = data.get("trends", {})
        if trends:
            output.write("## TRENDS SUMMARY\n")
            trend_writer = csv.writer(output)
            trend_writer.writerow(["Category", "Data Points", "Latest Confidence"])
            
            for category, trend_data in trends.items():
                if trend_data:
                    latest = trend_data[-1] if trend_data else {}
                    trend_writer.writerow([
                        category,
                        len(trend_data),
                        f"{latest.get('confidence', 0) * 100:.1f}%" if latest else "N/A"
                    ])
            
            output.write("\n")
        
        # Feedback section
        feedback = data.get("feedback", [])
        if feedback:
            output.write("## FEEDBACK HISTORY\n")
            fb_writer = csv.writer(output)
            fb_writer.writerow(["Feedback ID", "Pattern ID", "Helpful", "Feedback Text", "Created At"])
            
            for f in feedback:
                fb_writer.writerow([
                    f.get("id", ""),
                    f.get("pattern_id", ""),
                    "Yes" if f.get("is_helpful") else "No",
                    f.get("feedback_text", ""),
                    f.get("created_at", "")
                ])
        
        return output.getvalue()
    
    def _estimate_file_size(self, data: Dict[str, Any]) -> str:
        """Estimate the export file size."""
        # Rough estimation based on data counts
        patterns_size = len(data.get("patterns", [])) * 500  # ~500 bytes per pattern
        recs_size = len(data.get("recommendations", [])) * 200
        trends_size = sum(len(v) for v in data.get("trends", {}).values()) * 100
        feedback_size = len(data.get("feedback", [])) * 150
        
        total_bytes = patterns_size + recs_size + trends_size + feedback_size + 500  # metadata overhead
        
        if total_bytes < 1024:
            return f"{total_bytes} B"
        elif total_bytes < 1024 * 1024:
            return f"{total_bytes / 1024:.1f} KB"
        else:
            return f"{total_bytes / (1024 * 1024):.2f} MB"
    
    async def _log_export(
        self,
        creator_id: str,
        metadata: Dict[str, Any],
        checksum: str
    ) -> None:
        """Log the export for history tracking."""
        log_entry = {
            "export_id": metadata["export_id"],
            "creator_id": creator_id,
            "exported_at": metadata["exported_at"],
            "format": metadata["format"],
            "filters": metadata["filters_applied"],
            "record_counts": metadata["record_counts"],
            "checksum": checksum
        }
        
        try:
            await self.db.pattern_export_log.insert_one(log_entry)
        except Exception as e:
            logger.error(f"Error logging export: {e}")
