# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.13)
project(SQIsign VERSION 2.0 LANGUAGES C ASM)

set(SQISIGN_SO_VERSION "0")
set(CMAKE_C_STANDARD 11)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

include(CTest)

set(SQISIGN_PROFILE BASELINE CACHE STRING "Symmetric component research profile")
set(profile_names BASELINE STREEBOG_HASH RUSSIAN_PRNG COMBINED)
set_property(CACHE SQISIGN_PROFILE PROPERTY STRINGS ${profile_names})
if(NOT SQISIGN_PROFILE IN_LIST profile_names)
    message(FATAL_ERROR "Unknown SQISIGN_PROFILE ${SQISIGN_PROFILE}")
endif()
if(NOT SQISIGN_PROFILE STREQUAL "BASELINE")
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(NETTLE REQUIRED IMPORTED_TARGET nettle>=3.6)
endif()
if(SQISIGN_PROFILE MATCHES "^(STREEBOG_HASH|COMBINED)$")
    add_compile_definitions(SQI_STREEBOG_HASH)
endif()
if(SQISIGN_PROFILE MATCHES "^(RUSSIAN_PRNG|COMBINED)$")
    add_compile_definitions(SQI_RUSSIAN_PRNG)
endif()

option(ENABLE_STRICT "Build with strict compile options." ON)
option(ENABLE_PEDANTIC "Build with pedantic compile options." OFF)
option(ENABLE_TESTS  "Enable compilation of tests." ON)
option(ENABLE_CT_TESTING  "Enable compilation for constant time testing." OFF)
if (ENABLE_CT_TESTING)
  # RelWithDebInfo only: the suppressions need debug info, and NDEBUG must be set — asserts on
  # secret-derived values are themselves secret-dependent branches, so Debug builds cannot pass
  string(TOUPPER "${CMAKE_BUILD_TYPE}" CT_TESTING_BUILD_TYPE)
  if (NOT CT_TESTING_BUILD_TYPE STREQUAL "RELWITHDEBINFO")
    message(FATAL_ERROR "ENABLE_CT_TESTING requires debug info and NDEBUG. Configure with "
            "-DCMAKE_BUILD_TYPE=RelWithDebInfo (see README, 'Constant-time tests').")
  endif()
  include(CheckIncludeFile)
  check_include_file("valgrind/memcheck.h" HAVE_VALGRIND_MEMCHECK_H)
  if (NOT HAVE_VALGRIND_MEMCHECK_H)
    message(FATAL_ERROR "ENABLE_CT_TESTING requires the valgrind development header (valgrind/memcheck.h).")
  endif()
  # Must be global: constant-time annotations (secret poisoning at the RNG, predicate declassification at accepted
  # exceptions such as rejection sampling) live in the individual modules, not only in the common library
  add_compile_definitions(ENABLE_CT_TESTING)
  find_program(VALGRIND_EXECUTABLE valgrind)
  if (NOT VALGRIND_EXECUTABLE)
    message(WARNING "valgrind not found: the constant-time harnesses will build but will not be registered with ctest.")
  endif()
endif()
option(ENABLE_SIGN "Build with sign functionality" ON)
set(GF_RADIX "AUTO" CACHE STRING "Set the radix for the gf module (currently supported values: 32 or 64), or AUTO.")

if (NOT DEFINED SQISIGN_BUILD_TYPE)
  SET(SQISIGN_BUILD_TYPE "ref")
endif()

if (SQISIGN_BUILD_TYPE STREQUAL "ref")
  add_compile_definitions(SQISIGN_BUILD_TYPE_REF SQISIGN_GF_IMPL_REF)
elseif (SQISIGN_BUILD_TYPE STREQUAL "opt")
  add_compile_definitions(SQISIGN_BUILD_TYPE_OPT SQISIGN_GF_IMPL_REF)
elseif (SQISIGN_BUILD_TYPE STREQUAL "broadwell")
  add_compile_definitions(SQISIGN_BUILD_TYPE_BROADWELL SQISIGN_GF_IMPL_SAT64)
elseif (SQISIGN_BUILD_TYPE STREQUAL "arm64")
  add_compile_definitions(SQISIGN_BUILD_TYPE_ARM64 SQISIGN_GF_IMPL_SAT64)
else()
  message(FATAL_ERROR "Unknown SQISIGN_BUILD_TYPE: ${SQISIGN_BUILD_TYPE}")
endif()

SET(SVARIANT_S "")
# >>> ref-only parameter sets (managed by add_parameter_set.py) >>>
if(SQISIGN_BUILD_TYPE STREQUAL "ref" OR SQISIGN_BUILD_TYPE STREQUAL "opt")
    list(APPEND SVARIANT_S)
endif()
# <<< ref-only parameter sets <<<
# >>> asm-capable parameter sets (managed by add_parameter_set.py) >>>
if(SQISIGN_BUILD_TYPE STREQUAL "ref" OR SQISIGN_BUILD_TYPE STREQUAL "opt" OR SQISIGN_BUILD_TYPE STREQUAL "broadwell" OR SQISIGN_BUILD_TYPE STREQUAL "arm64")
    list(APPEND SVARIANT_S "p324_3" "p500_27" "p664_17")
endif()
# <<< asm-capable parameter sets <<<

include(.cmake/flags.cmake)
include(.cmake/sanitizers.cmake)
include(.cmake/target.cmake)
include(.cmake/format.cmake)
include(.cmake/cppcheck.cmake)
include(.cmake/clang-tidy.cmake)
include(.cmake/coverage.cmake)
if(ENABLE_SIGN)
	add_compile_definitions(ENABLE_SIGN)
endif()

set(BM_BINS "" CACHE INTERNAL "List of benchmark binaries")

set(SELECT_IMPL_TYPE ${PROJECT_SOURCE_DIR}/.cmake/impl_type.cmake)
set(SELECT_SQISIGN_VARIANT ${PROJECT_SOURCE_DIR}/.cmake/sqisign_variant.cmake)

set(INC_PUBLIC ${PROJECT_SOURCE_DIR}/include)

add_subdirectory(src)
add_subdirectory(apps)
add_subdirectory(test)

include(.cmake/bm.cmake)

#if(ENABLE_TESTS)
#    enable_testing()
#    add_subdirectory(test)
#endif()

option(SQISIGN_RESEARCH_TOOLS "Build Linux experiment drivers" OFF)
if(SQISIGN_RESEARCH_TOOLS)
    add_subdirectory(research)
endif()
