import logging
import requests
from django.conf import settings
from datetime import datetime

logger = logging.getLogger(__name__)


class CloudAPIClient:
    """HTTP client for VetCoreSoft Cloud API. Uses JWT authentication."""

    def __init__(self):
        self.base_url = getattr(settings, 'CLOUD_API_URL', 'http://cloud_api:8000')
        self.api_secret = getattr(settings, 'CLOUD_API_SECRET', 'vetcoresoft-dev-secret-change-in-prod')
        self._token = None
        self._token_expires = None

    def _get_token(self):
        if self._token and self._token_expires and datetime.now() < self._token_expires:
            return self._token
        resp = requests.post(
            f"{self.base_url}/admin/login",
            json={"secret": self.api_secret},
            timeout=10
        )
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        from datetime import timedelta
        self._token_expires = datetime.now() + timedelta(hours=23)
        return self._token

    def _headers(self):
        return {"Authorization": f"Bearer {self._get_token()}"}

    # --- License CRUD ---

    def list_licenses(self, is_active=None, plan=None, search=None):
        params = {}
        if is_active is not None:
            params['is_active'] = str(is_active).lower()
        if plan:
            params['plan'] = plan
        if search:
            params['search'] = search
        resp = requests.get(
            f"{self.base_url}/license/admin/list",
            headers=self._headers(), params=params, timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def get_license(self, hw_id):
        resp = requests.get(
            f"{self.base_url}/license/admin/{hw_id}",
            headers=self._headers(), timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def create_license(self, data):
        resp = requests.post(
            f"{self.base_url}/license/admin/create",
            json=data, headers=self._headers(), timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def update_license(self, hw_id, data):
        resp = requests.patch(
            f"{self.base_url}/license/admin/{hw_id}",
            json=data, headers=self._headers(), timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def revoke_license(self, hw_id):
        resp = requests.post(
            f"{self.base_url}/license/admin/revoke/{hw_id}",
            headers=self._headers(), timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def transfer_license(self, old_hw_id, new_hw_id):
        resp = requests.post(
            f"{self.base_url}/license/transfer",
            json={"old_hw_id": old_hw_id, "new_hw_id": new_hw_id},
            headers=self._headers(), timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def create_pending_action(self, hw_id, action_type, payload=None):
        resp = requests.post(
            f"{self.base_url}/auth/pending-action",
            json={"hardware_id": hw_id, "action_type": action_type, "payload": payload or {}},
            headers=self._headers(), timeout=10
        )
        resp.raise_for_status()
        return resp.json()
