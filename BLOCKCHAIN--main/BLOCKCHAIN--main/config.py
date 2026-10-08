import os

# Software Platform Access Audit & Anomaly Detection Configuration
CONTRACT_ADDRESS = os.getenv("AUDIT_CONTRACT_ADDRESS", "0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b")
MANTLE_RPC       = os.getenv("MANTLE_RPC_URL", "https://rpc.sepolia.mantle.xyz")
CHAIN_ID_TESTNET = 5003

# Anomaly Thresholds
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.80"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "15"))
EVENTS_PER_CYCLE = int(os.getenv("EVENTS_PER_CYCLE", "10"))
