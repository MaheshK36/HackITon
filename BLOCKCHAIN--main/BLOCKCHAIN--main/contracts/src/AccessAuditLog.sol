// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AccessAuditLog
 * @notice On-chain audit log for Software Platform Login/Logout events & anomaly findings.
 *         Every login/logout access event is hashed (SHA-256 off-chain) and recorded here,
 *         providing an immutable, tamper-evident audit trail on-chain.
 */
import "@openzeppelin/contracts/access/Ownable.sol";

contract AccessAuditLog is Ownable {

    // ── Events ──────────────────────────────────────────────────────────────

    event LogRecordRecorded(
        uint256 indexed logId,
        bytes32 indexed logHash,
        string  userId,
        string  eventType,      // "login" | "logout" | "failed_login"
        uint8   anomalyScore,   // 0-100 anomaly confidence score
        bool    isAnomaly,
        address indexed recorder,
        uint256 timestamp
    );

    event RecorderRegistered(address indexed recorder, string recorderName);

    // ── Storage ─────────────────────────────────────────────────────────────

    struct LogRecord {
        bytes32 logHash;        // SHA256 hash of canonical log record JSON
        string  userId;         // Platform user ID (or hash)
        string  eventType;      // "login", "logout", "failed_login"
        uint8   anomalyScore;   // 0-100
        bool    isAnomaly;
        address recorder;       // Auditor agent wallet
        uint256 timestamp;
        bool    exists;
    }

    mapping(uint256 => LogRecord) public logs;
    mapping(bytes32 => uint256)   public hashToLogId;      // reverse lookup
    mapping(address => bool)      public authorizedRecorders;
    mapping(string => uint256[])  private _logsByEventType; // eventType → log IDs

    uint256 public logCount;
    uint256 public anomalyCount;
    uint256[] private _allLogIds;

    // ── Constructor ──────────────────────────────────────────────────────────

    constructor() Ownable(msg.sender) {
        authorizedRecorders[msg.sender] = true;
    }

    // ── Modifiers ────────────────────────────────────────────────────────────

    modifier onlyAuthorized() {
        require(authorizedRecorders[msg.sender], "Not authorized recorder");
        _;
    }

    // ── Recorder Management ──────────────────────────────────────────────────

    function authorizeRecorder(address recorder, string calldata recorderName) external onlyOwner {
        authorizedRecorders[recorder] = true;
        emit RecorderRegistered(recorder, recorderName);
    }

    function revokeRecorder(address recorder) external onlyOwner {
        authorizedRecorders[recorder] = false;
    }

    // ── Core Audit Logging Function ─────────────────────────────────────────

    /**
     * @notice Record a new login/logout access audit record on-chain.
     * @param logHash SHA256 of canonical log record JSON
     * @param userId User identifier
     * @param eventType "login", "logout", or "failed_login"
     * @param anomalyScore 0-100 anomaly confidence score
     * @param isAnomaly True if flagged as an anomaly by detector
     */
    function recordLog(
        bytes32 logHash,
        string  calldata userId,
        string  calldata eventType,
        uint8   anomalyScore,
        bool    isAnomaly
    ) external onlyAuthorized returns (uint256 logId) {
        require(hashToLogId[logHash] == 0, "Log record already recorded");
        require(bytes(userId).length > 0, "Empty user ID");
        require(bytes(eventType).length > 0, "Empty event type");

        logCount++;
        logId = logCount;
        if (isAnomaly) {
            anomalyCount++;
        }

        logs[logId] = LogRecord({
            logHash:      logHash,
            userId:       userId,
            eventType:    eventType,
            anomalyScore: anomalyScore,
            isAnomaly:    isAnomaly,
            recorder:     msg.sender,
            timestamp:    block.timestamp,
            exists:       true
        });

        hashToLogId[logHash] = logId;
        _allLogIds.push(logId);
        _logsByEventType[eventType].push(logId);

        emit LogRecordRecorded(
            logId,
            logHash,
            userId,
            eventType,
            anomalyScore,
            isAnomaly,
            msg.sender,
            block.timestamp
        );
    }

    // ── Public Verification & Queries ────────────────────────────────────────

    /**
     * @notice Verify whether a specific log hash exists on-chain.
     */
    function verifyLogHash(bytes32 logHash)
        external
        view
        returns (
            bool exists,
            uint256 logId,
            string memory userId,
            string memory eventType,
            uint8 anomalyScore,
            bool isAnomaly,
            uint256 timestamp
        )
    {
        logId = hashToLogId[logHash];
        if (logId == 0) {
            return (false, 0, "", "", 0, false, 0);
        }
        LogRecord memory r = logs[logId];
        return (true, logId, r.userId, r.eventType, r.anomalyScore, r.isAnomaly, r.timestamp);
    }

    /**
     * @notice Paginated public query for audit logs.
     */
    function getPublicLogs(uint256 offset, uint256 limit)
        external
        view
        returns (uint256[] memory logIds, uint256 total)
    {
        total = _allLogIds.length;
        if (offset >= total) {
            return (new uint256[](0), total);
        }
        uint256 end = offset + limit;
        if (end > total) {
            end = total;
        }
        uint256 size = end - offset;
        logIds = new uint256[](size);
        for (uint256 i = 0; i < size; i++) {
            logIds[i] = _allLogIds[offset + i];
        }
    }

    /**
     * @notice Summary statistics for audit trail.
     */
    function getStats()
        external
        view
        returns (
            uint256 totalLogs,
            uint256 totalAnomalies,
            bool callerAuthorized
        )
    {
        return (logCount, anomalyCount, authorizedRecorders[msg.sender]);
    }
}
