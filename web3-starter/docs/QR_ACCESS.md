# Sistema conceptual de QR para acceso a eventos

## Objetivo

Usar QR como puente entre experiencia física y verificación digital sin exponer datos sensibles.

## Casos de uso

- Check-in a conferencia.
- Reclamo de Access Pass.
- Certificado de asistencia.
- Verificación de holder.
- Entrega de material token-gated.
- Registro de lectura, taller o laboratorio.

## Tipos de QR

### QR público informativo

Lleva a una landing page pública del evento.

Ejemplo:

```text
https://seresarte.example/events/SER-RENOVA-LAB-0001
```

### QR de reclamo

Incluye un código temporal o enlace firmado. No debe contener datos personales.

Ejemplo:

```text
https://seresarte.example/claim?event=SER-RENOVA-LAB-0001&code=REPLACE_WITH_ONE_TIME_CODE
```

### QR de verificación

Permite verificar certificado, hash, token o folio.

Ejemplo:

```text
https://seresarte.example/verify/SER-BRAIN-RENOVA-0001
```

## Datos mínimos recomendados

```json
{
  "event_code": "SER-RENOVA-LAB-0001",
  "claim_code_hash": "SHA256_OF_CLAIM_CODE",
  "expires_at": "YYYY-MM-DDTHH:mm:ssZ",
  "credential_type": "attendance-pass",
  "issuer": "SERESARTE / ℛenova"
}
```

## Reglas

1. No poner nombre completo en el QR si no es necesario.
2. No poner teléfono, correo, CURP, dirección ni datos sensibles.
3. Usar códigos de un solo uso para reclamos.
4. Separar QR público de QR privado.
5. Registrar hash del código, no el código en texto plano.
6. Verificar asistencia antes de mintear credencial si el evento lo requiere.
7. Permitir revocar o invalidar códigos comprometidos.

## Integración con contrato

El QR puede terminar en una página que permita:

- conectar wallet;
- reclamar pass;
- ver certificado;
- consultar hash;
- descargar PDF;
- abrir metadatos del NFT.

El contrato `SeresarteAccessPass.sol` almacena `eventCodeByPass` como referencia básica. Para producción, puede complementarse con firmas offchain, EAS, base de datos privada o credenciales no transferibles.