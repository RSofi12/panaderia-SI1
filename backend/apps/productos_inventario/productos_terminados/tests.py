"""
Pruebas base de la sub-app de Productos Terminados (CU12, CU18).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

Usuario = get_user_model()


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PruebasBaseProductosTerminados(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuario = Usuario.objects.create_user(
            nombre_usuario='vendedor',
            password='PanADERIA2026!',
            nombre_completo='Valeria Ventas',
            email='ventas.prueba@mail.com',
        )

    def test_existencias_requiere_autenticacion(self):
        respuesta = self.client.get('/api/productos-terminados/existencias/')
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_existencias_autenticado_responde_200(self):
        self.client.force_authenticate(user=self.usuario)
        respuesta = self.client.get('/api/productos-terminados/existencias/')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIsInstance(respuesta.data, list)

    def test_mermas_autenticado_responde_200(self):
        self.client.force_authenticate(user=self.usuario)
        respuesta = self.client.get('/api/productos-terminados/mermas/')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIsInstance(respuesta.data, list)
