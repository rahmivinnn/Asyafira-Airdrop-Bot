// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract Airdrop is Ownable {
    bytes32 public merkleRoot;
    mapping(address => bool) public claimed;
    event Claimed(address indexed account, uint256 amount);

    constructor(bytes32 _root) {
        merkleRoot = _root;
    }

    function setMerkleRoot(bytes32 _root) external onlyOwner {
        merkleRoot = _root;
    }

    // claim with merkle proof. Leaves assumed keccak256(abi.encodePacked(address, uint256))
    function claim(uint256 amount, bytes32[] calldata proof) external {
        require(!claimed[msg.sender], "Already claimed");
        bytes32 leaf = keccak256(abi.encodePacked(msg.sender, amount));
        require(MerkleProof.verify(proof, merkleRoot, leaf), "Invalid proof");

        claimed[msg.sender] = true;

        // For demo purposes: contract holds ERC20 or native token sending is omitted.
        // Emit event so relayer/client can react.
        emit Claimed(msg.sender, amount);
    }
}