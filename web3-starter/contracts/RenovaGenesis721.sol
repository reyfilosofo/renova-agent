// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/// @title RenovaGenesis721
/// @notice ERC-721 base para la colección fundacional ℛenova Genesis 314.
/// @dev Starter educativo. Auditar antes de usar con valor económico real.
contract RenovaGenesis721 is ERC721URIStorage, Ownable {
    uint256 public constant MAX_SUPPLY = 314;
    uint256 public nextTokenId = 1;
    string public contractURI;

    event RenovaMinted(address indexed to, uint256 indexed tokenId, string tokenURI_);
    event ContractURIUpdated(string newContractURI);

    constructor(
        address initialOwner,
        string memory initialContractURI
    ) ERC721("Renova Genesis 314", "RENOVA314") Ownable(initialOwner) {
        contractURI = initialContractURI;
    }

    function mint(address to, string calldata tokenURI_) external onlyOwner returns (uint256) {
        require(nextTokenId <= MAX_SUPPLY, "RENOVA: max supply reached");
        require(to != address(0), "RENOVA: zero address");

        uint256 tokenId = nextTokenId;
        nextTokenId += 1;

        _safeMint(to, tokenId);
        _setTokenURI(tokenId, tokenURI_);

        emit RenovaMinted(to, tokenId, tokenURI_);
        return tokenId;
    }

    function setContractURI(string calldata newContractURI) external onlyOwner {
        contractURI = newContractURI;
        emit ContractURIUpdated(newContractURI);
    }

    function totalMinted() external view returns (uint256) {
        return nextTokenId - 1;
    }
}
