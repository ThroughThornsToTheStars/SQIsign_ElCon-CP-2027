// SPDX-License-Identifier: Apache-2.0
#include <research_profile.h>
#include <nettle/hmac.h>
#include <nettle/version.h>
#include <stdio.h>
#include <string.h>

static void record(const char *name, const uint8_t *p, size_t n)
{
    printf("%s ", name);
    for (size_t i=0; i<n; ++i) printf("%02x", p[i]);
    putchar('\n');
}

int main(void)
{
    uint8_t seed[48], out[192], fields[80];
    for (unsigned i=0; i<sizeof(fields); ++i) fields[i]=(uint8_t)i;
    memcpy(seed, fields, sizeof(seed));
    struct streebog512_ctx h;
    struct hmac_streebog512_ctx hm;
    static const uint8_t msg[] = "012345678901234567890123456789012345678901234567890123456789012";
    static const uint8_t t[] = {1,0x26,0xbd,0xb8,0x78,0,0xaf,0x21,0x43,0x41,0x45,0x65,0x63,0x78,1,0};
    streebog512_init(&h);
    streebog512_update(&h, 31, msg);
    streebog512_update(&h, sizeof(msg)-1-31, msg+31);
#if NETTLE_VERSION_MAJOR < 4
    streebog512_digest(&h, 64, out);
#else
    streebog512_digest(&h, out);
#endif
    record("rfc6986", out, 64);
    hmac_streebog512_set_key(&hm, 32, seed);
    hmac_streebog512_update(&hm, sizeof(t), t);
#if NETTLE_VERSION_MAJOR < 4
    hmac_streebog512_digest(&hm, 64, out);
#else
    hmac_streebog512_digest(&hm, out);
#endif
    record("rfc7836", out, 64);
#ifdef SQI_STREEBOG_HASH
    for (unsigned n=16; n<=32; n+=8) {
        char name[8];
        snprintf(name, sizeof(name), "fs%u", n);
        sqi_fs_digest(out, (uint8_t)n, fields, sizeof(fields), (const uint8_t *)"hello", 5);
        record(name, out, n);
    }
#endif
#ifdef SQI_RUSSIAN_PRNG
    const char *domains[] = {"key","com","res","def"};
    sqi_stream state, copy;
    for (unsigned i=0; i<4; ++i) {
        sqi_stream_init(&state, seed, domains[i]);
        if (sqi_stream_read(&state, NULL, 0) || sqi_stream_read(&state, out, 13)) return 1;
        copy = state;
        uint8_t tail[179];
        if (sqi_stream_read(&state, out+13, 51) || sqi_stream_read(&state, out+64, 128) ||
            sqi_stream_read(&copy, tail, sizeof(tail)) || memcmp(tail, out+13, sizeof(tail))) return 1;
        record(domains[i], out, sizeof(out));
    }
    sqi_stream_init(&state, seed, "key");
    state.blocks = UINT32_MAX-1;
    memset(out, 0xa5, sizeof(out));
    copy = state;
    if (sqi_stream_read(&state, out, 65) != -1 || memcmp(&state,&copy,sizeof(copy))) return 1;
    for (size_t i=0; i<sizeof(out); ++i) if (out[i]!=0xa5) return 1;
    if (sqi_stream_read(&state,out,63) || sqi_stream_read(&state,out+63,2)!=-1 ||
        sqi_stream_read(&state,out+63,1) || sqi_stream_read(&state,out+64,1)!=-1 ||
        sqi_stream_read(&state,NULL,0)) return 1;
    record("final",out,64);
#endif
    return 0;
}
