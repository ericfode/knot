// Bun preload: records the length of every fs.writeSync to a descriptor above 2 in $KNOT_WRITE_LOG.
// The seed's JS runtime writes a byte list with one writeSync per File.write_bytes call.
const fs = require('fs');
const logPath = process.env.KNOT_WRITE_LOG;
const logFd = fs.openSync(logPath, 'a');
const original = fs.writeSync;
fs.writeSync = function (fd, buffer, offset, length, position) {
  const done = original.call(this, fd, buffer, offset, length, position);
  if (fd > 2 && fd !== logFd) original.call(this, logFd, `${length} ${done}\n`);
  return done;
};
