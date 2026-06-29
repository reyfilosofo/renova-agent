# SERESARTE / ℛenova Web3 Starter Pack

Infraestructura inicial para convertir la obra filosófica, editorial, artística y documental de SERESARTE / ℛenova en un sistema Web3 verificable: NFTs, certificados de asistencia, metadatos, hashes documentales, QR de acceso, landing page, contratos base y guía de operación desde iPhone con wallet externa.

## Propósito

Este proyecto no está diseñado como una colección especulativa ni como una promesa financiera. Está diseñado como una infraestructura cultural para:

- procedencia artística;
- archivo intelectual verificable;
- membresía cultural;
- acceso a eventos;
- certificados de asistencia;
- edición limitada de obra;
- registro de versiones;
- trazabilidad de documentos;
- presencia pública de ℛenova en Web3.

## Módulos incluidos

```text
web3-starter/
├─ contracts/
│  ├─ RenovaGenesis721.sol
│  ├─ SeresarteEdition1155.sol
│  └─ SeresarteAccessPass.sol
├─ scripts/
│  ├─ deploy.js
│  └─ generate-hashes.js
├─ metadata/
│  └─ renova-genesis/
│     ├─ manifest.demo.json
│     └─ 0001.json
├─ data/
│  ├─ events.demo.json
│  └─ document-registry.demo.json
├─ certificates/
│  └─ certificate-template.svg
├─ site/
│  ├─ index.html
│  └─ styles.css
├─ docs/
│  ├─ MANIFIESTO_WEB3.md
│  ├─ IPFS_ARWEAVE.md
│  ├─ IPHONE_MINT_GUIDE.md
│  ├─ QR_ACCESS.md
│  └─ LEGAL_AND_LICENSE.md
├─ hardhat.config.js
├─ package.json
└─ .gitignore
```

## Tres prototipos centrales

### 1. SERESARTE POAP / Access Pass

Credencial cultural para eventos, talleres, presentaciones, conferencias, inauguraciones, laboratorios, exposiciones y sesiones de filosofía aplicada.

### 2. ℛenova Genesis 314

Colección fundacional de 314 piezas filosófico-artísticas vinculadas a la sensibilidad fundante, el umbral, la vida plena, la renovación, la consciencia, la memoria, el cuidado, el arte y la transformación.

### 3. SERESARTE BRAIN onchain

Sistema de registro de hashes documentales para probar existencia, versión y procedencia sin publicar contenido privado o confidencial en blockchain.

## Qué puede hacer este starter

- Compilar contratos ERC-721, ERC-1155 y Access Pass.
- Crear una colección NFT única para ℛenova Genesis.
- Crear ediciones múltiples para DAO IAO 81, libros, láminas y certificados.
- Generar hashes SHA-256 de documentos.
- Mantener un manifiesto de archivos verificables.
- Documentar metadatos para IPFS o Arweave.
- Proponer QR de acceso a eventos sin custodiar wallets.
- Servir una landing page estática para presentar el proyecto.

## Qué no hace automáticamente

- No custodia seed phrases.
- No firma transacciones por el usuario.
- No paga gas.
- No garantiza ventas.
- No promete apreciación financiera.
- No sustituye asesoría legal, fiscal, financiera o regulatoria.

## Flujo recomendado desde iPhone

1. Crear o revisar el repositorio en GitHub.
2. Editar textos, metadatos y assets desde ChatGPT / GitHub.
3. Subir assets a IPFS o Arweave con una plataforma externa.
4. Copiar los CID resultantes en los metadatos.
5. Desplegar contratos desde una herramienta compatible con wallet externa.
6. Firmar únicamente desde una wallet propia: MetaMask, Rainbow, Coinbase Wallet u otra.
7. Publicar la landing page.
8. Usar QR para reclamo, verificación o asistencia.

## Estado actual

Versión inicial de arquitectura. No desplegada onchain. Lista para revisión técnica, diseño visual y despliegue controlado.

## Autoría conceptual

SERESARTE / ℛenova by Carlos Jonathan González Rodríguez.

## Nota

Este repositorio separa dos planos: el código abierto y la obra cultural. El código puede licenciarse como open source; los textos, marcas, manifiestos, imágenes, símbolos, nombres y conceptos deben tener una licencia cultural separada.