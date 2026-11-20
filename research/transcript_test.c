// SPDX-License-Identifier: Apache-2.0
// Test adapter for the same typed hash_to_challenge used by Sign and Verify.
#include <encoded_sizes.h>
#include <verification.h>
#include <stdio.h>
#include <stdint.h>

int main(void)
{
    uint8_t key_bytes[PUBLICKEY_BYTES], commitment_bytes[PUBLICKEY_BYTES], message[256];
    if (fread(key_bytes, 1, sizeof(key_bytes), stdin) != sizeof(key_bytes) ||
        fread(commitment_bytes, 1, sizeof(commitment_bytes), stdin) != sizeof(commitment_bytes))
        return 2;
    size_t length = fread(message, 1, sizeof(message), stdin);
    if (ferror(stdin) || fgetc(stdin) != EOF)
        return 2;

    public_key_t pk, commitment;
    public_key_from_bytes(&pk, key_bytes);
    public_key_from_bytes(&commitment, commitment_bytes);
    scalar_t scalar;
    hash_to_challenge(&scalar, &pk, &commitment.curve, message, length);

    // Export the integer limb by limb, independent of native memory order.
    for (size_t i = 0; i < sizeof(scalar); ++i) {
        digit_t limb = scalar[i / sizeof(digit_t)];
        if (putchar((uint8_t)(limb >> (8 * (i % sizeof(digit_t))))) == EOF)
            return 2;
    }
    return 0;
}
