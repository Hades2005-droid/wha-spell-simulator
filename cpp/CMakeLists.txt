cmake_minimum_required(VERSION 3.20)

project(shadow_garden_eden_contract LANGUAGES CXX)

option(
  EDEN_FETCH_CATCH2
  "Fetch the pinned Catch2 v3 dependency when it is not installed"
  OFF
)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(Catch2 3 CONFIG QUIET)

if(NOT TARGET Catch2::Catch2WithMain AND EDEN_FETCH_CATCH2)
  include(FetchContent)
  FetchContent_Declare(
    Catch2
    URL https://github.com/catchorg/Catch2/archive/refs/tags/v3.8.1.tar.gz
  )
  FetchContent_MakeAvailable(Catch2)
endif()

if(DEFINED catch2_SOURCE_DIR)
  list(APPEND CMAKE_MODULE_PATH "${catch2_SOURCE_DIR}/extras")
endif()

if(NOT TARGET Catch2::Catch2WithMain)
  message(
    FATAL_ERROR
    "Catch2 v3 is required. Install it or configure with -DEDEN_FETCH_CATCH2=ON."
  )
endif()

add_library(eden_ingest_policy INTERFACE)
target_include_directories(
  eden_ingest_policy
  INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

add_executable(eden_ingest_tests tests/eden_ingest_tests.cpp)
target_link_libraries(eden_ingest_tests PRIVATE eden_ingest_policy Catch2::Catch2WithMain)

include(CTest)
include(Catch)
catch_discover_tests(eden_ingest_tests)
