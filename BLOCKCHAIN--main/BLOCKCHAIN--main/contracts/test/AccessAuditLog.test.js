const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("AccessAuditLog Smart Contract", function () {
  let AccessAuditLog;
  let contract;
  let owner;
  let recorder1;
  let unauthorized;

  beforeEach(async function () {
    [owner, recorder1, unauthorized] = await ethers.getSigners();
    AccessAuditLog = await ethers.getContractFactory("AccessAuditLog");
    contract = await AccessAuditLog.deploy();
    await contract.waitForDeployment();
  });

  it("Should set deployer as owner and default authorized recorder", async function () {
    expect(await contract.owner()).to.equal(owner.address);
    expect(await contract.authorizedRecorders(owner.address)).to.equal(true);
  });

  it("Should allow owner to authorize and revoke new recorders", async function () {
    await contract.authorizeRecorder(recorder1.address, "Auditor Agent 1");
    expect(await contract.authorizedRecorders(recorder1.address)).to.equal(true);

    await contract.revokeRecorder(recorder1.address);
    expect(await contract.authorizedRecorders(recorder1.address)).to.equal(false);
  });

  it("Should record a login access log and verify hash", async function () {
    const dummyHash = ethers.keccak256(ethers.toUtf8Bytes("user_101|login|1788069600"));
    
    await expect(
      contract.recordLog(dummyHash, "user_101", "login", 95, true)
    ).to.emit(contract, "LogRecordRecorded");

    const stats = await contract.getStats();
    expect(stats.totalLogs).to.equal(1);
    expect(stats.totalAnomalies).to.equal(1);

    const verification = await contract.verifyLogHash(dummyHash);
    expect(verification.exists).to.equal(true);
    expect(verification.userId).to.equal("user_101");
    expect(verification.eventType).to.equal("login");
    expect(verification.isAnomaly).to.equal(true);
  });
});
