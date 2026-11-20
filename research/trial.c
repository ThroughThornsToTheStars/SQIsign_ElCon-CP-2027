// SPDX-License-Identifier: Apache-2.0
#define _POSIX_C_SOURCE 200809L
#include <api.h>
#include <rng.h>
#include <prng.h>
#include <fips202.h>
#include <encoded_sizes.h>
#ifdef SQI_STREEBOG_HASH
#include <research_profile.h>
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <inttypes.h>

static uint64_t now(void)
{
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) exit(2);
    return (uint64_t)t.tv_sec * 1000000000 + (uint64_t)t.tv_nsec;
}

static long memory_kib(const char *field)
{
    FILE *f = fopen("/proc/self/status", "r");
    if (!f) return -1;
    char line[256];
    long result = -1;
    while (fgets(line, sizeof(line), f)) {
        if (!strncmp(line, field, strlen(field))) {
            result = strtol(line + strlen(field), NULL, 10);
            break;
        }
    }
    fclose(f);
    return result;
}

static void components(const uint8_t *message, size_t length, uint64_t *hash, uint64_t *stream)
{
    uint8_t fields[PUBLICKEY_BYTES + FP2_ENCODED_BYTES] = {0}, digest[CHALLENGE_BYTES], buf[4096];
    /* Feed back one public byte to keep the work observable across LTO. */
    uint64_t start = now();
    for (unsigned j = 0; j < 256; ++j) {
#ifdef SQI_STREEBOG_HASH
        sqi_fs_digest(digest, CHALLENGE_BYTES, fields, sizeof(fields), message, length);
#else
        shake256incctx ctx;
        shake256_inc_init(&ctx);
        shake256_inc_absorb(&ctx, (const uint8_t *)"SQI", 3);
        shake256_inc_absorb(&ctx, fields, sizeof(fields));
        shake256_inc_absorb(&ctx, message, length);
        shake256_inc_finalize(&ctx);
        shake256_inc_squeeze(digest, sizeof(digest), &ctx);
        shake256_inc_ctx_release(&ctx);
#endif
        fields[0] = digest[0];
    }
    *hash = now() - start;
    static volatile uint8_t sink;
    sink = fields[0];
    if (prng_seed()) exit(2);
    start = now();
    for (unsigned j = 0; j < 64; ++j) {
        if (prng_random_bytes(&PRNG_default_domain, buf, sizeof(buf))) exit(2);
        sink = buf[0];
    }
    *stream = now() - start;
    (void)sink;
    prng_clear();
}

int main(int argc, char **argv)
{
    if (argc != 3) return 2;
    char *end;
    unsigned long index = strtoul(argv[2], &end, 10);
    if (*end || index > UINT32_MAX) return 2;
    uint8_t seed[48], msg[64], pk[CRYPTO_PUBLICKEYBYTES], sk[CRYPTO_SECRETKEYBYTES], sig[CRYPTO_BYTES];
    for (size_t i = 0; i < sizeof(seed); ++i) seed[i] = (uint8_t)i;
    for (unsigned i = 0; i < 4; ++i) seed[i] ^= (uint8_t)(index >> (8*i));
    for (size_t i = 0; i < sizeof(msg); ++i) msg[i] = (uint8_t)(index + 7*i);
    size_t mlen = index == 0 ? 0 : sizeof(msg);
    unsigned long long siglen = sizeof(sig);
    if (!strcmp(argv[1], "verify")) {
        if (fread(pk, 1, sizeof(pk), stdin) != sizeof(pk) ||
            fread(sig, 1, sizeof(sig), stdin) != sizeof(sig) || fgetc(stdin) != EOF) return 2;
        return crypto_sign_verify(sig, siglen, msg, mlen, pk) ? 1 : 0;
    }
    randombytes_init(seed, NULL, 256);
    uint64_t start = now();
    if (crypto_sign_keypair(pk, sk)) return 2;
    uint64_t after_key = now();
    if (crypto_sign_signature(sig, &siglen, msg, mlen, sk) || siglen != sizeof(sig)) return 2;
    uint64_t after_sign = now();
    if (crypto_sign_verify(sig, siglen, msg, mlen, pk)) return 2;
    uint64_t after_verify = now();
    if (!strcmp(argv[1], "vector")) {
        if (fwrite(pk, 1, sizeof(pk), stdout) != sizeof(pk) ||
            fwrite(sk, 1, sizeof(sk), stdout) != sizeof(sk) ||
            fwrite(sig, 1, sizeof(sig), stdout) != sizeof(sig)) return 2;
    } else if (!strcmp(argv[1], "trial")) {
        long rss = memory_kib("VmRSS:"), peak = memory_kib("VmHWM:");
        uint64_t hash, stream;
        components(msg, mlen, &hash, &stream);
        printf("%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%ld,%ld,%" PRIu64 ",%" PRIu64 ",%zu,%zu,%zu\n",
               after_key-start, after_sign-after_key, after_verify-after_sign, rss, peak,
               hash, stream, sizeof(pk), sizeof(sk), sizeof(sig));
    } else return 2;
    return 0;
}
