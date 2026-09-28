#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

uint32_t knot_invoke(const char *, size_t, const uint32_t *);
void knot_reset(void);

static uint32_t number(const char *s) {
  char *end;
  errno = 0;
  unsigned long value = strtoul(s, &end, 10);
  if (!*s || *s == '-' || *end || errno || value > UINT32_MAX) {
    fprintf(stderr, "invalid benchmark argument: %s\n", s);
    exit(1);
  }
  return (uint32_t)value;
}

static uint64_t nanoseconds(void) {
  struct timespec now;
  if (clock_gettime(CLOCK_MONOTONIC, &now)) {
    perror("clock_gettime");
    exit(1);
  }
  return (uint64_t)now.tv_sec * UINT64_C(1000000000) + (uint64_t)now.tv_nsec;
}

static void batch(const char *name, size_t argc, const uint32_t *args,
                  uint32_t expected, uint32_t count) {
  for (uint32_t i = 0; i < count; ++i) {
    knot_reset();
    uint32_t result = knot_invoke(name, argc, args);
    if (result != expected) {
      fprintf(stderr, "wrong result: expected %" PRIu32 ", got %" PRIu32 " at call %" PRIu32 "\n",
              expected, result, i);
      exit(1);
    }
  }
}

int main(int argc, char **argv) {
  if (argc < 6 || argc > 262) {
    fputs("usage: worker export expected warmup iterations repeat [ordinals...]\n", stderr);
    return 1;
  }
  uint32_t expected = number(argv[2]), warmup = number(argv[3]);
  uint32_t iterations = number(argv[4]), repeat = number(argv[5]);
  if (!warmup || !iterations || !repeat || repeat > 1000) {
    fputs("invalid benchmark counts\n", stderr);
    return 1;
  }
  uint32_t args[256];
  for (int i = 6; i < argc; ++i) args[i - 6] = number(argv[i]);
  struct timespec resolution;
  if (clock_getres(CLOCK_MONOTONIC, &resolution)) {
    perror("clock_getres");
    return 1;
  }
  batch(argv[1], (size_t)(argc - 6), args, expected, warmup);
  fputs("{\"samples\":[", stdout);
  for (uint32_t i = 0; i < repeat; ++i) {
    uint64_t start = nanoseconds();
    batch(argv[1], (size_t)(argc - 6), args, expected, iterations);
    uint64_t elapsed = nanoseconds() - start;
    if (!elapsed) {
      fputs("batch below timer resolution; increase iterations\n", stderr);
      return 1;
    }
    printf("%s%.6f", i ? "," : "", (double)elapsed / iterations);
  }
  printf("],\"valid\":true,\"result\":%" PRIu32 ",\"checkedCalls\":%" PRIu64 ",\"clockResolutionNs\":%" PRIu64 "}\n",
         expected, (uint64_t)warmup + (uint64_t)repeat * iterations,
         (uint64_t)resolution.tv_sec * UINT64_C(1000000000) + (uint64_t)resolution.tv_nsec);
  return 0;
}
