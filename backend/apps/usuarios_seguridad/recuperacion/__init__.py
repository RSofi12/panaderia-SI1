# Sub-app de datos del CU2 (Recuperar contraseña).
#
# Contiene el modelo `TokenRecuperacion` y los servicios de dominio. NO contiene
# vistas ni serializers: el transporte HTTP de la recuperación vive en
# `auth_app`, igual que el de CU1, para que todo lo que se expone bajo
# `/api/auth/` pase por el mismo urlconf y comparta la misma política de
# throttling.
