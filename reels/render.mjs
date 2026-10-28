// Renderiza un guion para Instagram.
//
//   node render.mjs guiones/01-desierto.json
//   node render.mjs guiones/01-desierto.json --solo-musica   (rehace solo el audio)
//   node render.mjs guiones/03-ansiedad.json                 (carrusel)
//
// Reels (vídeo vertical 1080×1920, 30 fps): genera en salida/<nombre>/
// reel.mp4, portada.png, musica.wav y publicacion.txt. Si el guion tiene un
// apartado "musica", se compone una banda sonora original con
// musica/generar.py; si no, el vídeo lleva una pista en silencio.
//
// Carruseles ("formato": "carrusel"): genera una imagen 1080×1350 por
// diapositiva (01.jpg, 02.jpg…) y publicacion.txt.

import { chromium } from "playwright";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const RAIZ = path.dirname(fileURLToPath(import.meta.url));
const FPS = 30;

const rutaGuion = process.argv[2];
const soloMusica = process.argv.includes("--solo-musica");
if (!rutaGuion) {
  console.error("Uso: node render.mjs guiones/<guion>.json");
  process.exit(1);
}
const guion = JSON.parse(await readFile(path.resolve(rutaGuion), "utf8"));
const nombre = path.basename(rutaGuion, ".json");
const carpeta = path.join(RAIZ, "salida", nombre);
await mkdir(carpeta, { recursive: true });

// Abre la plantilla del guion en un navegador sin ventana, servida desde un
// servidor local mínimo para que cargue las fuentes.
async function abrirPlantilla(viewport) {
  const TIPOS = { ".html": "text/html", ".css": "text/css", ".woff2": "font/woff2", ".json": "application/json", ".js": "text/javascript",
    ".jpg": "image/jpeg", ".png": "image/png", ".webp": "image/webp" };
  const servidor = createServer(async (req, res) => {
    const archivo = path.join(RAIZ, decodeURIComponent(new URL(req.url, "http://x").pathname));
    if (!archivo.startsWith(RAIZ) || !existsSync(archivo)) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { "content-type": TIPOS[path.extname(archivo)] || "application/octet-stream" });
    res.end(await readFile(archivo));
  }).listen(0, "127.0.0.1");
  await new Promise(r => servidor.once("listening", r));
  const puerto = servidor.address().port;

  const ejecutable = existsSync("/opt/pw-browsers/chromium") ? { executablePath: "/opt/pw-browsers/chromium" } : {};
  const navegador = await chromium.launch(ejecutable);
  const pagina = await navegador.newPage({ viewport });
  await pagina.goto(`http://127.0.0.1:${puerto}/plantillas/${guion.plantilla}.html`);
  await pagina.evaluate(async g => { document.body.classList.add("render"); await window.cargar(g); }, guion);
  return { pagina, cerrar: async () => { await navegador.close(); servidor.close(); } };
}

async function escribirPublicacion() {
  if (!guion.publicacion) return;
  const p = guion.publicacion;
  const partes = [`TEXTO DE LA PUBLICACIÓN\n\n${p.texto}`];
  if (p.musica) partes.push(`MÚSICA\n${p.musica}`);
  if (p.comentarioFijado) partes.push(`COMENTARIO FIJADO\n${p.comentarioFijado}`);
  await writeFile(path.join(carpeta, "publicacion.txt"), partes.join("\n\n") + "\n");
}

async function renderCarrusel() {
  const { pagina, cerrar } = await abrirPlantilla({ width: 1080, height: 1350 });
  for (let i = 0; i < guion.diapositivas.length; i++) {
    await pagina.evaluate(i => window.mostrar(i), i);
    const archivo = `${String(i + 1).padStart(2, "0")}.jpg`;
    await pagina.locator("#diapositiva").screenshot({ path: path.join(carpeta, archivo), type: "jpeg", quality: 95 });
  }
  await cerrar();
}

async function renderReel() {
  // Vídeo sin audio (se guarda aparte para poder rehacer solo la música).
  const soloVideo = path.join(carpeta, ".video.mp4");
  if (!soloMusica || !existsSync(soloVideo)) {
    const { pagina, cerrar } = await abrirPlantilla({ width: 1080, height: 1920 });

    const fotograma = async t => {
      // dibujar puede ser asíncrono (plantillas que cargan fotogramas o imágenes).
      const datos = await pagina.evaluate(async t => {
        await window.dibujar(t);
        return document.getElementById("lienzo").toDataURL("image/png");
      }, t);
      return Buffer.from(datos.split(",")[1], "base64");
    };

    // Portada (la cuadrícula del perfil recorta el centro en 3:4).
    await writeFile(path.join(carpeta, "portada.png"), await fotograma(guion.portada ?? 1));

    const ffmpeg = spawn("ffmpeg", [
      "-y", "-loglevel", "error",
      "-f", "image2pipe", "-framerate", String(FPS), "-i", "-",
      "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
      "-profile:v", "high",
      soloVideo,
    ], { stdio: ["pipe", "inherit", "inherit"] });
    const terminado = new Promise((ok, mal) => ffmpeg.on("close", c => (c === 0 ? ok() : mal(new Error(`ffmpeg salió con ${c}`)))));

    const total = Math.round(guion.duracion * FPS);
    for (let i = 0; i < total; i++) {
      const png = await fotograma(i / FPS);
      if (!ffmpeg.stdin.write(png)) await new Promise(r => ffmpeg.stdin.once("drain", r));
      if (i % FPS === 0) process.stdout.write(`\r${nombre}: ${Math.round((i / total) * 100)} %`);
    }
    ffmpeg.stdin.end();
    await terminado;
    process.stdout.write(`\r${nombre}: 100 %\n`);
    await cerrar();
  }

  // Música: original si el guion la define; si no, silencio.
  const ejecutar = (cmd, args) => new Promise((ok, mal) =>
    spawn(cmd, args, { stdio: "inherit" }).on("close", c => (c === 0 ? ok() : mal(new Error(`${cmd} salió con ${c}`)))));
  const musica = path.join(carpeta, "musica.wav");
  const audio = guion.musica
    ? (await ejecutar("python3", [path.join(RAIZ, "musica", "generar.py"), path.resolve(rutaGuion), musica]), ["-i", musica])
    : ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"];
  await ejecutar("ffmpeg", [
    "-y", "-loglevel", "error", "-i", soloVideo, ...audio,
    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
    "-shortest", "-movflags", "+faststart", path.join(carpeta, "reel.mp4"),
  ]);
}

if (guion.formato === "carrusel") await renderCarrusel();
else await renderReel();
await escribirPublicacion();
console.log(`Listo: ${path.relative(process.cwd(), carpeta)}/`);
