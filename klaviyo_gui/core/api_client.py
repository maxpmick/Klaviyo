"""
Klaviyo API client adapted from fetch_metrics.py
Handles all API interactions with proper error handling and rate limiting.
"""

import time
import json
import logging
import requests
from typing import Dict, Any, Optional, Iterable, Callable
from dataclasses import dataclass


@dataclass
class ApiConfig:
    """Configuration for API client"""
    api_key: str
    revision: str = "2025-07-15"
    base_url: str = "https://a.klaviyo.com/api"
    timeout: int = 60
    max_retries: int = 5


class KlaviyoApiClient:
    """
    Klaviyo API client with rate limiting, retries, and progress callbacks
    """
    
    def __init__(self, config: ApiConfig, progress_callback: Optional[Callable[[str], None]] = None):
        self.config = config
        self.progress_callback = progress_callback
        self.logger = logging.getLogger(__name__)
        
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "revision": config.revision,
            "Authorization": f"Klaviyo-API-Key {config.api_key}",
        }
    
    def _log_progress(self, message: str):
        """Log progress and call callback if provided"""
        self.logger.info(message)
        if self.progress_callback:
            self.progress_callback(message)
    
    def _get(self, url: str, params: Optional[dict] = None) -> dict:
        """
        HTTP GET with retry logic and rate limiting
        """
        for attempt in range(self.config.max_retries):
            try:
                response = requests.get(
                    url, 
                    headers=self.headers, 
                    params=params, 
                    timeout=self.config.timeout
                )
                
                if response.status_code == 429:
                    wait_time = int(response.headers.get("Retry-After", "2"))
                    self._log_progress(f"Rate limited (GET), waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                if 500 <= response.status_code < 600:
                    wait_time = 2 ** attempt
                    self._log_progress(f"Server error {response.status_code} (GET), retry in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == self.config.max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                self._log_progress(f"Request failed: {e}, retry in {wait_time}s")
                time.sleep(wait_time)
        
        return {}
    
    def _patch(self, url: str, payload: dict) -> dict:
        """
        HTTP PATCH with retry logic and rate limiting
        """
        body = json.dumps(payload)
        
        for attempt in range(self.config.max_retries):
            try:
                response = requests.patch(
                    url, 
                    headers=self.headers, 
                    data=body, 
                    timeout=self.config.timeout
                )
                
                if response.status_code == 429:
                    wait_time = int(response.headers.get("Retry-After", "2"))
                    self._log_progress(f"Rate limited (PATCH), waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                if 500 <= response.status_code < 600:
                    wait_time = 2 ** attempt
                    self._log_progress(f"Server error {response.status_code} (PATCH), retry in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                
                if response.status_code in (200, 202):
                    try:
                        return response.json()
                    except Exception:
                        return {}
                
                response.raise_for_status()
                
            except requests.exceptions.RequestException as e:
                if attempt == self.config.max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                self._log_progress(f"Request failed: {e}, retry in {wait_time}s")
                time.sleep(wait_time)
        
        return {}
    
    def test_connection(self) -> bool:
        """
        Test API connection by making a simple request
        """
        try:
            url = f"{self.config.base_url}/accounts"
            response = requests.get(url, headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def get_segment_profiles(self, segment_id: str, limit: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get all profiles from a segment with pagination
        Returns: {profile_id: attributes}
        """
        url = f"{self.config.base_url}/segments/{segment_id}/profiles"
        params = {}
        
        profiles = {}
        page_count = 0
        
        self._log_progress(f"Fetching profiles from segment {segment_id}...")
        
        while True:
            page_count += 1
            self._log_progress(f"Fetching page {page_count}...")
            
            data = self._get(url, params=params)
            
            for row in data.get("data", []):
                if row.get("type") == "profile":
                    profile_id = row.get("id")
                    attributes = row.get("attributes") or {}
                    profiles[profile_id] = attributes
                    
                    if limit and len(profiles) >= limit:
                        self._log_progress(f"Reached limit of {limit} profiles")
                        return profiles
            
            next_url = data.get("links", {}).get("next")
            if not next_url:
                break
            
            url, params = next_url, None
            
            # Small delay between pages to be courteous
            time.sleep(0.1)
        
        self._log_progress(f"Loaded {len(profiles)} profiles from segment {segment_id}")
        return profiles
    
    def iterate_profile_events(self, profile_id: str) -> Iterable[dict]:
        """
        Iterate through events for a profile, newest first
        """
        url = f"{self.config.base_url}/events"
        params = {
            "filter": f'equals(profile_id,"{profile_id}")',
            "sort": "-timestamp",
            "include": "metric",
            "fields[metric]": "name",
        }
        
        while True:
            data = self._get(url, params=params)
            
            # Build metric name lookup
            metric_name_by_id = {}
            for inc in data.get("included", []):
                if inc.get("type") == "metric":
                    metric_id = inc.get("id")
                    name = (inc.get("attributes", {}) or {}).get("name")
                    if metric_id and name:
                        metric_name_by_id[metric_id] = name
            
            # Yield events with metric names
            for event in data.get("data", []):
                rel = (event.get("relationships") or {}).get("metric") or {}
                metric_id = (rel.get("data") or {}).get("id")
                event["_metric_name"] = metric_name_by_id.get(metric_id, "")
                yield event
            
            next_url = data.get("links", {}).get("next")
            if not next_url:
                break
            
            url, params = next_url, None
    
    def patch_profile_snapshot(self, profile_id: str, snapshot: dict) -> None:
        """
        Update profile with checkout snapshot data
        """
        url = f"{self.config.base_url}/profiles/{profile_id}"
        payload = {
            "data": {
                "type": "profile",
                "id": profile_id,
                "attributes": {
                    "properties": {
                        "last_checkout_snapshot": snapshot
                    }
                }
            }
        }
        self._patch(url, payload)