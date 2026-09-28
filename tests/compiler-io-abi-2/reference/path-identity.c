#include <dirent.h>
#include <sys/stat.h>

// Missing paths are left to File.open. Every existing component must be an
// exact directory entry and must not be a symlink, including before a '..'.
static int knot_path_identity(const char *path, bool *canonical) {
  *canonical = true;
  char *parts = strdup(path);
  char *current = path[0] == '/' ? strdup("/") : getcwd(NULL, 0);
  if (!parts || !current) {
    int code = errno ? errno : ENOMEM;
    free(parts);
    free(current);
    return code;
  }
  int code = 0;
  char *save = NULL;
  for (char *part = strtok_r(parts, "/", &save); part; part = strtok_r(NULL, "/", &save)) {
    if (strcmp(part, ".") == 0) continue;
    if (strcmp(part, "..") == 0) {
      char *last = strrchr(current, '/');
      if (last) last[last == current ? 1 : 0] = '\0';
      continue;
    }
    size_t n = strlen(current), m = strlen(part);
    char *next = malloc(n + m + 2);
    if (!next) { code = ENOMEM; break; }
    snprintf(next, n + m + 2, "%s%s%s", current, n == 1 ? "" : "/", part);
    struct stat st;
    if (lstat(next, &st) != 0) {
      code = errno;
      free(next);
      break;
    }
    if (S_ISLNK(st.st_mode)) {
      *canonical = false;
      free(next);
      break;
    }
    DIR *directory = opendir(current);
    if (!directory) { code = errno; free(next); break; }
    bool exact = false;
    errno = 0;
    struct dirent *entry;
    while ((entry = readdir(directory)) != NULL) {
      if (strcmp(entry->d_name, part) == 0) { exact = true; break; }
    }
    code = errno;
    if (closedir(directory) != 0 && code == 0) code = errno;
    free(current);
    current = next;
    if (code != 0) break;
    if (!exact) { *canonical = false; break; }
  }
  free(parts);
  free(current);
  return code == ENOENT || code == ENOTDIR ? 0 : code;
}

static void knot_path_identity_call(IoWork *w) {
  bool canonical;
  w->code = knot_path_identity(w->data, &canonical);
  w->word = canonical ? 1 : 0;
}

static Term knot_path_identity_pack(Env e, IoWork *w) {
  free(w->data);
  return w->code ? io_fail(e, w->code, NULL)
    : io_done(e, term_pak(w->word ? CID(True) : CID(False), 0));
}

Term knot_path_identity_run(Env e, Term *f, IoWork *w) {
  w->data = io_cstr(e, f[0], &w->size);
  if (io_nul(w->data, w->size)) {
    w->code = EILSEQ;
    return knot_path_identity_pack(e, w);
  }
  return io_work(w, knot_path_identity_call, knot_path_identity_pack);
}

static void __attribute__((constructor)) knot_path_identity_use(void) {
  io_eff(CID(inspect), knot_path_identity_run, 0);
}
