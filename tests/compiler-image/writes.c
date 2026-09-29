/* Test shim: records the length of every write(2) to a regular file in $KNOT_WRITE_LOG.
 * Injected with DYLD_INSERT_LIBRARIES so the native compiler binary is observed unmodified.
 * Only the gate's own interposition is here; it changes nothing the program writes. */
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>

static ssize_t logged_write(int fd, const void *buffer, size_t count) {
  ssize_t done = write(fd, buffer, count);
  const char *path = getenv("KNOT_WRITE_LOG");
  struct stat info;
  if (path && fstat(fd, &info) == 0 && S_ISREG(info.st_mode)) {
    int log = open(path, O_WRONLY | O_APPEND | O_CREAT, 0644);
    if (log >= 0) {
      char line[64];
      int n = snprintf(line, sizeof line, "%zu %zd\n", count, done);
      write(log, line, (size_t)n);
      close(log);
    }
  }
  return done;
}

__attribute__((used)) static struct { const void *replacement; const void *original; }
    interposers[] __attribute__((section("__DATA,__interpose"))) = {
        {(const void *)logged_write, (const void *)write}};
