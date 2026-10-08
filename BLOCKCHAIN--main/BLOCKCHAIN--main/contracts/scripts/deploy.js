/**
 * AccessAuditLog — Deploy Script
 * Deploys AccessAuditLog to Mantle testnet OR mainnet.
 */

const hre = require("hardhat");
const fs  = require("fs");
const path = require("path");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const networkName = hre.network.name;

  console.log("════════════════════════════════════════════════════");
  console.log("  AccessAuditLog — Deploy Contract");
  console.log("════════════════════════════════════════════════════");
  console.log(`Network:   ${networkName}`);
  console.log(`Deployer:  ${deployer.address}`);

  const balance = await hre.ethers.provider.getBalance(deployer.address);
  const balEth  = hre.ethers.formatEther(balance);
  console.log(`Balance:   ${balEth} MNT`);

  if (parseFloat(balEth) < 0.001) {
    console.error("\n❌ INSUFFICIENT BALANCE for deployment.");
    process.exit(1);
  }

  const AccessAuditLog = await hre.ethers.getContractFactory("AccessAuditLog");
  console.log("\nDeploying AccessAuditLog...");

  const contract = await AccessAuditLog.deploy();
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log(`\n✅ AccessAuditLog deployed to: ${address}`);

  const deploymentData = {
    network: networkName,
    address: address,
    deployer: deployer.address,
    timestamp: new Date().toISOString()
  };

  fs.writeFileSync(
    path.join(__dirname, "../deployment.json"),
    JSON.stringify(deploymentData, null, 2)
  );

  console.log("Updated deployment.json");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
