"""
Data models for the Klaviyo Checkout Snapshot Sync Tool
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class LineItem:
    """Represents a line item in a checkout"""
    product_id: Optional[str]
    variant_id: Optional[str]
    title: str
    image_url: Optional[str]
    quantity: int
    line_price: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API"""
        return {
            "product_id": self.product_id,
            "variant_id": self.variant_id,
            "title": self.title,
            "image_url": self.image_url,
            "quantity": self.quantity,
            "line_price": self.line_price,
        }


@dataclass
class CheckoutSnapshot:
    """Represents a checkout snapshot"""
    checkout_url: Optional[str]
    currency: str
    updated_at: Optional[str]
    items: List[LineItem]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API"""
        return {
            "checkout_url": self.checkout_url,
            "currency": self.currency,
            "updated_at": self.updated_at,
            "items": [item.to_dict() for item in self.items],
        }


@dataclass
class ProfileInfo:
    """Represents profile information"""
    profile_id: str
    email: Optional[str]
    attributes: Dict[str, Any]
    
    @property
    def display_email(self) -> str:
        """Get email for display purposes"""
        if self.email:
            return self.email
        # Try to get email from properties
        props = self.attributes.get("properties", {})
        return props.get("$email", "no-email")


@dataclass
class ProcessingStats:
    """Statistics for processing operation"""
    total_profiles: int = 0
    processed: int = 0
    matched: int = 0
    updated: int = 0
    no_event: int = 0
    no_snapshot: int = 0
    errors: int = 0
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage"""
        if self.total_profiles == 0:
            return 0.0
        return (self.processed / self.total_profiles) * 100
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "total_profiles": self.total_profiles,
            "processed": self.processed,
            "matched": self.matched,
            "updated": self.updated,
            "no_event": self.no_event,
            "no_snapshot": self.no_snapshot,
            "errors": self.errors,
            "progress_percentage": self.progress_percentage,
        }


@dataclass
class SyncResult:
    """Result of a sync operation"""
    success: bool
    stats: ProcessingStats
    error_message: Optional[str] = None
    dry_run_results: Optional[List[str]] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "stats": self.stats.to_dict(),
            "error_message": self.error_message,
            "dry_run_results": self.dry_run_results,
        }