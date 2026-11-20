// SPDX-License-Identifier: Apache-2.0
#include <research_profile.h>
#include <mem.h>
#include <nettle/hmac.h>
#include <nettle/version.h>
#include <string.h>

/* Nettle 4 removed the length argument from the full-digest API. */
#if NETTLE_VERSION_MAJOR >= 4
#define FULL_DIGEST(fn, ctx, out) fn(ctx, out)
#else
#define FULL_DIGEST(fn, ctx, out) fn(ctx, STREEBOG512_DIGEST_SIZE, out)
#endif

#ifdef SQI_STREEBOG_HASH
int
sqi_fs_digest(uint8_t *out, uint8_t n, const uint8_t *fields, size_t fields_len,
              const uint8_t *message, size_t message_len)
{
    static const uint8_t label[] = "SQIsign3-FS-Streebog512-v1";
    struct streebog512_ctx ctx;
    uint8_t digest[64];
    if (n != 16 && n != 24 && n != 32)
        return -1;
    streebog512_init(&ctx);
    streebog512_update(&ctx, sizeof(label) - 1, label);
    streebog512_update(&ctx, 1, &n);
    streebog512_update(&ctx, 3, (const uint8_t *)"SQI");
    streebog512_update(&ctx, fields_len, fields);
    if (message_len)
        streebog512_update(&ctx, message_len, message);
    FULL_DIGEST(streebog512_digest, &ctx, digest);
    memcpy(out, digest, n);
    return 0;
}
#endif

#ifdef SQI_RUSSIAN_PRNG
void
sqi_stream_init(sqi_stream *stream, const uint8_t seed[48], const char domain[3])
{
    static const uint8_t label[] = "SQIsign3-PRNG-v1";
    struct hmac_streebog512_ctx ctx;
    uint8_t digest[64];
    hmac_streebog512_set_key(&ctx, 48, seed);
    hmac_streebog512_update(&ctx, sizeof(label) - 1, label);
    hmac_streebog512_update(&ctx, 3, (const uint8_t *)domain);
    FULL_DIGEST(hmac_streebog512_digest, &ctx, digest);
    sqisign_secure_clear(&ctx, sizeof(ctx));
    memset(stream, 0, sizeof(*stream));
    memcpy(stream->input + 15, digest, 48);
    sqisign_secure_clear(digest, sizeof(digest));
    stream->offset = sizeof(stream->cache);
}

int
sqi_stream_read(sqi_stream *stream, uint8_t *out, size_t len)
{
    const uint64_t remaining = (uint64_t)(UINT32_MAX - stream->blocks) * 64
                             + (sizeof(stream->cache) - stream->offset);
    if (len > remaining)
        return -1;

    while (len) {
        if (stream->offset == sizeof(stream->cache)) {
            struct streebog512_ctx ctx;
            ++stream->blocks;
            for (unsigned j = 0; j < 4; ++j)
                stream->input[j] = (uint8_t)(stream->blocks >> (8 * j));
            streebog512_init(&ctx);
            streebog512_update(&ctx, sizeof(stream->input), stream->input);
            FULL_DIGEST(streebog512_digest, &ctx, stream->cache);
            sqisign_secure_clear(&ctx, sizeof(ctx));
            stream->offset = 0;
        }
        size_t take = sizeof(stream->cache) - stream->offset;
        if (take > len)
            take = len;
        memcpy(out, stream->cache + stream->offset, take);
        stream->offset += take;
        out += take;
        len -= take;
    }
    return 0;
}
#endif
