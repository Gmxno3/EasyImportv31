#!/usr/bin/env node
/**
 * fig_decode — .fig dosyasını (Figma yeni arşiv formatı) Figma AÇMADAN ayrıştırır.
 *
 * Neden var: `master` dalındaki 10 gerçek tasarım (.fig) projenin en büyük eksiği olan
 * "gerçek veri"yi içeriyor (bkz. assistant/DURUM.md §6). Bu araç o veriyi offline çıkarır.
 *
 * Format (tersine mühendislikle doğrulandı):
 *   .fig  = ZIP  →  canvas.fig + thumbnail.png + meta.json + images/<hash>
 *   canvas.fig = "fig-kiwi" + uint32(şema sürümü) + [deflateRaw(kiwi şema)] + [ZSTD(kiwi mesaj)]
 *
 * Kritik noktalar (bunlar olmadan çalışmaz):
 *  1. Şema `kiwi-schema@0.5.0` ile çözülür. 0.4.7 "Invalid type -8" verir — format 0.5.0'da değişmiş.
 *  2. Mesaj gövdesi deflate DEĞİL **zstd**'dir (sihirli bayt 28 b5 2f fd).
 *     Node >= 22.15 `zlib.zstdDecompressSync` ile açılır (harici paket gerekmez).
 *
 * Kullanım:
 *   npm install                       # (bu klasörde, ilk sefer)
 *   node decode.mjs <dosya.fig> [-o cikti.json] [--ozet]
 *
 * Çıktı: { header, nodeChanges:[…], blobs:[…], … } — Figma'nın ham kiwi mesajı.
 */

import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const require = createRequire(import.meta.url);
const pako = require('pako');
const zlib = require('node:zlib');
const kiwi = require('kiwi-schema');
const { FigmaArchiveParser } = await import('fig-kiwi/dist/index.esm.js');

/** .fig bir ZIP'tir; canvas.fig'i geçici bir klasöre çıkarır. */
function figToCanvasBytes(figPath) {
  const dir = mkdtempSync(join(tmpdir(), 'figdecode-'));
  const out = join(dir, 'canvas.fig');
  execFileSync('python3', [
    '-c',
    `import zipfile,sys;open(sys.argv[1],'wb').write(zipfile.ZipFile(sys.argv[2]).read('canvas.fig'))`,
    out,
    figPath,
  ]);
  return new Uint8Array(readFileSync(out));
}

/** .fig → Figma kiwi mesajı. */
export function decodeFig(figPath) {
  const buf = figToCanvasBytes(figPath);
  const { header, files } = FigmaArchiveParser.parseArchive(buf);
  const [schemaChunk, messageChunk] = files;

  const schema = kiwi.decodeBinarySchema(pako.inflateRaw(schemaChunk));
  const compiled = kiwi.compileSchema(schema);

  const c = Buffer.from(messageChunk);
  // zstd sihirli baytı (0xFD2FB528 little-endian); yoksa deflate'a düş.
  const raw =
    c[0] === 0x28 && c[1] === 0xb5
      ? zlib.zstdDecompressSync(c)
      : Buffer.from(pako.inflateRaw(messageChunk));

  const message = compiled.decodeMessage(new Uint8Array(raw));
  return { header, schema, message };
}

function ozet(message) {
  const nc = message.nodeChanges || [];
  const tur = {};
  for (const n of nc) tur[n.type] = (tur[n.type] || 0) + 1;
  const metinler = nc
    .filter((n) => n.type === 'TEXT' && n.textData?.characters)
    .map((n) => n.textData.characters);
  return { dugum: nc.length, turler: tur, metinSayisi: metinler.length, metinler: metinler.slice(0, 20) };
}

// ---------------------------------------------------------------- CLI
// Yalnızca DOĞRUDAN çalıştırıldığında CLI olur; `import` edildiğinde sessiz kalır.
import { pathToFileURL } from 'node:url';
const dogrudanCalisti = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;

if (dogrudanCalisti) {
  const argv = process.argv.slice(2);
  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    console.log('kullanım: node decode.mjs <dosya.fig> [-o cikti.json] [--ozet]');
    process.exit(argv.length === 0 ? 1 : 0);
  }
  const figPath = argv[0];
  const outIdx = argv.indexOf('-o');
  const outPath = outIdx > -1 ? argv[outIdx + 1] : null;
  const sadeceOzet = argv.includes('--ozet');

  const { header, message } = decodeFig(figPath);
  const { dugum, turler, metinSayisi, metinler } = ozet(message);

  console.log(`şema sürümü : ${header.version}`);
  console.log(`düğüm        : ${dugum}`);
  console.log(`türler       : ${JSON.stringify(turler)}`);
  console.log(`metin düğümü : ${metinSayisi}`);

  if (sadeceOzet) {
    if (metinler.length) console.log(`örnek metin  : ${JSON.stringify(metinler)}`);
  } else if (outPath) {
    writeFileSync(
      outPath,
      JSON.stringify(message, (k, v) =>
        v instanceof Uint8Array ? `<bytes:${v.length}>` : typeof v === 'bigint' ? Number(v) : v,
      ),
    );
    console.log(`yazıldı      : ${outPath}`);
  }
}
