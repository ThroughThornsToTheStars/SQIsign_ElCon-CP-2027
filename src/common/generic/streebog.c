// SPDX-License-Identifier: Apache-2.0
#include "streebog.h"
#include <nettle/version.h>
#include <stdlib.h>
#include <string.h>

static void digest(struct streebog512_ctx *ctx, uint8_t out[64])
{
#if NETTLE_VERSION_MAJOR >= 4
    streebog512_digest(ctx, out);
#else
    streebog512_digest(ctx, 64, out);
#endif
}

void streebog_xof_init(streebog_xof_state *s)
{
    streebog512_init(&s->hash);
}

void streebog_xof_absorb(streebog_xof_state *s, const uint8_t *data, size_t n)
{
    if (n) streebog512_update(&s->hash, n, data);
}

void streebog_xof_finalize(streebog_xof_state *s)
{
    digest(&s->hash, s->digest);
    s->next = 1;
    s->offset = sizeof(s->block);
}

void streebog_xof_squeeze(streebog_xof_state *s, uint8_t *out, size_t n)
{
    /* The fips202 streaming interface has no error return. Fail before writing
     * any output on counter exhaustion, even with NDEBUG. */
    uint64_t available = (UINT32_MAX + UINT64_C(1) - s->next) * 64
                       + sizeof(s->block) - s->offset;
    if (n > available) abort();
    while (n) {
        if (s->offset == sizeof(s->block)) {
            uint32_t i = (uint32_t)s->next++;
            uint8_t counter[4] = { i >> 24, i >> 16, i >> 8, i };
            streebog512_init(&s->hash);
            streebog512_update(&s->hash, sizeof(s->digest), s->digest);
            streebog512_update(&s->hash, sizeof(counter), counter);
            digest(&s->hash, s->block);
            s->offset = 0;
        }
        size_t take = sizeof(s->block) - s->offset;
        if (take > n) take = n;
        memcpy(out, s->block + s->offset, take);
        s->offset += take;
        out += take;
        n -= take;
    }
}

int streebog_xof(uint8_t *out, size_t len, const uint8_t *data, size_t size)
{
    streebog_xof_state s;
    streebog_xof_init(&s);
    streebog_xof_absorb(&s, data, size);
    streebog_xof_finalize(&s);
    streebog_xof_squeeze(&s, out, len);
    return 0;
}
