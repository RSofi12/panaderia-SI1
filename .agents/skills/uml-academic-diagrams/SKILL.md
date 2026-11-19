---
name: uml-academic-diagrams
description: Generación y estándares de Diagramas UML académicos (Secuencia, Comunicación y Análisis de Clases BCE). USAR EXCLUSIVAMENTE cuando el usuario invoque explícitamente /uml-academic-diagrams o pida textualmente 'generame los diagramas uml del CU...', 'crea los diagramas del CU...' o peticiones directas equivalentes. NUNCA activar automáticamente por adjuntar imágenes, ni durante tareas de implementación de código Backend/Frontend.
---

# 📐 Estándar Oficial de Diagramas UML (PUDS / RUP / BCE)
### Clínica Vida Salud — Centro Médico La Cruz

Este documento define las reglas estrictas de modelado, diseño visual, nomenclatura, estructura relacional y sintaxis técnica para generar diagramas de **Secuencia**, **Comunicación** y **Análisis de Clases** bajo los más altos estándares académicos y de ingeniería de software.

---

## 1. 🏛️ Arquitectura BCE y Principios de Elaboración

### 1.1. Fuente de Verdad para la Elaboración de Diagramas
* **Caso de Uso ya Implementado (Fuente Primaria: Código Real):**  
  La elaboración de los diagramas UML se realiza **principalmente y con total fidelidad a partir del código ya implementado** en el sistema:
  - Métodos y rutas en controladores (`app/Http/Controllers/...`).
  - Servicios transaccionales y de dominio (`app/Services/...`).
  - FormRequests y reglas de validación (`app/Http/Requests/...`).
  - Modelos Eloquent en singular y relaciones en español (`app/Models/...`).
  - Tablas de base de datos (`docs/database/DDL_Database_Clinica_LaCruz.sql`).
  - Vistas y componentes modales React (`resources/js/...`).
* **Caso de Uso No Implementado (Plan de Implementación Previo):**  
  Si el usuario solicita generar los diagramas cuando el Caso de Uso **aún no está codificado**, se diagraman como un **plan de implementación previo completo, riguroso y detallado**, tomando obligatoriamente como fuentes de verdad:
  - Documentos de contexto (`docs/ai/ARCHITECTURE.md`, `docs/CU_ESPECIFICACION_SISTEMA.md`, `docs/Ex_Parcial_2_sistemas-1.md`).
  - Modelo general de clases y base de datos (`docs/database/diagrama_de_clases.puml`, `DDL_Database_Clinica_LaCruz.sql`).
  - Requerimientos, reglas de negocio e información funcional específica provista por el usuario.

### 1.2. Patrón Canónico Horizontal BCE
Todos los diagramas deben respetar el patrón **BCE (Boundary - Control - Entity)** y ordenarse de izquierda a derecha en **distribución horizontal continua**:

```text
[Actor / Actores] ──► [Boundary / Interfaz] ──► [Controlador / Control] ──► [Entidades de Dominio]
```

### Reglas Estructurales Obligatorias:
1. **Actor:** Humano iniciador (ej. `Administrador`, `Recepcionista`, `Médico`, `Paciente`). Si dos actores ejecutan idéntica interacción en el CU, se unifican con barra: `Recepcionista / Paciente`.
2. **Boundary (Interfaz / Pantalla):** Componente de frontend o vista (`:ConsultaRegistroModal`, `:AppointmentsManager`, `:PatientProfileView`).
3. **Control (Controlador):** Controlador de Laravel (`:ConsultasController`, `:AppointmentsController`). Toda la lógica, orquestación, transacciones (`DB::transaction`) y validaciones se centralizan aquí.
4. **Entity (Entidades de Dominio):** Modelos Eloquent / tablas PostgreSQL (`:Cita`, `:ConsultaMedica`, `:Diagnostico`, `:Bitacora`, etc.).
5. **Aislamiento Estricto de Entidades:**
   - Las entidades **NUNCA** se envían mensajes entre sí.
   - Las entidades **NUNCA** devuelven respuestas a otras entidades.
   - En el diagrama de comunicación, las entidades **NO** envían mensajes de regreso a los controladores (las respuestas de datos las orquesta el controller).
6. **Validaciones en Controlador:** Si el código ejecuta validaciones internas (reglas de negocio, chequeos anti-colisión, unicidad), se modelan como mensajes reflexivos hacia sí mismo (`self-call` en el Controller).

---

## 2. 🎬 Diagrama de Secuencia (JScript para Enterprise Architect)

* **Entorno:** Enterprise Architect 15.0+ (Motor JScript WSH).
* **Participantes (Lifelines):**
  - **Forma y Color:** Cuadros rectangulares con el **color por defecto que otorga Enterprise Architect** (sin forzar estilos ni colores personalizados).
  - **Sin icono de base de datos:** Las tablas o entidades persistentes se dibujan como cuadros rectangulares estándar con el estereotipo `<<Entity>>` o `<<Database>>`.
  - Estereotipos visibles: `<<Actor>>`, `<<Interface>>`, `<<Controller>>`, `<<Entity>>`.
  - Trazado de **línea de vida (lifeline)** visible y continua para cada componente, incluyendo el actor.
* **Mensajes y Funciones:**
  - Numeración jerárquica estricta: `1`, `1.1`, `1.2`, `1.2.1`, `2`, `2.1`, etc.
  - Nombres reales del código fuente (métodos de controladores, servicios, FormRequests, llamadas REST GET/POST y consultas Eloquent).
  - **Convención de Parámetros:** Funciones sin parámetros `metodo()` o con 1 parámetro `metodo(id)`. Si el método en el código recibe múltiples argumentos, **dejar los paréntesis vacíos `metodo()`**.
  - **Enlaces Direccionales y Retornos:**
    - Los mensajes secuenciales van en su link con flecha hacia adelante (`→`).
    - Los retornos van en su link separado con flecha hacia atrás (`←`) y línea discontinua (`dash`), únicamente hacia el controlador o la pantalla cuando el código tiene retorno explícito.
* **Fragmentos Combinados (UML 2.5+):**
  - **`alt` (Bifurcaciones / Decisiones):** Máximo **3 fragmentos `alt`** por diagrama para mantenerlo limpio y legible.
  - **`opt` (Opcionales):** Para pasos condicionales sin rama alternativa (ej. auditoría opcional, envío de notificación).
  - **`loop` (Iteraciones):** Para bucles de procesamiento (ej. iterar detalles de diagnóstico, recetas o slots).
  - **Comentarios Obligatorios de Rango de Mensajes:** En todo script JScript, antes de declarar cada fragmento (`alt`, `opt`, `loop`), es **obligatorio escribir en los comentarios desde qué mensaje y hasta qué mensaje abarca**:
    ```javascript
    // FRAGMENTO ALT [Guardia / Condicion]: Abarca desde Mensaje X.X hasta Y.Y
    // FRAGMENTO LOOP [Iteracion]: Abarca desde Mensaje Z.1 hasta Z.N
    // FRAGMENTO OPT [Condicion]: Abarca Mensaje W.W
    ```
  - Prohibido el uso de fragmentos redundantes o decorativos. Evitar cruces de líneas.

---

## 3. 💬 Diagrama de Comunicación

El Diagrama de Comunicación resalta la arquitectura y organización espacial de los objetos que colaboran en el CU.

* **Correspondencia 1:1 con Secuencia:** Debe incluir exactamente los mismos participantes y el mismo orden/numeración de mensajes que el diagrama de secuencia del mismo CU.
* **Iconos Canónicos BCE:** En este diagrama **SÍ se utilizan los iconos formales de estereotipos BCE**:
  - `Boundary`: Círculo con barra vertical a la izquierda (`shape=umlBoundary`).
  - `Control`: Círculo con flecha curva superior derecha (`shape=umlControl`).
  - `Entity`: Círculo con barra inferior horizontal (`shape=umlEntity`).
* **Nombres:** Sin prefijo de estereotipo en el texto visible; solo el nombre del objeto (`:AppointmentsController`, `:Cita`).

### 3.1. Estándar de Diseño para Draw.io (`.drawio`)
En Draw.io, el diagrama debe mantener holgura visual y máxima claridad estética:
1. **Flecha Gráfica Arriba de Cada Mensaje (Gold Standard: ver CU03):**  
   - **Prohibido terminantemente** colocar flechas como caracteres unicode dentro del texto (`1: mensaje() ->`) o pegadas lateralmente al texto (como en CU16 o CU23).
   - Cada mensaje se compone de **dos celdas (`mxCell`) independientes**:
     1. Una celda de texto para la etiqueta del método (ej. `1.1: index()`).
     2. Una celda tipo arista/flecha (`edge="1"`) posicionada **directamente encima de la celda de texto**, orientada horizontalmente hacia el componente receptor.
   - **Plantilla XML canónica en Draw.io (referencia oficial CU03):**
     ```xml
     <!-- Invocación hacia adelante (Arriba de la línea de relación) -->
     <mxCell id="CUxx-COMM-M1" parent="1" style="text;html=1;whiteSpace=wrap;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;rounded=1;fontSize=10;fontColor=#000000;fontStyle=1;labelBackgroundColor=none;" value="1: solicitarConsulta()" vertex="1">
       <mxGeometry height="26" width="160" x="130" y="200" as="geometry" />
     </mxCell>
     <mxCell id="CUxx-COMM-A1" edge="1" parent="1" source="CUxx-COMM-M1" target="CUxx-COMM-M1" style="endArrow=classic;html=1;rounded=1;strokeWidth=2;fontSize=10;strokeColor=#003366;exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0.75;entryY=0;entryDx=0;entryDy=0;" value="">
       <mxGeometry height="50" relative="1" width="50" as="geometry">
         <mxPoint x="180" y="195" as="sourcePoint" />
         <mxPoint x="215" y="195" as="targetPoint" />
       </mxGeometry>
     </mxCell>

     <!-- Retorno hacia atrás (Abajo de la línea de relación con línea discontinua) -->
     <mxCell id="CUxx-COMM-M14" parent="1" style="text;whiteSpace=wrap;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;rounded=1;fontSize=10;fontColor=#000000;fontStyle=1;labelBackgroundColor=none;" value="1.4: mostrarDatos()" vertex="1">
       <mxGeometry height="20" width="160" x="385" y="335" as="geometry" />
     </mxCell>
     <mxCell id="CUxx-COMM-A14" edge="1" parent="1" source="CUxx-COMM-M14" target="CUxx-COMM-M14" style="endArrow=classic;html=1;rounded=1;strokeWidth=1.5;fontSize=10;strokeColor=#003366;dashed=1;exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0.25;entryY=0;entryDx=0;entryDy=0;" value="">
       <mxGeometry relative="1" as="geometry">
         <mxPoint x="475" y="330" as="sourcePoint" />
         <mxPoint x="435" y="330" as="targetPoint" />
       </mxGeometry>
     </mxCell>
     ```
2. **Posición Respecto a la Línea de Relación:**
   - **Llamadas Secuenciales (Invocaciones):** Se ubican **ARRIBA** de la línea continua de relación con flecha continua (`endArrow=classic`).
   - **Retornos de Datos (Respuestas):** Se ubican **ABAJO** de la línea de relación con flecha a rayas / discontinua (`dashed=1;` / `<------`) orientada de regreso hacia el emisor.
3. **Diferenciación Cromática de Flujos (Solo en Flechas):**  
   - **Regla Estricta de Texto en Negro:** El texto de todas las funciones y mensajes permanece **SIEMPRE en color negro (fontColor=#000000)** para garantizar máxima legibilidad y pulcritud académica formal.
   - **Coloreado Exclusivo en Flechas:** Cada flujo principal de interacción (determinado por su número raíz: Flujo 1, Flujo 2, Flujo 3...) se distingue visualmente **ÚNICAMENTE en la flecha direccional superior (strokeColor)** utilizando la siguiente paleta formal de colores oscuros:
     - **Flujo 1 (Principal / Listado / Consulta):** Azul Marino Oscuro (strokeColor=#003366) o Negro (strokeColor=#000000).
     - **Flujo 2 (Creación / Filtros / Catálogo / Órdenes):** Verde Bosque Oscuro (strokeColor=#005522).
     - **Flujo 3 (Actualización / Adjuntos / Carga Cloud / Edición):** Púrpura / Morado Oscuro (strokeColor=#4B0082).
     - **Flujo 4 (Inspección / Detalle / Visores):** Azul Marino Oscuro (strokeColor=#003366).
     - **Flujo 5 (Eliminación / Baja Lógica / Estado):** Rojo Óxido Oscuro (strokeColor=#8B0000).
4. **Mensajes entre Boundary y Controller (Funciones vs. Endpoints):**
   - Según el estándar formal **UML 2.5+ y PUDS/RUP**, todo mensaje que llega a un objeto receptor representa una invocación de operación (`callOperation`) sobre dicho objeto.
   - Por tanto, la convención académica estándar es utilizar **el nombre del método/función real del Controller en el backend** (`index()`, `store()`, `update()`, `indexByPatient()`, etc.), con parámetros según la regla general `metodo()` o `metodo(parametro)`.
   - Si se requiere documentar la naturaleza REST/HTTP de la comunicación web entre el cliente y el servidor, se puede optar por el endpoint (`GET /ruta`, `POST /ruta`), pero **la preferencia académica estricta son las funciones de los métodos reales del controlador**, asegurando coherencia uniforme con las funciones invocadas en los modelos y entidades.
5. **Validaciones Reflexivas en Controlador:** Se representan con una auto-relación curva sobre el Controller con los mensajes de validación apilados a la izquierda o derecha del bucle.

### 3.2. Estándar para JScript (Enterprise Architect)
Enterprise Architect gestiona las flechas y mensajes mediante conectores de comunicación:
* **Separación Obligatoria en 2 Conectores (Llamadas vs. Retornos):**
  - **Prohibido unificar llamadas y retornos en una sola asociación.**
  - **Conector 1 (Llamadas Secuenciales / Forward):**
    - Creado desde el participante origen hacia el destino (`origen -> destino`).
    - Tipo: `"Communication"` (o `"Association"`).
    - Dirección explícita: `con.Direction = "Source -> Destination";` (garantiza flecha visible hacia el destino).
    - Métodos con sufijo direccional: `1: solicitar() →`.
  - **Conector 2 (Retornos / Respuestas):**
    - Creado desde el participante receptor de regreso hacia el emisor (`destino -> origen`).
    - Tipo: `"Communication"`.
    - Dirección explícita: `con.Direction = "Source -> Destination";` (garantiza flecha visible hacia el emisor original).
    - Estereotipo: `con.Stereotype = "return";`
    - Métodos con prefijo direccional: `← 1.14: 201 Created (consulta)`.
* **Conectores hacia Entidades:** Siempre **unidireccionales** desde el Controlador hacia las Entidades (`Direction = "Source -> Destination"`). Las entidades jamás retornan mensajes ni se conectan entre sí.

---

## 4. 📊 Diagrama de Análisis de Clases (Draw.io)

El Diagrama de Análisis de Clases (VOPC - *View of Participating Classes*) describe las clases del dominio y las fronteras arquitectónicas que participan en la realización de un Caso de Uso.

* **Formato:** Archivo `.drawio` en `docsUML/CUanalisisClase/CUxx_Nombre_CU.drawio`.
* **Geometría de Cajas Rectas (Sin Redondeado):**  
  Todas las clases e interfaces se dibujan como **rectángulos con esquinas rectas (`rounded=0;`)**, sin bordes redondeados (`rounded=1` o `curved=1` estrictamente prohibido en los vértices de las clases).
* **Estructura de Componentes:**
  - `Actor`: `shape=umlActor`.
  - `<<Interface>> [Boundary]`: Atributos de estado (`isListening: Boolean`, `loading: Boolean`) y métodos de eventos (`handleSubmit(): void`).
  - `<<Controller>> [Controller]`: Métodos REST del controlador Laravel con su tipo de retorno (`process(): JsonResponse`).
  - `<<Entity>> [Modelos]`: Atributos reales con tipos PostgreSQL (`Long [PK]`, `String`, `DateTime`, `Boolean`, `Decimal`) y relaciones Eloquent tipadas (`citas(): List`, `usuario(): User`).
* **⚠️ REGLA DE ORO DE RELACIONES Y CARDINALIDADES (INVIOLABLE):**
  - Las relaciones formales UML (**Composición**, **Agregación**, **Herencia / Generalización**, **Asociación**) y sus respectivas cardinalidades (`1`, `0..1`, `0..*`, `1..*`) se diagraman **ÚNICAMENTE ENTRE ENTIDADES**.
  - Las conexiones entre `Actor ➔ Interface`, `Interface ➔ Controller` y `Controller ➔ Entities` se trazan con líneas simples de navegación/dependencia (`endArrow=none;endFill=0`), **SIN cardinalidades ni multiplicidades**.

### 4.1. Regla UML VOPC: Entidades Participantes vs. Conexión con el Controller
* **¿Por qué hay entidades que NO se conectan directamente al Controller?**  
  En la especificación oficial de UML y el Proceso Unificado (PUDS/RUP), el diagrama de análisis de clases representa la **Vista de Clases Participantes (VOPC)** del Caso de Uso. Aquellas entidades que forman parte del agregado del dominio o cuyo ciclo de vida está subordinado a una entidad raíz (por ejemplo, `Diagnostico` respecto a `ConsultaMedica`, o `HistoriaClinica` respecto a `Paciente` y `ConsultaMedica`):
  - **NO requieren ni deben conectarse directamente con una línea artificial al Controller** si el controlador interactúa con ellas a través de la entidad raíz o mediante relaciones Eloquent en cascada.
  - Su presencia en el diagrama es fundamental porque **participan conceptual y estructuralmente** en los datos afectados por el Caso de Uso.
* **No Exigir Paridad 1:1 con Diagramas de Interacción:**  
  Los diagramas de interacción (Secuencia y Comunicación) modelan el **flujo dinámico de mensajes en tiempo de ejecución**, por lo que solo muestran los objetos que reciben o envían llamadas en ese escenario puntual. En cambio, el diagrama de análisis de clases modela la **estructura estática y contexto conceptual**, incluyendo entidades relacionadas que proporcionan el marco de integridad del dominio.

---

## 5. 📂 Archivos de Referencia y Ejemplos de la Skill

La carpeta de la skill almacena diagramas modelo de referencia:
* `.agents/skills/uml-academic-diagrams/examples/`:
  - `CU03_comm_gestionar_bitacora_auditoria.drawio`: Referencia canónica de diagrama de comunicación Draw.io con consultas paginadas, selectores dinámicos, métricas y fix de paginación sobre el conector.
  - `CU07_comm_gestionar_especialidades.drawio`: Referencia canónica de diagrama de comunicación con filtros de catálogo y validaciones de unicidad.
  - `CU16_comm_registrar_consulta_medica.drawio`: Referencia canónica para comunicación con arquitectura BCE limpia (1 Boundary, 1 Controller, múltiples entidades y colores oscuros por flujo).
  - `cu01_secuencia_autenticar_usuarios.png`: Referencia de renderizado de secuencia EA.
* `.agents/skills/uml-academic-diagrams/references/`:
  - `cu04_analisis_gestionar_pacientes.drawio`: Referencia canónica de Análisis de Clases.
  - `CU06_Gestionar_Medicos.drawio`: Referencia de Análisis de Clases con relaciones estructurales de catálogo.

---

## 6. 🚫 Regla de Memoria Multi-Agente para Diagramas
Al trabajar exclusivamente en la generación, corrección o documentación de diagramas (`.drawio`, `.js` en `docsUML/`, `.puml`):
* **NO crear sesiones en `docs/ai/sessions/`.**
* **NO modificar los archivos de relevo (`CURRENT_STATE.md`, `HANDOFF_LATEST.md`, `NEXT_STEPS.md`).**
* La memoria viva persistente se reserva de forma estricta para modificaciones en el código fuente, lógica de negocio o esquema de base de datos.
