set(SOURCE_FILES_COMMON_GENERIC
    randombytes_system.c
    fips202.c
    mem.c
    prng.c
    tools.c
)

foreach (SQISIGN_COMMON_TARGET sqisign_common_test sqisign_common_sys)
    add_library(${SQISIGN_COMMON_TARGET} STATIC ${SOURCE_FILES_COMMON_GENERIC})
    if(NOT SQISIGN_PROFILE STREQUAL "BASELINE")
        target_sources(${SQISIGN_COMMON_TARGET} PRIVATE research_profile.c)
        target_link_libraries(${SQISIGN_COMMON_TARGET} PUBLIC PkgConfig::NETTLE)
    endif()
    target_include_directories(${SQISIGN_COMMON_TARGET} PRIVATE include ${INC_PUBLIC})
    target_compile_options(${SQISIGN_COMMON_TARGET} PUBLIC ${C_OPT_FLAGS})
endforeach()

if (ENABLE_TESTS)
    add_subdirectory(test)
endif()
