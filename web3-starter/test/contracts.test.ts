import { expect } from "chai";
import { network } from "hardhat";

const { ethers } = await network.create();

describe("SERESARTE / Renova contracts", function () {
  it("mints Renova Genesis tokens only through the owner", async function () {
    const [owner, collector] = await ethers.getSigners();
    const genesis = await ethers.deployContract("RenovaGenesis721", [
      owner.address,
      "ipfs://contract",
    ]);
    await genesis.waitForDeployment();

    const collectorGenesis = genesis.connect(collector) as typeof genesis;
    await expect(collectorGenesis.mint(collector.address, "ipfs://1")).to.be.revertedWithCustomError(
      genesis,
      "OwnableUnauthorizedAccount",
    );

    await expect(genesis.mint(collector.address, "ipfs://1"))
      .to.emit(genesis, "RenovaMinted")
      .withArgs(collector.address, 1n, "ipfs://1");
    expect(await genesis.ownerOf(1n)).to.equal(collector.address);
    expect(await genesis.totalMinted()).to.equal(1n);
  });

  it("keeps access passes non-transferable until the owner enables transfers", async function () {
    const [owner, attendee, recipient] = await ethers.getSigners();
    const accessPass = await ethers.deployContract("SeresarteAccessPass", [
      owner.address,
      "ipfs://contract",
    ]);
    await accessPass.waitForDeployment();
    const attendeeAccessPass = accessPass.connect(attendee) as typeof accessPass;

    await accessPass.issuePass(attendee.address, "EVENT-001", "ipfs://pass/1");
    await expect(
      attendeeAccessPass.transferFrom(attendee.address, recipient.address, 1n),
    ).to.be.revertedWith("SERPASS: non-transferable credential");

    await accessPass.setTransfersEnabled(true);
    await attendeeAccessPass.transferFrom(attendee.address, recipient.address, 1n);
    expect(await accessPass.ownerOf(1n)).to.equal(recipient.address);
  });

  it("enforces edition definitions, positive mint amounts, and supply caps", async function () {
    const [owner, collector] = await ethers.getSigners();
    const editions = await ethers.deployContract("SeresarteEdition1155", [
      owner.address,
      "ipfs://editions/{id}.json",
      "ipfs://contract",
    ]);
    await editions.waitForDeployment();

    await expect(editions.createEdition(1n, "", 2n)).to.be.revertedWith(
      "SERESARTE: edition name required",
    );
    await editions.createEdition(1n, "DAO IAO 81", 2n);
    await expect(editions.mint(collector.address, 1n, 0n, "0x")).to.be.revertedWith(
      "SERESARTE: amount required",
    );
    await editions.mint(collector.address, 1n, 2n, "0x");
    expect(await editions.balanceOf(collector.address, 1n)).to.equal(2n);
    await expect(editions.mint(collector.address, 1n, 1n, "0x")).to.be.revertedWith(
      "SERESARTE: edition sold out",
    );
  });
});
