// Only the pinned seed's parse_book; no Knot semantics.
import * as fs from "node:fs";
const Bend: any = await import(process.argv[2]);
const rows = process.argv.slice(3).map(file => {
  try {
    Bend.parse_book(Bend.book_nil(), "/tmp/", fs.readFileSync(file, "utf8"), "probe", Object.create(null));
    return { file, ok: true };
  } catch (error: any) {
    const span = error?.spn ?? error?.s ?? error?.span;
    return { file, ok: false, expected: error?.exp ?? String(error?.message ?? error), offset: span?.beg ?? null };
  }
});
console.log(JSON.stringify(rows));
