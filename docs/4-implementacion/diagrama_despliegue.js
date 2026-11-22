/* =================================================================================
 * PROYECTO: Panadería "Santiago" (SI-1)
 * DIAGRAMA: 4.1.1 Diseño Físico — Diagrama de Despliegue (Deployment Diagram UML 2.5 / PUDS)
 * DESCRIPCIÓN: Modelo de despliegue físico y lógico estructurado según metodología PUDS:
 *              - Capa 1 (Superior): Dispositivos Clientes (Verde Claro #D5E8D4).
 *              - Capa 2: Red Internet (WAN / Telecomunicaciones públicas - Blanco #FFFFFF).
 *              - Capa 3: Servidor Web Frontend (Render Cloud Platform / Docker Container - Blanco).
 *              - Capa 4: Servidor Backend (Render Cloud Platform / Docker Container - Blanco).
 *              - Capa 5: Servidor de Correo / Mailpit (Docker Container - Blanco).
 *              - Capa 6 (Inferior): Servidor Base de Datos (Render Managed PostgreSQL 16 - Blanco).
 *              - Columna Lateral Derecha: Servicios Cloud Externos e Interfaces (Blanco):
 *                  * Web Speech API (W3C Browser Standard - Dictado y comandos por voz).
 *                  * Cloudinary Media Cloud (Almacenamiento y CDN para fotos de productos).
 *                  * Stripe API (Pasarela de pagos con tarjeta de crédito/débito).
 *              
 *              * Conectores con flecha direccional ("Source -> Destination") y etiqueta
 *                de protocolo/conexión, SIN el estereotipo «communication».
 *
 * ENTORNO: Enterprise Architect 15.0+ / 16.0+
 * LENGUAJE: JScript (Motor nativo WSH en Enterprise Architect)
 * ================================================================================= */

var DEFAULT_PACKAGE_NAME = "4. Diseño de Arquitectura";
var DIAGRAM_NAME = "4.1.1 Diagrama de Despliegue - Panaderia Santiago";

// Constantes de color BGR para Enterprise Architect
var COLOR_WHITE = 16777215;       // #FFFFFF (Blanco puro para nodos y servidores)
var COLOR_LIGHT_GREEN = 13954453;  // #D5E8D4 (Verde claro para dispositivos clientes)

function log(msg) {
    Session.Output("[Despliegue-Panaderia] " + msg);
}

/**
 * Obtiene el paquete de destino en el Project Browser o lo crea si no existe.
 */
function getTargetPackage() {
    var selectedPkg = Repository.GetTreeSelectedPackage();
    if (selectedPkg != null) {
        log("Usando paquete seleccionado en Project Browser: " + selectedPkg.Name);
        return selectedPkg;
    }

    var roots = Repository.Models;
    var root = (roots.Count > 0) ? roots.GetAt(0) : null;
    if (root == null) {
        Session.Prompt("No se encontró ningún modelo raíz en Enterprise Architect.", 0);
        return null;
    }

    for (var i = 0; i < root.Packages.Count; i++) {
        var p = root.Packages.GetAt(i);
        if (p.Name == DEFAULT_PACKAGE_NAME) {
            return p;
        }
    }

    var newPkg = root.Packages.AddNew(DEFAULT_PACKAGE_NAME, "Package");
    newPkg.Update();
    root.Packages.Refresh();
    log("Paquete creado: " + DEFAULT_PACKAGE_NAME);
    return newPkg;
}

/**
 * Recrea el diagrama de despliegue limpio.
 */
function recreateDiagram(pkg) {
    for (var i = pkg.Diagrams.Count - 1; i >= 0; i--) {
        var d = pkg.Diagrams.GetAt(i);
        if (d.Name == DIAGRAM_NAME) {
            try {
                pkg.Diagrams.Delete(i);
                pkg.Diagrams.Refresh();
                log("Diagrama previo eliminado para regeneración limpia.");
            } catch (e) {
                log("Aviso al eliminar: " + e.message);
            }
            break;
        }
    }

    var diagram = pkg.Diagrams.AddNew(DIAGRAM_NAME, "Deployment");
    diagram.Update();
    pkg.Diagrams.Refresh();
    return diagram;
}

/**
 * Crea un Nodo UML (Device o Node) con color de fondo configurable y lo posiciona en el diagrama.
 */
function addNode(pkg, diagram, name, stereotype, notes, l, r, t, b, bgColor) {
    var el = pkg.Elements.AddNew(name, "Node");
    if (stereotype && stereotype.length > 0) {
        el.Stereotype = stereotype;
    }
    if (notes && notes.length > 0) {
        el.Notes = notes;
    }
    el.Update();
    pkg.Elements.Refresh();

    var dObj = diagram.DiagramObjects.AddNew("l=" + l + ";r=" + r + ";t=" + t + ";b=" + b + ";", "");
    dObj.ElementID = el.ElementID;
    if (bgColor !== undefined && bgColor !== null) {
        dObj.BackgroundColor = bgColor;
        dObj.Style = "BCOL=" + bgColor + ";";
    }
    dObj.Update();

    return el;
}

/**
 * Crea un Artefacto UML como elemento hijo dentro de un Nodo y lo posiciona en el diagrama.
 */
function addArtifact(parentNode, diagram, name, stereotype, l, r, t, b) {
    var art = parentNode.Elements.AddNew(name, "Artifact");
    if (stereotype && stereotype.length > 0) {
        art.Stereotype = stereotype;
    }
    art.Update();
    parentNode.Elements.Refresh();

    var dObj = diagram.DiagramObjects.AddNew("l=" + l + ";r=" + r + ";t=" + t + ";b=" + b + ";", "");
    dObj.ElementID = art.ElementID;
    dObj.Update();

    return art;
}

/**
 * Crea un Entorno de Ejecución (Execution Environment) dentro de un Nodo y lo posiciona en el diagrama.
 */
function addExecutionEnv(parentNode, diagram, name, stereotype, l, r, t, b) {
    var env = parentNode.Elements.AddNew(name, "ExecutionEnvironment");
    if (stereotype && stereotype.length > 0) {
        env.Stereotype = stereotype;
    }
    env.Update();
    parentNode.Elements.Refresh();

    var dObj = diagram.DiagramObjects.AddNew("l=" + l + ";r=" + r + ";t=" + t + ";b=" + b + ";", "");
    dObj.ElementID = env.ElementID;
    dObj.Update();

    return env;
}

/**
 * Crea una vía de comunicación con flecha direccional y etiqueta de protocolo,
 * sin estereotipo «communication».
 */
function addCommunication(src, dst, protocolLabel) {
    var con = src.Connectors.AddNew(protocolLabel, "CommunicationPath");
    con.SupplierID = dst.ElementID;
    con.Direction = "Source -> Destination";
    con.Stereotype = ""; // Sin estereotipo visible «communication»
    con.Update();
    return con;
}

function main() {
    log("Iniciando generación del Diagrama de Despliegue para Panadería Santiago...");

    var pkg = getTargetPackage();
    if (pkg == null) return;

    var diagram = recreateDiagram(pkg);

    /* =========================================================================
     * 1. NIVEL 1: CAPA DE DISPOSITIVOS CLIENTES (Superior: Verde Claro)
     * ========================================================================= */
    // Dispositivo Punto de Venta y Producción (Mostrador / Fábrica)
    var nodoOperativo = addNode(
        pkg, diagram,
        "Dispositivo Punto de Venta & Producción\n(PC Mostrador / Tablet Táctil)",
        "device",
        "Dispositivo para Personal de Ventas (CU13 ventas mostrador/QR) y Maestro Panadero Miguel Ángel Rojas (CU10 producción diaria e insumos).",
        60, 420, -40, -250,
        COLOR_LIGHT_GREEN
    );
    addArtifact(nodoOperativo, diagram, "Portal Ventas & Producción SPA\n(React 19 + Tailwind CSS)", "artifact", 90, 390, -100, -165);
    addArtifact(nodoOperativo, diagram, "Navegador Web\n(Web Speech API Client - Voz)", "artifact", 90, 390, -180, -235);

    // Dispositivo Administrador & Propietario (Gerencia y Control)
    var nodoGerencia = addNode(
        pkg, diagram,
        "Dispositivo Admin & Propietario\n(PC Escritorio / Laptop)",
        "device",
        "Estación de trabajo para Administrador (roles, usuarios, bitácora) y Propietario Carlos Santiago Vargas (compras, precios y reportes financieros).",
        480, 840, -40, -250,
        COLOR_LIGHT_GREEN
    );
    addArtifact(nodoGerencia, diagram, "Dashboard Administrativo SPA\n(React 19 + Vite + Tailwind)", "artifact", 510, 810, -100, -165);
    addArtifact(nodoGerencia, diagram, "Navegador Web\n(Audio Capture & Voice Reports)", "artifact", 510, 810, -180, -235);

    /* =========================================================================
     * 2. NIVEL 2: RED INTERNET (WAN / Tránsito Seguro: Blanco)
     * ========================================================================= */
    var nodoInternet = addNode(
        pkg, diagram,
        "Red Internet\n(WAN / Red Pública Segura)",
        "device",
        "Infraestructura de telecomunicaciones pública con cifrado punto a punto (TCP/IP - TLS 1.3 / HTTPS).",
        270, 630, -300, -420,
        COLOR_WHITE
    );

    /* =========================================================================
     * 3. NIVEL 3: SERVIDOR WEB FRONTEND - RENDER STATIC / DOCKER (Blanco)
     * ========================================================================= */
    var nodoFrontend = addNode(
        pkg, diagram,
        "Servidor Web Frontend\n(Render Cloud Platform / Docker)",
        "device",
        "Plataforma PaaS Cloud para hosting de SPA React con CDN global, SSL automatizado y contenedor Docker 'panaderia_frontend'.",
        250, 650, -480, -690,
        COLOR_WHITE
    );
    var envFrontend = addExecutionEnv(
        nodoFrontend, diagram,
        "Contenedor Docker: panaderia_frontend\n(Nginx / Vite Static Web Server :5173 / :80)",
        "executionEnvironment",
        280, 620, -540, -670
    );
    addArtifact(
        nodoFrontend, diagram,
        "Bundle React 19 SPA\n(TypeScript, Tailwind CSS, Axios Interceptors)",
        "artifact",
        300, 600, -590, -655
    );

    /* =========================================================================
     * 4. NIVEL 4: SERVIDOR BACKEND - RENDER WEB SERVICE / DOCKER (Blanco)
     * ========================================================================= */
    var nodoBackend = addNode(
        pkg, diagram,
        "Servidor Backend\n(Render Cloud Platform / Docker)",
        "device",
        "PaaS en la nube ejecutando contenedor Docker 'panaderia_backend' con Python 3.12 y Django REST Framework con RBAC y transacciones ACID.",
        250, 650, -750, -980,
        COLOR_WHITE
    );
    var envBackend = addExecutionEnv(
        nodoBackend, diagram,
        "Contenedor Docker: panaderia_backend\n(Python 3.12 / Django 6+ DRF & Gunicorn :8000)",
        "executionEnvironment",
        280, 620, -810, -960
    );
    addArtifact(
        nodoBackend, diagram,
        "Django REST Framework API\n(5 Paquetes Apps, Serializers, Services, ORM)",
        "artifact",
        300, 600, -870, -945
    );

    /* =========================================================================
     * 5. NIVEL 5: SERVIDOR DE CORREO Y PRUEBAS - MAILPIT DOCKER (Blanco)
     * ========================================================================= */
    var nodoMailpit = addNode(
        pkg, diagram,
        "Servidor de Correo Mailpit\n(Docker Container - Entorno Pruebas)",
        "device",
        "Contenedor 'panaderia_mailpit' para captura y depuración de correos de recuperación de contraseña (CU2). SMTP :1025 y Web UI :8025.",
        40, 220, -780, -960,
        COLOR_WHITE
    );
    var envMailpit = addExecutionEnv(
        nodoMailpit, diagram,
        "Contenedor Docker: panaderia_mailpit\n(Mailpit Server Engine)",
        "executionEnvironment",
        55, 205, -835, -945
    );
    addArtifact(
        nodoMailpit, diagram,
        "Mailpit Service\n(SMTP :1025 / HTTP :8025)",
        "artifact",
        65, 195, -885, -935
    );

    /* =========================================================================
     * 6. NIVEL 6: SERVIDOR BASE DE DATOS - RENDER MANAGED POSTGRESQL (Blanco)
     * ========================================================================= */
    var nodoDatabase = addNode(
        pkg, diagram,
        "Servidor Base de Datos\n(Render Managed PostgreSQL / Docker)",
        "device",
        "Instancia administrada de PostgreSQL 16 ('panaderia_db') con copias de seguridad continuas, llaves foráneas y triggers de auditoría.",
        250, 650, -1040, -1250,
        COLOR_WHITE
    );
    var envPostgres = addExecutionEnv(
        nodoDatabase, diagram,
        "Contenedor Docker: panaderia_db\n(PostgreSQL 16 Alpine Engine :5432)",
        "executionEnvironment",
        280, 620, -1100, -1230
    );
    addArtifact(
        nodoDatabase, diagram,
        "Esquema BD Relacional\n(panaderia_db - 26 Tablas Normalizadas)",
        "artifact",
        300, 600, -1155, -1215
    );

    /* =========================================================================
     * 7. COLUMNA DERECHA: SERVICIOS CLOUD EXTERNOS E INTERFACES (Blanco)
     * ========================================================================= */
    // Servicio 1: Web Speech API (W3C Browser Standard Engine)
    var nodoWebSpeech = addNode(
        pkg, diagram,
        "Web Speech API Engine\n(Browser Native / W3C Standard)",
        "node",
        "API nativa del motor de ejecución del navegador (SpeechRecognition & Synthesis) para comandos de voz y dictado de reportes.",
        940, 1300, -40, -220,
        COLOR_WHITE
    );
    addArtifact(nodoWebSpeech, diagram, "SpeechRecognition API Client\n(W3C Standard)", "artifact", 970, 1270, -110, -190);

    // Servicio 2: Cloudinary Media Storage (CDN & Imágenes)
    var nodoCloudinary = addNode(
        pkg, diagram,
        "Cloudinary Media Cloud\n(Cloudinary Storage & CDN)",
        "node",
        "Plataforma Cloud externa para almacenamiento, transformación y entrega optimizada por CDN de fotografías de productos (CU5).",
        940, 1300, -380, -560,
        COLOR_WHITE
    );
    addArtifact(nodoCloudinary, diagram, "Cloudinary Upload & CDN REST API", "artifact", 970, 1270, -450, -530);

    // Servicio 3: Pasarela de Pagos Stripe
    var nodoStripe = addNode(
        pkg, diagram,
        "Pasarela de Pagos Stripe\n(Stripe Payments Cloud)",
        "node",
        "Infraestructura cloud para procesamiento seguro de pagos con tarjeta de crédito/débito y generación de intenciones de cobro (CU13).",
        940, 1300, -740, -920,
        COLOR_WHITE
    );
    addArtifact(nodoStripe, diagram, "Stripe Payments REST API\n(Payment Intents & Webhooks)", "artifact", 970, 1270, -810, -890);

    /* =========================================================================
     * 8. VÍAS DE COMUNICACIÓN (Direction: Source -> Destination, Sin «communication»)
     * ========================================================================= */
    // Flujo Vertical Principal
    addCommunication(nodoOperativo, nodoInternet, "HTTPS :443 (TLS 1.3)");
    addCommunication(nodoGerencia, nodoInternet, "HTTPS :443 (TLS 1.3)");
    addCommunication(nodoInternet, nodoFrontend, "HTTPS :443 (Render Global CDN)");
    addCommunication(nodoFrontend, nodoBackend, "HTTPS / REST JSON :8000 (Bearer JWT)");
    addCommunication(nodoBackend, nodoDatabase, "TCP/IP PostgreSQL :5432 (SSL / Auth)");

    // Conexión con Mailpit (Gestión de correos en Docker)
    addCommunication(nodoBackend, nodoMailpit, "SMTP :1025 (Envío Emails Reset Password CU2)");
    addCommunication(nodoGerencia, nodoMailpit, "HTTP :8025 (Web UI Inspección Correos)");

    // Conexiones a Servicios Externos
    addCommunication(nodoOperativo, nodoWebSpeech, "JavaScript Native API Call (Local Browser Engine)");
    addCommunication(nodoGerencia, nodoWebSpeech, "JavaScript Native API Call (Local Browser Engine)");
    addCommunication(nodoBackend, nodoCloudinary, "HTTPS :443 (Media Upload API / Bearer)");
    addCommunication(nodoFrontend, nodoCloudinary, "HTTPS :443 (CDN Image Fetch)");
    addCommunication(nodoBackend, nodoStripe, "HTTPS :443 (Payment Intents API / Secret Key)");
    addCommunication(nodoOperativo, nodoStripe, "HTTPS :443 (Stripe Elements / Checkout)");

    /* =========================================================================
     * 9. GUARDAR, REFRESCAR Y ABRIR DIAGRAMA
     * ========================================================================= */
    diagram.Update();
    Repository.SaveDiagram(diagram.DiagramID);
    Repository.ReloadDiagram(diagram.DiagramID);
    Repository.OpenDiagram(diagram.DiagramID);

    log("Diagrama de despliegue para Panadería Santiago generado exitosamente.");
    Session.Prompt("¡Diagrama de Despliegue de Panadería Santiago generado con éxito!\n- Nodos Dockerizados (Backend, Frontend, Mailpit, Database)\n- Servicios Externos (Stripe, Cloudinary, Web Speech API)\n- Flechas direccionales con etiquetas de conexión (sin estereotipo «communication»).", 0);
}

main();
