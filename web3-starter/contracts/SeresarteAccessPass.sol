// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/// @title SeresarteAccessPass
/// @notice Credencial cultural para asistencia, membresía y acceso a eventos SERESARTE / ℛenova.
/// @dev Starter educativo. Para producción, considerar EIP-712, EAS, soulbound o firmas offchain.
contract SeresarteAccessPass is ERC721URIStorage, Ownable {
    uint256 public nextPassId = 1;
    bool public transfersEnabled = false;
    string public contractURI;

    mapping(uint256 => string) public eventCodeByPass;

    event PassIssued(address indexed to, uint256 indexed passId, string eventCode, string tokenURI_);
    event TransfersEnabledUpdated(bool enabled);
    event ContractURIUpdated(string newContractURI);

    constructor(address initialOwner, string memory initialContractURI)
        ERC721("SERESARTE Access Pass", "SERPASS")
        Ownable(initialOwner)
    {
        contractURI = initialContractURI;
    }

    function issuePass(
        address to,
        string calldata eventCode,
        string calldata tokenURI_
    ) external onlyOwner returns (uint256) {
        require(to != address(0), "SERPASS: zero address");
        require(bytes(eventCode).length > 0, "SERPASS: event code required");

        uint256 passId = nextPassId;
        nextPassId += 1;

        _safeMint(to, passId);
        _setTokenURI(passId, tokenURI_);
        eventCodeByPass[passId] = eventCode;

        emit PassIssued(to, passId, eventCode, tokenURI_);
        return passId;
    }

    function setTransfersEnabled(bool enabled) external onlyOwner {
        transfersEnabled = enabled;
        emit TransfersEnabledUpdated(enabled);
    }

    function setContractURI(string calldata newContractURI) external onlyOwner {
        contractURI = newContractURI;
        emit ContractURIUpdated(newContractURI);
    }

    function _update(address to, uint256 tokenId, address auth)
        internal
        override
        returns (address)
    {
        address from = _ownerOf(tokenId);
        if (from != address(0) && to != address(0)) {
            require(transfersEnabled, "SERPASS: non-transferable credential");
        }
        return super._update(to, tokenId, auth);
    }
}
