const { expect } = require("chai");
const { ethers } = require("hardhat");
const { MerkleTree } = require('merkletreejs');
const keccak256 = require('keccak256');

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

describe("Airdrop Merkle", function () {
  let airdrop;
  let owner, addr1, addr2, addr3;
  let whitelist;
  let tree;
  let root;

  beforeEach(async function () {
    [owner, addr1, addr2, addr3] = await ethers.getSigners();

    whitelist = [
      { address: addr1.address, amount: 100 },
      { address: addr2.address, amount: 50 },
      { address: addr3.address, amount: 200 }
    ];

    // Create Merkle tree
    const leaves = makeLeaves(whitelist);
    tree = new MerkleTree(leaves, keccak256, { sortPairs: true });
    root = tree.getHexRoot();

    // Deploy contract
    const Airdrop = await ethers.getContractFactory("Airdrop");
    airdrop = await Airdrop.deploy(root);
    await airdrop.deployed();
  });

  describe("Deployment", function () {
    it("Should set the correct merkle root", async function () {
      expect(await airdrop.merkleRoot()).to.equal(root);
    });

    it("Should set the correct owner", async function () {
      expect(await airdrop.owner()).to.equal(owner.address);
    });
  });

  describe("Claiming", function () {
    it("Should allow valid claim with correct proof", async function () {
      const claimAmount = 100;
      const leaf = keccak256(encodeLeaf(addr1.address, claimAmount));
      const proof = tree.getHexProof(leaf);

      await expect(airdrop.connect(addr1).claim(claimAmount, proof))
        .to.emit(airdrop, "Claimed")
        .withArgs(addr1.address, claimAmount);

      expect(await airdrop.claimed(addr1.address)).to.be.true;
    });

    it("Should reject invalid proof", async function () {
      const claimAmount = 100;
      const wrongLeaf = keccak256(encodeLeaf(addr2.address, claimAmount));
      const wrongProof = tree.getHexProof(wrongLeaf);

      await expect(
        airdrop.connect(addr1).claim(claimAmount, wrongProof)
      ).to.be.revertedWith("Invalid proof");
    });

    it("Should reject wrong amount", async function () {
      const wrongAmount = 999;
      const leaf = keccak256(encodeLeaf(addr1.address, wrongAmount));
      const proof = tree.getHexProof(leaf);

      await expect(
        airdrop.connect(addr1).claim(wrongAmount, proof)
      ).to.be.revertedWith("Invalid proof");
    });

    it("Should prevent double claiming", async function () {
      const claimAmount = 100;
      const leaf = keccak256(encodeLeaf(addr1.address, claimAmount));
      const proof = tree.getHexProof(leaf);

      // First claim should succeed
      await airdrop.connect(addr1).claim(claimAmount, proof);

      // Second claim should fail
      await expect(
        airdrop.connect(addr1).claim(claimAmount, proof)
      ).to.be.revertedWith("Already claimed");
    });

    it("Should allow multiple different users to claim", async function () {
      // addr1 claims 100
      const leaf1 = keccak256(encodeLeaf(addr1.address, 100));
      const proof1 = tree.getHexProof(leaf1);
      await airdrop.connect(addr1).claim(100, proof1);

      // addr2 claims 50
      const leaf2 = keccak256(encodeLeaf(addr2.address, 50));
      const proof2 = tree.getHexProof(leaf2);
      await airdrop.connect(addr2).claim(50, proof2);

      expect(await airdrop.claimed(addr1.address)).to.be.true;
      expect(await airdrop.claimed(addr2.address)).to.be.true;
      expect(await airdrop.claimed(addr3.address)).to.be.false;
    });
  });

  describe("Owner functions", function () {
    it("Should allow owner to update merkle root", async function () {
      const newWhitelist = [
        { address: addr1.address, amount: 300 },
        { address: addr2.address, amount: 150 }
      ];
      
      const newLeaves = makeLeaves(newWhitelist);
      const newTree = new MerkleTree(newLeaves, keccak256, { sortPairs: true });
      const newRoot = newTree.getHexRoot();

      await airdrop.setMerkleRoot(newRoot);
      expect(await airdrop.merkleRoot()).to.equal(newRoot);
    });

    it("Should reject non-owner trying to update merkle root", async function () {
      const newRoot = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("new root"));
      
      await expect(
        airdrop.connect(addr1).setMerkleRoot(newRoot)
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });
});