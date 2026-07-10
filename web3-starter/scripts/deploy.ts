import { network } from "hardhat";

function setting(name: string, fallback: string): string {
  const value = process.env[name];
  return value && value.trim() ? value.trim() : fallback;
}

async function main(): Promise<void> {
  const { ethers, networkName } = await network.create();
  const [deployer] = await ethers.getSigners();
  const initialOwner = setting("INITIAL_OWNER", deployer.address);
  if (!ethers.isAddress(initialOwner)) {
    throw new Error("INITIAL_OWNER must be a valid Ethereum address");
  }

  const contractURI = setting("CONTRACT_URI", "ipfs://REPLACE/contract.json");
  const editionBaseURI = setting("EDITION_BASE_URI", "ipfs://REPLACE/{id}.json");

  const genesis = await ethers.deployContract("RenovaGenesis721", [initialOwner, contractURI]);
  await genesis.waitForDeployment();

  const editions = await ethers.deployContract("SeresarteEdition1155", [
    initialOwner,
    editionBaseURI,
    contractURI,
  ]);
  await editions.waitForDeployment();

  const accessPass = await ethers.deployContract("SeresarteAccessPass", [
    initialOwner,
    contractURI,
  ]);
  await accessPass.waitForDeployment();

  const result = {
    network: networkName,
    deployer: deployer.address,
    initialOwner,
    contracts: {
      RenovaGenesis721: await genesis.getAddress(),
      SeresarteEdition1155: await editions.getAddress(),
      SeresarteAccessPass: await accessPass.getAddress(),
    },
  };

  console.log(JSON.stringify(result, null, 2));
}

main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
