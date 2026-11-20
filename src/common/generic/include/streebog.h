// SPDX-License-Identifier: Apache-2.0
#ifndef SQISIGN_STREEBOG_H
#define SQISIGN_STREEBOG_H
#include <nettle/streebog.h>

typedef struct {
    struct streebog512_ctx hash;
    uint8_t digest[64], block[64];
    uint64_t next;
    size_t offset;
} streebog_xof_state;

/* init, zero or more absorbs, finalize once, then any number of squeezes.
 * Each block is H(H(input) || BE32(i)), i starts at 1. */
void streebog_xof_init(streebog_xof_state *state);
void streebog_xof_absorb(streebog_xof_state *state, const uint8_t *data, size_t len);
void streebog_xof_finalize(streebog_xof_state *state);
void streebog_xof_squeeze(streebog_xof_state *state, uint8_t *out, size_t len);
int streebog_xof(uint8_t *out, size_t len, const uint8_t *data, size_t size);
int streebog_selftest(void);
#endif
