// Piezas comunes a todas las plantillas de reels de Con Alma del Creador:
// colores, tipografías, logo cruz-wifi, texto por escenas y cierre de marca.
// Cada plantilla define su propio fondo y animaciones, y llama a
// iniciarPlantilla(dibujarFotograma).

const W = 1080, H = 1920;
const ORO = "#d4af6a";
const ORO_RGB = "212,175,106";
const BLANCO = "#f4efe6";
const lienzo = document.getElementById("lienzo");
const ctx = lienzo.getContext("2d");

const ESTILOS = {
  grande:     { fuente: "500 112px Cormorant", color: BLANCO, alto: 126 },
  oroGrande:  { fuente: "600 140px Cormorant", color: ORO, alto: 158 },
  normal:     { fuente: "500 86px Cormorant", color: BLANCO, alto: 100 },
  oro:        { fuente: "600 104px Cormorant", color: ORO, alto: 118 },
  cita:       { fuente: "italic 500 82px Cormorant", color: BLANCO, alto: 96 },
  referencia: { fuente: "500 34px Montserrat", color: ORO, alto: 90, espaciado: 10 },
};

// --- utilidades -----------------------------------------------------------
const limitar = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const suave = x => { x = limitar(x); return x * x * (3 - 2 * x); };
const salida = x => 1 - Math.pow(1 - limitar(x), 3);
function aleatorio(semilla) {
  return () => { semilla = (semilla * 1664525 + 1013904223) % 4294967296; return semilla / 4294967296; };
}

// --- logo cruz-wifi -------------------------------------------------------
// p: 0→1 progreso de aparición (cruz y luego las tres ondas una a una).
// Con la duración de 1,9 s que usan los cierres, las ondas se encienden a
// 0,95 s, 1,22 s y 1,48 s del inicio (útil para sincronizar campanas).
function dibujarLogo(cx, arriba, alto, p, alfa = 1) {
  const grosor = alto * 0.05;
  const brazo = alto * 0.58;
  const brazoY = arriba + alto * 0.30;
  const pCruz = salida(p / 0.45);
  ctx.save();
  ctx.globalAlpha = alfa;
  ctx.fillStyle = BLANCO;
  // Palo vertical que crece desde abajo.
  const h = alto * pCruz;
  ctx.fillRect(cx - grosor / 2, arriba + alto - h, grosor, h);
  // Travesaño que se abre desde el centro.
  const pBrazo = salida((p - 0.25) / 0.3);
  if (pBrazo > 0) ctx.fillRect(cx - brazo / 2 * pBrazo, brazoY - grosor / 2, brazo * pBrazo, grosor);
  // Ondas wifi sobre la cruz, encendiéndose de dentro hacia fuera.
  ctx.lineCap = "round";
  ctx.lineWidth = grosor * 0.95;
  for (let i = 0; i < 3; i++) {
    const pOnda = salida((p - 0.5 - i * 0.14) / 0.18);
    if (pOnda <= 0) continue;
    const r = alto * (0.12 + i * 0.12);
    ctx.strokeStyle = `rgba(${ORO_RGB},${pOnda})`;
    ctx.shadowColor = `rgba(${ORO_RGB},${0.8 * pOnda})`;
    ctx.shadowBlur = 30 * pOnda;
    ctx.beginPath();
    ctx.arc(cx, arriba - alto * 0.02, r, Math.PI * 1.25, Math.PI * 1.75);
    ctx.stroke();
  }
  ctx.restore();
}

// --- texto ----------------------------------------------------------------
function dibujarLinea(texto, estilo, x, y, alfa, subida) {
  const e = ESTILOS[estilo] || ESTILOS.normal;
  ctx.save();
  ctx.globalAlpha = alfa;
  ctx.font = e.fuente;
  ctx.fillStyle = e.color;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  if (e.espaciado) ctx.letterSpacing = `${e.espaciado}px`;
  ctx.shadowColor = "rgba(0,0,0,0.6)";
  ctx.shadowBlur = 24;
  ctx.fillText(texto, x, y + subida);
  ctx.restore();
}

// Escena de texto: las líneas se centran en esc.y (por defecto 840) y
// aparecen escalonadas, salvo que la escena sea visibleDesdeInicio.
function dibujarEscenaTexto(esc, t) {
  const lineas = esc.lineas;
  const total = lineas.reduce((s, l) => s + (ESTILOS[l.estilo] || ESTILOS.normal).alto, 0);
  let y = (esc.y ?? 840) - total / 2;
  const fuera = 1 - suave((t - (esc.fin - 0.45)) / 0.45);
  lineas.forEach((l, i) => {
    const alto = (ESTILOS[l.estilo] || ESTILOS.normal).alto;
    const centro = y + alto / 2;
    y += alto;
    let entrada = 1;
    if (!esc.visibleDesdeInicio) {
      const desde = esc.inicio + (l.en ?? i * 0.28);
      entrada = salida((t - desde) / 0.7);
    }
    if (entrada <= 0) return;
    dibujarLinea(l.texto, l.estilo, 540, centro, entrada * fuera, 26 * (1 - entrada));
  });
}

// Cierre de marca: logo que se dibuja, lema, nombre e invitación a compartir.
function dibujarCierre(esc, t) {
  const p = (t - esc.inicio) / 1.9;
  const entrada = salida((t - esc.inicio) / 0.5);
  dibujarLogo(540, 470, 360, p, entrada);
  const pTexto = salida((t - esc.inicio - 1.3) / 0.7);
  if (pTexto > 0) {
    dibujarLinea(esc.lema, "referencia", 540, 925, pTexto, 16 * (1 - pTexto));
    dibujarLinea(esc.nombre, "normal", 540, 1010, pTexto, 16 * (1 - pTexto));
  }
  const pCta = salida((t - esc.inicio - 1.9) / 0.7);
  if (pCta > 0) {
    ctx.save();
    ctx.globalAlpha = pCta;
    ctx.strokeStyle = `rgba(${ORO_RGB},0.6)`;
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(440, 1095); ctx.lineTo(640, 1095); ctx.stroke();
    ctx.restore();
    esc.cta.forEach((linea, i) =>
      dibujarLinea(linea, "cita", 540, 1175 + i * 80, pCta, 16 * (1 - pCta)));
  }
}

// Escena activa en el instante t (la última si t se pasa del final).
function escenaEn(guion, t) {
  return guion.escenas.find(e => t >= e.inicio && t < e.fin) || guion.escenas[guion.escenas.length - 1];
}

// --- arranque -------------------------------------------------------------
// window.cargar(guion) prepara fuentes; window.dibujar(t) pinta un fotograma.
// Abriendo la plantilla con ?guion=... se reproduce en bucle como vista previa.
function iniciarPlantilla(dibujarFotograma) {
  let guion = null;
  window.dibujar = t => dibujarFotograma(guion, t);
  window.cargar = async g => {
    guion = g;
    for (const e of Object.values(ESTILOS)) await document.fonts.load(e.fuente);
    await document.fonts.ready;
  };
  const params = new URLSearchParams(location.search);
  if (params.get("guion")) {
    fetch(params.get("guion")).then(r => r.json()).then(async g => {
      await window.cargar(g);
      const inicio = performance.now();
      const bucle = () => {
        window.dibujar(((performance.now() - inicio) / 1000) % g.duracion);
        requestAnimationFrame(bucle);
      };
      bucle();
    });
  }
}
