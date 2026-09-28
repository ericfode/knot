// Appended to the frozen query helper, without Bend runtime dependencies.
int main(int argc, char **argv) {
  if (argc != 2 || strlen(argv[1]) % 2) return 2;
  size_t n = strlen(argv[1]) / 2;
  char *path = calloc(n + 1, 1);
  if (!path) return 2;
  for (size_t i = 0; i < n; i++) {
    unsigned byte;
    if (sscanf(argv[1] + 2 * i, "%2x", &byte) != 1) { free(path); return 2; }
    path[i] = (char)byte;
  }
  bool canonical = false;
  // The foreign wrapper checks the complete byte range before its C-string query.
  int code = memchr(path, 0, n) ? EILSEQ : knot_path_identity(path, &canonical);
  printf("[%d,%d]\n", code, code ? 0 : canonical);
  free(path);
  return 0;
}
