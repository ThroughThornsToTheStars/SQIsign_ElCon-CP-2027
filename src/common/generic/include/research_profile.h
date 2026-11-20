// SPDX-License-Identifier: Apache-2.0
#ifndef SQISIGN_RESEARCH_PROFILE_H
#define SQISIGN_RESEARCH_PROFILE_H

#include <stddef.h>
#include <stdint.h>

typedef struct {
    uint8_t input[63];
    uint8_t cache[64];
    uint32_t blocks;
    size_t offset;
} sqi_stream;

void sqi_stream_init(sqi_stream *stream, const uint8_t seed[48], const char domain[3]);
int sqi_stream_read(sqi_stream *stream, uint8_t *out, size_t len);
/* Caller supplies one of the three protocol challenge sizes. */
int sqi_fs_digest(uint8_t *out, uint8_t n, const uint8_t *fields, size_t fields_len,
                   const uint8_t *message, size_t message_len);

#endif
