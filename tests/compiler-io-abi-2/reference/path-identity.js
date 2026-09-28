// This query observes filesystem identity; the Bend loader classifies it.
function knot_path_identity(path) {
  const bytes = io_bytes(path);
  if (bytes.includes(0)) return io_fail(process.platform === "darwin" ? 92 : 84);
  const fs = require("fs");
  // The compiler's path/source profile is ASCII. Buffer comparison also keeps
  // directory-entry case and normalization exact on insensitive filesystems.
  const parts = Buffer.from(bytes).toString("utf8").split("/");
  let current = path.startsWith("/") ? "/" : process.cwd();
  try {
    for (const part of parts) {
      if (part === "" || part === ".") continue;
      if (part === "..") {
        current = current.slice(0, current.lastIndexOf("/")) || "/";
        continue;
      }
      const next = current.replace(/\/$/, "") + "/" + part;
      const stat = fs.lstatSync(next);
      if (stat.isSymbolicLink()) return io_done(false);
      const exact = fs.readdirSync(current, { encoding: "buffer" })
        .some(name => Buffer.from(name).equals(Buffer.from(part)));
      if (!exact) return io_done(false);
      current = next;
    }
    return io_done(true);
  } catch (error) {
    if (error.code === "ENOENT" || error.code === "ENOTDIR") {
      return io_done(true);
    }
    return io_fail(typeof error.errno === "number" ? -error.errno : 5);
  }
}

io_eff(CID(inspect), knot_path_identity);
