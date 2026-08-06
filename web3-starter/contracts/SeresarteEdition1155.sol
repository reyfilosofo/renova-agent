// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/// @title SeresarteEdition1155
/// @notice ERC-1155 para ediciones múltiples: DAO IAO 81, libros, láminas, certificados y colecciones culturales.
/// @dev Starter educativo. Auditar antes de usar en producción.
contract SeresarteEdition1155 is ERC1155, Ownable {
    struct Edition {
        string name;
        uint256 maxSupply;
        uint256 minted;
        bool active;
    }

    mapping(uint256 => Edition) public editions;
    string public name;
    string public symbol;
    string public contractURI;

    event EditionCreated(uint256 indexed id, string name, uint256 maxSupply);
    event EditionMinted(address indexed to, uint256 indexed id, uint256 amount);
    event EditionStatusUpdated(uint256 indexed id, bool active);
    event ContractURIUpdated(string newContractURI);

    constructor(
        address initialOwner,
        string memory baseURI,
        string memory initialContractURI
    ) ERC1155(baseURI) Ownable(initialOwner) {
        name = "SERESARTE Cultural Editions";
        symbol = "SERESARTE1155";
        contractURI = initialContractURI;
    }

    function createEdition(uint256 id, string calldata editionName, uint256 maxSupply) external onlyOwner {
        require(id != 0, "SERESARTE: id zero reserved");
        require(bytes(editionName).length > 0, "SERESARTE: edition name required");
        require(maxSupply > 0, "SERESARTE: max supply required");
        require(bytes(editions[id].name).length == 0, "SERESARTE: edition exists");

        editions[id] = Edition({
            name: editionName,
            maxSupply: maxSupply,
            minted: 0,
            active: true
        });

        emit EditionCreated(id, editionName, maxSupply);
    }

    function mint(address to, uint256 id, uint256 amount, bytes calldata data) external onlyOwner {
        Edition storage edition = editions[id];
        require(edition.active, "SERESARTE: inactive edition");
        require(amount > 0, "SERESARTE: amount required");
        require(edition.minted + amount <= edition.maxSupply, "SERESARTE: edition sold out");
        require(to != address(0), "SERESARTE: zero address");

        edition.minted += amount;
        _mint(to, id, amount, data);
        emit EditionMinted(to, id, amount);
    }

    function setEditionActive(uint256 id, bool active) external onlyOwner {
        require(bytes(editions[id].name).length != 0, "SERESARTE: edition missing");
        editions[id].active = active;
        emit EditionStatusUpdated(id, active);
    }

    function setURI(string calldata newURI) external onlyOwner {
        _setURI(newURI);
    }

    function setContractURI(string calldata newContractURI) external onlyOwner {
        contractURI = newContractURI;
        emit ContractURIUpdated(newContractURI);
    }
}
