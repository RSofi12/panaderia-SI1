# Capa de servicio del CU2 (Recuperar contraseña).
#
# Igual que en `auth_app/services/`, acá vive la lógica de negocio para que pueda
# probarse sin levantar HTTP. La regla de la casa:
#
#   * el servicio DEVUELVE estado, no lanza excepciones de Django ni de DRF;
#   * el serializador o la vista deciden qué mensaje y qué código HTTP salen.
#
# Así, un test puede verificar "el token expiró" sin construir una Response.
