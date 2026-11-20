set(SOURCE_FILES_COMMON_SYS 
    randombytes_system.c 
    aes_c.c 
    fips202.c 
    mem.c
)

add_library(sqisign_common_sys ${SOURCE_FILES_COMMON_SYS})
target_include_directories(sqisign_common_sys PRIVATE include ../../include)
target_compile_options(sqisign_common_sys PUBLIC ${C_OPT_FLAGS})

set(SOURCE_FILES_COMMON_TEST 
    randombytes_ctrdrbg.c 
    aes_c.c 
    fips202.c 
    mem.c
)

add_library(sqisign_common_test ${SOURCE_FILES_COMMON_TEST})
target_include_directories(sqisign_common_test PRIVATE include ../include)
target_compile_options(sqisign_common_test PUBLIC ${C_OPT_FLAGS})

if (ENABLE_CT_TESTING)
    target_compile_definitions(sqisign_common_sys PUBLIC ENABLE_CT_TESTING)
    target_compile_definitions(sqisign_common_test PUBLIC ENABLE_CT_TESTING)
endif()

if(USE_STREEBOG)
    foreach(target sqisign_common_sys sqisign_common_test)
        target_sources(${target} PRIVATE streebog.c streebog_selftest.c)
        target_link_libraries(${target} PUBLIC ${NETTLE_LIBRARIES})
    endforeach()
endif()
