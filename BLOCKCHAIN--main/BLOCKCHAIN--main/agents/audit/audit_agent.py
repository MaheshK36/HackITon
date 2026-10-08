"""
Software Platform Login/Logout Audit & Anomaly Detection System — Audit Agent (Stage 3)
Computes SHA-256 hashes over canonical login/logout access records and submits them to AccessAuditLog.sol on-chain.
Enables full cryptographic verifiability of all software access logs and anomaly findings.
"""
from __future__ import annotations

import asyncio
import os
import json
import time
import hashlib
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
import structlog

logger = structlog.get_logger(__name__)

try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False

CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "logHash",      "type": "bytes32"},
            {"internalType": "string",  "name": "userId",       "type": "string"},
            {"internalType": "string",  "name": "eventType",    "type": "string"},
            {"internalType": "uint8",   "name": "anomalyScore", "type": "uint8"},
            {"internalType": "bool",    "name": "isAnomaly",    "type": "bool"},
        ],
        "name": "recordLog",
        "outputs": [{"internalType": "uint256", "name": "logId", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "logHash", "type": "bytes32"}],
        "name": "verifyLogHash",
        "outputs": [
            {"internalType": "bool",    "name": "exists",       "type": "bool"},
            {"internalType": "uint256", "name": "logId",        "type": "uint256"},
            {"internalType": "string",  "name": "userId",       "type": "string"},
            {"internalType": "string",  "name": "eventType",    "type": "string"},
            {"internalType": "uint8",   "name": "anomalyScore", "type": "uint8"},
            {"internalType": "bool",    "name": "isAnomaly",    "type": "bool"},
            {"internalType": "uint256", "name": "timestamp",    "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "logCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


@dataclass
class AuditRecord:
    event_id: str
    log_hash: str
    user_id: str
    event_type: str
    anomaly_score: int
    is_anomaly: bool
    on_chain_tx: Optional[str] = None
    on_chain_id: Optional[int] = None
    audit_status: str = "pending"  # pending | recorded | demo
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AuditAgent:
    """Stage 3: Hashes login access records and pushes them to AccessAuditLog.sol."""

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        contract_address: Optional[str] = None,
        private_key: Optional[str] = None,
    ):
        self.rpc_url = rpc_url or os.getenv("MANTLE_RPC_URL", "https://rpc.sepolia.mantle.xyz")
        self.contract_address = contract_address or os.getenv("AUDIT_CONTRACT_ADDRESS", "")
        self.private_key = private_key or os.getenv("AGENT_PRIVATE_KEY", "")

        self.logger = logger.bind(agent="audit")
        self.audit_log: List[AuditRecord] = []
        self.w3 = None
        self.contract = None
        self.demo_mode = True

        if WEB3_AVAILABLE and self.contract_address and self.private_key:
            try:
                self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
                if self.w3.is_connected():
                    self.contract = self.w3.eth.contract(
                        address=Web3.to_checksum_address(self.contract_address),
                        abi=CONTRACT_ABI
                    )
                    self.demo_mode = False
                    self.logger.info("onchain_audit_configured", contract=self.contract_address)
            except Exception as err:
                self.logger.warning("web3_init_failed", error=str(err))

        if self.demo_mode:
            self.logger.info("audit_agent_demo_mode", msg="Running in local demo mode. Logs saved locally.")

    def record_access_event(self, event: Dict[str, Any], anomaly_finding: Optional[Any] = None) -> AuditRecord:
        """Hash event and submit audit record to on-chain contract or local log store."""
        user_id = str(event.get("user_id", "unknown"))
        event_type = str(event.get("event_type", "login"))
        event_id = str(event.get("event_id", f"EVT-{time.time()}"))

        anomaly_score = int((anomaly_finding.confidence * 100)) if anomaly_finding else 0
        is_anomaly = bool(anomaly_finding and anomaly_finding.is_anomaly)

        # Compute SHA-256 canonical hash
        if anomaly_finding and hasattr(anomaly_finding, "sha256_hash"):
            log_hash = anomaly_finding.sha256_hash()
        else:
            core = {
                "event_id": event_id,
                "event_type": event_type,
                "timestamp": event.get("timestamp", ""),
                "user_id": user_id,
            }
            canonical = json.dumps(core, sort_keys=True, separators=(",", ":"))
            log_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        record = AuditRecord(
            event_id=event_id,
            log_hash=log_hash,
            user_id=user_id,
            event_type=event_type,
            anomaly_score=anomaly_score,
            is_anomaly=is_anomaly,
            audit_status="demo" if self.demo_mode else "pending"
        )

        if not self.demo_mode and self.contract and self.w3:
            try:
                account = self.w3.eth.account.from_key(self.private_key)
                bytes32_hash = bytes.fromhex(log_hash)
                
                tx = self.contract.functions.recordLog(
                    bytes32_hash, user_id, event_type, anomaly_score, is_anomaly
                ).build_transaction({
                    "from": account.address,
                    "nonce": self.w3.eth.get_transaction_count(account.address),
                    "gas": 200000,
                    "gasPrice": self.w3.eth.gas_price,
                })
                
                signed = self.w3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

                record.on_chain_tx = tx_hash.hex()
                record.audit_status = "recorded"
                self.logger.info("audit_recorded_onchain", tx_hash=tx_hash.hex(), event_id=event_id)
            except Exception as err:
                record.audit_status = "failed"
                self.logger.warning("onchain_record_failed", error=str(err), event_id=event_id)

        self.audit_log.append(record)
        return record

    def save_audit_log(self, filepath: str = "data/audit_events.jsonl"):
        """Persist audit records to disk."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "a", encoding="utf-8") as f:
            for rec in self.audit_log:
                f.write(json.dumps(rec.to_dict()) + "\n")
        self.audit_log.clear()
