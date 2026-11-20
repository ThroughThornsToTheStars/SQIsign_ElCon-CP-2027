// SPDX-License-Identifier: Apache-2.0
#include <fips202.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    /* Independent libgcrypt oracle for the experimental counter stream. */
    static const uint8_t message[] =
        "\xd1\xe5\x20\xe2\xe5\xf2\xf0\xe8\x2c\x20\xd1\xf2\xf0\xe8\xe1\xee"
        "\xe6\xe8\x20\xe2\xed\xf3\xf6\xe8\x2c\x20\xe2\xe5\xfe\xf2\xfa\x20"
        "\xf1\x20\xec\xee\xf0\xff\x20\xf1\xf2\xf0\xe5\xeb\xe0\xec\xe8\x20"
        "\xed\xe0\x20\xf5\xf0\xe0\xe1\xf0\xfb\xff\x20\xef\xeb\xfa\xea\xfb"
        "\x20\xc8\xe3\xee\xf0\xe5\xe2\xfb";
    static const uint8_t expected[] =
        "\x45\xc0\xfb\xdb\xf2\xf7\x6a\x59\x5c\xa1\x04\x4f\x71\xeb\x54\xd2"
        "\x53\xed\x65\x8e\x2e\x60\xc3\x8b\x69\x5e\xa9\xe8\x86\xba\x6f\xf5"
        "\xf5\x07\x3a\x00\x2a\x24\x7d\x3c\x1d\x15\x00\xf6\x64\x78\x2a\x20"
        "\x5b\xd0\x39\x7e\x21\x8b\x70\xe5\x14\x78\xcd\x71\x1b\xb5\x2f\x89"
        "\xc5\xd7\xeb\x15\x82\xbc\xcd\xa9\x1e\xf0\xf5\x38\xe0\xf5\xc7\x60"
        "\x3a\x2e\xe4\xa2\x7c\x88\x4a\x7e\x18\xac\x80\x89\x68\x93\xf2\xf9"
        "\xcd\xff\x0a\x4f\xf1\xf9\x03\x19\x9d\xeb\xa0\x0a\x35\x93\x60\xa8"
        "\x26\xdd\x5d\x62\x9a\x9b\x5e\xf2\xce\xe8\x2d\x2b\x88\xb6\xea\x59"
        "\x6a\x98\xac\x93\x7f\x24\x1a\x50\x7a\x92\x4d\xc9\x46\x43\xf0\x39"
        "\xa1\xf3\x9c\x7e\xe1\xcf\x21\x44\xad\xc4\x45\xe5\x11\xbe\x7e\x7d"
        "\x72\x54\xde\x6a\xe4\x9e\x4a\x52\xe6\xad\xf2\x96\x70\x19\x7b\xb0"
        "\x76\x6b\xc8\xe8\x07\x63\xe8\xaa\x3e\x62\x15\xd7\x6b\x6b\x21\xb3";
    uint8_t out[sizeof(expected)-1];
    if (!streebog_selftest()) return 1;
    if (SHAKE256(out, sizeof(out), message, sizeof(message)-1)
        || memcmp(out, expected, sizeof(out))) return 2;
    for (size_t split = 0; split <= sizeof(out); ++split) {
        memset(out, 0, sizeof(out));
        shake256incctx s;
        shake256_inc_init(&s);
        shake256_inc_absorb(&s, NULL, 0);
        shake256_inc_absorb(&s, message, 63);
        shake256_inc_absorb(&s, message+63, sizeof(message)-1-63);
        shake256_inc_finalize(&s);
        shake256_inc_squeeze(NULL, 0, &s);
        shake256_inc_squeeze(out, split, &s);
        shake256_inc_squeeze(out+split, sizeof(out)-split, &s);
        if (memcmp(out, expected, sizeof(out))) return 3;
    }
    shake256ctx blocks, clone;
    shake256_absorb(&blocks, message, sizeof(message)-1);
    shake256_ctx_clone(&clone, &blocks);
    memset(out, 0, sizeof(out));
    shake256_squeezeblocks(out, 1, &clone);
    if (memcmp(out, expected, SHAKE256_RATE)) return 4;
    shake256_ctx_release(&clone);
    shake256_ctx_release(&blocks);
    /* Empty input and the carry into the second counter octet. */
    static const uint8_t block256[] =
        "\x8a\x97\x94\x46\x1c\xd0\x4c\xbc\xe5\x62\xf7\xec\x43\x02\xf4\xba"
        "\x01\x54\x0f\x5b\xf6\xf9\x4f\x26\x56\x57\xb6\x84\x2e\x14\x5e\xaa"
        "\xa0\x57\x86\x7f\x8a\xa0\xdb\xb8\x9d\x0e\x54\x15\xd4\x59\x29\xd1"
        "\x79\x4f\xaa\xb7\x2b\x2c\xfa\x0b\x52\x6f\x89\xd5\xeb\x40\xe4\x21";
    streebog_xof_state empty;
    streebog_xof_init(&empty);
    streebog_xof_finalize(&empty);
    for (unsigned i = 1; i <= 256; ++i)
        streebog_xof_squeeze(&empty, out, 64);
    if (memcmp(out, block256, 64)) return 5;
    puts("RFC 6986 M1/M2 and counter stream: OK");
    return 0;
}
