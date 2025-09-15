# 🎁 Blockchain Airdrop System

A complete, production-ready blockchain airdrop system with Merkle proof verification, built with Solidity, Node.js, and modern web technologies.

## 🌟 Features

- **Smart Contract**: Secure Merkle tree-based airdrop contract with OpenZeppelin integration
- **Proof Server**: Express.js server for generating and serving Merkle proofs
- **Web Client**: Modern frontend with MetaMask integration for claiming tokens
- **Relayer Service**: EIP-712 signature verification and transaction relaying
- **Comprehensive Testing**: Full test suite with Hardhat and Chai
- **Multi-Network Support**: Deploy to any EVM-compatible blockchain

## 📁 Project Structure

```
airdrop-project/
├─ contract/                 # Smart contract and deployment
│  ├─ contracts/Airdrop.sol  # Main airdrop contract
│  ├─ test/airdrop.test.js   # Comprehensive test suite
│  ├─ scripts/deploy.js      # Deployment script
│  ├─ hardhat.config.js      # Hardhat configuration
│  └─ package.json           # Contract dependencies
├─ server/                   # Merkle proof server
│  ├─ index.js              # Express server with proof generation
│  ├─ whitelist.json        # Eligible addresses and amounts
│  └─ package.json          # Server dependencies
├─ client/                   # Frontend application
│  └─ index.html            # Web interface with MetaMask integration
├─ relayer/                  # Transaction relayer service
│  ├─ relayer.js            # EIP-712 signature verification
│  └─ package.json          # Relayer dependencies
├─ .env.example             # Environment variables template
├─ package.json             # Root package with scripts
└─ README.md                # This file
```

## 🚀 Quick Start

### Prerequisites

- Node.js >= 16.0.0
- npm >= 8.0.0
- MetaMask browser extension
- Git

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd airdrop-project

# Install all dependencies
npm run setup
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
# At minimum, set:
# - RPC_URL (your blockchain RPC endpoint)
# - RELAYER_PRIVATE_KEY (for relayer service)
# - CONTRACT_ADDRESS (after deployment)
```

### 3. Local Development

```bash
# Start local Hardhat node
npm run start:node

# In another terminal, deploy contract
npm run deploy:local

# Start proof server and relayer
npm run start:all

# Open client/index.html in your browser
```

## 📋 Detailed Setup Guide

### Smart Contract Deployment

1. **Configure Hardhat Network**
   ```javascript
   // In contract/hardhat.config.js
   networks: {
     sepolia: {
       url: process.env.SEPOLIA_URL,
       accounts: [process.env.DEPLOYER_PRIVATE_KEY]
     }
   }
   ```

2. **Update Whitelist**
   ```json
   // In server/whitelist.json
   [
     {
       "address": "0x742d35Cc6634C0532925a3b8D4C9db96c4b4Db44",
       "amount": "100"
     }
   ]
   ```

3. **Deploy Contract**
   ```bash
   cd contract
   npm run deploy:sepolia  # or deploy:local for testing
   ```

4. **Update Configuration**
   ```bash
   # Copy contract address from deployment output to .env
   CONTRACT_ADDRESS=0x...
   ```

### Server Configuration

1. **Proof Server**
   ```bash
   cd server
   npm install
   npm start  # Runs on port 3001
   ```

2. **Relayer Service** (Optional)
   ```bash
   cd relayer
   npm install
   npm start  # Runs on port 3002
   ```

### Client Setup

1. Open `client/index.html` in a web browser
2. Configure the proof server URL and contract address
3. Connect MetaMask wallet
4. Check eligibility and claim tokens

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `RPC_URL` | Blockchain RPC endpoint | Yes |
| `CONTRACT_ADDRESS` | Deployed contract address | Yes |
| `RELAYER_PRIVATE_KEY` | Private key for relayer | For relayer |
| `PROOF_SERVER_URL` | Proof server endpoint | Yes |
| `CHAIN_ID` | Blockchain chain ID | Yes |

### Network Configuration

Supported networks:
- **Local**: Hardhat node (Chain ID: 1337)
- **Sepolia**: Ethereum testnet
- **Mainnet**: Ethereum mainnet
- **Polygon**: Polygon network
- **BSC**: Binance Smart Chain

## 🧪 Testing

### Smart Contract Tests

```bash
cd contract
npm test
```

Test coverage includes:
- Merkle proof verification
- Claim functionality
- Double-claim prevention
- Owner functions
- Edge cases and error handling

### Manual Testing

1. **Local Testing**
   ```bash
   # Start local node
   npm run start:node
   
   # Deploy contract
   npm run deploy:local
   
   # Test proof generation
   curl http://localhost:3001/proof/0x70997970C51812dc3A010C7d01b50e0d17dc79C8/100
   ```

2. **Frontend Testing**
   - Connect MetaMask to local network (http://localhost:8545)
   - Import test accounts from Hardhat
   - Test claim flow through web interface

## 📚 API Documentation

### Proof Server Endpoints

- `GET /root` - Get Merkle root
- `GET /proof/:address/:amount` - Get proof for address/amount
- `GET /whitelist` - Get public whitelist
- `GET /verify/:address/:amount` - Verify eligibility
- `GET /health` - Health check

### Relayer Endpoints

- `POST /relay-claim` - Relay claim transaction
- `GET /tx-status/:hash` - Check transaction status
- `GET /info` - Get relayer information
- `POST /generate-signature` - Generate EIP-712 signature (testing)

## 🔐 Security Considerations

### Smart Contract Security

- ✅ Uses OpenZeppelin's audited contracts
- ✅ Merkle proof verification prevents unauthorized claims
- ✅ Double-claim prevention with mapping
- ✅ Owner-only functions for administrative tasks
- ✅ No direct token transfers (emit events for external handling)

### Server Security

- ✅ CORS configuration
- ✅ Input validation
- ✅ Rate limiting (recommended for production)
- ✅ Environment variable protection
- ⚠️ Add authentication for production use

### Relayer Security

- ✅ EIP-712 signature verification
- ✅ Nonce tracking to prevent replay attacks
- ✅ Deadline validation
- ✅ Proof verification before relaying
- ⚠️ Monitor relayer balance and gas usage

## 🚀 Production Deployment

### 1. Smart Contract

```bash
# Deploy to mainnet
CONTRACT_DEPLOYER_PRIVATE_KEY=0x... npm run deploy:mainnet

# Verify on Etherscan
ETHERSCAN_API_KEY=your_key npm run verify
```

### 2. Server Infrastructure

```bash
# Use PM2 for production
npm install -g pm2

# Start proof server
cd server
pm2 start index.js --name "airdrop-proof-server"

# Start relayer
cd ../relayer
pm2 start relayer.js --name "airdrop-relayer"
```

### 3. Frontend Deployment

- Deploy `client/index.html` to CDN or web server
- Update contract address and server URLs
- Configure HTTPS for production

### 4. Monitoring

- Monitor contract events
- Track server uptime and performance
- Monitor relayer balance and transaction status
- Set up alerts for failures

## 🛠️ Development Scripts

```bash
# Root level scripts
npm run setup           # Install all dependencies and compile
npm run install-all     # Install dependencies for all modules
npm run compile         # Compile smart contracts
npm test               # Run smart contract tests
npm run start:all      # Start server and relayer
npm run dev:all        # Start in development mode

# Contract specific
npm run deploy:local   # Deploy to local Hardhat node
npm run deploy:sepolia # Deploy to Sepolia testnet
npm run start:node     # Start local Hardhat node

# Server specific
npm run start:server   # Start proof server
npm run dev:server     # Start server in development mode

# Relayer specific
npm run start:relayer  # Start relayer service
npm run dev:relayer    # Start relayer in development mode
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Troubleshooting

### Common Issues

1. **"Invalid proof" error**
   - Ensure whitelist.json is properly formatted
   - Verify address case sensitivity
   - Check amount matches exactly

2. **MetaMask connection issues**
   - Ensure correct network is selected
   - Check contract address configuration
   - Verify sufficient gas balance

3. **Server connection errors**
   - Verify server is running on correct port
   - Check CORS configuration
   - Ensure firewall allows connections

4. **Deployment failures**
   - Check private key format
   - Verify sufficient balance for gas
   - Ensure RPC URL is correct

### Getting Help

- Check the [Issues](https://github.com/yourusername/airdrop-project/issues) page
- Review the test files for usage examples
- Consult the [Hardhat documentation](https://hardhat.org/docs)
- Check [OpenZeppelin documentation](https://docs.openzeppelin.com/)

## 🎯 Roadmap

- [ ] Add ERC20 token integration
- [ ] Implement batch claiming
- [ ] Add admin dashboard
- [ ] Create mobile app
- [ ] Add multi-signature support
- [ ] Implement vesting schedules
- [ ] Add analytics and reporting

---

**Built with ❤️ for the blockchain community**