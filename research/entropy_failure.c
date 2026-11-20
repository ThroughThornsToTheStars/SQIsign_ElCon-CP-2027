// SPDX-License-Identifier: Apache-2.0
// Test-only entropy provider, linked solely into this executable.
#include <api.h>
#include <rng.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static unsigned requests;
static int available;

int randombytes(unsigned char *dst, unsigned long long n)
{
    ++requests;
    if (!available || n != 48)
        return -1;
    for (size_t i = 0; i < 48; ++i)
        dst[i] = (uint8_t)i;
    return 0;
}

int main(void)
{
    uint8_t pk[CRYPTO_PUBLICKEYBYTES], sk[CRYPTO_SECRETKEYBYTES], sig[CRYPTO_BYTES];
    uint8_t expected_pk[sizeof(pk)], expected_sk[sizeof(sk)], expected_sig[sizeof(sig)];
    memset(expected_pk, 0xa5, sizeof(pk));
    memset(expected_sk, 0x5a, sizeof(sk));
    memset(expected_sig, 0x3c, sizeof(sig));
    memcpy(pk, expected_pk, sizeof(pk));
    memcpy(sk, expected_sk, sizeof(sk));
    if (crypto_sign_keypair(pk, sk) != -1 || requests != 1 ||
        memcmp(pk, expected_pk, sizeof(pk)) || memcmp(sk, expected_sk, sizeof(sk)))
        return 1;

    available = 1;
    if (crypto_sign_keypair(pk, sk) != 0 || requests != 2)
        return 1;
    available = 0;
    unsigned long long siglen = sizeof(sig);
    const uint8_t message[] = {0x42};
    memcpy(sig, expected_sig, sizeof(sig));
    if (crypto_sign_signature(sig, &siglen, message, sizeof(message), sk) != -1 ||
        requests != 3 || siglen != 0 || memcmp(sig, expected_sig, sizeof(sig)))
        return 1;
    puts("KeyGen and Sign propagated root-source failure; output sentinels intact.");
    return 0;
}
