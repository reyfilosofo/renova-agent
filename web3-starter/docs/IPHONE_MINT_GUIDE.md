# Guía operativa desde iPhone con wallet externa

## Principio básico

ChatGPT puede preparar código, metadatos, documentos y arquitectura. La firma onchain debe hacerla el usuario desde su propia wallet. No se debe compartir seed phrase, clave privada ni códigos de recuperación.

## Flujo seguro

1. Revisar contrato y metadatos en GitHub.
2. Confirmar que las imágenes y JSON públicos estén en IPFS o Arweave.
3. Usar una plataforma de despliegue o una dApp confiable compatible con wallet móvil.
4. Conectar wallet mediante aplicación móvil, deep link o QR.
5. Revisar red, contrato, gas y dirección antes de firmar.
6. Firmar sólo si todo coincide.
7. Guardar dirección del contrato, hash de transacción y red usada.
8. Agregar esos datos al registro del repositorio.

## Reglas de seguridad

- Nunca escribir la seed phrase en ChatGPT.
- Nunca subir `.env` con claves privadas a GitHub.
- Nunca pegar claves privadas en repositorios.
- Usar testnet antes de mainnet.
- Separar wallet de pruebas, wallet operativa y wallet patrimonial.
- Usar contratos auditados antes de vender o manejar valor económico.

## Redes sugeridas para prueba

- Sepolia para pruebas Ethereum.
- Redes compatibles con OpenZeppelin / Hardhat según disponibilidad.
- Plataformas de mint con opción sin código para validación inicial.

## Datos que conviene registrar después del despliegue

```json
{
  "network": "sepolia",
  "contract_name": "RenovaGenesis721",
  "contract_address": "0xREPLACE",
  "deployer_wallet": "0xREPLACE",
  "transaction_hash": "0xREPLACE",
  "metadata_base_uri": "ipfs://REPLACE",
  "deployment_date": "YYYY-MM-DD"
}
```

## Advertencia

Los contratos incluidos son starter code. Deben auditarse antes de una operación pública con dinero, venta o promesa comercial.