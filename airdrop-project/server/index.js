require('dotenv').config();
const express = require('express');
const { MerkleTree } = require('merkletreejs');
const keccak256 = require('keccak256');
const fs = require('fs');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

const whitelist = JSON.parse(fs.readFileSync(__dirname + '/whitelist.json', 'utf8'));
// whitelist: [{ "address": "0x...", "amount": "100" }, ...]

function encodeLeaf(addr, amount) {
  // same encoding as contract: abi.encodePacked(address, uint256) then keccak256
  // We'll construct the packed buffer: address (20 bytes) + uint256 (32 bytes big-endian)
  const addrBuf = Buffer.from(addr.replace(/^0x/, '').padStart(40, '0'), 'hex');
  const bn = BigInt(amount);
  const amountHex = bn.toString(16).padStart(64, '0');
  const amountBuf = Buffer.from(amountHex, 'hex');
  return Buffer.concat([addrBuf, amountBuf]);
}

const leaves = whitelist.map(e => keccak256(encodeLeaf(e.address.toLowerCase(), e.amount)));
const tree = new MerkleTree(leaves, keccak256, { sortPairs: true });
const root = tree.getHexRoot();
console.log('Merkle root:', root);

app.get('/root', (req, res) => res.json({ root }));

app.get('/proof/:address/:amount', (req, res) => {
  const addr = req.params.address.toLowerCase();
  const amount = req.params.amount;
  
  // Find the entry in whitelist
  const entry = whitelist.find(e => e.address.toLowerCase() === addr && e.amount === amount);
  
  if (!entry) {
    return res.status(404).json({ error: 'Address not found in whitelist or amount mismatch' });
  }
  
  // Generate proof
  const leaf = keccak256(encodeLeaf(addr, amount));
  const proof = tree.getHexProof(leaf);
  
  res.json({
    address: addr,
    amount: amount,
    proof: proof,
    leaf: '0x' + leaf.toString('hex'),
    root: root
  });
});

app.get('/whitelist', (req, res) => {
  // Return only addresses and amounts, no proofs for security
  const publicWhitelist = whitelist.map(e => ({
    address: e.address,
    amount: e.amount
  }));
  res.json(publicWhitelist);
});

app.get('/verify/:address/:amount', (req, res) => {
  const addr = req.params.address.toLowerCase();
  const amount = req.params.amount;
  
  const entry = whitelist.find(e => e.address.toLowerCase() === addr && e.amount === amount);
  
  res.json({
    eligible: !!entry,
    address: addr,
    amount: entry ? entry.amount : null
  });
});

app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    whitelistCount: whitelist.length,
    merkleRoot: root
  });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`Merkle proof server running on port ${PORT}`);
  console.log(`Whitelist contains ${whitelist.length} entries`);
  console.log('Available endpoints:');
  console.log('  GET /root - Get Merkle root');
  console.log('  GET /proof/:address/:amount - Get proof for address/amount');
  console.log('  GET /whitelist - Get public whitelist');
  console.log('  GET /verify/:address/:amount - Verify eligibility');
  console.log('  GET /health - Health check');
});