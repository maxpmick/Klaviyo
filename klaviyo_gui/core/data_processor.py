"""
Data processor for converting Klaviyo events to checkout snapshots
Adapted from fetch_metrics.py business logic
"""

import time
import logging
from typing import Dict, Any, Optional, List, Callable, Set
from .models import LineItem, CheckoutSnapshot, ProfileInfo, ProcessingStats, SyncResult
from .api_client import KlaviyoApiClient


class DataProcessor:
    """
    Processes Klaviyo events and creates checkout snapshots
    """
    
    def __init__(self, api_client: KlaviyoApiClient):
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        
        # Target metric names (case insensitive)
        self.target_metric_names: Set[str] = {
            name.lower() for name in ["Checkout Started", "Started Checkout"]
        }
    
    def _first_src(self, arr: Any) -> Optional[str]:
        """Extract first src from image array"""
        try:
            if isinstance(arr, list) and arr:
                item = arr[0]
                if isinstance(item, dict):
                    return item.get("src")
        except Exception:
            pass
        return None
    
    def _coerce_float(self, value: Any) -> float:
        """Convert value to float with fallback to 0.0"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                return float(value.strip())
        except Exception:
            pass
        return 0.0
    
    def _pick_image_url(self, item: dict) -> Optional[str]:
        """Pick the best image URL from item data"""
        product = item.get("product") or {}
        variant = product.get("variant") or {}
        variant_images = variant.get("images") or []
        product_images = product.get("images") or []
        
        return (
            self._first_src(variant_images) or
            self._first_src(product_images)
        )
    
    def _line_item_to_snapshot(self, item: dict) -> LineItem:
        """Convert line item data to LineItem model"""
        product = item.get("product") or {}
        title = (
            product.get("title") or 
            item.get("presentment_title") or 
            item.get("title") or 
            ""
        )
        
        return LineItem(
            product_id=product.get("id"),
            variant_id=item.get("variant_id") or (product.get("variant") or {}).get("id"),
            title=title,
            image_url=self._pick_image_url(item),
            quantity=int(item.get("quantity") or 0),
            line_price=self._coerce_float(item.get("line_price"))
        )
    
    def event_to_snapshot(self, event: dict) -> Optional[CheckoutSnapshot]:
        """Convert Klaviyo event to CheckoutSnapshot"""
        attrs = event.get("attributes") or {}
        
        # Handle different property structures
        props = attrs.get("properties") or attrs.get("event_properties") or {}
        
        # Try multiple locations for extra data
        extra = props.get("extra") or props.get("$extra") or {}
        
        # Try multiple locations for line items
        line_items_data = (
            extra.get("line_items") or 
            props.get("Items") or 
            props.get("items") or 
            []
        )
        
        items = [self._line_item_to_snapshot(item) for item in line_items_data]
        
        # Try multiple locations for checkout URL
        checkout_url = (
            extra.get("checkout_url") or
            extra.get("responsive_checkout_url") or
            props.get("checkout_url") or
            props.get("Checkout URL")
        )
        
        # Try multiple locations for currency
        currency = (
            extra.get("presentment_currency") or
            props.get("presentment_currency") or
            props.get("$currency_code") or
            "USD"
        )
        
        updated_at = attrs.get("timestamp") or attrs.get("datetime") or attrs.get("time")
        
        # Must have either checkout URL or items
        if not checkout_url and not items:
            return None
        
        return CheckoutSnapshot(
            checkout_url=checkout_url,
            currency=currency,
            updated_at=updated_at,
            items=items
        )
    
    def find_matching_event(self, profile_id: str) -> Optional[dict]:
        """Find the newest matching checkout event for a profile"""
        for event in self.api_client.iterate_profile_events(profile_id):
            metric_name = (event.get("_metric_name") or "").strip().lower()
            if metric_name in self.target_metric_names:
                return event
        return None
    
    def summarize_snapshot_for_display(self, profile: ProfileInfo, snapshot: CheckoutSnapshot) -> str:
        """Create a human-readable summary of the snapshot"""
        lines = []
        lines.append(f"Profile: {profile.profile_id}  Email: {profile.display_email}")
        lines.append(f"  Checkout URL: {snapshot.checkout_url or '-'}")
        lines.append(f"  Currency: {snapshot.currency}   Updated At: {snapshot.updated_at or '-'}")
        lines.append(f"  Items ({len(snapshot.items)}):")
        
        for i, item in enumerate(snapshot.items, 1):
            lines.append(f"    {i}. {item.title} | Qty: {item.quantity} | Price: {item.line_price:.2f}")
            lines.append(f"       image: {item.image_url or '-'}")
        
        return "\n".join(lines)
    
    def process_profiles(
        self,
        segment_id: str,
        limit: Optional[int] = None,
        dry_run: bool = False,
        progress_callback: Optional[Callable[[ProcessingStats], None]] = None,
        should_stop: Optional[Callable[[], bool]] = None
    ) -> SyncResult:
        """
        Process all profiles in a segment
        
        Args:
            segment_id: Klaviyo segment ID
            limit: Optional limit on number of profiles to process
            dry_run: If True, don't update profiles, just return results
            progress_callback: Called with stats updates
            should_stop: Called to check if processing should stop
        
        Returns:
            SyncResult with statistics and results
        """
        stats = ProcessingStats()
        dry_run_results = [] if dry_run else None
        
        try:
            # Get all profiles from segment
            profiles_data = self.api_client.get_segment_profiles(segment_id, limit)
            if not profiles_data:
                return SyncResult(
                    success=False,
                    stats=stats,
                    error_message=f"No profiles found in segment {segment_id}"
                )
            
            stats.total_profiles = len(profiles_data)
            
            # Process each profile
            for profile_id, profile_attrs in profiles_data.items():
                # Check if we should stop
                if should_stop and should_stop():
                    break
                
                profile = ProfileInfo(
                    profile_id=profile_id,
                    email=profile_attrs.get("email"),
                    attributes=profile_attrs
                )
                
                stats.processed += 1
                
                # Update progress
                if progress_callback:
                    progress_callback(stats)
                
                try:
                    # Find matching event
                    matching_event = self.find_matching_event(profile_id)
                    if not matching_event:
                        stats.no_event += 1
                        continue
                    
                    # Convert to snapshot
                    snapshot = self.event_to_snapshot(matching_event)
                    if not snapshot:
                        stats.no_snapshot += 1
                        continue
                    
                    stats.matched += 1
                    
                    if dry_run:
                        # Add to dry run results
                        summary = self.summarize_snapshot_for_display(profile, snapshot)
                        dry_run_results.append(summary)
                    else:
                        # Update the profile
                        self.api_client.patch_profile_snapshot(profile_id, snapshot.to_dict())
                        stats.updated += 1
                        
                        # Log progress every 25 updates
                        if stats.updated % 25 == 0:
                            self.logger.info(f"Updated {stats.updated} profiles so far...")
                
                except Exception as e:
                    stats.errors += 1
                    self.logger.error(f"Error processing profile {profile_id} ({profile.display_email}): {e}")
                
                # Small delay every 50 profiles to be courteous
                if stats.processed % 50 == 0:
                    time.sleep(0.2)
            
            # Final progress update
            if progress_callback:
                progress_callback(stats)
            
            return SyncResult(
                success=True,
                stats=stats,
                dry_run_results=dry_run_results
            )
            
        except Exception as e:
            self.logger.error(f"Error during processing: {e}")
            return SyncResult(
                success=False,
                stats=stats,
                error_message=str(e),
                dry_run_results=dry_run_results
            )