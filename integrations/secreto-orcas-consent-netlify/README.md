# Secreto de Orcas — consentimiento de un clic v2.2
**ℛenova Press & SERESARTE · Rey Filósofo by SERESARTE · 2026-10-23**
## Estado
Código implementado, seis pruebas locales satisfactorias, **no desplegado**. No se ha cambiado la redirección de Stripe LIVE. No se pueden enviar fotografías a esta app.
## Requisitos antes de activar
1. Crear proyecto Netlify utilizando **este directorio** como raíz, y publicar con HTTPS.
2. Configurar variables secretas en funciones: STRIPE_SECRET_KEY (cuenta ReyFilosofo by SERESARTE, LIVE), ORCAS_CONSENT_HASH_KEY (clave aleatoria robusta) y ORCAS_PRIVACY_URL (aviso integral público HTTPS, domicilio y ARCO real).
3. Validar la compra de prueba, verificar rechazo de sesiones no pagadas y guardar una sola constancia.
4. Solo tras la prueba, configurar la redirección de **los enlaces personalizados** de Stripe a https://DOMINIO/?session_id={CHECKOUT_SESSION_ID}; conservar el regreso a secretodeorcas.seresarte.chatgpt.site.
5. Para tratamiento de fotos: se necesita un paso separado de carga protegida validado contra esta autorización; NO está implementado en este módulo. La eliminación de fotos en 30 días se aplica a otros sistemas y exige auditoría independiente.
6. El aviso legal completo y revisión por abogado mexicano deben estar completados.
## Seguridad
La casilla no está preseleccionada; la función valida con Stripe que la sesión esté pagada y el Payment Link pertenezca al producto ilustrado autorizado. Guarda constancia mínima inmutable con hash HMAC, versión 2.2, marca UTC y huella SHA256 del texto. No publica nombres ni fotos. No se puede registrar con credenciales o aviso ausentes. No autoriza publicidad. Si el comprador no ejerce representación legal, debe intervenir madre, padre o tutor.
## Enlaces de pagos ya identificados
plink_1U84edGYktVBPuyCfPf3vPwm y plink_1U7sU4GYktVBPuyCTse426AJ.


## ACTUALIZACIÓN 2026-10-23 · STRIPE LIVE ACTIVADO
Dos enlaces de pago activos ya incluyen el campo de autorización **opcional** `autorizacion_imagen_ia` (sin selección predeterminada), con las opciones `siAutorizo` y `sinFotografia`, junto con el texto explicativo del uso de ChatGPT y 30 días de retención editorial. Verificado con lectura posterior de Stripe API.

- Edición Individualizada Ilustrada: `plink_1U84edGYktVBPuyCfPf3vPwm` — https://book.stripe.com/14A4gzfGwaQmgjNc2mbQY07
- Enlace premium anterior: `plink_1U7sU4GYktVBPuyCTse426AJ` — https://buy.stripe.com/cNi5kDcuk8Ie9Vp7M6bQY04

**Regla obligatoria de fulfillment**: `session.custom_fields.find(f=>f.key==='autorizacion_imagen_ia')?.dropdown?.value === 'siAutorizo'` para habilitar personalización basada en fotografía. Cualquier otra respuesta, ausencia del campo o sesión anterior a esta activación significa **no autorizado**. Nunca se aplica retroactivamente. Verifica también pago completado antes de procesar. La casilla no certifica documentalmente la patria potestad; es declaración bajo responsabilidad del comprador.

Se mantuvieron nombre, idioma y redirección de los enlaces, pero el tercer campo opcional de idea/descripcion fue sustituido; recoger dicho detalle por correo/ficha privada.

**Importante**: El frontend y backend de esta carpeta siguen sin desplegar y la retención/supresión en ChatGPT, correo y Drive continúa sin automatización verificada. Stripe está activado; esto NO equivale a la implementación completa del protocolo de fotos ni a blindaje legal integral.
