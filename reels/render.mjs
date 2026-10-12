// Renderiza un guion a vídeo vertical para Instagram (1080×1920, 30 fps).
//
//   node render.mjs guiones/01-desierto.json
//
// Genera en salida/<nombre>/: reel.mp4, portada.png y publicacion.txt.
// La música se añade después en Instagram desde su biblioteca (el vídeo
// lleva una pista de audio en silencio para que la app lo acepte sin problemas).

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
if (!rutaGuion) {
  console.error("Uso: node render.mjs guiones/<guion>.json");
  process.exit(1);
}
const guion = JSON.parse(await readFile(path.resolve(rutaGuion), "utf8"));
const nombre = path.basename(rutaGuion, ".json");
const carpeta = path.join(RAIZ, "salida", nombre);
await mkdir(carpeta, { recursive: true });

// Servidor local mínimo para que la plantilla cargue las fuentes.
const TIPOS = { ".html": "text/html", ".woff2": "font/woff2", ".json": "application/json", ".js": "text/javascript" };
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
const pagina = await navegador.newPage({ viewport: { width: 1080, height: 1920 } });
await pagina.goto(`http://127.0.0.1:${puerto}/plantillas/${guion.plantilla}.html`);
await pagina.evaluate(async g => { document.body.classList.add("render"); await window.cargar(g); }, guion);

const fotograma = async t => {
  const datos = await pagina.evaluate(t => {
    window.dibujar(t);
    return document.getElementById("lienzo").toDataURL("image/png");
  }, t);
  return Buffer.from(datos.split(",")[1], "base64");
};

// Portada (la cuadrícula del perfil recorta el centro en 3:4).
await writeFile(path.join(carpeta, "portada.png"), await fotograma(guion.portada ?? 1));

const salidaMp4 = path.join(carpeta, "reel.mp4");
const ffmpeg = spawn("ffmpeg", [
  "-y", "-loglevel", "error",
  "-f", "image2pipe", "-framerate", String(FPS), "-i", "-",
  "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
  "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
  "-profile:v", "high", "-movflags", "+faststart",
  "-c:a", "aac", "-b:a", "128k", "-shortest",
  salidaMp4,
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

if (guion.publicacion) {
  const p = guion.publicacion;
  await writeFile(path.join(carpeta, "publicacion.txt"),
    `TEXTO DE LA PUBLICACIÓN\n\n${p.texto}\n\nMÚSICA\n${p.musica}\n\nCOMENTARIO FIJADO\n${p.comentarioFijado}\n`);
}

await navegador.close();
servidor.close();
console.log(`Listo: ${path.relative(process.cwd(), carpeta)}/`);
