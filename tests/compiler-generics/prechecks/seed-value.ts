import * as fs from "node:fs";
const Bend: any = await import(process.argv[2]);
const book = Bend.book_nil();
Bend.parse_book(book, "/tmp/", fs.readFileSync(process.argv[3], "utf8"), "", Object.create(null));
Bend.book_valid(book);
const value = Bend.term_lower(Bend.term_snf(book, book.tlds.main.v));
if (value.$ !== "Ctr") throw new Error("expected a constructor result");
console.log(JSON.stringify({constructor: value.k, arity: value.x.length, display: Bend.term_show(value)}));
