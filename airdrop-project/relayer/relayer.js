require('dotenv').config();
const express = require('express');
const { ethers } = require('ethers');
const cors = require('cors');
const axios = require('axios');

const app = express();
app.use(cors());
app.use(express.json());

// EIP-712 Domain
const DOMAIN = {
    name: 'AirdropRelayer',
    version: '1',
    chainId: process.env.CHAIN_ID || 1337,
    verifyingContract: process.env.RELAYER_ADDRESS || '0x0000000000000000000000000000000000000000'
};

// EIP-712 Types
const TYPES = {
    ClaimRequest: [
        { name: 'recipient', type: 'address' },
        { name: 'amount', type: 'uint256' },
        { name: 'nonce', type: 'uint256' },
        { name: 'deadline', type: 'uint256' }
    ]
};

// Contract ABI
const CONTRACT_ABI = [
    'function claim(uint256 amount, bytes32[] calldata proof) external',
    'function claimed(address) external view returns (bool)',
    'function merkleRoot() external view returns (bytes32)',
    'event Claimed(address indexed account, uint256 amount)'
];

// Initialize provider and wallet
let provider, wallet, contract;
const usedNonces = new Set();
const pendingTxs = new Map();

function initializeProvider() {
    try {
        const rpcUrl = process.env.RPC_URL || 'http://127.0.0.1:8545';
        const privateKey = process.env.RELAYER_PRIVATE_KEY;
        const contractAddress = process.env.CONTRACT_ADDRESS;
        
        if (!privateKey) {
            throw new Error('RELAYER_PRIVATE_KEY not set in environment');
        }
        
        if (!contractAddress) {
            throw new Error('CONTRACT_ADDRESS not set in environment');
        }
        
        provider = new ethers.providers.JsonRpcProvider(rpcUrl);
        wallet = new ethers.Wallet(privateKey, provider);
        contract = new ethers.Contract(contractAddress, CONTRACT_ABI, wallet);
        
        console.log('Relayer initialized:');
        console.log('- Wallet address:', wallet.address);
        console.log('- Contract address:', contractAddress);
        console.log('- RPC URL:', rpcUrl);
        
    } catch (error) {
        console.error('Failed to initialize provider:', error.message);
        process.exit(1);
    }
}

// Verify EIP-712 signature
function verifySignature(message, signature, expectedSigner) {
    try {
        const digest = ethers.utils._TypedDataEncoder.hash(DOMAIN, TYPES, message);
        const recoveredAddress = ethers.utils.recoverAddress(digest, signature);
        return recoveredAddress.toLowerCase() === expectedSigner.toLowerCase();
    } catch (error) {
        console.error('Signature verification error:', error);
        return false;
    }
}

// Get proof from proof server
async function getProofFromServer(address, amount) {
    try {
        const proofServerUrl = process.env.PROOF_SERVER_URL || 'http://localhost:3001';
        const response = await axios.get(`${proofServerUrl}/proof/${address}/${amount}`);
        return response.data;
    } catch (error) {
        console.error('Error fetching proof:', error.message);
        throw new Error('Failed to fetch proof from server');
    }
}

// Relay claim transaction
app.post('/relay-claim', async (req, res) => {
    try {
        const { recipient, amount, nonce, deadline, signature } = req.body;
        
        // Validate required fields
        if (!recipient || !amount || !nonce || !deadline || !signature) {
            return res.status(400).json({ 
                error: 'Missing required fields: recipient, amount, nonce, deadline, signature' 
            });
        }
        
        // Check deadline
        const currentTime = Math.floor(Date.now() / 1000);
        if (currentTime > deadline) {
            return res.status(400).json({ error: 'Request expired' });
        }
        
        // Check nonce
        if (usedNonces.has(nonce)) {
            return res.status(400).json({ error: 'Nonce already used' });
        }
        
        // Verify signature
        const message = { recipient, amount, nonce, deadline };
        if (!verifySignature(message, signature, recipient)) {
            return res.status(400).json({ error: 'Invalid signature' });
        }
        
        // Check if already claimed
        const alreadyClaimed = await contract.claimed(recipient);
        if (alreadyClaimed) {
            return res.status(400).json({ error: 'Already claimed' });
        }
        
        // Get proof from server
        const proofData = await getProofFromServer(recipient, amount);
        if (!proofData.proof) {
            return res.status(400).json({ error: 'Invalid proof or not eligible' });
        }
        
        // Mark nonce as used
        usedNonces.add(nonce);
        
        // Submit transaction
        console.log(`Relaying claim for ${recipient}, amount: ${amount}`);
        const tx = await contract.claim(amount, proofData.proof, {
            gasLimit: 200000 // Set appropriate gas limit
        });
        
        // Store pending transaction
        pendingTxs.set(tx.hash, {
            recipient,
            amount,
            timestamp: Date.now()
        });
        
        console.log(`Transaction submitted: ${tx.hash}`);
        
        res.json({
            success: true,
            txHash: tx.hash,
            message: 'Claim transaction submitted successfully'
        });
        
        // Wait for confirmation in background
        tx.wait().then(receipt => {
            console.log(`Transaction confirmed: ${tx.hash}`);
            pendingTxs.delete(tx.hash);
        }).catch(error => {
            console.error(`Transaction failed: ${tx.hash}`, error);
            pendingTxs.delete(tx.hash);
            // Remove nonce from used set if transaction failed
            usedNonces.delete(nonce);
        });
        
    } catch (error) {
        console.error('Relay error:', error);
        
        // Remove nonce if it was added
        if (req.body.nonce) {
            usedNonces.delete(req.body.nonce);
        }
        
        res.status(500).json({ 
            error: 'Failed to relay transaction', 
            details: error.message 
        });
    }
});

// Get transaction status
app.get('/tx-status/:hash', async (req, res) => {
    try {
        const { hash } = req.params;
        
        if (pendingTxs.has(hash)) {
            return res.json({ status: 'pending', ...pendingTxs.get(hash) });
        }
        
        const receipt = await provider.getTransactionReceipt(hash);
        if (!receipt) {
            return res.json({ status: 'not_found' });
        }
        
        res.json({
            status: receipt.status === 1 ? 'confirmed' : 'failed',
            blockNumber: receipt.blockNumber,
            gasUsed: receipt.gasUsed.toString()
        });
        
    } catch (error) {
        console.error('Status check error:', error);
        res.status(500).json({ error: 'Failed to check transaction status' });
    }
});

// Get relayer info
app.get('/info', async (req, res) => {
    try {
        const balance = await provider.getBalance(wallet.address);
        const network = await provider.getNetwork();
        
        res.json({
            relayerAddress: wallet.address,
            balance: ethers.utils.formatEther(balance),
            network: network.name || `Chain ID: ${network.chainId}`,
            contractAddress: contract.address,
            pendingTransactions: pendingTxs.size,
            usedNonces: usedNonces.size
        });
    } catch (error) {
        console.error('Info error:', error);
        res.status(500).json({ error: 'Failed to get relayer info' });
    }
});

// Health check
app.get('/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        timestamp: new Date().toISOString(),
        uptime: process.uptime()
    });
});

// Generate EIP-712 signature example (for testing)
app.post('/generate-signature', async (req, res) => {
    try {
        const { recipient, amount, nonce, deadline, privateKey } = req.body;
        
        if (!recipient || !amount || !nonce || !deadline || !privateKey) {
            return res.status(400).json({ 
                error: 'Missing required fields: recipient, amount, nonce, deadline, privateKey' 
            });
        }
        
        const message = { recipient, amount, nonce, deadline };
        const signer = new ethers.Wallet(privateKey);
        
        const signature = await signer._signTypedData(DOMAIN, TYPES, message);
        
        res.json({
            message,
            signature,
            signer: signer.address,
            domain: DOMAIN,
            types: TYPES
        });
        
    } catch (error) {
        console.error('Signature generation error:', error);
        res.status(500).json({ error: 'Failed to generate signature' });
    }
});

// Initialize and start server
initializeProvider();

const PORT = process.env.PORT || 3002;
app.listen(PORT, () => {
    console.log(`Relayer service running on port ${PORT}`);
    console.log('Available endpoints:');
    console.log('  POST /relay-claim - Relay claim transaction');
    console.log('  GET /tx-status/:hash - Check transaction status');
    console.log('  GET /info - Get relayer information');
    console.log('  GET /health - Health check');
    console.log('  POST /generate-signature - Generate EIP-712 signature (testing)');
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('Shutting down relayer service...');
    process.exit(0);
});