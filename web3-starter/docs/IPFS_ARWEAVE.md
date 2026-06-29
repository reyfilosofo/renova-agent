# Guía de almacenamiento: IPFS y Arweave

## Objetivo

Separar correctamente tres tipos de material:

1. Assets públicos: imágenes NFT, portadas, badges, previews.
2. Metadatos públicos: JSON ERC-721 o ERC-1155.
3. Archivos privados o confidenciales: contratos, entregables, documentos internos, expedientes de clientes.

## IPFS

IPFS permite referenciar contenido mediante CIDs. Si un archivo cambia, cambia su CID. Esto ayuda a probar integridad y a evitar URLs frágiles.

Uso sugerido:

- Imágenes de NFTs.
- Metadatos JSON.
- Portadas públicas.
- Archivos de acceso abierto.

Ejemplo de metadato:

```json
{
  "name": "ℛenova Genesis #001",
  "image": "ipfs://CID/0001.png"
}
```

## Arweave

Arweave puede usarse para almacenamiento permanente o de largo plazo, según proveedor y flujo de pago.

Uso sugerido:

- Manifiestos finales.
- Ediciones públicas definitivas.
- Archivos curatoriales estables.
- Registro público de colección.

## Lo que no debe subirse públicamente

- Seed phrases.
- Claves privadas.
- Datos personales sensibles.
- Documentos confidenciales de clientes.
- PDFs internos sin licencia o autorización.
- Datos de menores.
- Material cuya licencia no permita distribución pública.

## Flujo recomendado

1. Preparar imágenes finales.
2. Preparar metadatos JSON con placeholders.
3. Subir imágenes a IPFS o Arweave.
4. Sustituir `REPLACE_WITH_IMAGE_CID` en los JSON.
5. Subir metadatos JSON.
6. Usar el CID de metadatos como base URI en contratos o plataformas de mint.
7. Guardar una copia del CID en el registro documental.

## Nota

Este repositorio no sube archivos a IPFS o Arweave por sí mismo. El usuario debe hacerlo en una plataforma externa y conservar control de su wallet y cuentas.