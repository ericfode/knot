// Seed syntax oracle: runs only the pinned seed's own parse_book on each file, in process.
// usage: bun seedparse.ts <path to the seed's bend.ts> FILE...   -> one JSON array on stdout
import * as fs from "node:fs";
const Bend: any = await import(process.argv[2]);
const out: any[] = [];
for (const f of process.argv.slice(3)) {
  const src = fs.readFileSync(f, "utf8");
  try {
    Bend.parse_book(Bend.book_nil(), "/tmp/", src, "probe", Object.create(null));
    out.push({ f, ok: true });
  } catch (e: any) {
    const s = e?.spn ?? e?.s ?? e?.span;
    out.push({ f, ok: false, exp: e?.exp ?? String(e?.message ?? e).slice(0, 200), beg: s?.beg ?? null });
  }
}
console.log(JSON.stringify(out));
