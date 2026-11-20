// Measure one deterministic trial. A separate process selects the backend.
#define _GNU_SOURCE
#include <api.h>
#include <sig.h>
#include <rng.h>
#include <protocols.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <linux/perf_event.h>
#include <sys/syscall.h>
#include <x86intrin.h>

struct stamp { uint64_t ns, tsc, cycles; };
static int pmu;
static struct stamp stamp(void)
{
    struct timespec ts;
    struct stamp s = {0};
    if (pmu >= 0 && read(pmu, &s.cycles, sizeof(s.cycles)) != sizeof(s.cycles))
        exit(2);
    if (clock_gettime(CLOCK_MONOTONIC_RAW, &ts)) exit(2);
    s.ns = (uint64_t)ts.tv_sec * 1000000000 + ts.tv_nsec;
    _mm_lfence();
    s.tsc = __rdtsc();
    _mm_lfence();
    return s;
}

int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    unsigned trial = strtoul(argv[1], NULL, 10);
    unsigned char seed[48] = {0}, m[32] = {0}, pk[CRYPTO_PUBLICKEYBYTES];
    unsigned char sk[CRYPTO_SECRETKEYBYTES], sm[CRYPTO_BYTES + sizeof(m)];
    unsigned long long len = 0;
    for (unsigned i = 0; i < 4; ++i) seed[i] = trial >> (8*i);
    m[0] = trial;
    randombytes_init(seed, NULL, 256);
    struct perf_event_attr attr = {.type = PERF_TYPE_HARDWARE, .size = sizeof(attr),
        .config = PERF_COUNT_HW_CPU_CYCLES, .exclude_kernel = 1, .exclude_hv = 1,
        .pinned = 1};
    pmu = syscall(SYS_perf_event_open, &attr, 0, -1, -1, 0);
    struct stamp s[4];
    s[0] = stamp();
    int k = sqisign_keypair(pk, sk);
    s[1] = stamp();
    if (k) return 1;
    int sign = sqisign_sign(sm, &len, m, sizeof(m), sk);
    s[2] = stamp();
    if (sign || len != sizeof(sm)) return 1;
    int verify = sqisign_verify(m, sizeof(m), sm, CRYPTO_BYTES, pk);
    s[3] = stamp();
    signature_t sig;
    public_key_t pub;
    signature_init(&sig);
    signature_decode(&sig, sm);
    public_key_decode(&pub, pk);
    int valid = protocols_verif(&sig, &pub, m, sizeof(m));
    signature_finalize(&sig);
    m[0] ^= 1;
    if (verify || valid != 1 || sqisign_verify(m, sizeof(m), sm, CRYPTO_BYTES, pk) != 1)
        return 1;
    const char *op[] = {"KeyGen","Sign","Verify"};
    for (int i=0; i<3; ++i) {
        printf("%u,%s,%"PRIu64",%"PRIu64",", trial, op[i],
               s[i+1].ns-s[i].ns, s[i+1].tsc-s[i].tsc);
        if (pmu >= 0) printf("%"PRIu64, s[i+1].cycles-s[i].cycles);
        puts(",1");
    }
    return 0;
}
