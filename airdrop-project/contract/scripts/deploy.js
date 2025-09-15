const { ethers } = require("hardhat");
const { MerkleTree } = require('merkletreejs');
const keccak256 = require('keccak256');
const fs = require('fs');
const path = require('path');

function encodeLeaf(address, amount) {
  // Match contract's abi.encodePacked(address, uint256)
  const addressBytes = ethers.utils.arrayify(address);
  const amountBytes = ethers.utils.zeroPad(ethers.BigNumber.from(amount).toHexString(), 32);
  return ethers.utils.concat([addressBytes, amountBytes]);
}

function makeLeaves(whitelist) {
  return whitelist.map(entry => {
    const packed = encodeLeaf(entry.address, entry.amount);
    return keccak256(packed);
  });
}

async function main() {
  console.log("Starting Airdrop contract deployment...");
  
  // Get deployer account
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);
  
  // Check balance
  const balance = await deployer.getBalance();
  console.log("Account balance:", ethers.utils.formatEther(balance), "ETH");
  
  // Load whitelist
  const whitelistPath = path.join(__dirname, '../../server/whitelist.json');
  let whitelist;
  
  try {
    whitelist = JSON.parse(fs.readFileSync(whitelistPath, 'utf8'));
    console.log(`Loaded whitelist with ${whitelist.length} entries`);
  } catch (error) {
    console.error("Error loading whitelist:", error.message);
    console.log("Using default whitelist for deployment...");
    
    // Default whitelist for testing
    whitelist = [
      { address: "0x70997970C51812dc3A010C7d01b50e0d17dc79C8", amount: "100" },
      { address: "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC", amount: "50" },
      { address: "0x90F79bf6EB2c4f870365E785982E1f101E93b906", amount: "200" }
    ];
  }
  
  // Generate Merkle tree
  console.log("Generating Merkle tree...");
  const leaves = makeLeaves(whitelist);
  const tree = new MerkleTree(leaves, keccak256, { sortPairs: true });
  const root = tree.getHexRoot();
  
  console.log("Merkle root:", root);
  
  // Deploy contract
  console.log("Deploying Airdrop contract...");
  const Airdrop = await ethers.getContractFactory("Airdrop");
  const airdrop = await Airdrop.deploy(root);
  
  await airdrop.deployed();
  
  console.log("\n=== Deployment Successful ===");
  console.log("Airdrop contract deployed to:", airdrop.address);
  console.log("Merkle root:", root);
  console.log("Transaction hash:", airdrop.deployTransaction.hash);
  console.log("Deployer address:", deployer.address);
  console.log("Network:", (await ethers.provider.getNetwork()).name);
  
  // Save deployment info
  const deploymentInfo = {
    contractAddress: airdrop.address,
    merkleRoot: root,
    deploymentTx: airdrop.deployTransaction.hash,
    deployer: deployer.address,
    network: (await ethers.provider.getNetwork()).name,
    chainId: (await ethers.provider.getNetwork()).chainId,
    timestamp: new Date().toISOString(),
    whitelistCount: whitelist.length
  };
  
  const deploymentPath = path.join(__dirname, '../deployment.json');
  fs.writeFileSync(deploymentPath, JSON.stringify(deploymentInfo, null, 2));
  console.log("Deployment info saved to:", deploymentPath);
  
  // Verify contract (optional)
  if (process.env.ETHERSCAN_API_KEY && (await ethers.provider.getNetwork()).chainId !== 1337) {
    console.log("\nWaiting for block confirmations...");
    await airdrop.deployTransaction.wait(6);
    
    console.log("Verifying contract on Etherscan...");
    try {
      await hre.run("verify:verify", {
        address: airdrop.address,
        constructorArguments: [root],
      });
      console.log("Contract verified successfully!");
    } catch (error) {
      console.log("Verification failed:", error.message);
    }
  }
  
  console.log("\n=== Next Steps ===");
  console.log("1. Update .env file with contract address:");
  console.log(`   CONTRACT_ADDRESS=${airdrop.address}`);
  console.log("2. Start the proof server:");
  console.log(`   cd server && npm install && npm start`);
  console.log("3. Start the relayer (if using):");
  console.log(`   cd relayer && npm install && npm start`);
  console.log("4. Open client/index.html and configure contract address");
  
  return {
    contract: airdrop,
    merkleRoot: root,
    whitelist: whitelist
  };
}

// Execute deployment
if (require.main === module) {
  main()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error("Deployment failed:", error);
      process.exit(1);
    });
}

module.exports = { main, encodeLeaf, makeLeaves };