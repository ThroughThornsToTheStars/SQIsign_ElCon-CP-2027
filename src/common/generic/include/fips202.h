// SPDX-License-Identifier: Apache-2.0

#ifndef FIPS202_H
#define FIPS202_H

#include <stddef.h>
#include <stdint.h>

int SHAKE128(unsigned char *output, size_t outputByteLen, const unsigned char *input, size_t inputByteLen);
#define SHAKE256_RATE 136

#ifdef USE_STREEBOG
#include <stdlib.h>
#include "streebog.h"

typedef streebog_xof_state shake256incctx;
typedef streebog_xof_state shake256ctx;
#define SHAKE256 streebog_xof
#define shake256_inc_init streebog_xof_init
#define shake256_inc_absorb streebog_xof_absorb
#define shake256_inc_finalize streebog_xof_finalize

static inline void shake256_inc_squeeze(uint8_t *out, size_t len, shake256incctx *s)
{
    streebog_xof_squeeze(s, out, len);
}

static inline void shake256_inc_ctx_clone(shake256incctx *dst, const shake256incctx *src)
{
    *dst = *src;
}

static inline void shake256_inc_ctx_release(shake256incctx *s)
{
    (void)s; /* Nettle embeds all state in the caller's context. */
}

#define shake256_ctx_clone shake256_inc_ctx_clone
#define shake256_ctx_release shake256_inc_ctx_release

static inline void shake256_absorb(shake256ctx *s, const uint8_t *input, size_t len)
{
    streebog_xof_init(s);
    streebog_xof_absorb(s, input, len);
    streebog_xof_finalize(s);
}

static inline void shake256_squeezeblocks(uint8_t *out, size_t blocks, shake256ctx *s)
{
    if (blocks > SIZE_MAX / SHAKE256_RATE) abort();
    streebog_xof_squeeze(s, out, blocks * SHAKE256_RATE);
}

static inline void shake256(uint8_t *out, size_t len, const uint8_t *input, size_t size)
{
    streebog_xof(out, len, input, size);
}
#else
/* Native context layouts and signatures from the bundled PQClean fips202.c. */
typedef struct { uint64_t *ctx; } shake256incctx;
typedef struct { uint64_t *ctx; } shake256ctx;
int SHAKE256(unsigned char *output, size_t outputByteLen, const unsigned char *input, size_t inputByteLen);
void shake256(uint8_t *out, size_t len, const uint8_t *input, size_t size);
void shake256_inc_init(shake256incctx *s);
void shake256_inc_absorb(shake256incctx *s, const uint8_t *data, size_t len);
void shake256_inc_finalize(shake256incctx *s);
void shake256_inc_squeeze(uint8_t *out, size_t len, shake256incctx *s);
void shake256_inc_ctx_clone(shake256incctx *dst, const shake256incctx *src);
void shake256_inc_ctx_release(shake256incctx *s);
void shake256_absorb(shake256ctx *s, const uint8_t *data, size_t len);
void shake256_squeezeblocks(uint8_t *out, size_t blocks, shake256ctx *s);
void shake256_ctx_clone(shake256ctx *dst, const shake256ctx *src);
void shake256_ctx_release(shake256ctx *s);
#endif

#endif
