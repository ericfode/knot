import * as fs from "node:fs";
const Bend: any = await import(process.argv[2]);
const rows = process.argv.slice(3).map(f => {
  try {
    Bend.parse_book(Bend.book_nil(), "/tmp/", fs.readFileSync(f, "utf8"), "probe", Object.create(null));
    return {ok: true};
  } catch (e: any) {
    const span = e?.spn ?? e?.s ?? e?.span;
    return {ok: false, expected: e?.exp ?? String(e?.message ?? e).slice(0, 200), begin: span?.beg ?? null};
  }
});
console.log(JSON.stringify(rows));
