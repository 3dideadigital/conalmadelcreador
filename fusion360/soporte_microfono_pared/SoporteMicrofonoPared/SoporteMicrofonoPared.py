"""
Soporte de pared para micrófono de mano (estilo pinza Shure, pero atornillado a la pared).

Qué hace este script:
  1. Crea un diseño nuevo en Fusion 360.
  2. Crea los PARÁMETROS DE USUARIO de la lista de abajo.
  3. Dibuja el soporte con bocetos acotados con esos parámetros.

Después de ejecutarlo NO hace falta tocar el código: cualquier medida se cambia en
    Modificar  >  Cambiar parámetros   (Modify > Change Parameters)
y el modelo se actualiza solo.

Orientación del modelo:
  - El eje del micrófono es el eje Z (vertical). La cabeza del micro va hacia arriba (+Z).
  - La ranura de la pinza mira hacia delante (-Y).
  - La cara trasera de la placa (la que toca la pared) está detrás, en +Y.
  - La base de la pieza está en Z = 0: así se imprime de pie y sin soportes.
"""

import traceback

import adsk.core
import adsk.fusion

# ---------------------------------------------------------------------------
# PARÁMETROS  (nombre, valor o fórmula, unidades, descripción)
# ---------------------------------------------------------------------------
PARAMETROS = [
    # --- Micrófono (medidas tomadas en el micro) ---
    ('mic_diam_ancho', '35 mm', 'mm',
     'Diámetro del micro en la parte ancha (arriba, línea azul de 35)'),
    ('mic_diam_estrecho', '31 mm', 'mm',
     'Diámetro del micro en la parte estrecha (abajo, línea azul de 31)'),
    ('mic_dist_medidas', '95 mm', 'mm',
     'Distancia entre las dos líneas azules (estimada por la foto: mídela)'),
    ('holgura', '0.5 mm', 'mm',
     'Holgura en el diámetro entre micro y pinza'),

    # --- Pinza (el aro que abraza el micro) ---
    ('pinza_alto', '40 mm', 'mm',
     'Altura de la pinza (también es la altura de la placa)'),
    ('pinza_grosor', '3 mm', 'mm',
     'Grosor de la pared de la pinza'),
    ('pinza_apertura', '20 mm', 'mm',
     'Ancho de la ranura frontal (por aquí pasa el cable)'),
    ('pinza_redondeo', '1 mm', 'mm',
     'Redondeo de los bordes de la ranura'),
    ('pinza_diam_arriba', 'mic_diam_ancho + holgura', 'mm',
     'Diámetro interior arriba (calculado)'),
    ('pinza_diam_abajo',
     'pinza_diam_arriba - (mic_diam_ancho - mic_diam_estrecho) * pinza_alto / mic_dist_medidas',
     'mm', 'Diámetro interior abajo (calculado con la conicidad del micro)'),

    # --- Placa de pared ---
    ('dist_eje_pared', '32 mm', 'mm',
     'Distancia de la pared al centro del micro (deja sitio a la cabeza)'),
    ('placa_ancho', '80 mm', 'mm', 'Ancho de la placa de pared'),
    ('placa_grosor', '5 mm', 'mm', 'Grosor de la placa de pared'),
    ('placa_radio', '6 mm', 'mm', 'Redondeo de las esquinas de la placa'),
    ('cuello_ancho', '20 mm', 'mm', 'Ancho del puente entre placa y pinza'),
    ('cuello_radio', '3 mm', 'mm', 'Redondeo de refuerzo entre puente y placa'),

    # --- Tornillos ---
    ('tornillo_diam', '4.5 mm', 'mm', 'Diámetro del agujero (tornillo de 4 mm)'),
    ('tornillo_cabeza_diam', '9 mm', 'mm', 'Diámetro del avellanado (cabeza del tornillo)'),
    ('tornillo_sep', '60 mm', 'mm', 'Distancia entre los dos agujeros'),
]

TOL = 0.001  # tolerancia para comparar posiciones (cm, unidades internas de Fusion)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def valor(design, nombre):
    """Valor actual de un parámetro de usuario, en cm (unidad interna de Fusion)."""
    return design.userParameters.itemByName(nombre).value


def punto(sketch, x, y, z):
    """Convierte un punto del modelo (x, y, z en cm) a coordenadas del boceto."""
    return sketch.modelToSketchSpace(adsk.core.Point3D.create(x, y, z))


def poligono(sketch, puntos):
    """Dibuja un polígono cerrado. El primer punto puede ser sketch.originPoint.
    Cada lado queda restringido horizontal o vertical. Devuelve los puntos del boceto."""
    lineas = sketch.sketchCurves.sketchLines
    vertices = [p if not isinstance(p, tuple) else punto(sketch, *p) for p in puntos]
    creadas = []
    anterior = vertices[0]
    for v in vertices[1:]:
        linea = lineas.addByTwoPoints(anterior, v)
        creadas.append(linea)
        anterior = linea.endSketchPoint
    creadas.append(lineas.addByTwoPoints(anterior, creadas[0].startSketchPoint))

    for linea in creadas:
        a = linea.startSketchPoint.geometry
        b = linea.endSketchPoint.geometry
        if abs(a.x - b.x) < TOL:
            sketch.geometricConstraints.addVertical(linea)
        elif abs(a.y - b.y) < TOL:
            sketch.geometricConstraints.addHorizontal(linea)
    return creadas, [linea.startSketchPoint for linea in creadas]


def cota(sketch, p1, p2, eje, expresion):
    """Cota de distancia entre dos puntos medida a lo largo de un eje del modelo
    ('X', 'Y' o 'Z'), enlazada a una expresión con parámetros."""
    direccion = {'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}[eje]
    a = punto(sketch, 0, 0, 0)
    b = punto(sketch, *direccion)
    if abs(b.x - a.x) > abs(b.y - a.y):
        orientacion = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
    else:
        orientacion = adsk.fusion.DimensionOrientations.VerticalDimensionOrientation
    g1, g2 = p1.geometry, p2.geometry
    texto = adsk.core.Point3D.create((g1.x + g2.x) / 2 + 0.5, (g1.y + g2.y) / 2 + 0.5, 0)
    dim = sketch.sketchDimensions.addDistanceDimension(p1, p2, orientacion, texto, True)
    dim.parameter.expression = expresion
    return dim


def coleccion(elementos):
    col = adsk.core.ObjectCollection.create()
    for e in elementos:
        col.add(e)
    return col


def extremos(arista):
    return arista.startVertex.geometry, arista.endVertex.geometry


def redondear(root, aristas, expresion, nombre):
    fillets = root.features.filletFeatures
    entrada = fillets.createInput()
    radio = adsk.core.ValueInput.createByString(expresion)
    try:
        entrada.edgeSetInputs.addConstantRadiusEdgeSet(coleccion(aristas), radio, False)
    except Exception:  # versiones antiguas de Fusion
        entrada.addConstantRadiusEdgeSet(coleccion(aristas), radio, False)
    fillets.add(entrada).name = nombre


def achaflanar(root, aristas, expresion, nombre):
    chamfers = root.features.chamferFeatures
    distancia = adsk.core.ValueInput.createByString(expresion)
    try:
        entrada = chamfers.createInput2()
        entrada.chamferEdgeSets.addEqualDistanceChamferEdgeSet(coleccion(aristas), distancia, False)
    except Exception:  # versiones antiguas de Fusion
        entrada = chamfers.createInput(coleccion(aristas), False)
        entrada.setToEqualDistance(distancia)
    chamfers.add(entrada).name = nombre


def perfil_cono(root, nombre, expr_radio_abajo, expr_radio_arriba, r_abajo, r_arriba, alto):
    """Boceto en el plano XZ con medio perfil de un tronco de cono (eje = Z).
    Devuelve (boceto, línea del eje) para revolucionarlo."""
    sk = root.sketches.add(root.xZConstructionPlane)
    sk.name = nombre
    origen = sk.originPoint
    lineas, pts = poligono(sk, [origen, (r_abajo, 0, 0), (r_arriba, 0, alto), (0, 0, alto)])
    _, p_abajo, p_arriba, p_eje = pts
    cota(sk, origen, p_eje, 'Z', 'pinza_alto')
    cota(sk, origen, p_abajo, 'X', expr_radio_abajo)
    cota(sk, p_eje, p_arriba, 'X', expr_radio_arriba)
    return sk, lineas[3]


def revolucionar(root, sk, eje, operacion, nombre):
    revolves = root.features.revolveFeatures
    entrada = revolves.createInput(sk.profiles.item(0), eje, operacion)
    entrada.setAngleExtent(False, adsk.core.ValueInput.createByString('360 deg'))
    feature = revolves.add(entrada)
    feature.name = nombre
    sk.isVisible = False
    return feature


# ---------------------------------------------------------------------------
# Script principal
# ---------------------------------------------------------------------------
def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        root = design.rootComponent
        nuevo = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        unir = adsk.fusion.FeatureOperations.JoinFeatureOperation
        cortar = adsk.fusion.FeatureOperations.CutFeatureOperation

        # 0. Parámetros de usuario
        for nombre, expresion, unidades, comentario in PARAMETROS:
            design.userParameters.add(nombre, adsk.core.ValueInput.createByString(expresion),
                                      unidades, comentario)

        H = valor(design, 'pinza_alto')
        D = valor(design, 'dist_eje_pared')
        T = valor(design, 'placa_grosor')
        G = valor(design, 'pinza_grosor')
        r_arriba = valor(design, 'pinza_diam_arriba') / 2
        r_abajo = valor(design, 'pinza_diam_abajo') / 2

        # 1. Anillo exterior: tronco de cono macizo alrededor del eje Z
        sk, eje = perfil_cono(root, 'Perfil anillo exterior',
                              'pinza_diam_abajo / 2 + pinza_grosor',
                              'pinza_diam_arriba / 2 + pinza_grosor',
                              r_abajo + G, r_arriba + G, H)
        revolucionar(root, sk, eje, nuevo, 'Anillo exterior')

        # 2. Placa de pared + cuello (perfil en T visto desde arriba, extruido hacia arriba)
        W = valor(design, 'placa_ancho')
        N = valor(design, 'cuello_ancho')
        sk = root.sketches.add(root.xYConstructionPlane)
        sk.name = 'Perfil placa y cuello'
        origen = sk.originPoint
        _, q = poligono(sk, [(-W / 2, D, 0), (W / 2, D, 0), (W / 2, D - T, 0),
                             (N / 2, D - T, 0), (N / 2, 0, 0), (-N / 2, 0, 0),
                             (-N / 2, D - T, 0), (-W / 2, D - T, 0)])
        cota(sk, q[0], q[1], 'X', 'placa_ancho')
        cota(sk, origen, q[1], 'X', 'placa_ancho / 2')
        cota(sk, origen, q[1], 'Y', 'dist_eje_pared')
        cota(sk, q[1], q[2], 'Y', 'placa_grosor')
        cota(sk, q[0], q[7], 'Y', 'placa_grosor')
        cota(sk, q[4], q[5], 'X', 'cuello_ancho')
        cota(sk, origen, q[4], 'X', 'cuello_ancho / 2')
        cota(sk, q[3], q[4], 'Y', 'dist_eje_pared - placa_grosor')
        extrusion = root.features.extrudeFeatures.addSimple(
            sk.profiles.item(0), adsk.core.ValueInput.createByString('pinza_alto'), unir)
        extrusion.name = 'Placa y cuello'
        sk.isVisible = False

        # 3. Hueco del micrófono: tronco de cono que se resta
        sk, eje = perfil_cono(root, 'Perfil hueco micro',
                              'pinza_diam_abajo / 2', 'pinza_diam_arriba / 2',
                              r_abajo, r_arriba, H)
        revolucionar(root, sk, eje, cortar, 'Hueco micro')

        # 4. Ranura frontal (hacia -Y) para meter el cable
        A = valor(design, 'pinza_apertura')
        L = r_arriba + G + 0.5
        expr_largo = 'pinza_diam_arriba / 2 + pinza_grosor + 5 mm'
        sk = root.sketches.add(root.xYConstructionPlane)
        sk.name = 'Perfil ranura'
        origen = sk.originPoint
        _, s = poligono(sk, [(-A / 2, 0, 0), (A / 2, 0, 0), (A / 2, -L, 0), (-A / 2, -L, 0)])
        cota(sk, s[0], s[1], 'X', 'pinza_apertura')
        cota(sk, origen, s[1], 'X', 'pinza_apertura / 2')
        cota(sk, origen, s[2], 'Y', expr_largo)
        cota(sk, s[1], s[2], 'Y', expr_largo)
        extrudes = root.features.extrudeFeatures
        entrada = extrudes.createInput(sk.profiles.item(0), cortar)
        entrada.setOneSideExtent(adsk.fusion.ThroughAllExtentDefinition.create(),
                                 adsk.fusion.ExtentDirections.PositiveExtentDirection,
                                 adsk.core.ValueInput.createByReal(0))
        extrudes.add(entrada).name = 'Ranura'
        sk.isVisible = False

        # 5. Agujeros de los tornillos (atraviesan la placa en dirección Y)
        S = valor(design, 'tornillo_sep')
        r_tornillo = valor(design, 'tornillo_diam') / 2
        sk = root.sketches.add(root.xZConstructionPlane)
        sk.name = 'Perfil agujeros'
        origen = sk.originPoint
        circulos = sk.sketchCurves.sketchCircles
        for lado in (-1, 1):
            c = circulos.addByCenterRadius(punto(sk, lado * S / 2, 0, H / 2), r_tornillo)
            centro = c.centerSketchPoint
            g = centro.geometry
            dim = sk.sketchDimensions.addDiameterDimension(
                c, adsk.core.Point3D.create(g.x + 0.6, g.y + 0.6, 0), True)
            dim.parameter.expression = 'tornillo_diam'
            cota(sk, origen, centro, 'X', 'tornillo_sep / 2')
            cota(sk, origen, centro, 'Z', 'pinza_alto / 2')
        perfiles = coleccion([sk.profiles.item(i) for i in range(sk.profiles.count)])
        entrada = extrudes.createInput(perfiles, cortar)
        entrada.setSymmetricExtent(adsk.core.ValueInput.createByString('4 * dist_eje_pared'), True,
                                   adsk.core.ValueInput.createByReal(0))
        extrudes.add(entrada).name = 'Agujeros'
        sk.isVisible = False

        cuerpo = root.bRepBodies.item(0)
        cuerpo.name = 'Soporte micro'

        # 6-9. Acabados: si alguno falla, el soporte queda igualmente creado
        avisos = []

        def acabado(nombre, funcion):
            try:
                funcion()
            except Exception:
                avisos.append(nombre)

        def es_avellanado(e):
            geo = adsk.core.Circle3D.cast(e.geometry) or adsk.core.Arc3D.cast(e.geometry)
            if not geo:
                return False
            return abs(geo.center.y - (D - T)) < TOL and abs(geo.radius - r_tornillo) < TOL

        def es_esquina_placa(e):
            a, b = extremos(e)
            return (abs(a.x - b.x) < TOL and abs(a.z - b.z) < TOL
                    and abs(abs(a.x) - W / 2) < TOL and (abs(a.z) < TOL or abs(a.z - H) < TOL))

        def es_union_cuello(e):
            a, b = extremos(e)
            return (abs(a.x - b.x) < TOL and abs(a.y - b.y) < TOL
                    and abs(abs(a.x) - N / 2) < TOL and abs(a.y - (D - T)) < TOL
                    and abs(abs(a.z - b.z) - H) < TOL)

        def es_borde_ranura(e):
            a, b = extremos(e)
            return (abs(abs(a.x) - A / 2) < TOL and abs(abs(b.x) - A / 2) < TOL
                    and a.y < 0 and b.y < 0 and abs(abs(a.z - b.z) - H) < TOL)

        def aristas(condicion):
            return [e for e in root.bRepBodies.item(0).edges if condicion(e)]

        acabado('Avellanado', lambda: achaflanar(
            root, aristas(es_avellanado), '(tornillo_cabeza_diam - tornillo_diam) / 2', 'Avellanado'))
        acabado('Esquinas placa', lambda: redondear(
            root, aristas(es_esquina_placa), 'placa_radio', 'Esquinas placa'))
        acabado('Refuerzo cuello', lambda: redondear(
            root, aristas(es_union_cuello), 'cuello_radio', 'Refuerzo cuello'))
        acabado('Bordes ranura', lambda: redondear(
            root, aristas(es_borde_ranura), 'pinza_redondeo', 'Bordes ranura'))

        app.activeViewport.fit()

        mensaje = ('Soporte creado.\n\n'
                   'Para cambiar medidas: Modificar > Cambiar parámetros.\n'
                   'Para imprimir: clic derecho en el cuerpo "Soporte micro" > Guardar como malla (STL/3MF).')
        if avisos:
            mensaje += ('\n\nNo se pudieron crear estos acabados (el soporte sirve igual): '
                        + ', '.join(avisos))
        ui.messageBox(mensaje, 'Soporte de micrófono')

    except Exception:
        if ui:
            ui.messageBox('Error al crear el soporte:\n{}'.format(traceback.format_exc()))
