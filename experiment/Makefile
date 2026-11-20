# Linux x86-64 reference build, with the upstream AES-CTR test RNG.
level ?= lvl1
backend ?= shake
out := build/experiment/$(level)/$(backend)
gf := src/gf/ref/$(level)
pre := src/precomp/ref/$(level)
common := src/common/generic
prime_lvl1 := fp_p1913
prime_lvl3 := fp_p47441
prime_lvl5 := fp_p318233
dirs := src/intbig/ref/generic src/quaternion/ref/generic src/klpt/ref/klptx \
        src/id2iso/ref/id2isox src/protocols/ref/protocolsx $(pre)
inc := include $(common)/include $(gf)/include $(pre)/include src/nistapi/$(level) \
       $(wildcard src/*/ref/include src/*/ref/generic/include)
CPPFLAGS += $(addprefix -I,$(inc)) -DTARGET_AMD64 -DRADIX_64 -DTARGET_OS_UNIX -DSQISIGN_VARIANT=$(level)
CFLAGS += -O3 -DNDEBUG -std=gnu99 -funroll-loops -fvisibility=hidden -MMD -MP
LDLIBS += -lgmp -lm
sources := $(wildcard $(addsuffix /*.c,$(dirs))) $(filter-out %-test.c,$(wildcard src/ec/ref/ecx/*.c)) \
           $(addprefix $(gf)/,fp.c fp2.c $(prime_$(level)).c) src/sqisign.c \
           $(addprefix $(common)/,aes_c.c fips202.c mem.c randombytes_ctrdrbg.c)
ifeq ($(backend),streebog)
CPPFLAGS += -DUSE_STREEBOG $(shell pkg-config --cflags nettle)
LDLIBS += $(shell pkg-config --libs nettle)
sources += $(common)/streebog.c
endif
objects := $(patsubst %.c,$(out)/%.o,$(sources))
test: $(out)/test_sqisign
bench: $(out)/measure
$(out)/measure: $(objects) $(out)/experiment/measure.o
	$(CC) $^ $(LDLIBS) -o $@
$(out)/test_sqisign: $(objects) $(out)/test/test_sqisign.o
	$(CC) $^ $(LDLIBS) -o $@
$(out)/%.o: %.c
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@
-include $(objects:.o=.d) $(wildcard $(out)/test/*.d $(out)/experiment/*.d)
.PHONY: test bench
$(out)/kat: $(objects) $(out)/test/test_kat.o
	$(CC) $^ $(LDLIBS) -o $@
$(out)/selftest: $(out)/src/common/generic/streebog_selftest.o $(out)/src/common/generic/streebog.o $(out)/test/test_streebog.o
	$(CC) $^ $(LDLIBS) -o $@
