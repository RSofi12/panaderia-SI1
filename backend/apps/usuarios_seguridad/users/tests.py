"""
Pruebas del caso de uso CU3 — Gestionar usuarios.

Organizadas por la regla que rompen, no por el método que ejercitan. Esa es la
diferencia entre una suite que sirve para defender el CU y una que solo sirve
para subir la cobertura: cada clase responde una pregunta que la docente
puede hacer.

    PruebasControlAcceso        ¿quién puede entrar a /api/usuarios/?
    PruebasAltaYEdicion         ¿se registran y modifican cuentas correctamente?
    PruebasUnicidad             ¿se pueden duplicar nombres de usuario?
    PruebasEstado               ¿activar e inactivar funciona y audita?
    PruebasGuardasAutoM         ¿se puede dejar el sistema sin Administrador?
    PruebasRestablecerClave     ¿el reset administrativo funciona y revoca?
    PruebasDesbloqueo           ¿el desbloqueo reutiliza la política de CU1?
    PruebasListadoYFiltros      ¿el listado filtra, busca, ordena y pagina?
    PruebasSinBorrado           ¿existe DELETE? (no, y por qué no debe existir)

Sobre el hash de contraseñas: `assertNotEqual(password, CONTRASENA)` es
intencionalmente débil, y aun así es la única comprobación honesta aquí. El
modelo usa el hasher por defecto de Django, así que un test que ناجara en
producción y pasara en local significaría que `PASSWORD_HASHERS` diverge entre
entornos. Lo que sí se verifica de verdad es que la contraseña NO vuelva en la
respuesta, que es el riesgo real de exponer un campo de escritura.
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
from apps.usuarios_seguridad.permisos.models import Permiso
from apps.usuarios_seguridad.roles.models import Rol, RolPermiso
from apps.usuarios_seguridad.users import views as users_views
from apps.usuarios_seguridad.users.models import Usuario
from apps.usuarios_seguridad.users.password_validators import validar_contrasena

Usuario = get_user_model()

CONTRASENA_VALIDA = 'PanADERIA2026!'


@override_settings(
    # El hasher por defecto (PBKDF2 con cientos de miles de iteraciones) está
    # diseñado para defenderse de un atacante que roba la base. En una suite que
    # crea decenas de usuarios, eso convierte cada prueba en segundos de espera
    # sin probar nada del CU3. Django ofrece `MD5PasswordHasher` exactamente
    # para esto, y está en el código fuente del framework como
    # "NO uses esto en producción".
    #
    # Consecuencia que hay que aceptar: los tests NO pueden afirmar el prefijo
    # del hash ('pbkdf2_...'). Comprueban la propiedad que importa, que es
    # `check_password()` acepta el texto plano y que la columna guardada no es
    # el texto plano.
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
)
class BasePruebaCU3(TestCase):
    """Datos mínimos y coherentes: un Administrador con el permiso, y un rol más."""

    def setUp(self):
        self.client = APIClient()

        # El listado de CU3 tiene throttling por usuario (120/min). Toda la suite
        # comparte la misma clave de caché porque el id del Administrador es el
        # mismo en cada base de prueba, así que sin esto las pruebas se
        # trippingarían unas a otras y los fallos serían ilegibles.
        patcher = patch.object(users_views.UsuarioViewSet, 'throttle_classes', [])
        patcher.start()
        self.addCleanup(patcher.stop)

        cache.clear()

        # --- Catálogos: es lo que hace que un rol "sea" algo y no solo un
        # nombre. Sin esta fila en `rol_permiso`, `get_permisos_nombres()`
        # devolvería una lista vacía y `TienePermiso` rechazaría todo.
        self.permiso_gestionar = Permiso.objects.create(
            id_permiso=1,
            nombre='gestionar_usuarios',
            descripcion='Crear, editar, activar o inactivar usuarios',
        )
        self.permiso_ventas = Permiso.objects.create(
            id_permiso=2,
            nombre='registrar_ventas',
            descripcion='Registrar ventas directas por unidad',
        )

        self.rol_admin = Rol.objects.create(
            id_rol=1,
            nombre='Administrador',
            descripcion='Acceso total',
        )
        self.rol_ventas = Rol.objects.create(
            id_rol=2,
            nombre='Personal de Ventas',
            descripcion='Registro de ventas',
        )

        RolPermiso.objects.create(rol=self.rol_admin, permiso=self.permiso_gestionar)
        RolPermiso.objects.create(rol=self.rol_ventas, permiso=self.permiso_ventas)

        self.admin = Usuario.objects.create_user(
            nombre_usuario='admin',
            password=CONTRASENA_VALIDA,
            nombre_completo='Administrador de Prueba',
            email='admin.prueba@mail.com',
            id_rol=self.rol_admin,
        )
        self.vendedor = Usuario.objects.create_user(
            nombre_usuario='mgonzales',
            password=CONTRASENA_VALIDA,
            nombre_completo='María Elena Gonzales',
            email='mgonzales@mail.com',
            id_rol=self.rol_ventas,
        )

        # Un SEGUNDO Administrador existe de entrada en la mayoría de los
        # contextos. La razón es que la guarda "no dejes el sistema sin
        # Administradores" compara contra los OTROS: con un único
        # Administrador, cualquier prueba de inactivación sería rechazada por
        # esa guarda y no llegaría a probar nada de la operación en sí.
        self.admin_respaldo = Usuario.objects.create_user(
            nombre_usuario='admin2',
            password=CONTRASENA_VALIDA,
            nombre_completo='Segundo Administrador',
            email='admin2.prueba@mail.com',
            id_rol=self.rol_admin,
        )

        self.url_lista = reverse('users:usuario-list')
        self.url_roles = reverse('users:usuario-roles')
        self.url_alta = reverse('users:usuario-list')
        self.url_detalle = reverse('users:usuario-detail', args=[self.vendedor.id_usuario])
        self.url_detalle_admin = reverse('users:usuario-detail', args=[self.admin.id_usuario])

    def autenticar_como_admin(self):
        self.client.force_authenticate(user=self.admin)
        return self.client

    def autenticar_como(self, usuario):
        self.client.force_authenticate(user=usuario)
        return self.client

    def url_accion(self, usuario, accion):
        return reverse(f'users:usuario-{accion}', args=[usuario.id_usuario])

    def datos_alta_validos(self, **sobrescrituras):
        datos = {
            'nombre_usuario': 'nueva',
            'nombre_completo': 'Cuenta Nueva de Prueba',
            'email': 'nueva.prueba@mail.com',
            'password': CONTRASENA_VALIDA,
            'id_rol': self.rol_ventas.id_rol,
        }
        datos.update(sobrescrituras)
        return datos


# ==================================================================
# Control de acceso
# ==================================================================


class PruebasControlAcceso(BasePruebaCU3):

    def test_sin_token_responde_401(self):
        respuesta = self.client.get(self.url_lista)
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_personal_de_ventas_responde_403(self):
        """
        El caso de uso lo pide textualmente: un usuario con rol
        'Personal de Ventas' que intenta entrar a /api/usuarios/ debe recibir
        403, no 404 ni 200.

        Importante: el vendedor ESTÁ autenticado. Lo que falta es el permiso
        `gestionar_usuarios`, que viene de la matriz `rol_permiso`. Esa
        separación entre "hay sesión" y "hay permiso" es justamente el control
        de acceso basado en roles que implementa `TienePermiso`.
        """
        self.autenticar_como(self.vendedor)

        respuesta = self.client.get(self.url_lista)

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_administrador_responde_200(self):
        self.autenticar_como_admin()

        respuesta = self.client.get(self.url_lista)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

    def test_usuario_sin_rol_responde_403(self):
        """
        `id_rol` admite NULL y el sistema lo permite: un usuario sin rol entra al
        panel pero no ve ningún módulo. `get_permisos_nombres()` devuelve `[]`
        y el permiso no se cumple. Es el comportamiento correcto y deja claro
        que la ausencia de rol no es un caso excepcional que se olvidó.
        """
        sin_rol = Usuario.objects.create_user(
            nombre_usuario='sinrol',
            password=CONTRASENA_VALIDA,
            nombre_completo='Cuenta Sin Rol',
            email='sinrol@mail.com',
        )

        self.autenticar_como(sin_rol)
        respuesta = self.client.get(self.url_lista)

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)


# ==================================================================
# Alta y edición
# ==================================================================


class PruebasAltaYEdicion(BasePruebaCU3):

    def test_alta_crea_la_cuenta_con_contrasena_hasheada(self):
        self.autenticar_como_admin()

        respuesta = self.client.post(self.url_alta, self.datos_alta_validos(), format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)

        creada = Usuario.objects.get(nombre_usuario='nueva')
        self.assertTrue(creada.check_password(CONTRASENA_VALIDA))
        # El hash guardado NO es el texto plano. Es la garantía que se puede
        # comprobar sin depender del algoritmo de hasheo configurado, y por eso
        # la suite corre con MD5PasswordHasher: ver la nota de la clase base.
        self.assertNotEqual(creada.password, CONTRASENA_VALIDA)

    def test_alta_nunca_devuelve_la_contrasena(self):
        """
        `password` es `write_only`. Este es el riesgo REAL de exponer un campo de
        escritura, y por eso tiene su propio test y no queda como nota al pie.
        """
        self.autenticar_como_admin()

        respuesta = self.client.post(self.url_alta, self.datos_alta_validos(), format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', respuesta.data)

    def test_alta_registra_en_bitacora(self):
        self.autenticar_como_admin()

        self.client.post(self.url_alta, self.datos_alta_validos(), format='json')

        registro = Bitacora.objects.filter(accion=AccionBitacora.ALTA_USUARIO).first()
        self.assertIsNotNone(registro)
        self.assertEqual(registro.usuario, self.admin)
        self.assertEqual(registro.tabla_afectada, 'usuario')
        self.assertIn('nueva', registro.descripcion)
        # La contraseña no puede aparecer en la bitácora ni por accidente.
        self.assertNotIn(CONTRASENA_VALIDA, registro.descripcion)

    def test_alta_rechaza_contrasena_debajo_de_la_politica(self):
        self.autenticar_como_admin()

        respuesta = self.client.post(
            self.url_alta,
            self.datos_alta_validos(password='corta1!'),
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', respuesta.data)
        self.assertFalse(Usuario.objects.filter(nombre_usuario='nueva').exists())

    def test_alta_rechaza_contrasena_parecida_al_nombre_de_usuario(self):
        """
        El validador de similitud de Django compara la contraseña contra los
        atributos del usuario. Para que funcione, el serializer tiene que
        construir una instancia provisional con los datos ya recibidos; si
        comparara contra una cuenta vacía, esta contraseña pasaría.

        El caso completo del validador está en `PruebasPoliticaContrasenas`,
        donde se comprueba de forma directa. Acá se comprueba que la regla llega
        hasta la API.
        """
        self.autenticar_como_admin()

        respuesta = self.client.post(
            self.url_alta,
            self.datos_alta_validos(
                nombre_usuario='admin.santiago',
                email='admin.santiago@mail.com',
                password='Admin.Santiago1!',
            ),
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', respuesta.data)
        self.assertFalse(Usuario.objects.filter(nombre_usuario='admin.santiago').exists())

    def test_alta_acepta_una_contrasena_que_no_se_parece(self):
        """
        El contraste del caso anterior: si la respuesta 400 fuera por cualquier
        otra regla, esta prueba lo detectaría.
        """
        self.autenticar_como_admin()

        respuesta = self.client.post(
            self.url_alta,
            self.datos_alta_validos(
                nombre_usuario='admin.santiago',
                email='admin.santiago@mail.com',
                password='Xy9$qLm2Kp',
            ),
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)

    def test_edicion_modifica_solo_los_campos_enviados(self):
        """
        Un PATCH parcial no debe tocar lo que no vino. Si el PATCH se aplicara
        sobre un objeto reinstanciado, el nombre y el correo se perderían: por
        eso la prueba compara el resto de los campos después del cambio.
        """
        self.autenticar_como_admin()

        respuesta = self.client.patch(
            self.url_detalle,
            {'nombre_completo': 'María Elena Gonzales Pérez'},
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.vendedor.refresh_from_db()
        self.assertEqual(self.vendedor.nombre_completo, 'María Elena Gonzales Pérez')
        self.assertEqual(self.vendedor.nombre_usuario, 'mgonzales')
        self.assertEqual(self.vendedor.email, 'mgonzales@mail.com')

    def test_edicion_no_toca_la_contrasena(self):
        """
        Editar el nombre de alguien no puede cambiar su clave. Si lo hiciera,
        el Administrador terminaría descubriendo o reescribiendo contraseñas que
        no le corresponden, y la auditoría de "qué cambió" se mezclaría.
        """
        self.autenticar_como_admin()

        self.client.patch(self.url_detalle, {'nombre_completo': 'Otro Nombre'}, format='json')

        self.vendedor.refresh_from_db()
        self.assertTrue(self.vendedor.check_password(CONTRASENA_VALIDA))

    def test_edicion_registra_el_diff_en_bitacora(self):
        self.autenticar_como_admin()

        self.client.patch(
            self.url_detalle,
            {'email': 'nuevo.correo@mail.com'},
            format='json',
        )

        registro = Bitacora.objects.filter(accion=AccionBitacora.EDICION_USUARIO).first()
        self.assertIsNotNone(registro)
        self.assertIn('mgonzales@mail.com', registro.descripcion)
        self.assertIn('nuevo.correo@mail.com', registro.descripcion)

    def test_edicion_ignora_campos_no_editables(self):
        """
        `activo` SÍ es editable por PATCH, pero `password` no aparece en el
        serializer. Mandarla debe ignorarse, no aceptarse: un campo que el
        endpoint no declara no puede cambiarse por él.
        """
        self.autenticar_como_admin()

        self.client.patch(
            self.url_detalle,
            {'password': 'OtraClave2026!'},
            format='json',
        )

        self.vendedor.refresh_from_db()
        self.assertTrue(self.vendedor.check_password(CONTRASENA_VALIDA))


# ==================================================================
# Unicidad
# ==================================================================


class PruebasUnicidad(BasePruebaCU3):

    def test_no_se_puede_duplicar_nombre_de_usuario_exacto(self):
        self.autenticar_como_admin()

        respuesta = self.client.post(
            self.url_alta,
            self.datos_alta_validos(
                nombre_usuario='mgonzales',
                email='otro.mail.com',
            ),
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nombre_usuario', respuesta.data)

    def test_no_se_puede_duplicar_nombre_de_usuario_por_mayusculas(self):
        """
        'MGONZALES' no es una cuenta nueva: es la misma cuenta. Sin el índice
        sobre `Lower(nombre_usuario)` (migración 0005) PostgreSQL lo aceptaría,
        y como el login busca por coincidencia exacta una de las dos quedaría
        inaccesible. El `__iexact` del serializer y el índice cuentan la misma
        historia, y por eso esta prueba y la migración van juntas.
        """
        self.autenticar_como_admin()

        respuesta = self.client.post(
            self.url_alta,
            self.datos_alta_validos(
                nombre_usuario='MGONZALES',
                email='otro.mail.com',
            ),
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nombre_usuario', respuesta.data)

    def test_no_se_puede_duplicar_correo_por_mayusculas(self):
        """El mismo criterio que el correo, que ya venía de CU2."""
        self.autenticar_como_admin()

        respuesta = self.client.post(
            self.url_alta,
            self.datos_alta_validos(email='MGONZALES@MAIL.COM'),
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', respuesta.data)

    def test_la_base_rechaza_el_duplicado_por_mayusculas(self):
        """
        El test anterior prueba el mensaje del serializer. Este prueba el
        ultimo recurso: si el validador se quitara, la BASE tiene que rechazar el
        INSERT igual. Es lo que hace el índice único sobre `Lower(...)`.
        """
        from django.db import transaction
        from django.db.utils import IntegrityError

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Usuario.objects.create_user(
                    nombre_usuario='MGONZALES',
                    password=CONTRASENA_VALIDA,
                    nombre_completo='Duplicado Por Mayusculas',
                    email='duplicado.mail.com',
                )


# ==================================================================
# Activación e inactivación
# ==================================================================


class PruebasEstado(BasePruebaCU3):

    def test_inactivar_una_venta_devuelve_200_y_cambia_el_estado(self):
        self.autenticar_como_admin()

        respuesta = self.client.patch(
            self.url_accion(self.vendedor, 'toggle-activo'),
            {'activo': False, 'motivo': 'Renuncia del empleado'},
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.vendedor.refresh_from_db()
        self.assertFalse(self.vendedor.activo)

    def test_activar_una_venta_devuelve_200(self):
        self.vendedor.activo = False
        self.vendedor.save(update_fields=['activo'])
        self.autenticar_como_admin()

        respuesta = self.client.patch(
            self.url_accion(self.vendedor, 'toggle-activo'),
            {'activo': True},
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.vendedor.refresh_from_db()
        self.assertTrue(self.vendedor.activo)

    def test_toggle_registra_en_bitacora_con_el_motivo(self):
        self.autenticar_como_admin()

        self.client.patch(
            self.url_accion(self.vendedor, 'toggle-activo'),
            {'activo': False, 'motivo': 'Renuncia del empleado'},
            format='json',
        )

        registro = Bitacora.objects.filter(accion=AccionBitacora.CAMBIAR_ESTADO_USUARIO).first()
        self.assertIsNotNone(registro)
        self.assertIn('Renuncia del empleado', registro.descripcion)
        self.assertEqual(registro.usuario, self.admin)

    def test_toggle_exige_el_campo_activo(self):
        self.autenticar_como_admin()

        respuesta = self.client.patch(
            self.url_accion(self.vendedor, 'toggle-activo'),
            {'motivo': 'sin el estado'},
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('activo', respuesta.data)

    def test_toggle_sobre_un_estado_igual_responde_400(self):
        """
        Reactivar una cuenta que ya está activa no es un no-op silencioso: se
        avisa. Es preferible a devolver 200 y no hacer nada, porque un `200`
        haría creer al frontend que la operación ocurrió.
        """
        self.autenticar_como_admin()

        respuesta = self.client.patch(
            self.url_accion(self.vendedor, 'toggle-activo'),
            {'activo': True},
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', respuesta.data)

    def test_activar_una_cuenta_bloqueada_le_vienta_el_bloqueo(self):
        """
        Si el Administrador reactiva a alguien que seguía bloqueado por intentos
        fallidos, la cuenta quedaría inusable sin explicación visible. La
        reactivación levanta el bloqueo y lo deja escrito en la bitácora.
        """
        from django.utils import timezone
        from datetime import timedelta

        self.vendedor.intentos_fallidos = 3
        self.vendedor.bloqueado_hasta = timezone.now() + timedelta(minutes=10)
        self.vendedor.activo = False
        self.vendedor.save()

        self.autenticar_como_admin()
        respuesta = self.client.patch(
            self.url_accion(self.vendedor, 'toggle-activo'),
            {'activo': True},
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.vendedor.refresh_from_db()
        self.assertTrue(self.vendedor.activo)
        self.assertIsNone(self.vendedor.bloqueado_hasta)
        self.assertEqual(self.vendedor.intentos_fallidos, 0)


# ==================================================================
# Guardas de auto-destrucción
# ==================================================================


class PruebasGuardasAutoM(BasePruebaCU3):

    def test_administrador_no_puede_inactivarse_a_si_mismo(self):
        """
        La guarda más obvia y la más importante. Sin ella, un clic de más deja
        el sistema sin administración, porque la única cuenta que podría
        revertir el error es la que acaba de quedar inactiva.
        """
        # Se deja al Administrador como el ÚNICO administrador activo para que
        # la prueba no dependa de cuál guarda salta primero.
        self.admin_respaldo.activo = False
        self.admin_respaldo.save(update_fields=['activo'])
        self.autenticar_como(self.admin)

        respuesta = self.client.patch(
            self.url_accion(self.admin, 'toggle-activo'),
            {'activo': False},
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.activo)

    def test_no_se_puede_quitar_el_propio_rol(self):
        """
        `id_rol` admite NULL, así que el sistema lo permite para OTROS usuarios.
        Para el que ejecuta la operación, no: se quedaría sin el permiso
        `gestionar_usuarios` que necesita justamente para recuperar el rol.
        """
        self.autenticar_como(self.admin)

        respuesta = self.client.patch(
            self.url_detalle_admin,
            {'id_rol': None},
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.id_rol_id, self.rol_admin.id_rol)

    def test_no_se_puede_dejar_sin_administradores_activos(self):
        """
        Desactivar al ÚNICO Administrador activo, incluso si lo hace otro
        Administrador, deja el sistema sin nadie que administre las cuentas.
        """
        self.autenticar_como(self.admin_respaldo)
        self.admin_respaldo.activo = False
        self.admin_respaldo.save(update_fields=['activo'])

        respuesta = self.client.patch(
            self.url_accion(self.admin, 'toggle-activo'),
            {'activo': False},
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.activo)

    def test_no_se_puede_quitar_el_rol_de_administrador_al_ultimo_activo(self):
        """
        La misma pérdida de acceso, pero por la otra vía: no se desactiva la
        cuenta, se le cambia el rol. Si nadie más tiene el rol Administrador
        activo, la cuenta sigue activa pero ya no administra nada.

        Quién ejecuta la operación es `self.admin`, que para esta prueba se
        deja INACTIVO a propósito. Tiene que ser así: si el ejecutor fuera un
        Administrador activo, existiría otro Administrador activo y la guarda no
        se dispararía, que es justamente lo que se quiere probar. Que una cuenta
        inactiva pueda ejecutar la operación es un artefacto de
        `force_authenticate` —el bypass de autenticación no comprueba `activo`—
        y no una vía real de producción: en producción un JWT de una cuenta
        inactiva no obtiene permisos, porque `activa` se evalúa en el login.
        """
        self.admin.activo = False
        self.admin.save(update_fields=['activo'])
        self.autenticar_como(self.admin)

        respuesta = self.client.patch(
            reverse('users:usuario-detail', args=[self.admin_respaldo.id_usuario]),
            {'id_rol': self.rol_ventas.id_rol},
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.admin_respaldo.refresh_from_db()
        self.assertEqual(self.admin_respaldo.id_rol_id, self.rol_admin.id_rol)

    def test_la_guarda_no_bloquea_desactivar_a_un_vendedor_sin_admin(self):
        """
        La guarda se evalúa SOLO si la cuenta era un Administrador activo. Sin
        ese filtro, desactivar a un vendedor cuando ya no queda ningún
        Administrador en el sistema también sería rechazado, cuando lo único que
        se está haciendo es administration de una cuenta sin permisos.
        """
        self.autenticar_como(self.admin)
        self.admin_respaldo.activo = False
        self.admin_respaldo.save(update_fields=['activo'])

        respuesta = self.client.patch(
            self.url_accion(self.vendedor, 'toggle-activo'),
            {'activo': False},
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.vendedor.refresh_from_db()
        self.assertFalse(self.vendedor.activo)


# ==================================================================
# Restablecimiento administrativo de contraseña (extensión aprobada)
# ==================================================================


class PruebasRestablecerClave(BasePruebaCU3):

    def test_restablecer_cambia_la_contrasena(self):
        self.autenticar_como_admin()
        nueva = 'NuevaClave2026!'

        respuesta = self.client.post(
            self.url_accion(self.vendedor, 'restablecer-contrasena'),
            {'nueva_contrasena': nueva, 'confirmar_contrasena': nueva},
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.vendedor.refresh_from_db()
        self.assertTrue(self.vendedor.check_password(nueva))
        self.assertFalse(self.vendedor.check_password(CONTRASENA_VALIDA))

    def test_restablecer_exige_confirmacion_coincidente(self):
        self.autenticar_como_admin()

        respuesta = self.client.post(
            self.url_accion(self.vendedor, 'restablecer-contrasena'),
            {
                'nueva_contrasena': 'NuevaClave2026!',
                'confirmar_contrasena': 'OtraClave2026!',
            },
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.vendedor.refresh_from_db()
        self.assertTrue(self.vendedor.check_password(CONTRASENA_VALIDA))

    def test_restablecer_aplica_la_politica_de_contrasenas(self):
        self.autenticar_como_admin()

        respuesta = self.client.post(
            self.url_accion(self.vendedor, 'restablecer-contrasena'),
            {'nueva_contrasena': 'debil', 'confirmar_contrasena': 'debil'},
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.vendedor.refresh_from_db()
        self.assertTrue(self.vendedor.check_password(CONTRASENA_VALIDA))

    def test_restablecer_registra_en_bitacora_sin_la_contrasena(self):
        self.autenticar_como_admin()
        nueva = 'NuevaClave2026!'

        self.client.post(
            self.url_accion(self.vendedor, 'restablecer-contrasena'),
            {'nueva_contrasena': nueva, 'confirmar_contrasena': nueva},
            format='json',
        )

        registro = Bitacora.objects.filter(accion=AccionBitacora.RESTABLECER_CONTRASENA).first()
        self.assertIsNotNone(registro)
        self.assertEqual(registro.usuario, self.admin)
        self.assertNotIn(nueva, registro.descripcion)

    def test_restablecer_levanta_el_bloqueo(self):
        """
        Restablecer la clave de una cuenta bloqueada por intentos fallidos y
        dejarla bloqueada sería un callejón sin salida: clave nueva que no se
        puede usar. Es el mismo criterio que aplica CU2 al recuperar la
        contraseña, y por eso comparte código y no solo intención.
        """
        from django.utils import timezone
        from datetime import timedelta

        self.vendedor.intentos_fallidos = 3
        self.vendedor.bloqueado_hasta = timezone.now() + timedelta(minutes=10)
        self.vendedor.save()

        self.autenticar_como_admin()
        nueva = 'NuevaClave2026!'
        self.client.post(
            self.url_accion(self.vendedor, 'restablecer-contrasena'),
            {'nueva_contrasena': nueva, 'confirmar_contrasena': nueva},
            format='json',
        )

        self.vendedor.refresh_from_db()
        self.assertIsNone(self.vendedor.bloqueado_hasta)
        self.assertEqual(self.vendedor.intentos_fallidos, 0)


# ==================================================================
# Desbloqueo (extensión aprobada)
# ==================================================================


class PruebasDesbloqueo(BasePruebaCU3):

    def test_desbloquear_levanta_el_bloqueo(self):
        from django.utils import timezone
        from datetime import timedelta

        self.vendedor.intentos_fallidos = 3
        self.vendedor.bloqueado_hasta = timezone.now() + timedelta(minutes=10)
        self.vendedor.save()

        self.autenticar_como_admin()
        respuesta = self.client.post(
            self.url_accion(self.vendedor, 'desbloquear'),
            {},
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.vendedor.refresh_from_db()
        self.assertIsNone(self.vendedor.bloqueado_hasta)
        self.assertEqual(self.vendedor.intentos_fallidos, 0)
        self.assertFalse(self.vendedor.is_bloqueado)

    def test_desbloquear_registra_con_la_accion_de_cu1(self):
        """
        `desbloquear_cuenta` delega en `politica_bloqueo.desbloquear_usuario`, y
        por eso la bitácora usa `DESBLOQUEO_CUENTA`, la acción que ya existía
        desde CU1. No se crea una acción "desbloqueo desde el panel" para no
        partir en dos el mismo hecho en el reporte.
        """
        from django.utils import timezone
        from datetime import timedelta

        self.vendedor.intentos_fallidos = 3
        self.vendedor.bloqueado_hasta = timezone.now() + timedelta(minutes=10)
        self.vendedor.save()

        self.autenticar_como_admin()
        self.client.post(self.url_accion(self.vendedor, 'desbloquear'), {}, format='json')

        registro = Bitacora.objects.filter(accion=AccionBitacora.DESBLOQUEO_CUENTA).first()
        self.assertIsNotNone(registro)
        self.assertEqual(registro.usuario, self.admin)

    def test_desbloquear_una_cuenta_sin_bloqueo_responde_400(self):
        self.autenticar_como_admin()

        respuesta = self.client.post(
            self.url_accion(self.vendedor, 'desbloquear'),
            {},
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', respuesta.data)


# ==================================================================
# Listado, filtros, búsqueda y orden
# ==================================================================


class PruebasListadoYFiltros(BasePruebaCU3):

    def test_listado_responde_200_con_estructura_paginada(self):
        """
        El listado devuelve `{count, next, previous, results}` y no un arreglo
        plano. El frontend tiene que leer `results`; esta prueba fija ese
        contrato para que un cambio futuro en la paginación no lo rompa en
        silencio.
        """
        self.autenticar_como_admin()

        respuesta = self.client.get(self.url_lista)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIn('count', respuesta.data)
        self.assertIn('results', respuesta.data)
        self.assertEqual(respuesta.data['count'], Usuario.objects.count())

    def test_listado_expone_el_estado_de_bloqueo(self):
        """
        `esta_bloqueado` y `minutos_bloqueo_restantes` son propiedades
        calculadas, no columnas. Van en la respuesta para que la tabla del
        Administrador pueda explicar por qué una cuenta no entra, en vez de
        dejar que el usuario deduzca lo que ocurre de tres columnas sueltas.
        """
        self.autenticar_como_admin()

        respuesta = self.client.get(self.url_lista)

        primera = respuesta.data['results'][0]
        for campo in ('esta_bloqueado', 'minutos_bloqueo_restantes', 'rol', 'total_permisos'):
            self.assertIn(campo, primera)

    def test_filtro_por_estado_inactivo(self):
        self.vendedor.activo = False
        self.vendedor.save(update_fields=['activo'])
        self.autenticar_como_admin()

        respuesta = self.client.get(self.url_lista, {'activo': 'false'})

        nombres = [fila['nombre_usuario'] for fila in respuesta.data['results']]
        self.assertIn('mgonzales', nombres)
        self.assertNotIn('admin', nombres)

    def test_filtro_por_estado_activo(self):
        self.vendedor.activo = False
        self.vendedor.save(update_fields=['activo'])
        self.autenticar_como_admin()

        respuesta = self.client.get(self.url_lista, {'activo': 'true'})

        nombres = [fila['nombre_usuario'] for fila in respuesta.data['results']]
        self.assertIn('admin', nombres)
        self.assertNotIn('mgonzales', nombres)

    def test_filtro_por_rol(self):
        self.autenticar_como_admin()

        respuesta = self.client.get(self.url_lista, {'id_rol': self.rol_ventas.id_rol})

        for fila in respuesta.data['results']:
            self.assertEqual(fila['id_rol'], self.rol_ventas.id_rol)

    def test_buscador_por_nombre_completo(self):
        """
        El término buscado es 'Elena' y no 'María' a propósito: en PostgreSQL
        `icontains` NO ignora los acentos, así que buscar 'Maria' no encontraría
        'María'. Es una limitación del motor de búsqueda, no un error del
        filtro, y conviene recordarlo para no perder tiempo más adelante.
        """
        self.autenticar_como_admin()

        respuesta = self.client.get(self.url_lista, {'search': 'Elena'})

        nombres = [fila['nombre_usuario'] for fila in respuesta.data['results']]
        self.assertIn('mgonzales', nombres)
        self.assertNotIn('admin', nombres)

    def test_orden_por_nombre_de_usuario(self):
        self.autenticar_como_admin()

        respuesta = self.client.get(self.url_lista, {'ordering': 'nombre_usuario'})

        nombres = [fila['nombre_usuario'] for fila in respuesta.data['results']]
        self.assertEqual(nombres, sorted(nombres))

    def test_roles_devuelve_el_catalogo_para_el_desplegable(self):
        self.autenticar_como_admin()

        respuesta = self.client.get(self.url_roles)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        nombres = [fila['nombre'] for fila in respuesta.data]
        self.assertIn('Administrador', nombres)
        self.assertIn('Personal de Ventas', nombres)

    def test_roles_no_expone_la_matriz_de_permisos(self):
        """
        `/api/usuarios/roles/` existe para el desplegable del formulario de
        CU3, no para administrar la matriz de permisos, que es CU4. Por eso
        `RolSimpleSerializer` no incluye el campo `permisos`.
        """
        self.autenticar_como_admin()

        respuesta = self.client.get(self.url_roles)

        for fila in respuesta.data:
            self.assertNotIn('permisos', fila)
            self.assertIn('total_permisos', fila)

    def test_roles_requiere_el_permiso_de_gestionar_usuarios(self):
        self.autenticar_como(self.vendedor)

        respuesta = self.client.get(self.url_roles)

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)


# ==================================================================
# Política de contraseñas
# ==================================================================


class PruebasPoliticaContrasenas(TestCase):
    """
    El validador, comprobado de forma directa y no a través de la API.

    Motivo: cuando varias reglas fallan a la vez, `validate_password` de Django
    las devuelve TODAS juntas. Una prueba de extremo a extremo que espera un 400
    no dice cuál de las reglas se violó, y una regla que empieza a dispararse
    sola pasaría inadvertida. Estos tests aíslan una regla por vez.
    """

    def test_una_contrasena_suficientemente_buena_pasa(self):
        usuario = Usuario(
            nombre_usuario='admin.santiago',
            nombre_completo='Administrador Santiago',
            email='admin.santiago@mail.com',
        )

        self.assertEqual(validar_contrasena('Xy9$qLm2Kp', usuario=usuario), [])

    def test_contrasena_corta_es_rechazada(self):
        usuario = Usuario(nombre_usuario='mrojas', email='mrojas@mail.com')

        self.assertTrue(validar_contrasena('Ab1!', usuario=usuario))

    def test_contrasena_parecida_al_nombre_de_usuario_es_rechazada(self):
        """
        'Admin.Santiago1!' cumple longitud, mayúscula, número y símbolo, y aun
        así se rechaza: es el nombre de usuario con dos caracteres pegados. Es
        justamente el caso que un validador de complejidad solo no cubre.
        """
        usuario = Usuario(
            nombre_usuario='admin.santiago',
            nombre_completo='Administrador Santiago',
            email='admin.santiago@mail.com',
        )

        errores = validar_contrasena('Admin.Santiago1!', usuario=usuario)

        self.assertTrue(errores)

    def test_contrasena_sin_usuario_no_puede_comparar_y_no_rompe(self):
        """
        `usuario` es opcional en la firma. Sin él, el validador de similitud
        simplemente no tiene contra qué comparar y el resto de las reglas
        siguen aplicándose. La función tiene que devolver una lista vacía y no
        reventar con `AttributeError` sobre un `None`.
        """
        self.assertEqual(validar_contrasena('Xy9$qLm2Kp'), [])
        self.assertTrue(validar_contrasena('corta', usuario=None))


# ==================================================================
# Ausencia de borrado
# ==================================================================


class PruebasSinBorrado(BasePruebaCU3):

    def test_delete_responde_405(self):
        """
        El CU3 no contempla el borrado de cuentas, y `usuario` es referenciado
        por `bitacora`, `token_recuperacion`, `pedido`, `venta`, `compra`,
        `produccion` y `movimiento_economico`. Un DELETE físico destruiría el
        historial económico y dejaría la auditoría sin autor.

        La respuesta es 405 y no 404 a propósito: 404 diría "esta ruta no
        existe", mientras que 405 dice "el borrado está en la API y está
        prohibido por diseño", que es la información que un cliente necesita.
        """
        self.autenticar_como_admin()

        respuesta = self.client.delete(self.url_detalle)

        self.assertEqual(respuesta.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(Usuario.objects.filter(pk=self.vendedor.pk).exists())
