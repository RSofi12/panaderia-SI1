/* =================================================================================
 * PROYECTO: Panadería Santiago — Sistema de Información Web (SI-1)
 * CASO DE USO: CU20 - Registrar Gasto o Inversión
 * DESCRIPCIÓN: El Propietario o Administrador gestiona los egresos operativos (alquiler,
 *              servicios, mantenimiento, otros) e inversiones de la panadería. Consulta
 *              con filtros, registra con transacción atómica auditada en Bitácora y
 *              anula de forma lógica sin eliminar el registro físico.
 * ACTOR: Administrador / Propietario
 * TIPO DE DIAGRAMA: Diagrama de Secuencia (Arquitectura BCE con recuadros rectangulares)
 * ENTORNO: Enterprise Architect 15+
 * LENGUAJE: JScript (Motor nativo WSH en Enterprise Architect)
 * PAQUETE BACKEND: apps.compras.gastos (GastoListCreateView, GastoAnularView, registrar_movimiento)
 * CICLO PUDS: Ciclo 4
 * ================================================================================= */

var DEFAULT_PACKAGE_NAME = "CUdiagrams";
var DIAGRAM_NAME = "CU20 - Registrar Gasto o Inversion";

function log(msg) {
    Session.Output("[CU20-Secuencia] " + msg);
}

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

    var diagram = pkg.Diagrams.AddNew(DIAGRAM_NAME, "Sequence");
    try {
        diagram.StyleEx = "ShowRobustness=0;SequenceCustomArt=0;";
    } catch (e) { }
    diagram.Update();
    pkg.Diagrams.Refresh();
    return diagram;
}

function addActorParticipant(pkg, diagram, name, leftX, width) {
    var el = pkg.Elements.AddNew(name, "Actor");
    el.Update();

    var rightX = leftX + width;
    var dObj = diagram.DiagramObjects.AddNew("l=" + leftX + ";r=" + rightX + ";t=-20;b=-2400;", "");
    dObj.ElementID = el.ElementID;
    dObj.Update();
    return el;
}

function addParticipant(pkg, diagram, name, stereotype, leftX, width) {
    var el = pkg.Elements.AddNew(name, "Sequence");
    if (stereotype && stereotype.length > 0) {
        el.Stereotype = stereotype;
    }
    el.Update();

    var rightX = leftX + width;
    var dObj = diagram.DiagramObjects.AddNew("l=" + leftX + ";r=" + rightX + ";t=-30;b=-2400;", "");
    dObj.ElementID = el.ElementID;
    dObj.Style = "usecustomart=0;HideIcon=1;";
    dObj.Update();
    return el;
}

function addEntityParticipant(pkg, diagram, name, leftX, width) {
    var el = pkg.Elements.AddNew(name, "Sequence");
    el.Stereotype = "Entity" + String.fromCharCode(160);
    el.Update();

    var rightX = leftX + width;
    var dObj = diagram.DiagramObjects.AddNew("l=" + leftX + ";r=" + rightX + ";t=-30;b=-2400;", "");
    dObj.ElementID = el.ElementID;
    dObj.Style = "usecustomart=0;HideIcon=1;";
    dObj.Update();
    return el;
}

function addMessage(src, dst, label, isReturn, sequenceNo) {
    var con = src.Connectors.AddNew(label, "Sequence");
    con.SupplierID = dst.ElementID;
    if (isReturn) {
        con.Stereotype = "return";
    }
    if (sequenceNo) {
        try {
            con.SequenceNo = sequenceNo;
        } catch (e) { }
    }
    con.Update();
    return con;
}

function addCombinedFragment(pkg, diagram, type, guardLabel, left, right, top, bottom) {
    try {
        var frag = pkg.Elements.AddNew(guardLabel, "InteractionFragment");
        frag.Stereotype = type;
        frag.Update();

        var dObj = diagram.DiagramObjects.AddNew("l=" + left + ";r=" + right + ";t=" + top + ";b=" + bottom + ";", "");
        dObj.ElementID = frag.ElementID;
        dObj.Update();
        return frag;
    } catch (err) {
        log("Nota al crear fragmento (" + type + "): " + err.message);
        return null;
    }
}

function stretchActorLifeline(diagram, actorEl) {
    for (var i = 0; i < diagram.DiagramObjects.Count; i++) {
        var dObj = diagram.DiagramObjects.GetAt(i);
        if (dObj.ElementID == actorEl.ElementID) {
            dObj.Top = -20;
            dObj.Bottom = -2400;
            dObj.Update();
            return;
        }
    }
}

function main() {
    log("Iniciando generación de CU20 (Diagrama de Secuencia BCE)...");

    var pkg = getTargetPackage();
    if (pkg == null) return;

    var diagram = recreateDiagram(pkg);

    // =========================================================================
    // PARTICIPANTES (Lifelines con recuadros rectangulares estándar EA)
    // =========================================================================
    // 1. Actor
    var actUser = addActorParticipant(pkg, diagram, ":Administrador / :Propietario", 40, 150);

    // 2. Boundary (Frontend React / Interfaz)
    var bndGastos = addParticipant(pkg, diagram, ":GastosPage", "Interface", 230, 140);

    // 3. Controller (Django REST Framework / API View)
    var ctrlGasto = addParticipant(pkg, diagram, ":GastoController", "Controller", 420, 150);

    // 4. Entities (Modelos ORM / Tablas PostgreSQL)
    var entMov = addEntityParticipant(pkg, diagram, ":MovimientoEconomico", 620, 160);
    var entBit = addEntityParticipant(pkg, diagram, ":Bitacora", 820, 130);

    stretchActorLifeline(diagram, actUser);

    var seq = 1;

    // =========================================================================
    // ESCENARIO 1: CONSULTA DE MOVIMIENTOS CON FILTROS (Mensajes 1.x)
    // =========================================================================
    addMessage(actUser, bndGastos, "1: solicitarListadoGastos(filtros)", false, seq++);
    addMessage(bndGastos, ctrlGasto, "1.1: get(filtros)", false, seq++);
    addMessage(ctrlGasto, ctrlGasto, "1.2: leer_filtros_gasto()", false, seq++);
    addMessage(ctrlGasto, entMov, "1.3: filter(tipo, categoria, fechas)", false, seq++);
    addMessage(ctrlGasto, entMov, "1.4: select_related(id_usuario)", false, seq++);
    addMessage(entMov, ctrlGasto, "1.5: QuerySet[MovimientoEconomico]", true, seq++);
    addMessage(ctrlGasto, bndGastos, "1.6: 200 OK (gastosJSON)", true, seq++);
    addMessage(bndGastos, actUser, "1.7: renderizarTablaGastos()", true, seq++);

    // =========================================================================
    // ESCENARIO 2: REGISTRO DE GASTO O INVERSIÓN (Mensajes 2.x)
    // =========================================================================
    addMessage(actUser, bndGastos, "2: abrirRegistrarGasto(datosGasto)", false, seq++);
    addMessage(bndGastos, ctrlGasto, "2.1: post(data)", false, seq++);
    addMessage(ctrlGasto, ctrlGasto, "2.2: is_valid()", false, seq++);

    // FRAGMENTO ALT [Validacion Datos]: Abarca desde 2.3 hasta 2.9
    // Rama 1: Datos válidos -> Transacción atómica en BD y auditoría
    addMessage(ctrlGasto, ctrlGasto, "2.3: registrar_movimiento()", false, seq++);
    addMessage(ctrlGasto, entMov, "2.4: create(datos)", false, seq++);
    addMessage(entMov, ctrlGasto, "2.5: movimiento", true, seq++);
    addMessage(ctrlGasto, entBit, "2.6: registrar(ALTA_MOVIMIENTO_ECONOMICO)", false, seq++);
    addMessage(ctrlGasto, bndGastos, "2.7: 201 Created (movimientoJSON)", true, seq++);
    addMessage(bndGastos, actUser, "2.8: cerrarModalRegistro()", true, seq++);

    // =========================================================================
    // ESCENARIO 3: ANULACIÓN LÓGICA DE MOVIMIENTO ECONÓMICO (Mensajes 3.x)
    // =========================================================================
    addMessage(actUser, bndGastos, "3: solicitarAnulacion(idMovimiento)", false, seq++);
    addMessage(bndGastos, ctrlGasto, "3.1: post(id)", false, seq++);
    addMessage(ctrlGasto, ctrlGasto, "3.2: anular_movimiento()", false, seq++);
    addMessage(ctrlGasto, entMov, "3.3: select_for_update()", false, seq++);
    addMessage(entMov, ctrlGasto, "3.4: movimiento", true, seq++);
    addMessage(ctrlGasto, entMov, "3.5: save(anulado=True)", false, seq++);
    addMessage(ctrlGasto, entBit, "3.6: registrar(ANULACION_MOVIMIENTO_ECONOMICO)", false, seq++);
    addMessage(ctrlGasto, bndGastos, "3.7: 200 OK (movimientoAnuladoJSON)", true, seq++);
    addMessage(bndGastos, actUser, "3.8: actualizarEstadoEnTabla()", true, seq++);

    // =========================================================================
    // FRAGMENTOS COMBINADOS UML 2.5
    // =========================================================================
    // FRAGMENTO OPT [Registro Atomico]: Abarca desde Mensaje 2.3 hasta 2.6
    addCombinedFragment(pkg, diagram, "opt", "[Transaccion Atomica: Registro y Bitacora]", 390, 980, -780, -1280);

    // FRAGMENTO OPT [Anulacion Logica]: Abarca desde Mensaje 3.2 hasta 3.6
    addCombinedFragment(pkg, diagram, "opt", "[Transaccion Atomica: Anulacion y Bitacora]", 390, 980, -1450, -1950);

    diagram.Update();
    Repository.SaveDiagram(diagram.DiagramID);
    Repository.ReloadDiagram(diagram.DiagramID);
    Repository.OpenDiagram(diagram.DiagramID);

    log("CU20 generado exitosamente.");
    Session.Prompt("¡Diagrama de Secuencia CU20 (Registrar Gasto o Inversión) generado con éxito en Enterprise Architect!", 0);
}

main();
